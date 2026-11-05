import logging
import uuid

from payment_api.constants import CartStatus, ErrorCode, ErrorMessage, PaymentStatus
from payment_api.data_classes import PaymentDetails
from payment_api.exceptions import BadRequest, Conflict, NotFound, PaymentRequired
from payment_api.managers import CartManager, PaymentManager, PaymentMethodManager
from payment_api.models.payment import Payment
from payment_api.models.user_payment_method import UserPaymentMethod
from payment_api.services.cart_total import CartTotalService
from payment_api.services.provider import MockPaymentProvider


class PaymentService:
    """Orchestrates the payment use-case: validation + provider charge +
    persistence. Managers are used for persistence only.
    """

    def __init__(self,
                 cart_manager: CartManager,
                 payment_method_manager: PaymentMethodManager,
                 payment_manager: PaymentManager,
                 provider: MockPaymentProvider,
                 logger: logging.Logger):
        self.cart_manager = cart_manager
        self.payment_method_manager = payment_method_manager
        self.payment_manager = payment_manager
        self.provider = provider
        self.logger = logger

    def start_payment(self,
                      cart_id: uuid.UUID,
                      payment_method_id: uuid.UUID | None = None) -> PaymentDetails:
        """Charge the user's card for the given cart.

        The cart row is locked (SELECT ... FOR UPDATE) for the whole attempt
        and everything commits in one transaction, so a concurrent or
        retried request can never charge the same cart twice.
        """
        cart = self._get_payable_cart(cart_id)
        total = CartTotalService.calculate(cart)
        method = self._resolve_payment_method(cart.user_id, payment_method_id)

        payment = self.payment_manager.add(Payment(
            cart_id=cart.id,
            user_id=cart.user_id,
            payment_method_id=method.id,
            amount=total.amount,
            currency=total.currency,
            status=PaymentStatus.PENDING,
        ))

        result = self.provider.charge(method.provider_token, total.amount, total.currency)

        if not result.success:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = result.error
            self.payment_manager.save(payment)
            self.logger.info('Payment %s for cart %s declined: %s',
                             payment.id, cart_id, result.error)
            raise PaymentRequired(message=ErrorMessage.PAYMENT_FAILED,
                                  error_code=ErrorCode.PAYMENT_FAILED)

        payment.status = PaymentStatus.SUCCEEDED
        payment.provider_reference = result.reference
        cart.status = CartStatus.CHECKED_OUT
        self.payment_manager.save(payment)
        self.logger.info('Payment %s for cart %s succeeded: %s %s',
                         payment.id, cart_id, payment.amount, payment.currency)
        return PaymentDetails.from_db_result(payment)

    def _get_payable_cart(self, cart_id: uuid.UUID):
        cart = self.cart_manager.get_by_id(cart_id, for_update=True)
        if cart is None:
            raise NotFound(message=ErrorMessage.CART_NOT_FOUND,
                           error_code=ErrorCode.CART_NOT_FOUND)
        if cart.status == CartStatus.CHECKED_OUT:
            raise Conflict(message=ErrorMessage.CART_ALREADY_CHECKED_OUT,
                           error_code=ErrorCode.CART_ALREADY_CHECKED_OUT)
        if cart.status == CartStatus.ABANDONED:
            raise Conflict(message=ErrorMessage.CART_NOT_PAYABLE,
                           error_code=ErrorCode.CART_NOT_PAYABLE)
        return cart

    def _resolve_payment_method(self,
                                user_id: uuid.UUID,
                                payment_method_id: uuid.UUID | None) -> UserPaymentMethod:
        """An explicit method must belong to the cart's owner; without one we
        fall back to the user's default card."""
        if payment_method_id is not None:
            method = self.payment_method_manager.get_for_user(payment_method_id, user_id)
            if method is None:
                raise BadRequest(message=ErrorMessage.PAYMENT_METHOD_NOT_FOUND,
                                 error_code=ErrorCode.PAYMENT_METHOD_NOT_FOUND)
            return method
        method = self.payment_method_manager.get_default_for_user(user_id)
        if method is None:
            raise BadRequest(message=ErrorMessage.NO_PAYMENT_METHOD,
                             error_code=ErrorCode.NO_PAYMENT_METHOD)
        return method
