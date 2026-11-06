import uuid
from typing import TYPE_CHECKING

from payment_api.constants import ErrorCode, ErrorMessage, PaymentStatus
from payment_api.exceptions import BadRequest, PaymentRequired
from payment_api.validators.base import _to_uuid
from payment_api.managers import PaymentManager

if TYPE_CHECKING:
    from payment_api.data_classes import ProviderChargeResult
    from payment_api.models import UserPaymentMethod, Payment


def validate_payment_method_id(value) -> uuid.UUID | None:
    """Validate the optional payment_method_id body field; returns a UUID."""
    if value is None:
        return None
    return _to_uuid(value, 'payment_method_id')


def validate_payment_method(method: 'UserPaymentMethod | None') -> 'UserPaymentMethod':
    """An explicitly chosen method must exist for the cart's owner."""
    if method is None:
        raise BadRequest(message=ErrorMessage.PAYMENT_METHOD_NOT_FOUND,
                         error_code=ErrorCode.PAYMENT_METHOD_NOT_FOUND)
    return method


def validate_default_payment_method(method: 'UserPaymentMethod | None') -> 'UserPaymentMethod':
    """Without an explicit method the user must have a default card."""
    if method is None:
        raise BadRequest(message=ErrorMessage.NO_PAYMENT_METHOD,
                         error_code=ErrorCode.NO_PAYMENT_METHOD)
    return method


def validate_charge_result(result: 'ProviderChargeResult') -> None:
    """A declined provider charge fails the payment attempt."""
    if not result.success:
        raise PaymentRequired(message=ErrorMessage.PAYMENT_FAILED,
                              error_code=ErrorCode.PAYMENT_FAILED)
