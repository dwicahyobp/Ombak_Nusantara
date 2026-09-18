import os
import sys
from os.path import abspath, dirname

# 1. Paksakan Python untuk mengenali folder root 'Ombak_Nusantara'
BASE_DIR = dirname(dirname(abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import sqlmodel
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 2. Import settings dan model spesifik proyek Ombak Nusantara
from backend.app.core.settings import settings
from backend.app.models.database import User, SurfPlan, SurfReport 

# Object config bawaan Alembic
config = context.config

# Setup logger bawaan Alembic
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. Target metadata diarahkan ke SQLModel agar autogenerate bekerja
target_metadata = sqlmodel.SQLModel.metadata

# 4. Inject URL database secara dinamis dari file .env milikmu
config.set_main_option("sqlalchemy.url", settings.db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, render_as_batch=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
