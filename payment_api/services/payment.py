import logging
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from payment_api.constants import CartStatus, PaymentStatus
from payment_api.data_classes import PaymentDetails, ProviderChargeResult
from payment_api.managers import PaymentManager, PaymentMethodManager
from payment_api.services.cart_total import CartTotalService
from payment_api.services.provider import MockPaymentProvider
from payment_api.validators import (validate_cart_id,
                                    validate_payment_method_id,
                                    validate_payment_method,
                                    validate_default_payment_method,
                                    validate_charge_result)

if TYPE_CHECKING:
    from payment_api.models import Payment, UserPaymentMethod

@dataclass
class PaymentService:
    """Orchestrates the payment use-case: validation + provider charge +
    persistence. Managers are used for persistence only; the total comes
    from the (stand-in) total calculation service.
    """
    payment_method_manager: PaymentMethodManager
    payment_manager: PaymentManager
    total_service: CartTotalService
    provider: MockPaymentProvider
    logger: logging.Logger

    def start_payment(self,
                      cart_id: str,
                      payment_method_id: str | None = None) -> PaymentDetails:
        """Charge the user's card for the given cart.

        The cart row is locked (SELECT ... FOR UPDATE) for the whole attempt
        and everything commits in one transaction, so a concurrent or
        retried request can never charge the same cart twice.
        """
        payment_method_id = validate_payment_method_id(payment_method_id)
        cart = validate_cart_id(cart_id)
        total = self.total_service.calculate(cart)
        method = self._resolve_payment_method(cart.user_id, payment_method_id)

        payment = self.payment_manager.add({'cart_id': cart.id,
                                            'user_id': cart.user_id,
                                            'payment_method_id': method.id,
                                            'amount': total.amount,
                                            'currency': total.currency,
                                            'status': PaymentStatus.PENDING})
        result = self.provider_charge(method, payment)
        payment.status = PaymentStatus.SUCCEEDED
        payment.provider_reference = result.reference
        cart.status = CartStatus.CHECKED_OUT
        self.payment_manager.save(payment)
        self.logger.info('Payment %s for cart %s succeeded: %s %s',
                         payment.id, cart_id, payment.amount, payment.currency)
        return PaymentDetails.from_db_result(payment)

    def _resolve_payment_method(self,
                                user_id: uuid.UUID,
                                payment_method_id: uuid.UUID | None) -> 'UserPaymentMethod':
        """An explicit method must belong to the cart's owner; without one we
        fall back to the user's default card."""
        if payment_method_id is not None:
            method = self.payment_method_manager.get_for_user(payment_method_id, user_id)
            return validate_payment_method(method)
        method = self.payment_method_manager.get_default_for_user(user_id)
        return validate_default_payment_method(method)

    def provider_charge(self,
                        method: 'UserPaymentMethod',
                        payment: 'Payment') -> ProviderChargeResult:
        result = self.provider.charge(method.provider_token)
        if not result.success:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = result.error
            self.payment_manager.save(payment)
        validate_charge_result(result)
        return result