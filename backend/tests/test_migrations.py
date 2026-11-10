"""Alembic migration tests against isolated temporary SQLite databases."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import create_database_engine
from app.models.customer import Customer


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
    legacy_table_names = ("customers", "diagnostics", "findings")
    legacy_tables = [Base.metadata.tables[name] for name in legacy_table_names]
    engine = create_database_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(bind=engine, tables=legacy_tables)
    with Session(engine) as session:
        customer = Customer(name="Existing customer")
        session.add(customer)
        session.commit()
        customer_id = customer.id
    engine.dispose()

    upgrade_database(database_path)

    migrated_engine = create_database_engine(f"sqlite:///{database_path}")
    try:
        with migrated_engine.connect() as connection:
            assert connection.execute(select(Customer.id, Customer.name)).all() == [
                (customer_id, "Existing customer")
            ]
        table_names = set(inspect(migrated_engine).get_table_names())
        assert set(Base.metadata.tables).issubset(table_names)
        assert inspect(migrated_engine).has_table("alembic_version")
    finally:
        migrated_engine.dispose()
