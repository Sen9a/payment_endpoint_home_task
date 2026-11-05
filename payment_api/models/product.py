import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, TYPE_CHECKING

from sqlalchemy import CheckConstraint, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from payment_api.database.db import Base

if TYPE_CHECKING:
    from .cart_item import CartItem


class Product(Base):
    __tablename__ = 'products'
    __table_args__ = (
        CheckConstraint('price >= 0'),
        CheckConstraint('stock_quantity >= 0'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column()
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), server_default='USD')
    stock_quantity: Mapped[int] = mapped_column(server_default='0')
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    cart_items: Mapped[List['CartItem']] = relationship(back_populates='product')

    def __repr__(self):
        return f'<Product {self.name}>'
