import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from payment_api.database.db import Base

if TYPE_CHECKING:
    from .cart import Cart
    from .product import Product


class CartItem(Base):
    """unit_price is stored on the row so the price at checkout is stable
    if the product price changes later."""
    __tablename__ = 'cart_items'
    __table_args__ = (
        CheckConstraint('quantity > 0'),
        Index('idx_cart_items_cart_id', 'cart_id'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          server_default=func.gen_random_uuid())
    cart_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('carts.id', ondelete='CASCADE'))
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('products.id'))
    quantity: Mapped[int] = mapped_column()
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    cart: Mapped['Cart'] = relationship(back_populates='items')
    product: Mapped['Product'] = relationship(back_populates='cart_items')

    def __repr__(self):
        return f'<CartItem {self.quantity}x {self.unit_price}>'
