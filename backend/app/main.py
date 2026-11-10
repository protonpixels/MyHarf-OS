"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routes.customers import router as customers_router
from app.api.routes.diagnostics import router as diagnostics_router
from app.api.routes.findings import router as findings_router
from app.api.routes.customer_fixes import router as customer_fixes_router
from app.api.routes.fix_types import router as fix_types_router
from app.api.routes.quotations import router as quotations_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
import app.models  # noqa: F401 - registers model tables with Base metadata

settings = get_settings()


app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(health_router, prefix="/api/v1")
app.include_router(customers_router, prefix="/api/v1")
app.include_router(diagnostics_router, prefix="/api/v1")
app.include_router(findings_router, prefix="/api/v1")
app.include_router(fix_types_router, prefix="/api/v1")
app.include_router(customer_fixes_router, prefix="/api/v1")
app.include_router(quotations_router, prefix="/api/v1")
register_exception_handlers(app)
