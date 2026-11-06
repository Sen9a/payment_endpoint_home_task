import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from payment_api.constants import CartStatus
from payment_api.database.db import Base

if TYPE_CHECKING:
    from .cart_item import CartItem
    from .payment import Payment
    from .user import User


class Cart(Base):
    __tablename__ = 'carts'
    __table_args__ = (
        CheckConstraint(f"status IN ('{CartStatus.ACTIVE}', "
                        f"'{CartStatus.CHECKED_OUT}', "
                        f"'{CartStatus.ABANDONED}')"),
        Index('idx_carts_user_id', 'user_id'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          server_default=func.gen_random_uuid())
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(server_default=CartStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    user: Mapped['User'] = relationship(back_populates='carts')
    items: Mapped[List['CartItem']] = relationship(back_populates='cart',
                                                   cascade='all, delete-orphan')
    payments: Mapped[List['Payment']] = relationship(back_populates='cart')

    def __repr__(self):
        return f'<Cart {self.id} ({self.status})>'
