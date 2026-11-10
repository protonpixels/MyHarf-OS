"""Finding API schemas."""

from datetime import datetime
from enum import Enum

from pydantic import Field, HttpUrl, field_validator, model_validator

from app.schemas.common import APIModel
from app.schemas.customer import normalized_required_text


class FindingStatus(str, Enum):
    IDENTIFIED = "identified"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"
    ARCHIVED = "archived"


class FindingCreate(APIModel):
    title: str = Field(min_length=1, max_length=250)
    description: str | None = None
    page_url: HttpUrl | None = None
    evidence: str | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return normalized_required_text(value)


class FindingUpdate(APIModel):
    title: str | None = Field(default=None, min_length=1, max_length=250)
    description: str | None = None
    page_url: HttpUrl | None = None
    evidence: str | None = None
    status: FindingStatus | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        return normalized_required_text(value)

    @model_validator(mode="after")
    def require_update_field(self) -> "FindingUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field must be supplied")
        return self


class FindingRead(APIModel):
    id: int
    diagnostic_id: int
    title: str
    description: str | None
    page_url: HttpUrl | None
    evidence: str | None
    status: FindingStatus
    created_at: datetime
    updated_at: datetime
