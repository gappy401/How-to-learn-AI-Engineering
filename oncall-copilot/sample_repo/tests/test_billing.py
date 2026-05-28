"""Tests for the billing service.

These encode the *correct* expected behavior. They currently FAIL because
of the discount regression in src/billing.py.
"""

from decimal import Decimal

from src.billing import apply_discount, apply_tax, compute_invoice_total


def test_apply_discount_ten_percent():
    # 10% off 100.00 -> 90.00
    assert apply_discount(Decimal("100.00"), Decimal("10")) == Decimal("90.00")


def test_apply_discount_zero():
    assert apply_discount(Decimal("50.00"), Decimal("0")) == Decimal("50.00")


def test_apply_tax_eight_percent():
    assert apply_tax(Decimal("100.00"), Decimal("0.08")) == Decimal("108.00")


def test_compute_invoice_total():
    # 200.00, 25% off -> 150.00, +8% tax -> 162.00
    total = compute_invoice_total(
        Decimal("200.00"), Decimal("25"), Decimal("0.08")
    )
    assert total == Decimal("162.00")
