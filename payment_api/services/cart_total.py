from dataclasses import dataclass
from decimal import Decimal

from payment_api.data_classes import CartTotal
from payment_api.models.cart import Cart
from payment_api.validators import validate_cart_currencies


@dataclass
class CartTotalService:
    """Stand-in for the payment total calculation service that the task
    describes as already existing (test_task.txt:13).

    It is the only place that knows how much to charge for a cart: the sum
    of quantity * unit_price over the cart items (unit_price is frozen on
    the cart item row, so the total is stable against later product price
    changes). PaymentService consumes the resulting CartTotal and never
    calculates anything itself.
    """
    @staticmethod
    def calculate(cart: Cart) -> CartTotal:
        currency = validate_cart_currencies(cart)
        amount = sum((item.unit_price * item.quantity for item in cart.items),
                     start=Decimal('0'))
        return CartTotal(amount=amount, currency=currency)
