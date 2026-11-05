"""Health endpoint handler — request/response adapter only."""
from payment_api.managers import CartManager
from payment_api.services import HealthService


def health() -> dict:
    return HealthService(CartManager()).check_health()
