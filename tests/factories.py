from decimal import Decimal

import factory
from factory.alchemy import SQLAlchemyModelFactory

from payment_api.constants import CartStatus
from payment_api.models import Cart, CartItem, Product, User, UserPaymentMethod

DEFAULT_PROVIDER_TOKEN = 'tok_test_visa'
FAIL_PROVIDER_TOKEN = 'tok_fail_visa'


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = None  # bound per-test in conftest
        sqlalchemy_session_persistence = 'commit'

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    name = factory.Sequence(lambda n: f'User {n}')


class ProductFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Product
        sqlalchemy_session = None
        sqlalchemy_session_persistence = 'commit'

    name = factory.Sequence(lambda n: f'Product {n}')
    price = Decimal('45.00')
    currency = 'USD'
    stock_quantity = 10


class CartFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Cart
        sqlalchemy_session = None
        sqlalchemy_session_persistence = 'commit'

    user = factory.SubFactory(UserFactory)
    status = CartStatus.ACTIVE


class CartItemFactory(SQLAlchemyModelFactory):
    class Meta:
        model = CartItem
        sqlalchemy_session = None
        sqlalchemy_session_persistence = 'commit'

    cart = factory.SubFactory(CartFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 1
    # the price is frozen on the row, like the real checkout flow
    unit_price = factory.LazyAttribute(lambda item: item.product.price)


class PaymentMethodFactory(SQLAlchemyModelFactory):
    class Meta:
        model = UserPaymentMethod
        sqlalchemy_session = None
        sqlalchemy_session_persistence = 'commit'

    user = factory.SubFactory(UserFactory)
    provider_token = DEFAULT_PROVIDER_TOKEN
    last_four = '4242'
    is_default = True
