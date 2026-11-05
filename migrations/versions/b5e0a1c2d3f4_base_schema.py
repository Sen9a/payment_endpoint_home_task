"""Base shop schema (users, products, carts, cart_items, user_payment_methods).

The statements are taken verbatim from the task-provided SQLMigrations.sql
(including the sample data for local testing), so the whole schema is
managed by Alembic and `alembic upgrade head` works on an empty database.

Revision ID: b5e0a1c2d3f4
Revises:
Create Date: 2026-11-05

"""
from collections.abc import Sequence

from alembic import op

revision: str = 'b5e0a1c2d3f4'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Requires PostgreSQL 13 or later.
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # Users of the shop.
    op.execute("""
        CREATE TABLE users (
            id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            email      TEXT        NOT NULL UNIQUE,
            name       TEXT        NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # The physical products the shop sells.
    op.execute("""
        CREATE TABLE products (
            id             UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
            name           TEXT           NOT NULL,
            price          NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
            currency       CHAR(3)        NOT NULL DEFAULT 'USD',
            stock_quantity INTEGER        NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
            created_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            updated_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW()
        )
    """)

    # A shopping cart. A user can have many carts over time.
    # One cart is "active" at a time. The user pays for that cart.
    op.execute("""
        CREATE TABLE carts (
            id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id    UUID        NOT NULL REFERENCES users(id),
            status     TEXT        NOT NULL DEFAULT 'active'
                                   CHECK (status IN ('active', 'checked_out', 'abandoned')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute('CREATE INDEX idx_carts_user_id ON carts(user_id)')

    # The products a user added to a cart.
    # unit_price is stored on the row so the price at checkout is stable
    # if the product price changes later.
    op.execute("""
        CREATE TABLE cart_items (
            id         UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
            cart_id    UUID           NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
            product_id UUID           NOT NULL REFERENCES products(id),
            quantity   INTEGER        NOT NULL CHECK (quantity > 0),
            unit_price NUMERIC(12, 2) NOT NULL,
            created_at TIMESTAMPTZ    NOT NULL DEFAULT NOW()
        )
    """)
    op.execute('CREATE INDEX idx_cart_items_cart_id ON cart_items(cart_id)')

    # The payment methods a user has saved.
    # provider_token is the token from the external payment provider; the
    # real card number is not stored — the provider holds it.
    op.execute("""
        CREATE TABLE user_payment_methods (
            id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id        UUID        NOT NULL REFERENCES users(id),
            provider_token TEXT        NOT NULL,
            last_four      CHAR(4),
            is_default     BOOLEAN     NOT NULL DEFAULT FALSE,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute('CREATE INDEX idx_user_payment_methods_user_id ON user_payment_methods(user_id)')

    # Sample data for local testing.
    op.execute("""
        INSERT INTO users (id, email, name) VALUES
            ('11111111-1111-1111-1111-111111111111', 'alice@example.com', 'Alice'),
            ('22222222-2222-2222-2222-222222222222', 'bob@example.com',   'Bob')
    """)
    op.execute("""
        INSERT INTO products (id, name, price, currency, stock_quantity) VALUES
            ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Blue Kettle',   45.00, 'USD',  10),
            ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Wool Blanket',  89.99, 'USD',   5),
            ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'Ceramic Mug',   12.50, 'USD', 100)
    """)
    op.execute("""
        INSERT INTO carts (id, user_id, status) VALUES
            ('c1c1c1c1-c1c1-c1c1-c1c1-c1c1c1c1c1c1',
             '11111111-1111-1111-1111-111111111111',
             'active')
    """)
    op.execute("""
        INSERT INTO cart_items (cart_id, product_id, quantity, unit_price) VALUES
            ('c1c1c1c1-c1c1-c1c1-c1c1-c1c1c1c1c1c1',
             'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 1, 45.00),
            ('c1c1c1c1-c1c1-c1c1-c1c1-c1c1c1c1c1c1',
             'cccccccc-cccc-cccc-cccc-cccccccccccc', 2, 12.50)
    """)
    op.execute("""
        INSERT INTO user_payment_methods (id, user_id, provider_token, last_four, is_default) VALUES
            ('11111111-2222-3333-4444-555555555555',
             '11111111-1111-1111-1111-111111111111',
             'tok_test_alice_visa', '4242', TRUE)
    """)


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS user_payment_methods, cart_items, carts, products, users')
