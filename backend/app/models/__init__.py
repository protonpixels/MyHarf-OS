"""SQLAlchemy models registered with the declarative metadata."""

from app.models.customer import Customer
from app.models.diagnostic import Diagnostic
from app.models.finding import Finding

__all__ = ["Customer", "Diagnostic", "Finding"]
