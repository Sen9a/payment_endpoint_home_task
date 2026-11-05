import uuid

from payment_api.constants import ErrorCode
from payment_api.exceptions import BadRequest


def validate_payment_method_id(value) -> uuid.UUID | None:
    """Validate the optional payment_method_id body field; returns a UUID."""
    if value is None:
        return None
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        raise BadRequest(message=f"'{value}' is not a valid payment_method_id",
                         error_code=ErrorCode.VALIDATION_ERROR)
