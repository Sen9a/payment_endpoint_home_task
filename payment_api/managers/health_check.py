from sqlalchemy import select

from payment_api.database.db import db_session


class HealthCheckManager:
    """Manager for health check."""

    @staticmethod
    def check_db_connection() -> None:
        """Raise if the database is not reachable."""
        db_session.execute(select(1)).scalar()
