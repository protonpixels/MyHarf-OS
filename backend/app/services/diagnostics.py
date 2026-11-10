"""Diagnostic persistence and business operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.diagnostic import Diagnostic
from app.schemas.diagnostic import DiagnosticCreate, DiagnosticUpdate
from app.services.errors import ResourceConflictError, ResourceNotFoundError


def list_diagnostics(db: Session, customer_id: int) -> list[Diagnostic]:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise ResourceNotFoundError("Customer not found")
    return list(db.scalars(select(Diagnostic).where(Diagnostic.customer_id == customer_id).order_by(Diagnostic.id)))


def get_diagnostic(db: Session, diagnostic_id: int) -> Diagnostic:
    diagnostic = db.get(Diagnostic, diagnostic_id)
    if diagnostic is None:
        raise ResourceNotFoundError("Diagnostic not found")
    return diagnostic


def create_diagnostic(db: Session, customer_id: int, data: DiagnosticCreate) -> Diagnostic:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise ResourceNotFoundError("Customer not found")
    if customer.status != "active":
        raise ResourceConflictError("Cannot create a diagnostic for an archived customer")
    diagnostic = Diagnostic(
        customer_id=customer_id,
        website_url=str(data.website_url),
        summary=data.summary,
    )
    db.add(diagnostic)
    db.commit()
    db.refresh(diagnostic)
    return diagnostic


def update_diagnostic(db: Session, diagnostic_id: int, data: DiagnosticUpdate) -> Diagnostic:
    diagnostic = get_diagnostic(db, diagnostic_id)
    for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(diagnostic, field, str(value) if field == "website_url" else value)
    db.commit()
    db.refresh(diagnostic)
    return diagnostic


def archive_diagnostic(db: Session, diagnostic_id: int) -> Diagnostic:
    diagnostic = get_diagnostic(db, diagnostic_id)
    diagnostic.status = "archived"
    db.commit()
    db.refresh(diagnostic)
    return diagnostic
