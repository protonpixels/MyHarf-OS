"""CRUD, validation, relationship, and persistence tests for core records."""

import pytest
from pydantic import ValidationError
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.api.routes.customers import router as customers_router
from app.api.routes.diagnostics import router as diagnostics_router
from app.api.routes.findings import router as findings_router
from app.db.base import Base
from app.models.customer import Customer
from app.models.diagnostic import Diagnostic
from app.models.finding import Finding
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.diagnostic import DiagnosticCreate, DiagnosticStatus, DiagnosticUpdate
from app.schemas.finding import FindingCreate, FindingStatus, FindingUpdate
from app.services import customers, diagnostics, findings
from app.services.errors import ResourceConflictError, ResourceNotFoundError
from app.main import app


def make_customer(db_session, name: str = "Acme") -> Customer:
    return customers.create_customer(db_session, CustomerCreate(name=name))


def make_diagnostic(db_session, customer_id: int, url: str = "https://example.com") -> Diagnostic:
    return diagnostics.create_diagnostic(db_session, customer_id, DiagnosticCreate(website_url=url))


def test_customer_crud_archival_and_persistence(test_session_factory) -> None:
    with test_session_factory() as session:
        customer = customers.create_customer(
            session,
            CustomerCreate(name="  Example Co  ", email="contact@example.com", phone="555-0100"),
        )
        customer_id = customer.id
        assert customer.name == "Example Co"
        assert customer.created_at is not None
        assert customer.updated_at is not None

        updated = customers.update_customer(
            session, customer_id, CustomerUpdate(name="Updated Co", business_name="Example" )
        )
        assert updated.name == "Updated Co"
        assert updated.business_name == "Example"

    with test_session_factory() as session:
        persisted = customers.get_customer(session, customer_id)
        assert persisted.email == "contact@example.com"
        assert [item.id for item in customers.list_customers(session)] == [customer_id]
        archived = customers.archive_customer(session, customer_id)
        assert archived.status == "archived"
        assert customers.list_customers(session) == []
        assert customers.list_customers(session, include_archived=True)[0].id == customer_id


def test_diagnostic_crud_validates_customer_relationship(db_session) -> None:
    customer = make_customer(db_session)
    second_customer = make_customer(db_session, "Other Co")

    with pytest.raises(ResourceNotFoundError, match="Customer not found"):
        diagnostics.create_diagnostic(db_session, 99999, DiagnosticCreate(website_url="https://example.com"))

    diagnostic = make_diagnostic(db_session, customer.id)
    other_diagnostic = make_diagnostic(db_session, second_customer.id, "https://other.example")
    assert diagnostic.customer_id == customer.id
    assert diagnostic.customer.name == "Acme"
    assert [row.id for row in diagnostics.list_diagnostics(db_session, customer.id)] == [diagnostic.id]

    updated = diagnostics.update_diagnostic(
        db_session,
        diagnostic.id,
        DiagnosticUpdate(status=DiagnosticStatus.COMPLETED, summary="Reviewed"),
    )
    assert updated.status == "completed"
    assert updated.summary == "Reviewed"
    assert diagnostics.get_diagnostic(db_session, other_diagnostic.id).customer_id == second_customer.id

    customers.archive_customer(db_session, second_customer.id)
    with pytest.raises(ResourceConflictError, match="archived customer"):
        diagnostics.create_diagnostic(
            db_session, second_customer.id, DiagnosticCreate(website_url="https://example.org")
        )

    archived = diagnostics.archive_diagnostic(db_session, diagnostic.id)
    assert archived.status == "archived"
    assert db_session.get(Diagnostic, diagnostic.id) is not None


def test_finding_crud_and_relationships(db_session) -> None:
    customer = make_customer(db_session)
    diagnostic = make_diagnostic(db_session, customer.id)

    with pytest.raises(ResourceNotFoundError, match="Diagnostic not found"):
        findings.create_finding(db_session, 77777, FindingCreate(title="Broken link"))

    finding = findings.create_finding(
        db_session,
        diagnostic.id,
        FindingCreate(
            title="  Broken link  ",
            description="A link returns an error.",
            page_url="https://example.com/about",
            evidence="404 response",
        ),
    )
    assert finding.title == "Broken link"
    assert finding.diagnostic.id == diagnostic.id
    assert finding.diagnostic.customer_id == customer.id
    second_finding = findings.create_finding(
        db_session, diagnostic.id, FindingCreate(title="Slow page")
    )
    assert [row.id for row in findings.list_findings(db_session, diagnostic.id)] == [
        finding.id,
        second_finding.id,
    ]

    updated = findings.update_finding(
        db_session, finding.id, FindingUpdate(status=FindingStatus.REVIEWED, evidence="Confirmed")
    )
    assert updated.status == "reviewed"
    assert updated.evidence == "Confirmed"
    assert findings.archive_finding(db_session, finding.id).status == "archived"
    assert db_session.get(Finding, finding.id) is not None

    diagnostics.archive_diagnostic(db_session, diagnostic.id)
    with pytest.raises(ResourceConflictError, match="archived diagnostic"):
        findings.create_finding(db_session, diagnostic.id, FindingCreate(title="Another finding"))


def test_database_enforces_foreign_keys_and_restricts_hard_delete(db_session) -> None:
    customer = make_customer(db_session)
    diagnostic = make_diagnostic(db_session, customer.id)
    db_session.add(Finding(diagnostic_id=diagnostic.id, title="A finding"))
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.execute(delete(Customer).where(Customer.id == customer.id))
        db_session.commit()
    db_session.rollback()

    orphan = Diagnostic(customer_id=98765, website_url="https://orphan.example")
    db_session.add(orphan)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: CustomerCreate(name="   "),
        lambda: CustomerCreate(name="Valid", email="not-an-email"),
        lambda: CustomerUpdate(),
        lambda: CustomerUpdate(name=None),
        lambda: DiagnosticCreate(website_url="not a url"),
        lambda: DiagnosticCreate(website_url="https://example.com", customer_id=1),
        lambda: DiagnosticUpdate(),
        lambda: DiagnosticUpdate(status="unknown"),
        lambda: FindingCreate(title="  "),
        lambda: FindingCreate(title="Valid", diagnostic_id=1),
        lambda: FindingUpdate(),
        lambda: FindingUpdate(status="unknown"),
    ],
)
def test_schemas_reject_invalid_input(factory) -> None:
    with pytest.raises(ValidationError):
        factory()


def test_api_is_versioned_and_models_have_constraints() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/health" in paths
    assert "/api/v1/customers" in paths
    assert "/api/v1/customers/{customer_id}/diagnostics" in paths
    assert "/api/v1/diagnostics/{diagnostic_id}/findings" in paths
    assert {"id", "name", "status", "created_at", "updated_at"}.issubset(Base.metadata.tables["customers"].columns.keys())
    assert "customer_id" in Base.metadata.tables["diagnostics"].columns
    assert "diagnostic_id" in Base.metadata.tables["findings"].columns

    for router in (customers_router, diagnostics_router, findings_router):
        assert router.routes
