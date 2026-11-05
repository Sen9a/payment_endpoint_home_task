from payment_api import __version__
from payment_api.managers import CartManager


class HealthService:
    """Monitoring use-case: confirms the API is up and the DB is reachable."""

    def __init__(self, cart_manager: CartManager):
        self.cart_manager = cart_manager

    def check_health(self) -> dict:
        self.cart_manager.check_db_connection()
        return {'status': 'Healthy', 'version': __version__}
