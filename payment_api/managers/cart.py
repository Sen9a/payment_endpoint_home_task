import uuid

from sqlalchemy import select

from payment_api.database.db import db_session
from payment_api.models.cart import Cart


class CartManager:
    model = Cart

    @classmethod
    def get_by_id(cls,
                  cart_id: uuid.UUID,
                  for_update: bool = False) -> Cart | None:
        query = select(cls.model).where(cls.model.id == cart_id)
        if for_update:
            # serialize concurrent payment attempts on the same cart
            query = query.with_for_update()
        return db_session.execute(query).scalar_one_or_none()
