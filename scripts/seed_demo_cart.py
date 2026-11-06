#!/usr/bin/env python3
"""Seed a fresh payable cart for presenting the payment endpoint.

Every run creates a brand-new demo user, default payment method, cart and
cart items, so the endpoint can be demoed as many times as needed — each
printed cart_id is payable exactly once.

Usage:
    .venv/bin/python scripts/seed_demo_cart.py          # charge will succeed
    .venv/bin/python scripts/seed_demo_cart.py --fail   # provider declines it
"""
import argparse
import uuid
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from payment_api import settings
from payment_api.models import Cart, CartItem, Product, User, UserPaymentMethod

DEMO_PRODUCT = {'name': 'Demo Product', 'price': Decimal('45.00'),
                'currency': 'USD', 'stock_quantity': 10}
QUANTITY = 2


def seed_cart(fail: bool) -> uuid.UUID:
    engine = create_engine(settings.DATABASE_URI)
    with Session(engine) as session, session.begin():
        product = session.scalar(select(Product).limit(1))
        if product is None:
            product = Product(**DEMO_PRODUCT)

        token = 'tok_fail_visa' if fail else 'tok_demo_visa'
        user = User(email=f'demo-{uuid.uuid4().hex[:8]}@example.com',
                    name='Demo User')
        UserPaymentMethod(user=user, provider_token=token,
                          last_four='4242', is_default=True)
        cart = Cart(user=user)
        CartItem(cart=cart, product=product,
                 quantity=QUANTITY, unit_price=product.price)
        session.add(cart)
        session.flush()
        return cart.id, product.price, product.currency


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--fail', action='store_true',
                        help='seed a declining card to present the 402 path')
    args = parser.parse_args()

    cart_id, unit_price, currency = seed_cart(args.fail)
    print(f'Payable cart: {cart_id}  ({QUANTITY} x {unit_price} = '
          f'{unit_price * QUANTITY} {currency}, card will '
          f'{"be declined" if args.fail else "succeed"})')
    print()
    print(f'curl -X POST http://127.0.0.1:8080/carts/{cart_id}/payments \\')
    print("     -H 'Content-Type: application/json' -d '{}'")


if __name__ == '__main__':
    main()
