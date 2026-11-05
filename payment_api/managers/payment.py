import uuid
from typing import Optional

from sqlalchemy import select

from payment_api.database.db import db_session
from payment_api.models.payment import Payment


class PaymentManager:
    """Persistence for payments — no business logic here."""

    @staticmethod
    def add(payment: Payment) -> Payment:
        """Stage a new payment row (flushed, not committed)."""
        db_session.add(payment)
        db_session.flush()
        return payment

    @staticmethod
    def save(payment: Payment) -> Payment:
        db_session.commit()
        return payment
