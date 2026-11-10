"""Quotation creation, status update, and immutable response schemas."""

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import Field, StrictBool, field_validator, model_validator

from app.schemas.common import APIModel


class QuotationStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


CustomerFixId = Annotated[int, Field(strict=True, gt=0)]


class QuotationItemSelection(APIModel):
    customer_fix_id: CustomerFixId
    includes_documentation: StrictBool
    includes_implementation: StrictBool

    @model_validator(mode="after")
    def require_a_selected_service(self) -> "QuotationItemSelection":
        if not self.includes_documentation and not self.includes_implementation:
            raise ValueError("at least one service must be selected")
        return self


class QuotationCreate(APIModel):
    items: list[QuotationItemSelection] = Field(min_length=1)
    currency: str = Field(default="USD", min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        if isinstance(value, str):
            return value.upper()
        return value


class QuotationStatusUpdate(APIModel):
    status: QuotationStatus


class QuotationItemRead(APIModel):
    id: int
    customer_fix_id: int
    fix_name_snapshot: str
    fix_description_snapshot: str | None
    includes_documentation: bool
    documentation_price_cents: int
    includes_implementation: bool
    implementation_price_cents: int
    line_total_cents: int


class QuotationRead(APIModel):
    id: int
    customer_id: int
    status: QuotationStatus
    currency: str
    documentation_subtotal_cents: int
    implementation_subtotal_cents: int
    grand_total_cents: int
    created_at: datetime
    updated_at: datetime
    items: list[QuotationItemRead]
