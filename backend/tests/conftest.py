"""Fixtures use a fresh temporary SQLite database for every test."""

import pytest
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401 - ensure every model is registered
from app.db.base import Base
from app.db.session import create_database_engine


@pytest.fixture
def test_session_factory(tmp_path):
    engine = create_database_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session(test_session_factory) -> Session:
    with test_session_factory() as session:
        yield session
