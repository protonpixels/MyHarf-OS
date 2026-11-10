"""Individual website diagnostic finding model."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Finding(Base):
    __tablename__ = "findings"
    __table_args__ = (
        CheckConstraint(
            "status IN ('identified', 'reviewed', 'dismissed', 'archived')",
            name="ck_findings_status",
        ),
        CheckConstraint("length(trim(title)) > 0", name="ck_findings_title_not_blank"),
        Index("ix_findings_diagnostic_id", "diagnostic_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    diagnostic_id: Mapped[int] = mapped_column(ForeignKey("diagnostics.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    page_url: Mapped[str | None] = mapped_column(String(2048))
    evidence: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="identified", server_default="identified"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    diagnostic: Mapped["Diagnostic"] = relationship(back_populates="findings")
    customer_fixes: Mapped[list["CustomerFix"]] = relationship(back_populates="finding", passive_deletes=True)


