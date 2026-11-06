import uuid

from payment_api import settings
from payment_api.data_classes import ProviderChargeResult


class MockPaymentProvider:
    """Mock stand-in for the real payment provider — no network calls.

    Deterministic by design: any provider token containing the configured
    fail marker (default 'fail', e.g. 'tok_fail_visa') is declined, every
    other token is charged successfully.
    """

    @staticmethod
    def charge(provider_token: str) -> ProviderChargeResult:
        fail_marker = settings.PROVIDER_FAIL_TOKEN_MARKER
        if fail_marker in provider_token:
            return ProviderChargeResult(
                success=False,
                error=f'Card declined by mock provider (token marker: {fail_marker})',
            )
        return ProviderChargeResult(success=True,
                                    reference=f'mock_charge_{uuid.uuid4().hex}')
