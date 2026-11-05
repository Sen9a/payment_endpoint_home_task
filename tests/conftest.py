import os
from collections import namedtuple

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from payment_api.app import create_app
from payment_api.database.db import db_session
from tests.factories import (CartFactory, CartItemFactory, PaymentMethodFactory,
                             ProductFactory, UserFactory)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_SQL_FILE = os.path.join(ROOT_DIR, 'SQLMigrations.sql')
ALEMBIC_INI = os.path.join(ROOT_DIR, 'alembic.ini')

TEST_DATABASE_URI = os.environ.get(
    'TEST_DATABASE_URI',
    'postgresql+psycopg://postgres:postgres@localhost:5432/payment_shop_test')

ALL_TABLES = ('payments', 'cart_items', 'carts',
              'user_payment_methods', 'products', 'users')

PayableCart = namedtuple('PayableCart', ['user', 'cart', 'payment_method'])


def _reset_schema(engine) -> None:
    """Start every test run from an empty schema."""
    with engine.begin() as conn:
        conn.execute(text('DROP SCHEMA public CASCADE'))
        conn.execute(text('CREATE SCHEMA public'))


def _apply_base_schema(engine) -> None:
    """Apply the task's base schema file (SQLMigrations.sql)."""
    with open(BASE_SQL_FILE) as sql_file:
        statements = [statement.strip()
                      for statement in sql_file.read().split(';')]
    with engine.begin() as conn:
        for statement in statements:
            if statement:
                conn.exec_driver_sql(statement)


def _run_migrations() -> None:
    """Apply the payments-table migration through the real Alembic path."""
    alembic_cfg = Config(ALEMBIC_INI)
    alembic_cfg.set_main_option('sqlalchemy.url', TEST_DATABASE_URI)
    command.upgrade(alembic_cfg, 'head')


@pytest.fixture(scope='session', autouse=True)
def database():
    engine = create_engine(TEST_DATABASE_URI)
    _reset_schema(engine)
    _apply_base_schema(engine)
    _run_migrations()
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables(database):
    with database.begin() as conn:
        conn.execute(text(f"TRUNCATE {', '.join(ALL_TABLES)} RESTART IDENTITY CASCADE"))
    yield
    db_session.remove()


@pytest.fixture
def app(database):
    return create_app(extra_config={'DATABASE_URI': TEST_DATABASE_URI})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    for model_factory in (UserFactory, ProductFactory, CartFactory,
                          CartItemFactory, PaymentMethodFactory):
        model_factory._meta.sqlalchemy_session = db_session
    yield db_session
    db_session.rollback()


@pytest.fixture
def payable_cart(db):
    """A user with a default card, an active cart and one item (1 x 45.00)."""
    user = UserFactory()
    cart = CartFactory(user=user)
    CartItemFactory(cart=cart)
    payment_method = PaymentMethodFactory(user=user)
    return PayableCart(user=user, cart=cart, payment_method=payment_method)
