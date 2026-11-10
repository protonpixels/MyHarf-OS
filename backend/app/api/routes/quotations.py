"""REST endpoints for creating and reading quotations."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.quotation import QuotationCreate, QuotationRead, QuotationStatusUpdate
from app.services import quotations

router = APIRouter(tags=["quotations"])


@router.post(
    "/customers/{customer_id}/quotations",
    response_model=QuotationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_quotation(
    customer_id: int, data: QuotationCreate, db: Session = Depends(get_db)
) -> QuotationRead:
    return quotations.create_quotation(db, customer_id, data)


@router.get("/customers/{customer_id}/quotations", response_model=list[QuotationRead])
def list_customer_quotations(customer_id: int, db: Session = Depends(get_db)) -> list[QuotationRead]:
    return quotations.list_customer_quotations(db, customer_id)


@router.get("/quotations/{quotation_id}", response_model=QuotationRead)
def get_quotation(quotation_id: int, db: Session = Depends(get_db)) -> QuotationRead:
    return quotations.get_quotation(db, quotation_id)


@router.patch("/quotations/{quotation_id}/status", response_model=QuotationRead)
def update_quotation_status(
    quotation_id: int,
    data: QuotationStatusUpdate,
    db: Session = Depends(get_db),
) -> QuotationRead:
    return quotations.update_quotation_status(db, quotation_id, data)
