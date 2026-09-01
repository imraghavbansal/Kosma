from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from kosma_api.config import get_settings
from kosma_api.db.base import Base
from kosma_api.models import *  # noqa: F401,F403  (registers all models on Base.metadata)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # see kosma_api/db/session.py's comment - needed when DATABASE_URL
        # points at Supabase's transaction-mode pooler, as it does in
        # deployed environments (e.g. Railway) where the direct connection's
        # IPv6-only address isn't reachable.
        connect_args={"prepare_threshold": None},
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
