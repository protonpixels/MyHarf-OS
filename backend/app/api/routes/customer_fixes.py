"""REST endpoints for customer-specific fixes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.fix import (
    CustomerFixCreate,
    CustomerFixRead,
    CustomerFixStatus,
    CustomerFixUpdate,
    FixComplexity,
    FixPriority,
)
from app.services import customer_fixes

router = APIRouter(tags=["customer fixes"])


def _list_fixes(
    db: Session,
    *,
    customer_id: int | None,
    finding_id: int | None,
    status_filter: CustomerFixStatus | None,
    priority: FixPriority | None,
    complexity: FixComplexity | None,
    include_archived: bool,
) -> list[CustomerFixRead]:
    return customer_fixes.list_customer_fixes(
        db,
        customer_id=customer_id,
        finding_id=finding_id,
        status=status_filter,
        priority=priority,
        complexity=complexity,
        include_archived=include_archived,
    )


@router.get("/fixes", response_model=list[CustomerFixRead])
def list_all_fixes(
    customer_id: int | None = Query(default=None, ge=1),
    finding_id: int | None = Query(default=None, ge=1),
    status_filter: CustomerFixStatus | None = Query(default=None, alias="status"),
    priority: FixPriority | None = None,
    complexity: FixComplexity | None = None,
    include_archived: bool = False,
    db: Session = Depends(get_db),
) -> list[CustomerFixRead]:
    return _list_fixes(
        db,
        customer_id=customer_id,
        finding_id=finding_id,
        status_filter=status_filter,
        priority=priority,
        complexity=complexity,
        include_archived=include_archived,
    )


@router.get("/customers/{customer_id}/fixes", response_model=list[CustomerFixRead])
def list_customer_fixes(
    customer_id: int,
    finding_id: int | None = Query(default=None, ge=1),
    status_filter: CustomerFixStatus | None = Query(default=None, alias="status"),
    priority: FixPriority | None = None,
    complexity: FixComplexity | None = None,
    include_archived: bool = False,
    db: Session = Depends(get_db),
) -> list[CustomerFixRead]:
    return _list_fixes(
        db,
        customer_id=customer_id,
        finding_id=finding_id,
        status_filter=status_filter,
        priority=priority,
        complexity=complexity,
        include_archived=include_archived,
    )


@router.post(
    "/customers/{customer_id}/fixes",
    response_model=CustomerFixRead,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_fix(
    customer_id: int, data: CustomerFixCreate, db: Session = Depends(get_db)
) -> CustomerFixRead:
    return customer_fixes.create_customer_fix(db, customer_id, data)


@router.get("/fixes/{customer_fix_id}", response_model=CustomerFixRead)
def get_customer_fix(customer_fix_id: int, db: Session = Depends(get_db)) -> CustomerFixRead:
    return customer_fixes.get_customer_fix(db, customer_fix_id)


@router.patch("/fixes/{customer_fix_id}", response_model=CustomerFixRead)
def update_customer_fix(
    customer_fix_id: int, data: CustomerFixUpdate, db: Session = Depends(get_db)
) -> CustomerFixRead:
    return customer_fixes.update_customer_fix(db, customer_fix_id, data)


@router.delete("/fixes/{customer_fix_id}", response_model=CustomerFixRead)
def archive_customer_fix(customer_fix_id: int, db: Session = Depends(get_db)) -> CustomerFixRead:
    return customer_fixes.archive_customer_fix(db, customer_fix_id)
