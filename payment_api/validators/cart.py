from typing import TYPE_CHECKING

from payment_api.constants import ErrorMessage, ErrorCode, CartStatus
from payment_api.exceptions import NotFound, Conflict, BadRequest
from payment_api.managers import CartManager
from payment_api.validators.base import _to_uuid

if TYPE_CHECKING:
    from payment_api.models import Cart


def validate_cart_id(cart_id: str) -> 'Cart':
    """Validate the cart_id path parameter; returns the payable cart."""
    cart_uuid = _to_uuid(cart_id, 'cart_id')
    cart = CartManager.get_by_id(cart_uuid, for_update=True)
    if cart is None:
        raise NotFound(message=ErrorMessage.CART_NOT_FOUND,
                       error_code=ErrorCode.CART_NOT_FOUND)
    match cart.status:
        case CartStatus.CHECKED_OUT:
            raise Conflict(message=ErrorMessage.CART_ALREADY_CHECKED_OUT,
                           error_code=ErrorCode.CART_ALREADY_CHECKED_OUT)
        case CartStatus.ABANDONED:
            raise Conflict(message=ErrorMessage.CART_NOT_PAYABLE,
                           error_code=ErrorCode.CART_NOT_PAYABLE)
        case _:
            return cart


def validate_cart_currencies(cart: 'Cart') -> str:
    """A payable cart is non-empty and single-currency; returns the currency."""
    if not cart.items:
        raise BadRequest(message=ErrorMessage.EMPTY_CART,
                         error_code=ErrorCode.EMPTY_CART)

    currencies = {item.product.currency for item in cart.items}
    if len(currencies) > 1:
        raise Conflict(message=ErrorMessage.MIXED_CURRENCIES,
                       error_code=ErrorCode.MIXED_CURRENCIES)
    return currencies.pop()
