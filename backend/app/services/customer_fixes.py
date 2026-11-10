"""Customer fix ledger persistence, filtering, and relationship validation."""

from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.customer import Customer
from app.models.customer_fix import CustomerFix
from app.models.finding import Finding
from app.models.fix_type import FixType
from app.schemas.fix import (
    CustomerFixCreate,
    CustomerFixStatus,
    CustomerFixUpdate,
    FixComplexity,
    FixPriority,
)
from app.services.errors import InvalidRelationshipError, ResourceConflictError, ResourceNotFoundError


def _get_active_customer(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise ResourceNotFoundError("Customer not found")
    if customer.status != "active":
        raise ResourceConflictError("Cannot create or update a fix for an archived customer")
    return customer


def _get_active_fix_type(db: Session, fix_type_id: int) -> FixType:
    fix_type = db.get(FixType, fix_type_id)
    if fix_type is None:
        raise ResourceNotFoundError("Fix type not found")
    if fix_type.status != "active":
        raise ResourceConflictError("Inactive fix types cannot be assigned to customer fixes")
    return fix_type


def _validate_finding_customer(db: Session, finding_id: int, customer_id: int) -> Finding:
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise ResourceNotFoundError("Finding not found")
    if finding.diagnostic.customer_id != customer_id:
        raise InvalidRelationshipError("Finding must belong to the same customer as the customer fix")
    if finding.status == "archived":
        raise ResourceConflictError("Archived findings cannot be assigned to new customer fixes")
    return finding


def list_customer_fixes(
    db: Session,
    *,
    customer_id: int | None = None,
    finding_id: int | None = None,
    status: CustomerFixStatus | None = None,
    priority: FixPriority | None = None,
    complexity: FixComplexity | None = None,
    include_archived: bool = False,
) -> list[CustomerFix]:
    statement = select(CustomerFix).order_by(CustomerFix.id)
    if customer_id is not None:
        if db.get(Customer, customer_id) is None:
            raise ResourceNotFoundError("Customer not found")
        statement = statement.where(CustomerFix.customer_id == customer_id)
    if finding_id is not None:
        if db.get(Finding, finding_id) is None:
            raise ResourceNotFoundError("Finding not found")
        statement = statement.where(CustomerFix.finding_id == finding_id)
    if status is not None:
        statement = statement.where(CustomerFix.status == status.value)
    if priority is not None:
        statement = statement.where(CustomerFix.priority == priority.value)
    if complexity is not None:
        statement = statement.where(CustomerFix.complexity == complexity.value)
    if not include_archived:
        statement = statement.where(CustomerFix.archived_at.is_(None))
    return list(db.scalars(statement))


def get_customer_fix(db: Session, customer_fix_id: int) -> CustomerFix:
    customer_fix = db.get(CustomerFix, customer_fix_id)
    if customer_fix is None:
        raise ResourceNotFoundError("Customer fix not found")
    return customer_fix


def create_customer_fix(db: Session, customer_id: int, data: CustomerFixCreate) -> CustomerFix:
    _get_active_customer(db, customer_id)
    fix_type = _get_active_fix_type(db, data.fix_type_id)
    if data.finding_id is not None:
        _validate_finding_customer(db, data.finding_id, customer_id)

    customer_fix = CustomerFix(
        customer_id=customer_id,
        finding_id=data.finding_id,
        fix_type_id=fix_type.id,
        title=data.title or fix_type.name,
        description=data.description if data.description is not None else fix_type.description,
        priority=data.priority.value,
        complexity=data.complexity.value,
        status=data.status.value,
        documentation_price_override_cents=data.documentation_price_override_cents,
        implementation_price_override_cents=data.implementation_price_override_cents,
    )
    db.add(customer_fix)
    db.commit()
    db.refresh(customer_fix)
    return customer_fix


def update_customer_fix(db: Session, customer_fix_id: int, data: CustomerFixUpdate) -> CustomerFix:
    customer_fix = get_customer_fix(db, customer_fix_id)
    if customer_fix.archived_at is not None:
        raise ResourceConflictError("Archived customer fixes cannot be updated")
    if customer_fix.customer.status != "active":
        raise ResourceConflictError("Cannot update a fix for an archived customer")

    updates = data.model_dump(exclude_unset=True)
    if "fix_type_id" in updates:
        fix_type = _get_active_fix_type(db, updates.pop("fix_type_id"))
        customer_fix.fix_type_id = fix_type.id
    if "finding_id" in updates:
        finding_id = updates.pop("finding_id")
        if finding_id is not None:
            _validate_finding_customer(db, finding_id, customer_fix.customer_id)
        customer_fix.finding_id = finding_id

    for field, value in updates.items():
        setattr(customer_fix, field, value.value if hasattr(value, "value") else value)
    db.commit()
    db.refresh(customer_fix)
    return customer_fix


def archive_customer_fix(db: Session, customer_fix_id: int) -> CustomerFix:
    customer_fix = get_customer_fix(db, customer_fix_id)
    if customer_fix.archived_at is None:
        customer_fix.archived_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(customer_fix)
    return customer_fix
