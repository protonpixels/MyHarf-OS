"""Customer-specific actionable fix record."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CustomerFix(Base):
    __tablename__ = "customer_fixes"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="ck_customer_fixes_title_not_blank"),
        CheckConstraint(
            "status IN ('identified', 'documented', 'approved', 'in_progress', 'implemented', 'tested', 'delivered')",
            name="ck_customer_fixes_status",
        ),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name="ck_customer_fixes_priority"),
        CheckConstraint("complexity IN ('low', 'medium', 'high')", name="ck_customer_fixes_complexity"),
        CheckConstraint(
            "documentation_price_override_cents IS NULL OR documentation_price_override_cents >= 0",
            name="ck_customer_fixes_documentation_override_nonnegative",
        ),
        CheckConstraint(
            "implementation_price_override_cents IS NULL OR implementation_price_override_cents >= 0",
            name="ck_customer_fixes_implementation_override_nonnegative",
        ),
        Index("ix_customer_fixes_customer_id", "customer_id"),
        Index("ix_customer_fixes_finding_id", "finding_id"),
        Index("ix_customer_fixes_fix_type_id", "fix_type_id"),
        Index("ix_customer_fixes_status_priority_complexity", "status", "priority", "complexity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    finding_id: Mapped[int | None] = mapped_column(ForeignKey("findings.id", ondelete="RESTRICT"))
    fix_type_id: Mapped[int] = mapped_column(ForeignKey("fix_types.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium", server_default="medium")
    complexity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium", server_default="medium")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="identified", server_default="identified")
    documentation_price_override_cents: Mapped[int | None] = mapped_column(Integer)
    implementation_price_override_cents: Mapped[int | None] = mapped_column(Integer)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    customer: Mapped["Customer"] = relationship(back_populates="fixes")
    finding: Mapped["Finding | None"] = relationship(back_populates="customer_fixes")
    fix_type: Mapped["FixType"] = relationship(back_populates="customer_fixes")
