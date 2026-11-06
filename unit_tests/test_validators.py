"""Unit tests for the validators — the only layer allowed to raise."""
import uuid
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from payment_api.constants import CartStatus, ErrorCode
from payment_api.data_classes import ProviderChargeResult
from payment_api.exceptions import BadRequest, Conflict, NotFound, PaymentRequired
from payment_api.validators import (validate_cart_currencies, validate_cart_id,
                                    validate_charge_result,
                                    validate_default_payment_method,
                                    validate_payment_method,
                                    validate_payment_method_id)


# --- validate_payment_method_id -------------------------------------------------

def test_payment_method_id_none_passes_through():
    assert validate_payment_method_id(None) is None


def test_payment_method_id_parses_a_uuid_string():
    value = str(uuid.uuid4())

    assert validate_payment_method_id(value) == uuid.UUID(value)


def test_payment_method_id_rejects_garbage():
    with pytest.raises(BadRequest) as exc_info:
        validate_payment_method_id('not-a-uuid')

    assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR


# --- validate_payment_method / validate_default_payment_method -------------------

def test_validate_payment_method_returns_the_method():
    method = Mock()

    assert validate_payment_method(method) is method


def test_validate_payment_method_rejects_missing_method():
    with pytest.raises(BadRequest) as exc_info:
        validate_payment_method(None)

    assert exc_info.value.error_code == ErrorCode.PAYMENT_METHOD_NOT_FOUND


def test_validate_default_payment_method_rejects_missing_default():
    with pytest.raises(BadRequest) as exc_info:
        validate_default_payment_method(None)

    assert exc_info.value.error_code == ErrorCode.NO_PAYMENT_METHOD


# --- validate_charge_result -------------------------------------------------------

def test_validate_charge_result_passes_on_success():
    validate_charge_result(ProviderChargeResult(success=True, reference='ref'))


def test_validate_charge_result_raises_on_decline():
    with pytest.raises(PaymentRequired) as exc_info:
        validate_charge_result(ProviderChargeResult(success=False, error='no funds'))

    assert exc_info.value.error_code == ErrorCode.PAYMENT_FAILED


# --- validate_cart_currencies ------------------------------------------------------

def _cart_with_currencies(*currencies):
    items = [SimpleNamespace(product=SimpleNamespace(currency=c)) for c in currencies]
    return SimpleNamespace(items=items)


def test_cart_currencies_returns_the_single_currency():
    assert validate_cart_currencies(_cart_with_currencies('USD', 'USD')) == 'USD'


def test_cart_currencies_rejects_an_empty_cart():
    with pytest.raises(BadRequest) as exc_info:
        validate_cart_currencies(SimpleNamespace(items=[]))

    assert exc_info.value.error_code == ErrorCode.EMPTY_CART


def test_cart_currencies_rejects_mixed_currencies():
    with pytest.raises(Conflict) as exc_info:
        validate_cart_currencies(_cart_with_currencies('USD', 'EUR'))

    assert exc_info.value.error_code == ErrorCode.MIXED_CURRENCIES


# --- validate_cart_id --------------------------------------------------------------

@pytest.fixture
def cart_manager():
    with patch('payment_api.validators.cart.CartManager') as manager:
        yield manager


def _cart(status):
    return SimpleNamespace(id=uuid.uuid4(), status=status)


def test_cart_id_returns_an_active_cart(cart_manager):
    cart = _cart(CartStatus.ACTIVE)
    cart_manager.get_by_id.return_value = cart
    cart_id = str(uuid.uuid4())

    result = validate_cart_id(cart_id)

    assert result is cart
    # the row must be locked for the whole payment attempt
    cart_manager.get_by_id.assert_called_once_with(uuid.UUID(cart_id), for_update=True)


def test_cart_id_rejects_a_missing_cart(cart_manager):
    cart_manager.get_by_id.return_value = None

    with pytest.raises(NotFound) as exc_info:
        validate_cart_id(str(uuid.uuid4()))

    assert exc_info.value.error_code == ErrorCode.CART_NOT_FOUND


def test_cart_id_rejects_a_checked_out_cart(cart_manager):
    cart_manager.get_by_id.return_value = _cart(CartStatus.CHECKED_OUT)

    with pytest.raises(Conflict) as exc_info:
        validate_cart_id(str(uuid.uuid4()))

    assert exc_info.value.error_code == ErrorCode.CART_ALREADY_CHECKED_OUT


def test_cart_id_rejects_an_abandoned_cart(cart_manager):
    cart_manager.get_by_id.return_value = _cart(CartStatus.ABANDONED)

    with pytest.raises(Conflict) as exc_info:
        validate_cart_id(str(uuid.uuid4()))

    assert exc_info.value.error_code == ErrorCode.CART_NOT_PAYABLE


def test_cart_id_rejects_a_non_uuid(cart_manager):
    with pytest.raises(BadRequest) as exc_info:
        validate_cart_id('not-a-uuid')

    assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR
    cart_manager.get_by_id.assert_not_called()
