"""SQLAlchemy models registered with the declarative metadata."""

from app.models.customer import Customer
from app.models.customer_fix import CustomerFix
from app.models.diagnostic import Diagnostic
from app.models.fix_type import FixType
from app.models.finding import Finding
from app.models.quotation import Quotation, QuotationItem

__all__ = ["Customer", "CustomerFix", "Diagnostic", "Finding", "FixType", "Quotation", "QuotationItem"]
