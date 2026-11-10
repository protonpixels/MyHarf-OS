"""Catalog and customer fix ledger behavior tests."""

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.models.customer_fix import CustomerFix
from app.models.fix_type import FixType
from app.schemas.customer import CustomerCreate
from app.schemas.diagnostic import DiagnosticCreate
from app.schemas.finding import FindingCreate
from app.schemas.fix import (
    CustomerFixCreate,
    CustomerFixStatus,
    CustomerFixUpdate,
    FixComplexity,
    FixPriority,
    FixTypeCreate,
    FixTypeStatus,
    FixTypeUpdate,
)
from app.services import customer_fixes, customers, diagnostics, findings, fix_types
from app.services.errors import (
    InvalidRelationshipError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.main import app


def make_customer(db_session, name: str = "Acme"):
    return customers.create_customer(db_session, CustomerCreate(name=name))


def make_finding(db_session, customer_id: int, title: str = "Slow page"):
    diagnostic = diagnostics.create_diagnostic(
        db_session, customer_id, DiagnosticCreate(website_url="https://example.com")
    )
    return findings.create_finding(db_session, diagnostic.id, FindingCreate(title=title))


def make_fix_type(db_session, name: str = "Image optimization", **values):
    defaults = {
        "name": name,
        "documentation_price_cents": 5000,
        "implementation_price_cents": 12000,
    }
    defaults.update(values)
    return fix_types.create_fix_type(db_session, FixTypeCreate(**defaults))


def test_fix_type_crud_and_deactivation(db_session) -> None:
    fix_type = make_fix_type(db_session, description="Optimize oversized images")
    assert fix_type.status == "active"
    assert fix_type.created_at is not None
    assert fix_type.updated_at is not None
    assert fix_types.list_fix_types(db_session) == [fix_type]

    updated = fix_types.update_fix_type(
        db_session,
        fix_type.id,
        FixTypeUpdate(
            name="Image compression",
            documentation_price_cents=6000,
            implementation_price_cents=13000,
        ),
    )
    assert updated.name == "Image compression"
    assert updated.documentation_price_cents == 6000
    assert updated.implementation_price_cents == 13000

    inactive = fix_types.deactivate_fix_type(db_session, fix_type.id)
    assert inactive.status == "inactive"
    assert fix_types.list_fix_types(db_session) == []
    assert fix_types.list_fix_types(db_session, include_inactive=True)[0].id == fix_type.id
    assert fix_types.get_fix_type(db_session, fix_type.id).status == "inactive"


def test_customer_fixes_support_optional_finding_and_multiple_fixes(db_session) -> None:
    customer = make_customer(db_session)
    finding = make_finding(db_session, customer.id)
    fix_type = make_fix_type(db_session)

    first = customer_fixes.create_customer_fix(
        db_session,
        customer.id,
        CustomerFixCreate(
            fix_type_id=fix_type.id,
            finding_id=finding.id,
            documentation_price_override_cents=0,
            priority=FixPriority.HIGH,
            complexity=FixComplexity.LOW,
        ),
    )
    second = customer_fixes.create_customer_fix(
        db_session,
        customer.id,
        CustomerFixCreate(
            fix_type_id=fix_type.id,
            finding_id=finding.id,
            title="Resize the hero image",
            implementation_price_override_cents=7777,
        ),
    )
    standalone = customer_fixes.create_customer_fix(
        db_session,
        customer.id,
        CustomerFixCreate(fix_type_id=fix_type.id, title="General site cleanup"),
    )

    assert first.finding.id == finding.id
    assert second.finding.id == finding.id
    assert first.customer.id == customer.id
    assert first.fix_type.id == fix_type.id
    assert first.title == fix_type.name
    assert first.description == fix_type.description
    assert first.documentation_price_override_cents == 0
    assert first.implementation_price_override_cents is None
    assert second.documentation_price_override_cents is None
    assert second.implementation_price_override_cents == 7777
    assert standalone.finding_id is None
    assert len(finding.customer_fixes) == 2
    assert CustomerFixCreate.model_validate(
        {
            "fix_type_id": fix_type.id,
            "finding_id": finding.id,
            "status": "tested",
        }
    ).status == CustomerFixStatus.TESTED


def test_finding_customer_ownership_and_inactive_catalog_rules(db_session) -> None:
    customer = make_customer(db_session, "First Co")
    other_customer = make_customer(db_session, "Second Co")
    finding = make_finding(db_session, other_customer.id)
    fix_type = make_fix_type(db_session)

    with pytest.raises(InvalidRelationshipError, match="same customer"):
        customer_fixes.create_customer_fix(
            db_session,
            customer.id,
            CustomerFixCreate(fix_type_id=fix_type.id, finding_id=finding.id),
        )

    with pytest.raises(ResourceNotFoundError, match="Finding not found"):
        customer_fixes.create_customer_fix(
            db_session, customer.id, CustomerFixCreate(fix_type_id=fix_type.id, finding_id=88888)
        )

    existing = customer_fixes.create_customer_fix(
        db_session, other_customer.id, CustomerFixCreate(fix_type_id=fix_type.id, finding_id=finding.id)
    )
    fix_types.deactivate_fix_type(db_session, fix_type.id)
    assert customer_fixes.get_customer_fix(db_session, existing.id).fix_type.status == "inactive"
    with pytest.raises(ResourceConflictError, match="Inactive fix types"):
        customer_fixes.create_customer_fix(
            db_session, customer.id, CustomerFixCreate(fix_type_id=fix_type.id)
        )


def test_customer_fix_updates_keep_overrides_independent(db_session) -> None:
    customer = make_customer(db_session)
    fix_type = make_fix_type(db_session)
    customer_fix = customer_fixes.create_customer_fix(
        db_session,
        customer.id,
        CustomerFixCreate(
            fix_type_id=fix_type.id,
            documentation_price_override_cents=1000,
            implementation_price_override_cents=9000,
        ),
    )

    updated = customer_fixes.update_customer_fix(
        db_session,
        customer_fix.id,
        CustomerFixUpdate(documentation_price_override_cents=None, status=CustomerFixStatus.DOCUMENTED),
    )
    assert updated.documentation_price_override_cents is None
    assert updated.implementation_price_override_cents == 9000
    assert updated.status == "documented"

    updated = customer_fixes.update_customer_fix(
        db_session,
        customer_fix.id,
        CustomerFixUpdate(implementation_price_override_cents=0, priority=FixPriority.URGENT),
    )
    assert updated.documentation_price_override_cents is None
    assert updated.implementation_price_override_cents == 0
    assert updated.priority == "urgent"


def test_customer_fix_filters_and_archival(db_session) -> None:
    first_customer = make_customer(db_session, "First Co")
    second_customer = make_customer(db_session, "Second Co")
    finding = make_finding(db_session, first_customer.id)
    fix_type = make_fix_type(db_session)
    first = customer_fixes.create_customer_fix(
        db_session,
        first_customer.id,
        CustomerFixCreate(
            fix_type_id=fix_type.id,
            finding_id=finding.id,
            status=CustomerFixStatus.APPROVED,
            priority=FixPriority.HIGH,
            complexity=FixComplexity.HIGH,
        ),
    )
    second = customer_fixes.create_customer_fix(
        db_session,
        first_customer.id,
        CustomerFixCreate(fix_type_id=fix_type.id, priority=FixPriority.LOW),
    )
    third = customer_fixes.create_customer_fix(
        db_session,
        second_customer.id,
        CustomerFixCreate(fix_type_id=fix_type.id, complexity=FixComplexity.HIGH),
    )

    filtered = customer_fixes.list_customer_fixes(
        db_session,
        customer_id=first_customer.id,
        finding_id=finding.id,
        status=CustomerFixStatus.APPROVED,
        priority=FixPriority.HIGH,
        complexity=FixComplexity.HIGH,
    )
    assert [item.id for item in filtered] == [first.id]
    assert {item.id for item in customer_fixes.list_customer_fixes(db_session, customer_id=first_customer.id)} == {
        first.id,
        second.id,
    }
    assert [item.id for item in customer_fixes.list_customer_fixes(db_session, finding_id=finding.id)] == [
        first.id
    ]
    assert [
        item.id
        for item in customer_fixes.list_customer_fixes(db_session, status=CustomerFixStatus.APPROVED)
    ] == [first.id]
    assert [item.id for item in customer_fixes.list_customer_fixes(db_session, priority=FixPriority.HIGH)] == [
        first.id
    ]
    assert {item.id for item in customer_fixes.list_customer_fixes(db_session, complexity=FixComplexity.HIGH)} == {
        first.id,
        third.id,
    }
    assert {item.id for item in customer_fixes.list_customer_fixes(db_session)} == {
        first.id,
        second.id,
        third.id,
    }

    archived = customer_fixes.archive_customer_fix(db_session, first.id)
    assert archived.archived_at is not None
    assert archived.status == "approved"
    assert first.id not in {item.id for item in customer_fixes.list_customer_fixes(db_session)}
    assert customer_fixes.get_customer_fix(db_session, first.id).id == first.id
    assert customer_fixes.list_customer_fixes(db_session, include_archived=True)[0].archived_at is not None
    with pytest.raises(ResourceConflictError, match="Archived customer fixes"):
        customer_fixes.update_customer_fix(db_session, first.id, CustomerFixUpdate(priority=FixPriority.LOW))


@pytest.mark.parametrize(
    "factory",
    [
        lambda: FixTypeCreate(name="  ", documentation_price_cents=0, implementation_price_cents=0),
        lambda: FixTypeCreate(name="Valid", documentation_price_cents=-1, implementation_price_cents=0),
        lambda: FixTypeCreate(name="Valid", documentation_price_cents=1.2, implementation_price_cents=0),
        lambda: FixTypeUpdate(),
        lambda: FixTypeUpdate(documentation_price_cents=-1),
        lambda: FixTypeUpdate(status="unknown"),
        lambda: CustomerFixCreate(fix_type_id=1, documentation_price_override_cents=-1),
        lambda: CustomerFixCreate(fix_type_id=1, implementation_price_override_cents=4.5),
        lambda: CustomerFixCreate(fix_type_id=0),
        lambda: CustomerFixCreate(fix_type_id=1, priority="blocker"),
        lambda: CustomerFixCreate(fix_type_id=1, status="queued"),
        lambda: CustomerFixUpdate(),
        lambda: CustomerFixUpdate(fix_type_id=None),
        lambda: CustomerFixUpdate(title="  "),
        lambda: CustomerFixUpdate(implementation_price_override_cents=-1),
    ],
)
def test_fix_schemas_reject_invalid_values(factory) -> None:
    with pytest.raises(ValidationError):
        factory()


def test_database_constraints_and_versioned_endpoints(db_session) -> None:
    with pytest.raises(IntegrityError):
        db_session.add(
            FixType(
                name="Invalid price",
                documentation_price_cents=-1,
                implementation_price_cents=0,
            )
        )
        db_session.commit()
    db_session.rollback()

    customer = make_customer(db_session)
    fix_type = make_fix_type(db_session)
    with pytest.raises(IntegrityError):
        db_session.add(
            CustomerFix(
                customer_id=customer.id,
                fix_type_id=fix_type.id,
                title="Invalid override",
                documentation_price_override_cents=-1,
            )
        )
        db_session.commit()
    db_session.rollback()

    paths = app.openapi()["paths"]
    assert "/api/v1/fix-types" in paths
    assert "/api/v1/fix-types/{fix_type_id}" in paths
    assert "/api/v1/customers/{customer_id}/fixes" in paths
    assert "/api/v1/fixes" in paths
    assert "/api/v1/fixes/{customer_fix_id}" in paths
