from __future__ import with_statement
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
import logging

# Add your model's MetaData object here for 'autogenerate' support
from app.models.user import User, SpiritualRecord, PrayerRequest, BibleStudy
from app import db

# this is the Alembic Config object
config = context.config

# Interpret the config file for logging
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

def get_engine():
    try:
        # The connection string is in the app config
        from app import create_app
        app = create_app()
        return app.extensions['sqlalchemy'].db.engine
    except Exception:
        # Fallback to config section
        return engine_from_config(
            config.get_section(config.config_ini_section),
            prefix='sqlalchemy.',
            poolclass=pool.NullPool)

def get_metadata():
    if hasattr(db, 'metadatas'):
        return db.metadatas[None]
    return db.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    
    # Handle the case where we need to create multiple engines
    engines = {'': get_engine()}
    
    # Configure migration context with all engines
    for name, engine in engines.items():
        engine_metadata = get_metadata()
        
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=engine_metadata,
                process_revision_directives=process_revision_directives,
                **current_app.extensions['migrate'].configure_args
            )
            
            with context.begin_transaction():
                context.run_migrations()

def process_revision_directives(context, revision, directives):
    """Allow conditional modification of revision directives"""
    if config.cmd_opts.autogenerate:
        script = directives[0]
        if script.upgrade_ops.is_empty():
            directives[:] = []
            logger.info('No changes detected in schema.')

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
