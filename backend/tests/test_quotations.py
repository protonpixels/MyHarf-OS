"""Pricing and immutable quotation behavior tests."""

import pytest
from pydantic import ValidationError
from sqlalchemy import event, func, select

from app.models.customer_fix import CustomerFix
from app.models.quotation import Quotation, QuotationItem
from app.schemas.customer import CustomerCreate
from app.schemas.diagnostic import DiagnosticCreate
from app.schemas.finding import FindingCreate
from app.schemas.fix import CustomerFixCreate, CustomerFixUpdate, FixTypeCreate, FixTypeUpdate
from app.schemas.quotation import (
    QuotationCreate,
    QuotationItemSelection,
    QuotationStatus,
    QuotationStatusUpdate,
)
from app.services import customer_fixes, customers, diagnostics, findings, fix_types, quotations
from app.services.errors import (
    InvalidRelationshipError,
    ResourceConflictError,
)
from app.services.pricing import (
    calculate_quotation_totals,
    price_selected_services,
    resolve_documentation_price,
    resolve_implementation_price,
)
from app.main import app


def make_customer(db_session, name: str = "Quotation Customer"):
    return customers.create_customer(db_session, CustomerCreate(name=name))


def make_fix_type(db_session, **values):
    return fix_types.create_fix_type(
        db_session,
        FixTypeCreate(
            name="Page speed work",
            description="Improve a page's loading speed",
            documentation_price_cents=12000,
            implementation_price_cents=30000,
            **values,
        ),
    )


def make_customer_fix(db_session, customer_id: int, fix_type_id: int, **values):
    return customer_fixes.create_customer_fix(
        db_session,
        customer_id,
        CustomerFixCreate(fix_type_id=fix_type_id, **values),
    )


def make_quote_request(*selections: QuotationItemSelection, currency: str = "USD") -> QuotationCreate:
    return QuotationCreate(items=list(selections), currency=currency)


def test_pricing_uses_catalog_defaults_and_independent_overrides(db_session) -> None:
    customer = make_customer(db_session)
    fix_type = make_fix_type(db_session)
    catalog_only = make_customer_fix(db_session, customer.id, fix_type.id)
    docs_override = make_customer_fix(
        db_session,
        customer.id,
        fix_type.id,
        documentation_price_override_cents=7000,
    )
    impl_override = make_customer_fix(
        db_session,
        customer.id,
        fix_type.id,
        implementation_price_override_cents=24000,
    )

    assert resolve_documentation_price(catalog_only) == 12000
    assert resolve_implementation_price(catalog_only) == 30000
    assert resolve_documentation_price(docs_override) == 7000
    assert resolve_implementation_price(docs_override) == 30000
    assert resolve_documentation_price(impl_override) == 12000
    assert resolve_implementation_price(impl_override) == 24000

    db_session.refresh(catalog_only)
    catalog_only.priority = "urgent"
    catalog_only.complexity = "high"
    db_session.commit()
    assert resolve_documentation_price(catalog_only) == 12000
    assert resolve_implementation_price(catalog_only) == 30000


@pytest.mark.parametrize(
    ("includes_docs", "includes_impl", "doc_total", "impl_total", "line_total"),
    [
        (True, False, 12000, 0, 12000),
        (False, True, 0, 30000, 30000),
        (True, True, 12000, 30000, 42000),
    ],
)
def test_documentation_implementation_and_combined_quotation_totals(
    db_session,
    includes_docs: bool,
    includes_impl: bool,
    doc_total: int,
    impl_total: int,
    line_total: int,
) -> None:
    customer = make_customer(db_session)
    fix_type = make_fix_type(db_session)
    customer_fix = make_customer_fix(db_session, customer.id, fix_type.id)

    quotation = quotations.create_quotation(
        db_session,
        customer.id,
        make_quote_request(
            QuotationItemSelection(
                customer_fix_id=customer_fix.id,
                includes_documentation=includes_docs,
                includes_implementation=includes_impl,
            )
        ),
    )

    assert quotation.status == "draft"
    assert quotation.currency == "USD"
    assert quotation.documentation_subtotal_cents == doc_total
    assert quotation.implementation_subtotal_cents == impl_total
    assert quotation.grand_total_cents == line_total
    assert quotation.items[0].documentation_price_cents == doc_total
    assert quotation.items[0].implementation_price_cents == impl_total
    assert quotation.items[0].line_total_cents == line_total


