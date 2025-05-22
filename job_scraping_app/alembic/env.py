from __future__ import with_statement
import os
import sys
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# Ensure the app directory is in the Python path for model imports
# This assumes env.py is in job_scraping_app/alembic/
# and your app's root is job_scraping_app/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.base_class import Base # Your SQLAlchemy Base
# Import all models here so Base.metadata knows about them for autogenerate
from app.models import claimant # noqa
from app.models import job_posting # noqa
# Add other model imports if you have them, e.g.:
# from app.models.search_criteria import SQLSearchCriteria # noqa
# from app.models.matched_jobs import SQLMatchedJobs # noqa

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Use DATABASE_URL from settings for offline mode
    from app.core.config import settings
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL not set in settings for offline migration.")
    
    context.configure(
        url=settings.DATABASE_URL, # Use URL from settings
        target_metadata=target_metadata, 
        literal_binds=True,
        dialect_opts={"paramstyle": "named"} # Added for consistency
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Use DATABASE_URL from settings for online mode engine configuration
    from app.core.config import settings
    if not settings.DATABASE_URL:
        # This should ideally not happen if offline mode also checks it,
        # but good to have a guard.
        raise ValueError("DATABASE_URL not set in settings for online migration.")

    # Create an engine configuration dictionary for engine_from_config
    # This ensures that the engine uses the DATABASE_URL from your app's settings.
    # Alembic's engine_from_config expects a dictionary-like object for its first argument.
    # config.get_section(config.config_ini_section) returns this.
    # We then update the 'sqlalchemy.url' key in this dictionary.
    
    engine_config = config.get_section(config.config_ini_section)
    if engine_config is None: # Should not happen with default alembic.ini structure
        engine_config = {}
    
    # Ensure the DATABASE_URL uses the 'postgresql://' scheme
    db_url = settings.DATABASE_URL
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    engine_config['sqlalchemy.url'] = db_url
    
    connectable = engine_from_config(
        engine_config, # Use the modified config section
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
