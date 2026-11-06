"""Unit tests for PaymentService orchestration — every collaborator is mocked.

Only validate_cart_id is patched (it hits the database); the remaining
validators are pure functions and run for real, so the wiring between the
service and the validators is covered too.
"""
import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from payment_api.constants import CartStatus, PaymentStatus
from payment_api.data_classes import CartTotal, ProviderChargeResult
from payment_api.exceptions import BadRequest, PaymentRequired
from payment_api.models.payment import Payment
from payment_api.services.payment import PaymentService

CART_ID = str(uuid.uuid4())
TOTAL = CartTotal(amount=Decimal('70.00'), currency='USD')


@pytest.fixture
def collaborators():
    return SimpleNamespace(
        payment_method_manager=Mock(),
        payment_manager=Mock(),
        total_service=Mock(),
        provider=Mock(),
        logger=Mock(),
    )


@pytest.fixture
def service(collaborators):
    collaborators.total_service.calculate.return_value = TOTAL
    collaborators.payment_manager.add.side_effect = \
        lambda payload: Payment(**payload)
    return PaymentService(**vars(collaborators))


@pytest.fixture
def cart():
    return SimpleNamespace(id=uuid.UUID(CART_ID), user_id=uuid.uuid4(),
                           status=CartStatus.ACTIVE)


@pytest.fixture
def method():
    return SimpleNamespace(id=uuid.uuid4(), provider_token='tok_good_visa')


@pytest.fixture
def fetch_cart(cart):
    with patch('payment_api.services.payment.validate_cart_id',
               return_value=cart) as validator:
        yield validator


def test_success_charges_the_default_method_and_checks_out_the_cart(
        service, collaborators, fetch_cart, cart, method):
    collaborators.payment_method_manager.get_default_for_user.return_value = method
    collaborators.provider.charge.return_value = ProviderChargeResult(
        success=True, reference='mock_charge_1')

    result = service.start_payment(CART_ID)

    assert result.status == PaymentStatus.SUCCEEDED
    assert result.amount == TOTAL.amount
    assert result.currency == TOTAL.currency
    assert result.provider_reference == 'mock_charge_1'
    assert cart.status == CartStatus.CHECKED_OUT
    collaborators.provider.charge.assert_called_once_with('tok_good_visa')
    collaborators.payment_manager.save.assert_called_once()
    collaborators.payment_method_manager.get_for_user.assert_not_called()


def test_payment_row_is_built_from_the_total_service_output(
        service, collaborators, fetch_cart, cart, method):
    collaborators.payment_method_manager.get_default_for_user.return_value = method
    collaborators.provider.charge.return_value = ProviderChargeResult(success=True)

    service.start_payment(CART_ID)

    payload = collaborators.payment_manager.add.call_args[0][0]
    assert payload == {'cart_id': cart.id,
                       'user_id': cart.user_id,
                       'payment_method_id': method.id,
                       'amount': TOTAL.amount,
                       'currency': TOTAL.currency,
                       'status': PaymentStatus.PENDING}


def test_decline_records_the_failed_payment_before_raising(
        service, collaborators, fetch_cart, cart, method):
    collaborators.payment_method_manager.get_default_for_user.return_value = method
    collaborators.provider.charge.return_value = ProviderChargeResult(
        success=False, error='no funds')

    with pytest.raises(PaymentRequired):
        service.start_payment(CART_ID)

    payment = collaborators.payment_manager.save.call_args[0][0]
    assert payment.status == PaymentStatus.FAILED
    assert payment.failure_reason == 'no funds'
    # the decline must be persisted before the error propagates
    collaborators.payment_manager.save.assert_called_once()
    # and the cart must stay payable for a retry
    assert cart.status == CartStatus.ACTIVE


def test_explicit_payment_method_is_resolved_for_the_cart_owner(
        service, collaborators, fetch_cart, cart, method):
    collaborators.payment_method_manager.get_for_user.return_value = method
    collaborators.provider.charge.return_value = ProviderChargeResult(success=True)
    method_id = str(uuid.uuid4())

    service.start_payment(CART_ID, payment_method_id=method_id)

    collaborators.payment_method_manager.get_for_user.assert_called_once_with(
        uuid.UUID(method_id), cart.user_id)
    collaborators.payment_method_manager.get_default_for_user.assert_not_called()


def test_explicit_payment_method_of_another_user_is_rejected(
        service, collaborators, fetch_cart, cart):
    collaborators.payment_method_manager.get_for_user.return_value = None

    with pytest.raises(BadRequest):
        service.start_payment(CART_ID, payment_method_id=str(uuid.uuid4()))

    collaborators.provider.charge.assert_not_called()
    collaborators.payment_manager.add.assert_not_called()


def test_missing_default_method_is_rejected_before_charging(
        service, collaborators, fetch_cart, cart):
    collaborators.payment_method_manager.get_default_for_user.return_value = None

    with pytest.raises(BadRequest):
        service.start_payment(CART_ID)

    collaborators.provider.charge.assert_not_called()
    collaborators.payment_manager.add.assert_not_called()
