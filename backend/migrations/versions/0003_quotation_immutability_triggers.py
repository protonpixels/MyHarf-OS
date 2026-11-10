"""Add SQLite triggers for immutable quotation history."""

from typing import Sequence, Union
import re

from alembic import op
import sqlalchemy as sa

revision: str = "0003_quote_immutability"
down_revision: Union[str, None] = "0002_quotation_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TRIGGERS = {
    "trg_quotations_financial_fields_immutable": """CREATE TRIGGER trg_quotations_financial_fields_immutable
        BEFORE UPDATE OF customer_id, currency, documentation_subtotal_cents,
        implementation_subtotal_cents, grand_total_cents ON quotations
        BEGIN SELECT RAISE(ABORT, 'quotation financial snapshot is immutable'); END""",
    "trg_quotations_finalization_one_way": """CREATE TRIGGER trg_quotations_finalization_one_way
        BEFORE UPDATE OF is_finalized ON quotations
        WHEN OLD.is_finalized = 1 OR NEW.is_finalized != 1
        BEGIN SELECT RAISE(ABORT, 'quotation finalization is one-way'); END""",
    "trg_quotations_validate_finalization": """CREATE TRIGGER trg_quotations_validate_finalization
        BEFORE UPDATE OF is_finalized ON quotations
        WHEN OLD.is_finalized = 0 AND NEW.is_finalized = 1
        BEGIN
            SELECT RAISE(ABORT, 'quotation requires at least one item')
            WHERE NOT EXISTS (SELECT 1 FROM quotation_items WHERE quotation_id = NEW.id);
            SELECT RAISE(ABORT, 'quotation documentation subtotal does not match items')
            WHERE NEW.documentation_subtotal_cents != COALESCE(
                (SELECT SUM(documentation_price_cents) FROM quotation_items WHERE quotation_id = NEW.id), 0
            );
            SELECT RAISE(ABORT, 'quotation implementation subtotal does not match items')
            WHERE NEW.implementation_subtotal_cents != COALESCE(
                (SELECT SUM(implementation_price_cents) FROM quotation_items WHERE quotation_id = NEW.id), 0
            );
        END""",
    "trg_quotations_no_finalized_insert": """CREATE TRIGGER trg_quotations_no_finalized_insert
        BEFORE INSERT ON quotations
        WHEN NEW.is_finalized != 0
        BEGIN SELECT RAISE(ABORT, 'quotation must be finalized after its items are inserted'); END""",
    "trg_quotations_delete_immutable": """CREATE TRIGGER trg_quotations_delete_immutable
        BEFORE DELETE ON quotations
        BEGIN SELECT RAISE(ABORT, 'quotations cannot be deleted'); END""",
    "trg_quotation_items_no_late_insert": """CREATE TRIGGER trg_quotation_items_no_late_insert
        BEFORE INSERT ON quotation_items
        WHEN (SELECT is_finalized FROM quotations WHERE id = NEW.quotation_id) = 1
        BEGIN SELECT RAISE(ABORT, 'quotation items are immutable after finalization'); END""",
    "trg_quotation_items_update_immutable": """CREATE TRIGGER trg_quotation_items_update_immutable
        BEFORE UPDATE ON quotation_items
        BEGIN SELECT RAISE(ABORT, 'quotation items are immutable'); END""",
    "trg_quotation_items_delete_immutable": """CREATE TRIGGER trg_quotation_items_delete_immutable
        BEFORE DELETE ON quotation_items
        BEGIN SELECT RAISE(ABORT, 'quotation items are immutable'); END""",
}


def _normalize(sql: str) -> str:
    return re.sub(r"\s+", "", sql).rstrip(";").lower()


def upgrade() -> None:
    connection = op.get_bind()
    if connection.dialect.name != "sqlite":
        raise RuntimeError("Quotation immutability triggers are currently implemented for SQLite only")

    for name, statement in TRIGGERS.items():
        existing = connection.execute(
            sa.text("SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = :name"),
            {"name": name},
        ).scalar_one_or_none()
        if existing is not None:
            if _normalize(existing) != _normalize(statement):
                raise RuntimeError(
                    f"Existing SQLite trigger '{name}' has an incompatible definition; "
                    "manual review is required before upgrading."
                )
            continue
        op.execute(statement)


def downgrade() -> None:
    raise RuntimeError("Quotation immutability migrations are forward-only to protect quotation history")
