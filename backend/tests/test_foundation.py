"""Basic tests for the backend foundation."""

from sqlalchemy import text

from app.api.routes.health import health_check
from app.core.config import Settings
from app.db.base import Base
from app.db.session import create_database_engine
from app.main import app


def test_health_endpoint_is_registered_and_reports_ok() -> None:
    assert "/health" in app.openapi()["paths"]
    assert health_check() == {"status": "ok"}


def test_settings_use_safe_defaults_and_allow_environment_values() -> None:
    defaults = Settings(_env_file=None)
    configured = Settings(_env_file=None, app_name="Test API", database_url="sqlite:///test.db")

    assert defaults.app_name == "MyHarf OS API"
    assert defaults.database_url == "sqlite:///./myharf.db"
    assert configured.app_name == "Test API"
    assert configured.database_url == "sqlite:///test.db"


def test_sqlite_engine_connects_and_declarative_base_is_available() -> None:
    engine = create_database_engine("sqlite://")
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
        assert Base.metadata is not None
    finally:
        engine.dispose()
