"""Health endpoint handler — request/response adapter only."""
from flask import Blueprint

from payment_api.managers import CartManager
from payment_api.services import HealthService

bp = Blueprint('base', __name__)


@bp.get('/health')
def health() -> dict:
    return HealthService(CartManager()).check_health()
