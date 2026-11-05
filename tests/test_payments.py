import uuid
from decimal import Decimal

from payment_api.constants import CartStatus, PaymentStatus
from payment_api.models import Payment
from tests.factories import (FAIL_PROVIDER_TOKEN, CartFactory, CartItemFactory,
                             PaymentMethodFactory, ProductFactory, UserFactory)

PUBLIC_PAYMENT_FIELDS = {'payment_id', 'cart_id', 'user_id', 'amount', 'currency',
                         'status', 'provider', 'provider_reference', 'created_at'}


def _get_payment(db, payment_id):
    return db.get(Payment, uuid.UUID(payment_id))


def _refresh(db, instance):
    """Re-attach a factory object after a request (the app teardown removes
    the scoped session) and reload it from the database."""
    db.add(instance)
    db.refresh(instance)
    return instance


# --- success path -----------------------------------------------------------


def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'Healthy'


def test_start_payment_success(client, db, payable_cart):
    response = client.post(f'/carts/{payable_cart.cart.id}/payments')
    assert response.status_code == 201
    body = response.json()
    assert body['status'] == PaymentStatus.SUCCEEDED
    assert body['amount'] == '45.00'
    assert body['currency'] == 'USD'
    assert body['cart_id'] == str(payable_cart.cart.id)
    assert body['user_id'] == str(payable_cart.user.id)
    assert body['provider'] == 'mock'
    assert body['provider_reference'].startswith('mock_charge_')

    payment = _get_payment(db, body['payment_id'])
    assert payment.status == PaymentStatus.SUCCEEDED
    assert payment.payment_method_id == payable_cart.payment_method.id
    _refresh(db, payable_cart.cart)
    assert payable_cart.cart.status == CartStatus.CHECKED_OUT


def test_payment_response_has_exact_public_shape(client, payable_cart):
    """Fails loudly if PaymentDetails ever grows a field — the public shape
    is defined solely by PaymentDetails.to_dict() and must not change
    silently."""
    response = client.post(f'/carts/{payable_cart.cart.id}/payments')
    assert response.status_code == 201
    assert set(response.json()) == PUBLIC_PAYMENT_FIELDS


def test_payment_total_sums_quantities(client, db):
    user = UserFactory()
    cart = CartFactory(user=user)
    kettle = ProductFactory(price=Decimal('45.00'))
    mug = ProductFactory(price=Decimal('12.50'))
    CartItemFactory(cart=cart, product=kettle, quantity=1)
    CartItemFactory(cart=cart, product=mug, quantity=2)
    PaymentMethodFactory(user=user)

    response = client.post(f'/carts/{cart.id}/payments')
    assert response.status_code == 201
    assert response.json()['amount'] == '70.00'


def test_payment_total_uses_price_frozen_on_cart_item(client, db, payable_cart):
    """unit_price is frozen on the cart item, so later product price changes
    do not affect how much is charged."""
    item = payable_cart.cart.items[0]
    item.product.price = Decimal('999.00')
    db.commit()

    response = client.post(f'/carts/{payable_cart.cart.id}/payments')
    assert response.status_code == 201
    assert response.json()['amount'] == '45.00'


def test_payment_with_explicit_payment_method(client, db, payable_cart):
    other_method = PaymentMethodFactory(user=payable_cart.user,
                                        provider_token='tok_test_mastercard',
                                        last_four='5555', is_default=False)
    response = client.post(f'/carts/{payable_cart.cart.id}/payments',
                           json={'payment_method_id': str(other_method.id)})
    assert response.status_code == 201
    payment = _get_payment(db, response.json()['payment_id'])
    assert payment.payment_method_id == other_method.id


# --- cart state -------------------------------------------------------------


def test_payment_for_missing_cart(client):
    response = client.post(f'/carts/{uuid.uuid4()}/payments')
    assert response.status_code == 404
    assert response.json()['error']['code'] == 'CART_NOT_FOUND'


def test_payment_for_non_uuid_cart_id(client):
    # rejected by the OpenAPI uuid format at request-validation level
    response = client.post('/carts/not-a-uuid/payments')
    assert response.status_code == 400
    assert response.json()['error']['code'] == 'VALIDATION_ERROR'


def test_payment_for_checked_out_cart(client, db, payable_cart):
    payable_cart.cart.status = CartStatus.CHECKED_OUT
    db.commit()

    response = client.post(f'/carts/{payable_cart.cart.id}/payments')
    assert response.status_code == 409
    assert response.json()['error']['code'] == 'CART_ALREADY_CHECKED_OUT'


