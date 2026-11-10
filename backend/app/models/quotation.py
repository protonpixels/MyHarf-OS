"""Quotation and immutable itemized price snapshot models."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    false,
    func,
    inspect,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


QUOTATION_STATUSES = "'draft', 'sent', 'accepted', 'rejected', 'expired'"


class Quotation(Base):
    __tablename__ = "quotations"
    __table_args__ = (
        CheckConstraint(f"status IN ({QUOTATION_STATUSES})", name="ck_quotations_status"),
        CheckConstraint("length(currency) = 3 AND currency = upper(currency)", name="ck_quotations_currency"),
        CheckConstraint("documentation_subtotal_cents >= 0", name="ck_quotations_documentation_subtotal_nonnegative"),
        CheckConstraint("implementation_subtotal_cents >= 0", name="ck_quotations_implementation_subtotal_nonnegative"),
        CheckConstraint("grand_total_cents >= 0", name="ck_quotations_grand_total_nonnegative"),
        CheckConstraint(
            "grand_total_cents = documentation_subtotal_cents + implementation_subtotal_cents",
            name="ck_quotations_grand_total_matches_subtotals",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", server_default="draft")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")
    documentation_subtotal_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    implementation_subtotal_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    grand_total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    is_finalized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    customer: Mapped["Customer"] = relationship(back_populates="quotations")
    items: Mapped[list["QuotationItem"]] = relationship(
        back_populates="quotation", order_by="QuotationItem.id", passive_deletes=True
    )


class QuotationItem(Base):
    __tablename__ = "quotation_items"
    __table_args__ = (
        UniqueConstraint("quotation_id", "customer_fix_id", name="uq_quotation_items_quotation_customer_fix"),
        CheckConstraint("length(trim(fix_name_snapshot)) > 0", name="ck_quotation_items_fix_name_not_blank"),
        CheckConstraint("documentation_price_cents >= 0", name="ck_quotation_items_documentation_price_nonnegative"),
        CheckConstraint("implementation_price_cents >= 0", name="ck_quotation_items_implementation_price_nonnegative"),
        CheckConstraint("line_total_cents >= 0", name="ck_quotation_items_line_total_nonnegative"),
        CheckConstraint(
            "includes_documentation = 1 OR documentation_price_cents = 0",
            name="ck_quotation_items_unselected_documentation_zero",
        ),
        CheckConstraint(
            "includes_implementation = 1 OR implementation_price_cents = 0",
            name="ck_quotation_items_unselected_implementation_zero",
        ),
        CheckConstraint(
            "includes_documentation = 1 OR includes_implementation = 1",
            name="ck_quotation_items_service_selected",
        ),
        CheckConstraint(
            "line_total_cents = documentation_price_cents + implementation_price_cents",
            name="ck_quotation_items_total_matches_prices",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_id: Mapped[int] = mapped_column(ForeignKey("quotations.id", ondelete="RESTRICT"), nullable=False)
    customer_fix_id: Mapped[int] = mapped_column(ForeignKey("customer_fixes.id", ondelete="RESTRICT"), nullable=False)
    fix_name_snapshot: Mapped[str] = mapped_column(String(250), nullable=False)
    fix_description_snapshot: Mapped[str | None] = mapped_column(Text)
    includes_documentation: Mapped[bool] = mapped_column(Boolean, nullable=False)
    documentation_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    includes_implementation: Mapped[bool] = mapped_column(Boolean, nullable=False)
    implementation_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    quotation: Mapped["Quotation"] = relationship(back_populates="items")
    customer_fix: Mapped["CustomerFix"] = relationship(back_populates="quotation_items")


@event.listens_for(Quotation, "before_update")
def prevent_quotation_amount_changes(_mapper, _connection, quotation: Quotation) -> None:
    """Allow status changes, but protect persisted financial snapshots."""

    state = inspect(quotation)
    protected_fields = (
        "customer_id",
        "currency",
        "documentation_subtotal_cents",
        "implementation_subtotal_cents",
        "grand_total_cents",
    )
    if any(state.attrs[field].history.has_changes() for field in protected_fields):
        raise ValueError("Quotation customer, currency, and amounts are immutable")
    finalized_history = state.attrs.is_finalized.history
    if finalized_history.has_changes() and not (
        finalized_history.deleted == [False] and finalized_history.added == [True]
    ):
        raise ValueError("Quotation finalization is a one-way transition")


@event.listens_for(QuotationItem, "before_update")
def prevent_quotation_item_changes(_mapper, _connection, _item: QuotationItem) -> None:
    """Quotation items are immutable snapshots after creation."""

    raise ValueError("Quotation items are immutable snapshots")


@event.listens_for(QuotationItem, "before_delete")
def prevent_quotation_item_deletion(_mapper, _connection, _item: QuotationItem) -> None:
    """Quotation items cannot be removed from an existing quotation."""

    raise ValueError("Quotation items are immutable snapshots")


@event.listens_for(Quotation, "before_delete")
def prevent_quotation_deletion(_mapper, _connection, _quotation: Quotation) -> None:
    """Quotations are retained as customer history."""

    raise ValueError("Quotations cannot be deleted")