def test_selected_service_prices_are_integer_cents_and_sum_exactly(db_session) -> None:
    customer = make_customer(db_session)
    fix_type = make_fix_type(db_session)
    customer_fix = make_customer_fix(
        db_session,
        customer.id,
        fix_type.id,
        documentation_price_override_cents=0,
        implementation_price_override_cents=777,
    )
    line = price_selected_services(
        customer_fix, includes_documentation=True, includes_implementation=True
    )
    totals = calculate_quotation_totals([line, line])

    assert (line.documentation_price_cents, line.implementation_price_cents, line.line_total_cents) == (
        0,
        777,
        777,
    )
    assert totals.documentation_subtotal_cents == 0
    assert totals.implementation_subtotal_cents == 1554
    assert totals.grand_total_cents == 1554


def test_quotation_rejects_unselected_duplicate_foreign_and_archived_fixes(db_session) -> None:
    customer = make_customer(db_session, "First Co")
    other_customer = make_customer(db_session, "Other Co")
    fix_type = make_fix_type(db_session)
    own_fix = make_customer_fix(db_session, customer.id, fix_type.id)
    foreign_fix = make_customer_fix(db_session, other_customer.id, fix_type.id)
    selection = QuotationItemSelection(
        customer_fix_id=own_fix.id,
        includes_documentation=True,
        includes_implementation=False,
    )

    with pytest.raises(ValidationError, match="at least one service"):
        QuotationItemSelection(
            customer_fix_id=own_fix.id,
            includes_documentation=False,
            includes_implementation=False,
        )
    with pytest.raises(ResourceConflictError, match="only appear once"):
        quotations.create_quotation(db_session, customer.id, make_quote_request(selection, selection))
    with pytest.raises(InvalidRelationshipError, match="belong to the quotation customer"):
        quotations.create_quotation(
            db_session,
            customer.id,
            make_quote_request(
                QuotationItemSelection(
                    customer_fix_id=foreign_fix.id,
                    includes_documentation=True,
                    includes_implementation=False,
                )
            ),
        )

    customer_fixes.archive_customer_fix(db_session, own_fix.id)
    with pytest.raises(ResourceConflictError, match="Archived customer fixes"):
        quotations.create_quotation(db_session, customer.id, make_quote_request(selection))


def test_inactive_fix_type_does_not_block_existing_fix_quotation(db_session) -> None:
    customer = make_customer(db_session)
    fix_type = make_fix_type(db_session)
    customer_fix = make_customer_fix(db_session, customer.id, fix_type.id)
    fix_types.deactivate_fix_type(db_session, fix_type.id)

    quotation = quotations.create_quotation(
        db_session,
        customer.id,
        make_quote_request(
            QuotationItemSelection(
                customer_fix_id=customer_fix.id,
                includes_documentation=True,
                includes_implementation=True,
            )
        ),
    )
    assert quotation.grand_total_cents == 42000