def test_payment_for_abandoned_cart(client, db, payable_cart):
    payable_cart.cart.status = CartStatus.ABANDONED
    db.commit()

    response = client.post(f'/carts/{payable_cart.cart.id}/payments')
    assert response.status_code == 409
    assert response.json()['error']['code'] == 'CART_NOT_PAYABLE'


def test_second_payment_attempt_is_rejected(client, payable_cart):
    first = client.post(f'/carts/{payable_cart.cart.id}/payments')
    assert first.status_code == 201
    # a retried/duplicate request must not charge the card again
    second = client.post(f'/carts/{payable_cart.cart.id}/payments')
    assert second.status_code == 409
    assert second.json()['error']['code'] == 'CART_ALREADY_CHECKED_OUT'


def test_payment_for_empty_cart(client, db):
    user = UserFactory()
    cart = CartFactory(user=user)
    PaymentMethodFactory(user=user)

    response = client.post(f'/carts/{cart.id}/payments')
    assert response.status_code == 400
    assert response.json()['error']['code'] == 'EMPTY_CART'


def test_payment_for_mixed_currency_cart(client, db):
    user = UserFactory()
    cart = CartFactory(user=user)
    CartItemFactory(cart=cart, product=ProductFactory(currency='USD'))
    CartItemFactory(cart=cart, product=ProductFactory(currency='EUR'))
    PaymentMethodFactory(user=user)

    response = client.post(f'/carts/{cart.id}/payments')
    assert response.status_code == 409
    assert response.json()['error']['code'] == 'MIXED_CURRENCIES'


# --- payment method ---------------------------------------------------------


def test_payment_without_payment_method(client, db):
    user = UserFactory()
    cart = CartFactory(user=user)
    CartItemFactory(cart=cart)

    response = client.post(f'/carts/{cart.id}/payments')
    assert response.status_code == 400
    assert response.json()['error']['code'] == 'NO_PAYMENT_METHOD'


def test_payment_method_must_belong_to_cart_owner(client, db, payable_cart):
    stranger_method = PaymentMethodFactory(user=UserFactory())
    response = client.post(f'/carts/{payable_cart.cart.id}/payments',
                           json={'payment_method_id': str(stranger_method.id)})
    assert response.status_code == 400
    assert response.json()['error']['code'] == 'PAYMENT_METHOD_NOT_FOUND'


def test_payment_with_malformed_payment_method_id(client, payable_cart):
    response = client.post(f'/carts/{payable_cart.cart.id}/payments',
                           json={'payment_method_id': 'not-a-uuid'})
    assert response.status_code == 400
    assert response.json()['error']['code'] == 'VALIDATION_ERROR'


# --- provider failures ------------------------------------------------------


def test_payment_declined_by_provider(client, db, payable_cart):
    payable_cart.payment_method.provider_token = FAIL_PROVIDER_TOKEN
    db.commit()

    response = client.post(f'/carts/{payable_cart.cart.id}/payments')
    assert response.status_code == 402
    assert response.json()['error']['code'] == 'PAYMENT_FAILED'

    # the failed attempt is recorded and the cart stays payable
    payment = db.query(Payment).filter_by(cart_id=payable_cart.cart.id).one()
    assert payment.status == PaymentStatus.FAILED
    assert payment.failure_reason is not None
    assert payment.provider_reference is None
    _refresh(db, payable_cart.cart)
    assert payable_cart.cart.status == CartStatus.ACTIVE


def test_payment_retry_after_decline_can_succeed(client, db, payable_cart):
    payable_cart.payment_method.provider_token = FAIL_PROVIDER_TOKEN
    db.commit()
    assert client.post(f'/carts/{payable_cart.cart.id}/payments').status_code == 402

    # the user fixes the card (new provider token) and retries
    db.add(payable_cart.payment_method)  # re-attach after the request teardown
    payable_cart.payment_method.provider_token = 'tok_test_visa'
    db.commit()
    response = client.post(f'/carts/{payable_cart.cart.id}/payments')
    assert response.status_code == 201
    assert response.json()['status'] == PaymentStatus.SUCCEEDED

    attempts = db.query(Payment).filter_by(cart_id=payable_cart.cart.id).all()
    assert sorted(attempt.status for attempt in attempts) == [PaymentStatus.FAILED,
                                                              PaymentStatus.SUCCEEDED]
