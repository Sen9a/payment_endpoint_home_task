from decimal import Decimal

from payment_api.constants import ErrorCode, ErrorMessage
from payment_api.data_classes import CartTotal
from payment_api.exceptions import BadRequest, Conflict
from payment_api.models.cart import Cart


class CartTotalService:
    """Stand-in for the existing payment total calculation service.

    The task provides this service as a given; here it simply sums
    quantity * unit_price over the cart items (unit_price is frozen on the
    cart item row, so the total is stable against later product price
    changes).
    """

    @staticmethod
    def calculate(cart: Cart) -> CartTotal:
        if not cart.items:
            raise BadRequest(message=ErrorMessage.EMPTY_CART,
                             error_code=ErrorCode.EMPTY_CART)

        currencies = {item.product.currency for item in cart.items}
        if len(currencies) > 1:
            raise Conflict(message=ErrorMessage.MIXED_CURRENCIES,
                           error_code=ErrorCode.MIXED_CURRENCIES)

        amount = sum((item.unit_price * item.quantity for item in cart.items),
                     start=Decimal('0'))
        return CartTotal(amount=amount, currency=currencies.pop())
