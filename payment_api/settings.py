"""Flat env-driven configuration module.

Every setting can be overridden with an environment variable; the values
below are development defaults only.
"""
import os
env = os.environ

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# --- Database -------------------------------------------------------------
DATABASE_URI = env.get(
    'DATABASE_URI',
    'postgresql+psycopg://postgres:postgres@localhost:5432/payment_shop'
)

# --- Payment provider -------------------------------------------------------
# Mock provider only: any provider token containing this marker is declined.
PROVIDER_FAIL_TOKEN_MARKER = env.get('PROVIDER_FAIL_TOKEN_MARKER', 'fail')

# --- Logging ----------------------------------------------------------------
LOG_LEVEL = env.get('LOG_LEVEL', 'INFO')
