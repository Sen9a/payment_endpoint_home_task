import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from payment_api.constants import PROVIDER_NAME, PaymentStatus
from payment_api.database.db import Base

if TYPE_CHECKING:
    from .cart import Cart
    from .user import User
    from .user_payment_method import UserPaymentMethod


class Payment(Base):
    """One payment attempt for a cart.

    A cart may have several attempts (e.g. after a decline) but at most one
    successful payment — enforced by the partial unique index
    uq_payments_succeeded_cart.
    """
    __tablename__ = 'payments'
    __table_args__ = (
        CheckConstraint(f"status IN ('{PaymentStatus.PENDING}', "
                        f"'{PaymentStatus.SUCCEEDED}', "
                        f"'{PaymentStatus.FAILED}')"),
        CheckConstraint('amount >= 0'),
        Index('idx_payments_cart_id', 'cart_id'),
        Index('idx_payments_user_id', 'user_id'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          server_default=func.gen_random_uuid())
    cart_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('carts.id'))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))
    payment_method_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey('user_payment_methods.id', ondelete='SET NULL'), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), server_default='USD')
    status: Mapped[str] = mapped_column(server_default=PaymentStatus.PENDING)
    provider: Mapped[str] = mapped_column(server_default=PROVIDER_NAME)
    provider_reference: Mapped[str | None] = mapped_column(nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    cart: Mapped['Cart'] = relationship(back_populates='payments')
    user: Mapped['User'] = relationship(back_populates='payments')
    payment_method: Mapped['UserPaymentMethod | None'] = relationship(back_populates='payments')

    def __repr__(self):
        return f'<Payment {self.id} ({self.status})>'
