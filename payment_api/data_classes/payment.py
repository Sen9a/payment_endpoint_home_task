import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class PaymentDetails:
    """Public representation of a payment attempt."""
    payment_id: uuid.UUID
    cart_id: uuid.UUID
    user_id: uuid.UUID
    amount: Decimal
    currency: str
    status: str
    provider: str
    provider_reference: str | None
    created_at: datetime

    @classmethod
    def from_db_result(cls, db_result) -> 'PaymentDetails':
        return cls(
            payment_id=db_result.id,
            cart_id=db_result.cart_id,
            user_id=db_result.user_id,
            amount=db_result.amount,
            currency=db_result.currency,
            status=db_result.status,
            provider=db_result.provider,
            provider_reference=db_result.provider_reference,
            created_at=db_result.created_at,
        )

    def to_dict(self) -> dict:
        return {
            'payment_id': str(self.payment_id),
            'cart_id': str(self.cart_id),
            'user_id': str(self.user_id),
            'amount': f'{self.amount:.2f}',
            'currency': self.currency,
            'status': self.status,
            'provider': self.provider,
            'provider_reference': self.provider_reference,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
