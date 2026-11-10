"""Deterministic, integer-cents pricing rules for individual customer fixes."""

from dataclasses import dataclass

from app.models.customer_fix import CustomerFix


@dataclass(frozen=True)
class SelectedLinePrices:
    documentation_price_cents: int
    implementation_price_cents: int
    line_total_cents: int


@dataclass(frozen=True)
class QuotationTotals:
    documentation_subtotal_cents: int
    implementation_subtotal_cents: int
    grand_total_cents: int


def resolve_documentation_price(customer_fix: CustomerFix) -> int:
    """Resolve documentation price from its override or catalog default."""

    if customer_fix.documentation_price_override_cents is not None:
        return customer_fix.documentation_price_override_cents
    return customer_fix.fix_type.documentation_price_cents


def resolve_implementation_price(customer_fix: CustomerFix) -> int:
    """Resolve implementation price from its override or catalog default."""

    if customer_fix.implementation_price_override_cents is not None:
        return customer_fix.implementation_price_override_cents
    return customer_fix.fix_type.implementation_price_cents


def price_selected_services(
    customer_fix: CustomerFix,
    *,
    includes_documentation: bool,
    includes_implementation: bool,
) -> SelectedLinePrices:
    """Return selected service prices, recording zero for unselected services."""

    documentation_price = resolve_documentation_price(customer_fix) if includes_documentation else 0
    implementation_price = resolve_implementation_price(customer_fix) if includes_implementation else 0
    return SelectedLinePrices(
        documentation_price_cents=documentation_price,
        implementation_price_cents=implementation_price,
        line_total_cents=documentation_price + implementation_price,
    )


def calculate_quotation_totals(lines: list[SelectedLinePrices]) -> QuotationTotals:
    """Aggregate itemized values using integer addition only."""

    documentation_subtotal = sum(line.documentation_price_cents for line in lines)
    implementation_subtotal = sum(line.implementation_price_cents for line in lines)
    return QuotationTotals(
        documentation_subtotal_cents=documentation_subtotal,
        implementation_subtotal_cents=implementation_subtotal,
        grand_total_cents=documentation_subtotal + implementation_subtotal,
    )
