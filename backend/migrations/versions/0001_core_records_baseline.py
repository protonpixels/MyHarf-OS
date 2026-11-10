"""Idempotent baseline for the Phase 1-3 schema.

This revision creates only tables and indexes absent from the target database.
Existing tables and rows are left in place. It also fills in Phase 3 tables for
databases created before the fix ledger was added.
"""

from typing import Sequence, Union
import re

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


def _validate_index(table: str, name: str, expected_columns: list[str]) -> None:
    existing = next(
        (index for index in sa.inspect(op.get_bind()).get_indexes(table) if index["name"] == name),
        None,
    )
    if existing is not None and existing.get("column_names") != expected_columns:
        raise RuntimeError(f"Existing index '{name}' on '{table}' has incompatible columns")


SAFE_ADDITIONS = {
    "customers": {
        "business_name": sa.Column("business_name", sa.String(length=200), nullable=True),
        "email": sa.Column("email", sa.String(length=320), nullable=True),
        "phone": sa.Column("phone", sa.String(length=50), nullable=True),
    },
    "diagnostics": {
        "summary": sa.Column("summary", sa.Text(), nullable=True),
    },
    "findings": {
        "description": sa.Column("description", sa.Text(), nullable=True),
        "page_url": sa.Column("page_url", sa.String(length=2048), nullable=True),
        "evidence": sa.Column("evidence", sa.Text(), nullable=True),
    },
    "fix_types": {
        "description": sa.Column("description", sa.Text(), nullable=True),
    },
    "customer_fixes": {
        "finding_id": sa.Column(
            "finding_id",
            sa.Integer(),
            sa.ForeignKey("findings.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        "description": sa.Column("description", sa.Text(), nullable=True),
        "documentation_price_override_cents": sa.Column(
            "documentation_price_override_cents", sa.Integer(), nullable=True
        ),
        "implementation_price_override_cents": sa.Column(
            "implementation_price_override_cents", sa.Integer(), nullable=True
        ),
        "archived_at": sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    },
}

EXPECTED_COLUMNS = {
    "customers": {
        "id": ("integer", False, None), "name": ("string", False, 200),
        "business_name": ("string", True, 200), "email": ("string", True, 320),
        "phone": ("string", True, 50), "status": ("string", False, 20),
        "created_at": ("datetime", False, None), "updated_at": ("datetime", False, None),
    },
    "diagnostics": {
        "id": ("integer", False, None), "customer_id": ("integer", False, None),
        "website_url": ("string", False, 2048), "status": ("string", False, 20),
        "summary": ("text", True, None), "created_at": ("datetime", False, None),
        "updated_at": ("datetime", False, None),
    },
    "findings": {
        "id": ("integer", False, None), "diagnostic_id": ("integer", False, None),
        "title": ("string", False, 250), "description": ("text", True, None),
        "page_url": ("string", True, 2048), "evidence": ("text", True, None),
        "status": ("string", False, 20), "created_at": ("datetime", False, None),
        "updated_at": ("datetime", False, None),
    },
    "fix_types": {
        "id": ("integer", False, None), "name": ("string", False, 200),
        "description": ("text", True, None), "documentation_price_cents": ("integer", False, None),
        "implementation_price_cents": ("integer", False, None), "status": ("string", False, 20),
        "created_at": ("datetime", False, None), "updated_at": ("datetime", False, None),
    },
    "customer_fixes": {
        "id": ("integer", False, None), "customer_id": ("integer", False, None),
        "finding_id": ("integer", True, None), "fix_type_id": ("integer", False, None),
        "title": ("string", False, 250), "description": ("text", True, None),
        "priority": ("string", False, 20), "complexity": ("string", False, 20),
        "status": ("string", False, 20), "documentation_price_override_cents": ("integer", True, None),
        "implementation_price_override_cents": ("integer", True, None), "archived_at": ("datetime", True, None),
        "created_at": ("datetime", False, None), "updated_at": ("datetime", False, None),
    },
}

EXPECTED_CHECKS = {
    "customers": {
        "ck_customers_name_not_blank": "length(trim(name)) > 0",
        "ck_customers_status": "status IN ('active', 'archived')",
    },
    "diagnostics": {
        "ck_diagnostics_status": "status IN ('planned', 'in_progress', 'completed', 'cancelled', 'archived')",
    },
    "findings": {
        "ck_findings_status": "status IN ('identified', 'reviewed', 'dismissed', 'archived')",
        "ck_findings_title_not_blank": "length(trim(title)) > 0",
    },
    "fix_types": {
        "ck_fix_types_name_not_blank": "length(trim(name)) > 0",
        "ck_fix_types_documentation_price_nonnegative": "documentation_price_cents >= 0",
        "ck_fix_types_implementation_price_nonnegative": "implementation_price_cents >= 0",
        "ck_fix_types_status": "status IN ('active', 'inactive')",
    },
    "customer_fixes": {
        "ck_customer_fixes_title_not_blank": "length(trim(title)) > 0",
        "ck_customer_fixes_status": "status IN ('identified', 'documented', 'approved', 'in_progress', 'implemented', 'tested', 'delivered')",
        "ck_customer_fixes_priority": "priority IN ('low', 'medium', 'high', 'urgent')",
        "ck_customer_fixes_complexity": "complexity IN ('low', 'medium', 'high')",
        "ck_customer_fixes_documentation_override_nonnegative": "documentation_price_override_cents IS NULL OR documentation_price_override_cents >= 0",
        "ck_customer_fixes_implementation_override_nonnegative": "implementation_price_override_cents IS NULL OR implementation_price_override_cents >= 0",
    },
}

EXPECTED_FOREIGN_KEYS = {
    "diagnostics": {("customer_id", "customers", "id", "RESTRICT")},
    "findings": {("diagnostic_id", "diagnostics", "id", "RESTRICT")},
    "customer_fixes": {
        ("customer_id", "customers", "id", "RESTRICT"),
        ("finding_id", "findings", "id", "RESTRICT"),
        ("fix_type_id", "fix_types", "id", "RESTRICT"),
    },
}


def _normalize_sql(expression: str) -> str:
    return re.sub(r"\s+", "", expression).lower()


def _type_matches(actual_type, expected_kind: str, expected_length: int | None) -> bool:
    actual = str(actual_type).upper()
    if expected_kind == "integer":
        return "INT" in actual
    if expected_kind == "datetime":
        return "DATETIME" in actual or "TIMESTAMP" in actual
    if expected_kind == "text":
        return "TEXT" in actual
    if expected_kind == "string":
        return ("CHAR" in actual or "TEXT" in actual) and getattr(actual_type, "length", None) == expected_length
    return False


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


def _validate_existing_tables() -> None:
    inspector = sa.inspect(op.get_bind())
    for table, expected_columns in EXPECTED_COLUMNS.items():
        actual_columns = {column["name"]: column for column in inspector.get_columns(table)}
        for name, column in SAFE_ADDITIONS.get(table, {}).items():
            if name not in actual_columns:
                op.add_column(table, column)
        inspector = sa.inspect(op.get_bind())
        actual_columns = {column["name"]: column for column in sa.inspect(op.get_bind()).get_columns(table)}
        missing = set(expected_columns) - set(actual_columns)
        if missing:
            raise RuntimeError(
                f"Existing table '{table}' is missing required columns {sorted(missing)}; "
                "automatic reconstruction could discard data. Repair it explicitly before upgrading."
            )
        for name, (kind, nullable, length) in expected_columns.items():
            column = actual_columns[name]
            if not _type_matches(column["type"], kind, length) or bool(column["nullable"]) != nullable:
                raise RuntimeError(
                    f"Existing table '{table}' column '{name}' has an incompatible type or nullability; "
                    "automatic table rebuilding is disabled to protect existing records."
                )

        primary_key = inspector.get_pk_constraint(table).get("constrained_columns", [])
        if primary_key != ["id"]:
            raise RuntimeError(f"Existing table '{table}' has an incompatible primary key")

        checks = {check["name"]: check["sqltext"] for check in inspector.get_check_constraints(table)}
        for name, expression in EXPECTED_CHECKS[table].items():
            if name not in checks or _normalize_sql(checks[name]) != _normalize_sql(expression):
                raise RuntimeError(
                    f"Existing table '{table}' is missing or has an incompatible constraint '{name}'; "
                    "automatic constraint rebuilding is disabled to protect existing records."
                )

        actual_fks = _foreign_key_tuples(table, inspector)
        if actual_fks != EXPECTED_FOREIGN_KEYS.get(table, set()):
            raise RuntimeError(
                f"Existing table '{table}' has incompatible foreign keys; "
                "automatic constraint rebuilding is disabled to protect existing records."
            )


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
        if _has_table(table):
            _validate_index(table, name, columns)
        if _has_table(table) and not _has_index(table, name):
            op.create_index(name, table, columns)

    _validate_existing_tables()


def downgrade() -> None:
    raise RuntimeError("Schema baseline migrations are forward-only to protect existing data")
