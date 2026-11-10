"""Quotation creation, status management, and immutable history reads."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.customer import Customer
from app.models.customer_fix import CustomerFix
from app.models.quotation import Quotation, QuotationItem
from app.schemas.quotation import QuotationCreate, QuotationStatus, QuotationStatusUpdate
from app.services.errors import InvalidRelationshipError, ResourceConflictError, ResourceNotFoundError
from app.services.pricing import SelectedLinePrices, calculate_quotation_totals, price_selected_services


def create_quotation(db: Session, customer_id: int, data: QuotationCreate) -> Quotation:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise ResourceNotFoundError("Customer not found")
    if customer.status != "active":
        raise ResourceConflictError("Cannot create a quotation for an archived customer")

    requested_ids = [item.customer_fix_id for item in data.items]
    if len(requested_ids) != len(set(requested_ids)):
        raise ResourceConflictError("A customer fix can only appear once in a quotation")

    statement = (
        select(CustomerFix)
        .where(CustomerFix.id.in_(requested_ids))
        .options(selectinload(CustomerFix.fix_type))
        .with_for_update()
    )
    fixes_by_id = {customer_fix.id: customer_fix for customer_fix in db.scalars(statement)}
    missing_ids = [fix_id for fix_id in requested_ids if fix_id not in fixes_by_id]
    if missing_ids:
        raise ResourceNotFoundError(f"Customer fix not found: {missing_ids[0]}")

    selected_lines: list[tuple[CustomerFix, bool, bool, SelectedLinePrices]] = []
    for selection in data.items:
        customer_fix = fixes_by_id[selection.customer_fix_id]
        if customer_fix.customer_id != customer_id:
            raise InvalidRelationshipError("Every customer fix must belong to the quotation customer")
        if customer_fix.archived_at is not None:
            raise ResourceConflictError("Archived customer fixes cannot be quoted")
        prices = price_selected_services(
            customer_fix,
            includes_documentation=selection.includes_documentation,
            includes_implementation=selection.includes_implementation,
        )
        selected_lines.append(
            (customer_fix, selection.includes_documentation, selection.includes_implementation, prices)
        )

    totals = calculate_quotation_totals([line[3] for line in selected_lines])
    quotation = Quotation(
        customer_id=customer_id,
        status=QuotationStatus.DRAFT.value,
        currency=data.currency,
        documentation_subtotal_cents=totals.documentation_subtotal_cents,
        implementation_subtotal_cents=totals.implementation_subtotal_cents,
        grand_total_cents=totals.grand_total_cents,
    )
    db.add(quotation)
    try:
        db.flush()
        for customer_fix, includes_documentation, includes_implementation, prices in selected_lines:
            quotation.items.append(
                QuotationItem(
                    customer_fix_id=customer_fix.id,
                    fix_name_snapshot=customer_fix.title,
                    fix_description_snapshot=customer_fix.description,
                    includes_documentation=includes_documentation,
                    documentation_price_cents=prices.documentation_price_cents,
                    includes_implementation=includes_implementation,
                    implementation_price_cents=prices.implementation_price_cents,
                    line_total_cents=prices.line_total_cents,
                )
            )
        db.commit()
        db.refresh(quotation)
    except IntegrityError as exc:
        db.rollback()
        raise ResourceConflictError("Quotation creation conflicted with an existing record") from exc
    except Exception:
        db.rollback()
        raise
    return quotation


def list_customer_quotations(db: Session, customer_id: int) -> list[Quotation]:
    if db.get(Customer, customer_id) is None:
        raise ResourceNotFoundError("Customer not found")
    statement = (
        select(Quotation)
        .where(Quotation.customer_id == customer_id)
        .options(selectinload(Quotation.items))
        .order_by(Quotation.id.desc())
    )
    return list(db.scalars(statement))


def get_quotation(db: Session, quotation_id: int) -> Quotation:
    statement = (
        select(Quotation)
        .where(Quotation.id == quotation_id)
        .options(selectinload(Quotation.items))
    )
    quotation = db.scalar(statement)
    if quotation is None:
        raise ResourceNotFoundError("Quotation not found")
    return quotation


def update_quotation_status(
    db: Session, quotation_id: int, data: QuotationStatusUpdate
) -> Quotation:
    quotation = get_quotation(db, quotation_id)
    quotation.status = data.status.value
    db.commit()
    db.refresh(quotation)
    return quotation
