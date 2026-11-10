"""Add quotation and immutable quotation item snapshot tables."""

from typing import Sequence, Union
import re

from alembic import op
import sqlalchemy as sa

revision: str = "0002_quotation_tables"
down_revision: Union[str, None] = "0001_core_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _normalize_sql(expression: str) -> str:
    normalized = re.sub(r"\s+", "", expression).lower()
    normalized = normalized.replace("=1", "").replace("=true", "")
    while normalized.startswith("(") and normalized.endswith(")"):
        normalized = normalized[1:-1]
    return normalized


def _foreign_key_tuples(table: str, inspector) -> set[tuple[str, str, str, str]]:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return {
            (row["from"], row["table"], row["to"], row["on_delete"].upper())
            for row in bind.exec_driver_sql(f"PRAGMA foreign_key_list({table})").mappings()
        }
    actual = set()
    for key in inspector.get_foreign_keys(table):
        if len(key["constrained_columns"]) == len(key["referred_columns"]) == 1:
            actual.add(
                (
                    key["constrained_columns"][0],
                    key["referred_table"],
                    key["referred_columns"][0],
                    key.get("options", {}).get("ondelete", "").upper(),
                )
            )
    return actual


def _validate_quote_tables() -> None:
    inspector = sa.inspect(op.get_bind())
    expected_columns = {
        "quotations": {
            "id": ("INTEGER", False), "customer_id": ("INTEGER", False),
            "status": ("VARCHAR", False), "currency": ("VARCHAR", False),
            "documentation_subtotal_cents": ("INTEGER", False),
            "implementation_subtotal_cents": ("INTEGER", False),
            "grand_total_cents": ("INTEGER", False), "is_finalized": ("BOOLEAN", False),
            "created_at": ("DATETIME", False), "updated_at": ("DATETIME", False),
        },
        "quotation_items": {
            "id": ("INTEGER", False), "quotation_id": ("INTEGER", False),
            "customer_fix_id": ("INTEGER", False), "fix_name_snapshot": ("VARCHAR", False),
            "fix_description_snapshot": ("TEXT", True), "includes_documentation": ("BOOLEAN", False),
            "documentation_price_cents": ("INTEGER", False),
            "includes_implementation": ("BOOLEAN", False),
            "implementation_price_cents": ("INTEGER", False), "line_total_cents": ("INTEGER", False),
        },
    }
    expected_checks = {
        "quotations": {
            "ck_quotations_status": "status IN ('draft', 'sent', 'accepted', 'rejected', 'expired')",
            "ck_quotations_currency": "length(currency) = 3 AND currency = upper(currency)",
            "ck_quotations_documentation_subtotal_nonnegative": "documentation_subtotal_cents >= 0",
            "ck_quotations_implementation_subtotal_nonnegative": "implementation_subtotal_cents >= 0",
            "ck_quotations_grand_total_nonnegative": "grand_total_cents >= 0",
            "ck_quotations_grand_total_matches_subtotals":
                "grand_total_cents = documentation_subtotal_cents + implementation_subtotal_cents",
        },
        "quotation_items": {
            "ck_quotation_items_fix_name_not_blank": "length(trim(fix_name_snapshot)) > 0",
            "ck_quotation_items_documentation_price_nonnegative": "documentation_price_cents >= 0",
            "ck_quotation_items_implementation_price_nonnegative": "implementation_price_cents >= 0",
            "ck_quotation_items_line_total_nonnegative": "line_total_cents >= 0",
            "ck_quotation_items_unselected_documentation_zero":
                "includes_documentation OR documentation_price_cents = 0",
            "ck_quotation_items_unselected_implementation_zero":
                "includes_implementation OR implementation_price_cents = 0",
            "ck_quotation_items_service_selected": "includes_documentation OR includes_implementation",
            "ck_quotation_items_total_matches_prices":
                "line_total_cents = documentation_price_cents + implementation_price_cents",
        },
    }
    expected_fks = {
        "quotations": {("customer_id", "customers", "id", "RESTRICT")},
        "quotation_items": {
            ("quotation_id", "quotations", "id", "RESTRICT"),
            ("customer_fix_id", "customer_fixes", "id", "RESTRICT"),
        },
    }

    for table, columns in expected_columns.items():
        found = {column["name"]: column for column in inspector.get_columns(table)}
        missing = set(columns) - set(found)
        if missing:
            raise RuntimeError(f"Existing table '{table}' is missing required columns {sorted(missing)}")
        for name, (expected_type, nullable) in columns.items():
            column = found[name]
            if expected_type not in str(column["type"]).upper() or bool(column["nullable"]) != nullable:
                raise RuntimeError(
                    f"Existing table '{table}' column '{name}' is incompatible; "
                    "automatic reconstruction is disabled to preserve quotation history."
                )
        checks = {check["name"]: check["sqltext"] for check in inspector.get_check_constraints(table)}
        for name, expression in expected_checks[table].items():
            if name not in checks or _normalize_sql(checks[name]) != _normalize_sql(expression):
                raise RuntimeError(
                    f"Existing table '{table}' is missing or has an incompatible constraint '{name}'"
                )
        foreign_keys = _foreign_key_tuples(table, inspector)
        if foreign_keys != expected_fks[table]:
            raise RuntimeError(f"Existing table '{table}' has incompatible foreign keys")
    unique_constraints = inspector.get_unique_constraints("quotation_items")
    if not any(
        constraint.get("column_names") == ["quotation_id", "customer_fix_id"]
        for constraint in unique_constraints
    ):
        raise RuntimeError("Existing quotation_items table does not prevent duplicate fixes per quotation")


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
            sa.Column("is_finalized", sa.Boolean(), server_default=sa.false(), nullable=False),
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
    elif "is_finalized" not in {column["name"] for column in sa.inspect(op.get_bind()).get_columns("quotations")}:
        # Existing Phase 4 quotes predate the internal assembly flag. Mark all
        # existing records finalized so their current items cannot be extended.
        op.add_column(
            "quotations",
            sa.Column("is_finalized", sa.Boolean(), server_default=sa.true(), nullable=False),
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

    _validate_quote_tables()


def downgrade() -> None:
    raise RuntimeError("Quotation migrations are forward-only to protect quotation history")
