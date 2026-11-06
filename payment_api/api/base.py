"""Health endpoint handler — request/response adapter only."""
from payment_api.managers import HealthCheckManager
from payment_api.services import HealthService


def health() -> dict:
    return HealthService(HealthCheckManager()).check_health()
