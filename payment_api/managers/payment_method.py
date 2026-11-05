import uuid
from typing import Optional

from sqlalchemy import select

from payment_api.database.db import db_session
from payment_api.models.user_payment_method import UserPaymentMethod


class PaymentMethodManager:
    """Persistence for saved payment methods — no business logic here."""

    @staticmethod
    def get_default_for_user(user_id: uuid.UUID) -> Optional[UserPaymentMethod]:
        query = (select(UserPaymentMethod)
                 .where(UserPaymentMethod.user_id == user_id,
                        UserPaymentMethod.is_default.is_(True)))
        return db_session.execute(query).scalar_one_or_none()

    @staticmethod
    def get_for_user(payment_method_id: uuid.UUID,
                     user_id: uuid.UUID) -> Optional[UserPaymentMethod]:
        query = (select(UserPaymentMethod)
                 .where(UserPaymentMethod.id == payment_method_id,
                        UserPaymentMethod.user_id == user_id))
        return db_session.execute(query).scalar_one_or_none()
