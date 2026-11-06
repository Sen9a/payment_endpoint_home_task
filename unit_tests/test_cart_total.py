"""Unit tests for the total-calculation stand-in service.

The currency validation collaborator is mocked out — it has its own test
module (test_validators.py) — so these tests isolate the math only.
"""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from payment_api.services.cart_total import CartTotalService


@pytest.fixture
def service():
    return CartTotalService()


@pytest.fixture
def validate_currencies():
    with patch('payment_api.services.cart_total.validate_cart_currencies',
               return_value='USD') as validator:
        yield validator


def _cart(*items):
    return SimpleNamespace(items=list(items))


def _item(unit_price, quantity):
    return SimpleNamespace(unit_price=unit_price, quantity=quantity)


def test_calculate_sums_unit_price_times_quantity(service, validate_currencies):
    cart = _cart(_item(Decimal('45.00'), 1), _item(Decimal('12.50'), 2))

    total = service.calculate(_cart(*cart.items))

    assert total.amount == Decimal('70.00')
    assert total.currency == 'USD'


def test_calculate_returns_the_currency_from_the_validator(service, validate_currencies):
    validate_currencies.return_value = 'EUR'

    total = service.calculate(_cart(_item(Decimal('1.00'), 1)))

    assert total.currency == 'EUR'


def test_calculate_uses_decimal_not_float(service, validate_currencies):
    total = service.calculate(_cart(_item(Decimal('0.10'), 3)))

    assert total.amount == Decimal('0.30')
    assert isinstance(total.amount, Decimal)
