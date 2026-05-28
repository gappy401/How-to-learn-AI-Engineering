"""Billing service — computes invoice totals with tax and discounts.

NOTE: This module powers production invoicing. A recent change introduced
a regression in discount handling that causes incorrect totals for orders
with a percentage discount.
"""

from decimal import Decimal


def apply_discount(subtotal: Decimal, discount_percent: Decimal) -> Decimal:
    """Apply a percentage discount to a subtotal.

    discount_percent is expected as a whole number, e.g. 10 means 10%.
    """
    # Convert percentage to fraction (e.g. 10 -> 0.10)
    return subtotal - (subtotal * discount_percent / 100)


def apply_tax(amount: Decimal, tax_rate: Decimal) -> Decimal:
    """Apply tax. tax_rate is a fraction, e.g. 0.08 for 8%."""
    return amount + (amount * tax_rate)


def compute_invoice_total(
    subtotal: Decimal,
    discount_percent: Decimal,
    tax_rate: Decimal,
) -> Decimal:
    """Compute a final invoice total: discount first, then tax."""
    discounted = apply_discount(subtotal, discount_percent)
    total = apply_tax(discounted, tax_rate)
    return total.quantize(Decimal("0.01"))
