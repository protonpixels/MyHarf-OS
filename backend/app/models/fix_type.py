"""Configurable catalog entry describing a type of website fix."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FixType(Base):
    __tablename__ = "fix_types"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_fix_types_name_not_blank"),
        CheckConstraint("documentation_price_cents >= 0", name="ck_fix_types_documentation_price_nonnegative"),
        CheckConstraint("implementation_price_cents >= 0", name="ck_fix_types_implementation_price_nonnegative"),
        CheckConstraint("status IN ('active', 'inactive')", name="ck_fix_types_status"),
        Index("ix_fix_types_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    documentation_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    implementation_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", server_default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    customer_fixes: Mapped[list["CustomerFix"]] = relationship(back_populates="fix_type", passive_deletes=True)
