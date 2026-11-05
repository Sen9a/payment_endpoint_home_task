"""Alembic environment.

The database URL comes from the DATABASE_URI environment variable (falling
back to payment_api.settings), so the same migrations run locally, in tests
and in Docker without editing alembic.ini.
"""
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from payment_api import models  # noqa: F401  register models on Base.metadata
from payment_api.database.db import Base
from payment_api import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

if not config.get_main_option('sqlalchemy.url'):
    config.set_main_option('sqlalchemy.url',
                           os.environ.get('DATABASE_URI', settings.DATABASE_URI))


def run_migrations_offline() -> None:
    context.configure(url=config.get_main_option('sqlalchemy.url'),
                      target_metadata=target_metadata,
                      literal_binds=True,
                      dialect_opts={'paramstyle': 'named'})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}),
                                     prefix='sqlalchemy.',
                                     poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
