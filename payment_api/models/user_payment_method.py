import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from payment_api.database.db import Base

if TYPE_CHECKING:
    from .payment import Payment
    from .user import User


class UserPaymentMethod(Base):
    """A saved card. provider_token is sent to the payment provider to charge
    the card; the real card number is never stored here."""
    __tablename__ = 'user_payment_methods'
    __table_args__ = (
        Index('idx_user_payment_methods_user_id', 'user_id'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          server_default=func.gen_random_uuid())
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))
    provider_token: Mapped[str] = mapped_column()
    last_four: Mapped[str | None] = mapped_column(String(4), nullable=True)
    is_default: Mapped[bool] = mapped_column(server_default='false')
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped['User'] = relationship(back_populates='payment_methods')
    payments: Mapped[List['Payment']] = relationship(back_populates='payment_method')

    def __repr__(self):
        return f'<UserPaymentMethod {self.id} (default={self.is_default})>'
