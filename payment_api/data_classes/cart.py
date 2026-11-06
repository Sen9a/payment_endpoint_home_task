from dataclasses import dataclass
from decimal import Decimal


@dataclass
class CartTotal:
    """How much to charge for a cart, as produced by the total-calculation
    service (see payment_api.services.cart_total)."""
    amount: Decimal
    currency: str
