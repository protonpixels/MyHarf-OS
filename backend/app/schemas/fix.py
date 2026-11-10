"""Fix catalog and customer fix request/response schemas."""

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from app.schemas.common import APIModel
from app.schemas.customer import normalized_required_text


class FixTypeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class FixPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class FixComplexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CustomerFixStatus(str, Enum):
    IDENTIFIED = "identified"
    DOCUMENTED = "documented"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    DELIVERED = "delivered"


PriceCents = Annotated[int, Field(strict=True, ge=0)]
PositiveId = Annotated[int, Field(strict=True, gt=0)]


class FixTypeCreate(APIModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    documentation_price_cents: PriceCents
    implementation_price_cents: PriceCents
    status: FixTypeStatus = FixTypeStatus.ACTIVE

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return normalized_required_text(value)


class FixTypeUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    documentation_price_cents: PriceCents | None = None
    implementation_price_cents: PriceCents | None = None
    status: FixTypeStatus | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str:
        return normalized_required_text(value)

    @field_validator("documentation_price_cents", "implementation_price_cents", "status")
    @classmethod
    def reject_null_for_non_nullable_fields(cls, value):
        if value is None:
            raise ValueError("must not be null")
        return value

    @model_validator(mode="after")
    def require_update_field(self) -> "FixTypeUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field must be supplied")
        return self


class FixTypeRead(APIModel):
    id: int
    name: str
    description: str | None
    documentation_price_cents: int
    implementation_price_cents: int
    status: FixTypeStatus
    created_at: datetime
    updated_at: datetime


class CustomerFixCreate(APIModel):
    fix_type_id: PositiveId
    finding_id: PositiveId | None = None
    title: str | None = Field(default=None, min_length=1, max_length=250)
    description: str | None = None
    priority: FixPriority = FixPriority.MEDIUM
    complexity: FixComplexity = FixComplexity.MEDIUM
    status: CustomerFixStatus = CustomerFixStatus.IDENTIFIED
    documentation_price_override_cents: PriceCents | None = None
    implementation_price_override_cents: PriceCents | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        return normalized_required_text(value) if value is not None else None


class CustomerFixUpdate(APIModel):
    fix_type_id: PositiveId | None = None
    finding_id: PositiveId | None = None
    title: str | None = Field(default=None, min_length=1, max_length=250)
    description: str | None = None
    priority: FixPriority | None = None
    complexity: FixComplexity | None = None
    status: CustomerFixStatus | None = None
    documentation_price_override_cents: PriceCents | None = None
    implementation_price_override_cents: PriceCents | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("must not be null")
        return normalized_required_text(value)

    @field_validator("fix_type_id", "priority", "complexity", "status")
    @classmethod
    def reject_null_for_non_nullable_fields(cls, value):
        if value is None:
            raise ValueError("must not be null")
        return value

    @model_validator(mode="after")
    def require_update_field(self) -> "CustomerFixUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field must be supplied")
        return self


class CustomerFixRead(APIModel):
    id: int
    customer_id: int
    finding_id: int | None
    fix_type_id: int
    title: str
    description: str | None
    priority: FixPriority
    complexity: FixComplexity
    status: CustomerFixStatus
    documentation_price_override_cents: int | None
    implementation_price_override_cents: int | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
