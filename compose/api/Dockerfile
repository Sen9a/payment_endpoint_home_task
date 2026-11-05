FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# install runtime dependencies first for better layer caching
COPY pyproject.toml poetry.lock ./
COPY payment_api ./payment_api
RUN pip install --no-cache-dir .

COPY alembic.ini server.py ./
COPY migrations ./migrations
COPY compose/api/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
