"""Idempotent baseline for the Phase 1-3 schema.

This revision creates only tables and indexes absent from the target database.
Existing tables and rows are left in place. It also fills in Phase 3 tables for
databases created before the fix ledger was added.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_core_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _has_index(table: str, name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(index["name"] == name for index in inspector.get_indexes(table))


def upgrade() -> None:
    if not _has_table("customers"):
        op.create_table(
            "customers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("business_name", sa.String(length=200), nullable=True),
            sa.Column("email", sa.String(length=320), nullable=True),
            sa.Column("phone", sa.String(length=50), nullable=True),
            sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint("length(trim(name)) > 0", name="ck_customers_name_not_blank"),
            sa.CheckConstraint("status IN ('active', 'archived')", name="ck_customers_status"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("diagnostics"):
        op.create_table(
            "diagnostics",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("customer_id", sa.Integer(), nullable=False),
            sa.Column("website_url", sa.String(length=2048), nullable=False),
            sa.Column("status", sa.String(length=20), server_default="planned", nullable=False),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint(
                "status IN ('planned', 'in_progress', 'completed', 'cancelled', 'archived')",
                name="ck_diagnostics_status",
            ),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("findings"):
        op.create_table(
            "findings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("diagnostic_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=250), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("page_url", sa.String(length=2048), nullable=True),
            sa.Column("evidence", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), server_default="identified", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint(
                "status IN ('identified', 'reviewed', 'dismissed', 'archived')",
                name="ck_findings_status",
            ),
            sa.CheckConstraint("length(trim(title)) > 0", name="ck_findings_title_not_blank"),
            sa.ForeignKeyConstraint(["diagnostic_id"], ["diagnostics.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("fix_types"):
        op.create_table(
            "fix_types",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("documentation_price_cents", sa.Integer(), nullable=False),
            sa.Column("implementation_price_cents", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint("length(trim(name)) > 0", name="ck_fix_types_name_not_blank"),
            sa.CheckConstraint(
                "documentation_price_cents >= 0", name="ck_fix_types_documentation_price_nonnegative"
            ),
            sa.CheckConstraint(
                "implementation_price_cents >= 0", name="ck_fix_types_implementation_price_nonnegative"
            ),
            sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_fix_types_status"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("customer_fixes"):
        op.create_table(
            "customer_fixes",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("customer_id", sa.Integer(), nullable=False),
            sa.Column("finding_id", sa.Integer(), nullable=True),
            sa.Column("fix_type_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=250), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("priority", sa.String(length=20), server_default="medium", nullable=False),
            sa.Column("complexity", sa.String(length=20), server_default="medium", nullable=False),
            sa.Column("status", sa.String(length=20), server_default="identified", nullable=False),
            sa.Column("documentation_price_override_cents", sa.Integer(), nullable=True),
            sa.Column("implementation_price_override_cents", sa.Integer(), nullable=True),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint("length(trim(title)) > 0", name="ck_customer_fixes_title_not_blank"),
            sa.CheckConstraint(
                "status IN ('identified', 'documented', 'approved', 'in_progress', 'implemented', 'tested', 'delivered')",
                name="ck_customer_fixes_status",
            ),
            sa.CheckConstraint(
                "priority IN ('low', 'medium', 'high', 'urgent')", name="ck_customer_fixes_priority"
            ),
            sa.CheckConstraint(
                "complexity IN ('low', 'medium', 'high')", name="ck_customer_fixes_complexity"
            ),
            sa.CheckConstraint(
                "documentation_price_override_cents IS NULL OR documentation_price_override_cents >= 0",
                name="ck_customer_fixes_documentation_override_nonnegative",
            ),
            sa.CheckConstraint(
                "implementation_price_override_cents IS NULL OR implementation_price_override_cents >= 0",
                name="ck_customer_fixes_implementation_override_nonnegative",
            ),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["finding_id"], ["findings.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["fix_type_id"], ["fix_types.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
        )

    for table, name, columns in (
        ("diagnostics", "ix_diagnostics_customer_id", ["customer_id"]),
        ("findings", "ix_findings_diagnostic_id", ["diagnostic_id"]),
        ("fix_types", "ix_fix_types_status", ["status"]),
        ("customer_fixes", "ix_customer_fixes_customer_id", ["customer_id"]),
        ("customer_fixes", "ix_customer_fixes_finding_id", ["finding_id"]),
        ("customer_fixes", "ix_customer_fixes_fix_type_id", ["fix_type_id"]),
        (
            "customer_fixes",
            "ix_customer_fixes_status_priority_complexity",
            ["status", "priority", "complexity"],
        ),
    ):
        if _has_table(table) and not _has_index(table, name):
            op.create_index(name, table, columns)


def downgrade() -> None:
    raise RuntimeError("Schema baseline migrations are forward-only to protect existing data")
