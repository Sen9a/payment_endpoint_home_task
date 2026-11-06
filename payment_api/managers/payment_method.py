import uuid

from sqlalchemy import select

from payment_api.database.db import db_session
from payment_api.models.user_payment_method import UserPaymentMethod


class PaymentMethodManager:
    """Persistence for saved payment methods — no business logic here."""

    model = UserPaymentMethod

    def get_default_for_user(self,
                             user_id: uuid.UUID) -> UserPaymentMethod | None:
        query = (select(self.model)
                 .where(self.model.user_id == user_id,
                        self.model.is_default.is_(True)))
        return db_session.execute(query).scalar_one_or_none()

    def get_for_user(self, payment_method_id: uuid.UUID,
                     user_id: uuid.UUID) -> UserPaymentMethod | None:
        query = (select(self.model)
                 .where(self.model.id == payment_method_id,
                        self.model.user_id == user_id))
        return db_session.execute(query).scalar_one_or_none()
