import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from payment_api.database.db import Base

if TYPE_CHECKING:
    from .cart import Cart
    from .payment import Payment
    from .user_payment_method import UserPaymentMethod


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          server_default=func.gen_random_uuid())
    email: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    carts: Mapped[List['Cart']] = relationship(back_populates='user')
    payment_methods: Mapped[List['UserPaymentMethod']] = relationship(back_populates='user')
    payments: Mapped[List['Payment']] = relationship(back_populates='user')

    def __repr__(self):
        return f'<User {self.email}>'
