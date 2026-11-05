"""HTTP error hierarchy rendered as {"error": {"code": ..., "message": ...}}."""
from http import HTTPStatus


class APIException(Exception):
    """Base API exception carrying an HTTP status and a stable error code."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR.value
    error_code: str = 'INTERNAL_ERROR'

    def __init__(self, message: str = None, error_code: str = None, status_code: int = None):
        self.message = message or HTTPStatus(self.status_code).phrase
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)

    def to_json(self) -> dict:
        return {"error": {"code": self.error_code, "message": self.message}}

    def __str__(self):
        return self.message


class BadRequest(APIException):
    status_code = HTTPStatus.BAD_REQUEST.value
    error_code = 'BAD_REQUEST'


class PaymentRequired(APIException):
    status_code = HTTPStatus.PAYMENT_REQUIRED.value
    error_code = 'PAYMENT_FAILED'


class NotFound(APIException):
    status_code = HTTPStatus.NOT_FOUND.value
    error_code = 'NOT_FOUND'


class Conflict(APIException):
    status_code = HTTPStatus.CONFLICT.value
    error_code = 'CONFLICT'


class InternalServerError(APIException):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
    error_code = 'INTERNAL_ERROR'
