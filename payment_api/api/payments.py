"""Payment endpoint handlers — request/response adapters only.

All logic lives in `payment_api.services.payment.PaymentService`.
"""
from http import HTTPStatus
from typing import Any, Dict, Tuple

from flask import current_app

from payment_api.managers import CartManager, PaymentManager, PaymentMethodManager
from payment_api.services import MockPaymentProvider, PaymentService
from payment_api.validators import validate_cart_id, validate_payment_method_id


def _payment_service() -> PaymentService:
    return PaymentService(cart_manager=CartManager(),
                          payment_method_manager=PaymentMethodManager(),
                          payment_manager=PaymentManager(),
                          provider=MockPaymentProvider(),
                          logger=current_app.logger)


def start_payment(cart_id: str, body: Dict[str, Any] = None, **_kwargs) -> Tuple[dict, int]:
    """Start a payment for a cart. The body is optional; when omitted (or
    empty) the user's default payment method is charged."""
    body = body or {}
    payment = _payment_service().start_payment(
        cart_id=validate_cart_id(cart_id),
        payment_method_id=validate_payment_method_id(body.get('payment_method_id')),
    )
    return payment.to_dict(), HTTPStatus.CREATED.value
