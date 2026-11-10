"""Add quotation and immutable quotation item snapshot tables."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_quotation_tables"
down_revision: Union[str, None] = "0001_core_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    if not _has_table("quotations"):
        op.create_table(
            "quotations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("customer_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
            sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
            sa.Column("documentation_subtotal_cents", sa.Integer(), nullable=False),
            sa.Column("implementation_subtotal_cents", sa.Integer(), nullable=False),
            sa.Column("grand_total_cents", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint(
                "status IN ('draft', 'sent', 'accepted', 'rejected', 'expired')",
                name="ck_quotations_status",
            ),
            sa.CheckConstraint(
                "length(currency) = 3 AND currency = upper(currency)", name="ck_quotations_currency"
            ),
            sa.CheckConstraint(
                "documentation_subtotal_cents >= 0", name="ck_quotations_documentation_subtotal_nonnegative"
            ),
            sa.CheckConstraint(
                "implementation_subtotal_cents >= 0", name="ck_quotations_implementation_subtotal_nonnegative"
            ),
            sa.CheckConstraint("grand_total_cents >= 0", name="ck_quotations_grand_total_nonnegative"),
            sa.CheckConstraint(
                "grand_total_cents = documentation_subtotal_cents + implementation_subtotal_cents",
                name="ck_quotations_grand_total_matches_subtotals",
            ),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("quotation_items"):
        op.create_table(
            "quotation_items",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("quotation_id", sa.Integer(), nullable=False),
            sa.Column("customer_fix_id", sa.Integer(), nullable=False),
            sa.Column("fix_name_snapshot", sa.String(length=250), nullable=False),
            sa.Column("fix_description_snapshot", sa.Text(), nullable=True),
            sa.Column("includes_documentation", sa.Boolean(), nullable=False),
            sa.Column("documentation_price_cents", sa.Integer(), nullable=False),
            sa.Column("includes_implementation", sa.Boolean(), nullable=False),
            sa.Column("implementation_price_cents", sa.Integer(), nullable=False),
            sa.Column("line_total_cents", sa.Integer(), nullable=False),
            sa.CheckConstraint(
                "length(trim(fix_name_snapshot)) > 0", name="ck_quotation_items_fix_name_not_blank"
            ),
            sa.CheckConstraint(
                "documentation_price_cents >= 0", name="ck_quotation_items_documentation_price_nonnegative"
            ),
            sa.CheckConstraint(
                "implementation_price_cents >= 0", name="ck_quotation_items_implementation_price_nonnegative"
            ),
            sa.CheckConstraint("line_total_cents >= 0", name="ck_quotation_items_line_total_nonnegative"),
            sa.CheckConstraint(
                "includes_documentation OR documentation_price_cents = 0",
                name="ck_quotation_items_unselected_documentation_zero",
            ),
            sa.CheckConstraint(
                "includes_implementation OR implementation_price_cents = 0",
                name="ck_quotation_items_unselected_implementation_zero",
            ),
            sa.CheckConstraint(
                "includes_documentation OR includes_implementation",
                name="ck_quotation_items_service_selected",
            ),
            sa.CheckConstraint(
                "line_total_cents = documentation_price_cents + implementation_price_cents",
                name="ck_quotation_items_total_matches_prices",
            ),
            sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["customer_fix_id"], ["customer_fixes.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("quotation_id", "customer_fix_id", name="uq_quotation_items_quotation_customer_fix"),
        )


def downgrade() -> None:
    raise RuntimeError("Quotation migrations are forward-only to protect quotation history")
