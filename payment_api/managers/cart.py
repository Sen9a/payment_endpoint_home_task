import uuid
from typing import Optional

from sqlalchemy import select

from payment_api.database.db import db_session
from payment_api.models.cart import Cart


class CartManager:
    """Persistence for carts — no business logic here."""

    @staticmethod
    def check_db_connection() -> None:
        """Raise if the database is not reachable."""
        db_session.execute(select(1)).scalar()

    @staticmethod
    def get_by_id(cart_id: uuid.UUID, for_update: bool = False) -> Optional[Cart]:
        query = select(Cart).where(Cart.id == cart_id)
        if for_update:
            # serialize concurrent payment attempts on the same cart
            query = query.with_for_update()
        return db_session.execute(query).scalar_one_or_none()
