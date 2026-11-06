from typing import  Any


from payment_api.database.db import db_session
from payment_api.models import Payment


class PaymentManager:
    """Persistence for payments — no business logic here."""
    model = Payment

    @classmethod
    def add(cls, payment_payload: dict[str, Any]) -> Payment:
        """Stage a new payment row (flushed, not committed)."""
        payment = cls.model(**payment_payload)
        db_session.add(payment)
        db_session.flush()
        return payment

    @staticmethod
    def save(payment: Payment) -> Payment:
        db_session.commit()
        return payment
