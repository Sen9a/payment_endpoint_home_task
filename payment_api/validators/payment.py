import uuid

from payment_api.constants import ErrorCode
from payment_api.exceptions import BadRequest


def _to_uuid(value, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        raise BadRequest(message=f"'{value}' is not a valid {field}",
                         error_code=ErrorCode.VALIDATION_ERROR)


def validate_cart_id(cart_id: str) -> uuid.UUID:
    """Validate the cart_id path parameter; returns a UUID."""
    return _to_uuid(cart_id, 'cart_id')


def validate_payment_method_id(value) -> uuid.UUID | None:
    """Validate the optional payment_method_id body field; returns a UUID."""
    if value is None:
        return None
    return _to_uuid(value, 'payment_method_id')