def test_quotation_snapshots_survive_catalog_and_customer_fix_price_changes(db_session) -> None:
    customer = make_customer(db_session)
    fix_type = make_fix_type(db_session)
    customer_fix = make_customer_fix(
        db_session,
        customer.id,
        fix_type.id,
        title="Custom title before quote",
        description="Custom description before quote",
        documentation_price_override_cents=11000,
        implementation_price_override_cents=28000,
    )
    quotation = quotations.create_quotation(
        db_session,
        customer.id,
        make_quote_request(
            QuotationItemSelection(
                customer_fix_id=customer_fix.id,
                includes_documentation=True,
                includes_implementation=True,
            )
        ),
    )
    quote_id = quotation.id

    fix_types.update_fix_type(
        db_session,
        fix_type.id,
        FixTypeUpdate(documentation_price_cents=99000, implementation_price_cents=88000),
    )
    customer_fixes.update_customer_fix(
        db_session,
        customer_fix.id,
        CustomerFixUpdate(
            title="Changed title later",
            description="Changed description later",
            documentation_price_override_cents=77000,
            implementation_price_override_cents=66000,
        ),
    )

    persisted = quotations.get_quotation(db_session, quote_id)
    item = persisted.items[0]
    assert item.fix_name_snapshot == "Custom title before quote"
    assert item.fix_description_snapshot == "Custom description before quote"
    assert item.documentation_price_cents == 11000
    assert item.implementation_price_cents == 28000
    assert item.line_total_cents == 39000
    assert persisted.grand_total_cents == 39000

    item.documentation_price_cents = 1
    with pytest.raises(ValueError, match="immutable snapshots"):
        db_session.commit()
    db_session.rollback()


def test_quotation_status_updates_preserve_financial_history(db_session) -> None:
    customer = make_customer(db_session)
    fix_type = make_fix_type(db_session)
    customer_fix = make_customer_fix(db_session, customer.id, fix_type.id)
    quotation = quotations.create_quotation(
        db_session,
        customer.id,
        make_quote_request(
            QuotationItemSelection(
                customer_fix_id=customer_fix.id,
                includes_documentation=True,
                includes_implementation=False,
            )
        ),
    )
    original_totals = (
        quotation.documentation_subtotal_cents,
        quotation.implementation_subtotal_cents,
        quotation.grand_total_cents,
    )
    updated = quotations.update_quotation_status(
        db_session, quotation.id, QuotationStatusUpdate(status=QuotationStatus.SENT)
    )
    assert updated.status == "sent"
    assert (
        updated.documentation_subtotal_cents,
        updated.implementation_subtotal_cents,
        updated.grand_total_cents,
    ) == original_totals
    assert len(updated.items) == 1

    updated.status = "accepted"
    updated.grand_total_cents += 1
    with pytest.raises(ValueError, match="amounts are immutable"):
        db_session.commit()
    db_session.rollback()


def test_quotation_creation_rolls_back_all_staged_rows_on_failure(db_session, monkeypatch) -> None:
    customer = make_customer(db_session)
    fix_type = make_fix_type(db_session)
    customer_fix = make_customer_fix(db_session, customer.id, fix_type.id)

    def fail_commit():
        raise RuntimeError("simulated database commit failure")

    monkeypatch.setattr(db_session, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="simulated database commit failure"):
        quotations.create_quotation(
            db_session,
            customer.id,
            make_quote_request(
                QuotationItemSelection(
                    customer_fix_id=customer_fix.id,
                    includes_documentation=True,
                    includes_implementation=False,
                )
            ),
        )
    monkeypatch.undo()
    assert db_session.scalar(select(func.count()).select_from(Quotation)) == 0
    assert db_session.scalar(select(func.count()).select_from(QuotationItem)) == 0


@pytest.mark.parametrize(
    "data",
    [
        {"items": []},
        {
            "items": [
                {
                    "customer_fix_id": 1,
                    "includes_documentation": False,
                    "includes_implementation": False,
                }
            ]
        },
        {
            "items": [
                {
                    "customer_fix_id": 1,
                    "includes_documentation": True,
                    "includes_implementation": False,
                }
            ],
            "currency": "US",
        },
        {
            "items": [
                {
                    "customer_fix_id": 1,
                    "includes_documentation": 1,
                    "includes_implementation": False,
                }
            ]
        },
    ],
)
def test_quotation_request_rejects_invalid_selections_and_currency(data) -> None:
    with pytest.raises(ValidationError):
        QuotationCreate(**data)


def test_quotation_endpoints_are_versioned_and_have_no_recalculate_route() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/customers/{customer_id}/quotations" in paths
    assert "/api/v1/quotations/{quotation_id}" in paths
    assert "/api/v1/quotations/{quotation_id}/status" in paths
    assert not any("recalculate" in path for path in paths)
