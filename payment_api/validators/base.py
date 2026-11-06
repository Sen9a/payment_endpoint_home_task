import uuid

from payment_api.constants import ErrorCode
from payment_api.exceptions import BadRequest


def _to_uuid(value, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        raise BadRequest(message=f"'{value}' is not a valid {field}",
                         error_code=ErrorCode.VALIDATION_ERROR)
