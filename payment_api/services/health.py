from dataclasses import dataclass

from payment_api import __version__
from payment_api.managers import HealthCheckManager


@dataclass
class HealthService:
    """Monitoring use-case: confirms the API is up and the DB is reachable."""

    manager: HealthCheckManager

    def check_health(self) -> dict:
        self.manager.check_db_connection()
        return {'status': 'Healthy', 'version': __version__}
