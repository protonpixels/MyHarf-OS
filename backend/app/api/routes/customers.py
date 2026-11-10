"""REST endpoints for customer records."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.services import customers

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerRead])
def list_customers(
    include_archived: bool = Query(default=False), db: Session = Depends(get_db)
) -> list[CustomerRead]:
    return customers.list_customers(db, include_archived=include_archived)


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)) -> CustomerRead:
    return customers.create_customer(db, data)


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, db: Session = Depends(get_db)) -> CustomerRead:
    return customers.get_customer(db, customer_id)


@router.patch("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int, data: CustomerUpdate, db: Session = Depends(get_db)
) -> CustomerRead:
    return customers.update_customer(db, customer_id, data)


@router.delete("/{customer_id}", response_model=CustomerRead)
def archive_customer(customer_id: int, db: Session = Depends(get_db)) -> CustomerRead:
    return customers.archive_customer(db, customer_id)
