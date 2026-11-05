"""Add the payments table.

The base shop schema (users, products, carts, cart_items,
user_payment_methods) is applied separately via SQLMigrations.sql; this is
the new migration for the payment part designed in this task.

Revision ID: f3a9c1d2e4b5
Revises:
Create Date: 2026-11-05

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'f3a9c1d2e4b5'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True),
                  server_default=sa.func.gen_random_uuid(), nullable=False),
        sa.Column('cart_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_method_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='USD', nullable=False),
        sa.Column('status', sa.String(), server_default='pending', nullable=False),
        sa.Column('provider', sa.String(), server_default='mock', nullable=False),
        sa.Column('provider_reference', sa.String(), nullable=True),
        sa.Column('failure_reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'succeeded', 'failed')"),
        sa.CheckConstraint('amount >= 0'),
        sa.ForeignKeyConstraint(['cart_id'], ['carts.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        # keep payment history when the saved card is removed
        sa.ForeignKeyConstraint(['payment_method_id'], ['user_payment_methods.id'],
                                ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_payments_cart_id', 'payments', ['cart_id'])
    op.create_index('idx_payments_user_id', 'payments', ['user_id'])
    # a cart can be paid only once; retries after a failure are still possible
    op.create_index('uq_payments_succeeded_cart', 'payments', ['cart_id'],
                    unique=True,
                    postgresql_where=sa.text("status = 'succeeded'"))


def downgrade() -> None:
    op.drop_index('uq_payments_succeeded_cart', table_name='payments')
    op.drop_index('idx_payments_user_id', table_name='payments')
    op.drop_index('idx_payments_cart_id', table_name='payments')
    op.drop_table('payments')
