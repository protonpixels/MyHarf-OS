"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routes.customers import router as customers_router
from app.api.routes.diagnostics import router as diagnostics_router
from app.api.routes.findings import router as findings_router
from app.api.routes.customer_fixes import router as customer_fixes_router
from app.api.routes.fix_types import router as fix_types_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401 - registers model tables with Base metadata

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create tables for the initial SQLite release on application startup."""

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(health_router)
app.include_router(health_router, prefix="/api/v1")
app.include_router(customers_router, prefix="/api/v1")
app.include_router(diagnostics_router, prefix="/api/v1")
app.include_router(findings_router, prefix="/api/v1")
app.include_router(fix_types_router, prefix="/api/v1")
app.include_router(customer_fixes_router, prefix="/api/v1")
register_exception_handlers(app)
