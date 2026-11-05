"""Payment endpoint handlers — request/response adapters only.

All logic lives in `payment_api.services.payment.PaymentService`.
"""
import uuid
from http import HTTPStatus
from typing import Tuple

from flask import Blueprint, current_app, request

from payment_api.constants import ErrorCode
from payment_api.exceptions import BadRequest
from payment_api.managers import CartManager, PaymentManager, PaymentMethodManager
from payment_api.services import MockPaymentProvider, PaymentService
from payment_api.validators import validate_payment_method_id

bp = Blueprint('payments', __name__)


def _payment_service() -> PaymentService:
    return PaymentService(cart_manager=CartManager(),
                          payment_method_manager=PaymentMethodManager(),
                          payment_manager=PaymentManager(),
                          provider=MockPaymentProvider(),
                          logger=current_app.logger)


@bp.post('/carts/<uuid:cart_id>/payments')
def start_payment(cart_id: uuid.UUID) -> Tuple[dict, int]:
    """Start a payment for a cart. The body is optional JSON; when omitted
    (or empty) the user's default payment method is charged."""
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        raise BadRequest(message='Request body must be a JSON object',
                         error_code=ErrorCode.VALIDATION_ERROR)

    payment = _payment_service().start_payment(
        cart_id=cart_id,
        payment_method_id=validate_payment_method_id(body.get('payment_method_id')),
    )
    return payment.to_dict(), HTTPStatus.CREATED.value
