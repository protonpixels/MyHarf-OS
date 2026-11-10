"""Customer persistence and business operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.services.errors import ResourceNotFoundError


def list_customers(db: Session, *, include_archived: bool = False) -> list[Customer]:
    statement = select(Customer).order_by(Customer.id)
    if not include_archived:
        statement = statement.where(Customer.status == "active")
    return list(db.scalars(statement))


def get_customer(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise ResourceNotFoundError("Customer not found")
    return customer


def create_customer(db: Session, data: CustomerCreate) -> Customer:
    customer = Customer(**data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(db: Session, customer_id: int, data: CustomerUpdate) -> Customer:
    customer = get_customer(db, customer_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer


def archive_customer(db: Session, customer_id: int) -> Customer:
    customer = get_customer(db, customer_id)
    customer.status = "archived"
    db.commit()
    db.refresh(customer)
    return customer
