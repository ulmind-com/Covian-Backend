import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import our app configuration and SQLAlchemy base
from app.core.config import settings
from app.db.base import Base

# This is the Alembic Config object, which provides access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Dynamically set the SQLAlchemy database URI from settings
# This ensures we have a single source of truth for configuration
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)

# Set the metadata of the models so Alembic can discover tables and run autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    This configures the context with just a URL and not a Engine,
    though an Engine is acceptable here as well. By skipping the Engine creation
    we don't even need a DB API to be installed.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """
    Helper function to execute migrations in a synchronous context.
    Called inside connection.run_sync() during online migrations.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    In this scenario we need to associate a connection with the context
    and execute migrations. We use the async engine to handle connection.
    """
    # Create the async engine from config
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"ssl": False},
    )

    async with connectable.connect() as connection:
        # Run migrations synchronously inside the async connection
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Run the async online migration using the event loop
    asyncio.run(run_migrations_online())
