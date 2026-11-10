"""Website diagnostic API schemas."""

from datetime import datetime
from enum import Enum

from pydantic import HttpUrl, model_validator

from app.schemas.common import APIModel
from app.schemas.customer import normalized_required_text


class DiagnosticStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class DiagnosticCreate(APIModel):
    website_url: HttpUrl
    summary: str | None = None


class DiagnosticUpdate(APIModel):
    website_url: HttpUrl | None = None
    status: DiagnosticStatus | None = None
    summary: str | None = None

    @model_validator(mode="after")
    def require_update_field(self) -> "DiagnosticUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field must be supplied")
        return self


class DiagnosticRead(APIModel):
    id: int
    customer_id: int
    website_url: HttpUrl
    status: DiagnosticStatus
    summary: str | None
    created_at: datetime
    updated_at: datetime
