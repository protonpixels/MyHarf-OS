"""Customer API schemas."""

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from app.schemas.common import APIModel


def normalized_required_text(value: str | None) -> str:
    if not isinstance(value, str):
        raise ValueError("must not be null")
    value = value.strip()
    if not value:
        raise ValueError("must not be blank")
    return value


class CustomerCreate(APIModel):
    name: str = Field(min_length=1, max_length=200)
    business_name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str | None = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return normalized_required_text(value)


class CustomerUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    business_name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str | None = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str:
        return normalized_required_text(value)

    @model_validator(mode="after")
    def require_update_field(self) -> "CustomerUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field must be supplied")
        return self


class CustomerRead(APIModel):
    id: int
    name: str
    business_name: str | None
    email: str | None
    phone: str | None
    status: str
    created_at: datetime
    updated_at: datetime
