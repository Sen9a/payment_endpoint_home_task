"""Error codes, messages and shared domain constants."""


class ErrorCode:
    BAD_REQUEST = 'BAD_REQUEST'
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    CART_NOT_FOUND = 'CART_NOT_FOUND'
    CART_NOT_PAYABLE = 'CART_NOT_PAYABLE'
    CART_ALREADY_CHECKED_OUT = 'CART_ALREADY_CHECKED_OUT'
    EMPTY_CART = 'EMPTY_CART'
    MIXED_CURRENCIES = 'MIXED_CURRENCIES'
    NO_PAYMENT_METHOD = 'NO_PAYMENT_METHOD'
    PAYMENT_METHOD_NOT_FOUND = 'PAYMENT_METHOD_NOT_FOUND'
    PAYMENT_FAILED = 'PAYMENT_FAILED'
    NOT_FOUND = 'NOT_FOUND'
    METHOD_NOT_ALLOWED = 'METHOD_NOT_ALLOWED'
    DB_ERROR = 'DB_ERROR'
    INTERNAL_ERROR = 'INTERNAL_ERROR'


class ErrorMessage:
    CART_NOT_FOUND = 'Cart not found'
    CART_NOT_PAYABLE = 'Cart is abandoned and cannot be paid'
    CART_ALREADY_CHECKED_OUT = 'Cart has already been paid for'
    EMPTY_CART = 'Cart has no items'
    MIXED_CURRENCIES = 'Cart items use more than one currency; cannot charge a single payment'
    NO_PAYMENT_METHOD = 'User has no payment method on file'
    PAYMENT_METHOD_NOT_FOUND = 'Payment method not found for this user'
    PAYMENT_FAILED = 'The payment provider declined the charge'
    DB_ERROR = 'A database error occurred'
    INTERNAL_ERROR = 'An unexpected internal error occurred'


class CartStatus:
    ACTIVE = 'active'
    CHECKED_OUT = 'checked_out'
    ABANDONED = 'abandoned'


class PaymentStatus:
    PENDING = 'pending'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


PROVIDER_NAME = 'mock'

STATUS_TO_CODE = {
    400: ErrorCode.VALIDATION_ERROR,
    401: 'UNAUTHORIZED',
    403: 'FORBIDDEN',
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
    415: 'UNSUPPORTED_MEDIA_TYPE',
    500: ErrorCode.INTERNAL_ERROR,
}
