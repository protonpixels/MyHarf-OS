"""Alembic migration tests against isolated temporary SQLite databases."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.session import create_database_engine


BACKEND_DIR = Path(__file__).resolve().parents[1]


def upgrade_database(database_path: Path) -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{database_path}"
    command.upgrade(config, "head")


def test_migrations_create_full_schema_for_a_fresh_database(tmp_path) -> None:
    database_path = tmp_path / "fresh.db"
    upgrade_database(database_path)

    engine = create_engine(f"sqlite:///{database_path}")
    try:
        table_names = set(inspect(engine).get_table_names())
        expected_tables = set(Base.metadata.tables) | {"alembic_version"}
        assert expected_tables.issubset(table_names)
    finally:
        engine.dispose()


def test_baseline_preserves_existing_records_and_adds_missing_schema(tmp_path) -> None:
    database_path = tmp_path / "existing.db"
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.begin() as connection:
        # This fixture intentionally captures the Phase 1-2 SQLite DDL instead
        # of deriving a supposed legacy database from current model metadata.
        connection.exec_driver_sql(
            """CREATE TABLE customers (
                id INTEGER NOT NULL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                business_name VARCHAR(200),
                email VARCHAR(320),
                phone VARCHAR(50),
                status VARCHAR(20) DEFAULT 'active' NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                CONSTRAINT ck_customers_name_not_blank CHECK (length(trim(name)) > 0),
                CONSTRAINT ck_customers_status CHECK (status IN ('active', 'archived'))
            )"""
        )
        connection.exec_driver_sql(
            """CREATE TABLE diagnostics (
                id INTEGER NOT NULL PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                website_url VARCHAR(2048) NOT NULL,
                status VARCHAR(20) DEFAULT 'planned' NOT NULL,
                summary TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                CONSTRAINT ck_diagnostics_status CHECK (
                    status IN ('planned', 'in_progress', 'completed', 'cancelled', 'archived')
                ),
                FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE RESTRICT
            )"""
        )
        connection.exec_driver_sql(
            """CREATE TABLE findings (
                id INTEGER NOT NULL PRIMARY KEY,
                diagnostic_id INTEGER NOT NULL,
                title VARCHAR(250) NOT NULL,
                description TEXT,
                page_url VARCHAR(2048),
                evidence TEXT,
                status VARCHAR(20) DEFAULT 'identified' NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                CONSTRAINT ck_findings_status CHECK (
                    status IN ('identified', 'reviewed', 'dismissed', 'archived')
                ),
                CONSTRAINT ck_findings_title_not_blank CHECK (length(trim(title)) > 0),
                FOREIGN KEY(diagnostic_id) REFERENCES diagnostics (id) ON DELETE RESTRICT
            )"""
        )
        connection.exec_driver_sql(
            "INSERT INTO customers (name) VALUES (?)", ("Existing customer",)
        )
        customer_id = connection.execute(text("SELECT id FROM customers")).scalar_one()
        connection.exec_driver_sql(
            "INSERT INTO diagnostics (customer_id, website_url) VALUES (?, ?)",
            (customer_id, "https://existing.example"),
        )
        diagnostic_id = connection.execute(text("SELECT id FROM diagnostics")).scalar_one()
        connection.exec_driver_sql(
            "INSERT INTO findings (diagnostic_id, title) VALUES (?, ?)",
            (diagnostic_id, "Existing finding"),
        )
    engine.dispose()

    upgrade_database(database_path)

    migrated_engine = create_database_engine(f"sqlite:///{database_path}")
    try:
        with migrated_engine.connect() as connection:
            assert connection.execute(
                text("SELECT id, name FROM customers WHERE id = :id"), {"id": customer_id}
            ).all() == [(customer_id, "Existing customer")]
            assert connection.execute(text("SELECT count(*) FROM diagnostics")).scalar_one() == 1
            assert connection.execute(text("SELECT count(*) FROM findings")).scalar_one() == 1
        table_names = set(inspect(migrated_engine).get_table_names())
        assert set(Base.metadata.tables).issubset(table_names)
        assert inspect(migrated_engine).has_table("alembic_version")
    finally:
        migrated_engine.dispose()


def test_baseline_rejects_incompatible_legacy_schema_explicitly(tmp_path) -> None:
    database_path = tmp_path / "incompatible.db"
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT)")
    engine.dispose()

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{database_path}"
    try:
        command.upgrade(config, "head")
    except RuntimeError as exc:
        assert "incompatible type or nullability" in str(exc) or "missing required columns" in str(exc)
    else:
        raise AssertionError("incompatible legacy table should not be silently stamped")


def test_baseline_adds_safe_nullable_column_without_rewriting_customer(tmp_path) -> None:
    database_path = tmp_path / "safe-addition.db"
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            """CREATE TABLE customers (
                id INTEGER NOT NULL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                business_name VARCHAR(200),
                email VARCHAR(320),
                status VARCHAR(20) DEFAULT 'active' NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                CONSTRAINT ck_customers_name_not_blank CHECK (length(trim(name)) > 0),
                CONSTRAINT ck_customers_status CHECK (status IN ('active', 'archived'))
            )"""
        )
        connection.execute(text("INSERT INTO customers (name) VALUES ('Preserved customer')"))
    engine.dispose()

    upgrade_database(database_path)

    migrated_engine = create_engine(f"sqlite:///{database_path}")
    try:
        with migrated_engine.connect() as connection:
            assert connection.execute(text("SELECT name, phone FROM customers")).one() == (
                "Preserved customer",
                None,
            )
    finally:
        migrated_engine.dispose()


def test_sqlite_triggers_protect_quote_fields_items_and_deletions(tmp_path) -> None:
    database_path = tmp_path / "immutable.db"
    upgrade_database(database_path)
    engine = create_database_engine(f"sqlite:///{database_path}")

    with engine.begin() as connection:
        connection.execute(text("INSERT INTO customers (name) VALUES ('History customer')"))
        connection.execute(
            text("INSERT INTO fix_types (name, documentation_price_cents, implementation_price_cents) "
                 "VALUES ('Catalog entry', 100, 200)")
        )
        connection.execute(
            text("INSERT INTO customer_fixes (customer_id, fix_type_id, title) VALUES (1, 1, 'Fix before quote')")
        )
        connection.execute(
            text("""INSERT INTO quotations (
                customer_id, status, currency, documentation_subtotal_cents,
                implementation_subtotal_cents, grand_total_cents
            ) VALUES (1, 'draft', 'USD', 100, 0, 100)""")
        )
        connection.execute(
            text("""INSERT INTO quotation_items (
                quotation_id, customer_fix_id, fix_name_snapshot, fix_description_snapshot,
                includes_documentation, documentation_price_cents,
                includes_implementation, implementation_price_cents, line_total_cents
            ) VALUES (1, 1, 'Fix before quote', 'Snapshot text', 1, 100, 0, 0, 100)""")
        )
        connection.execute(text("UPDATE quotations SET is_finalized = 1 WHERE id = 1"))

    protected_quote_updates = {
        "customer_id": "1",
        "currency": "'EUR'",
        "documentation_subtotal_cents": "101",
        "implementation_subtotal_cents": "1",
        "grand_total_cents": "101",
    }
    for column, value in protected_quote_updates.items():
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(text(f"UPDATE quotations SET {column} = {value} WHERE id = 1"))

    protected_item_columns = (
        "id",
        "quotation_id",
        "customer_fix_id",
        "fix_name_snapshot",
        "fix_description_snapshot",
        "includes_documentation",
        "documentation_price_cents",
        "includes_implementation",
        "implementation_price_cents",
        "line_total_cents",
    )
    for column in protected_item_columns:
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(text(f"UPDATE quotation_items SET {column} = {column} WHERE id = 1"))

    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO quotation_items SELECT * FROM quotation_items WHERE id = 1"))
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM quotation_items WHERE id = 1"))
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM quotations WHERE id = 1"))

    # The immutable-field trigger deliberately excludes status changes.
    with engine.begin() as connection:
        connection.execute(text("UPDATE quotations SET status = 'sent' WHERE id = 1"))
        assert connection.execute(
            text("SELECT status, grand_total_cents, is_finalized FROM quotations WHERE id = 1")
        ).one() == ("sent", 100, 1)
        assert connection.execute(
            text("SELECT fix_name_snapshot, fix_description_snapshot, line_total_cents "
                 "FROM quotation_items WHERE id = 1")
        ).one() == ("Fix before quote", "Snapshot text", 100)
    engine.dispose()
