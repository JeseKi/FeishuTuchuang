from logging.config import fileConfig
import sys
from pathlib import Path

# Add the project root to Python path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))


from alembic import context

# Import your database configuration and models
from src.server.database import engine, Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata to your application's Base
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    from src.server.config import global_config
    from src.server.database import import_all_models
    from pathlib import Path

    # Import all models to ensure Alembic can detect them
    import_all_models()

    # Use the database configuration from your application
    database_path = Path(global_config.database_path)
    url = f"{global_config.database_protocol}:///{database_path}"

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Import all models to ensure Alembic can detect them
    from src.server.database import import_all_models

    import_all_models()

    # Use the existing database engine from the application
    connectable = engine

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
