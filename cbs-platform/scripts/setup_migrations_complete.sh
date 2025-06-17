#!/bin/bash

# CBS_PYTHON V2.0 Complete Database Migration Setup
# This script creates Alembic migration configurations for all services

set -e

PLATFORM_ROOT="/home/asus/CBS_PYTHON/cbs-platform"
SERVICES_DIR="$PLATFORM_ROOT/services"

echo "🚀 Setting up database migrations for all CBS_PYTHON V2.0 services..."

# Services that need migration setup
SERVICES=(
    "audit-service"
    "customer-service" 
    "gateway-service"
    "loan-service"
    "notification-service"
    "payment-service"
    "transaction-service"
)

# Function to create migration setup for a service
setup_service_migration() {
    local service=$1
    local service_dir="$SERVICES_DIR/$service"
    local migrations_dir="$service_dir/migrations"
    
    echo "📦 Setting up migrations for $service..."
    
    # Create migrations directory if it doesn't exist
    mkdir -p "$migrations_dir"
    mkdir -p "$migrations_dir/versions"
    
    # Create alembic.ini
    cat > "$service_dir/alembic.ini" << EOF
# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = migrations

# template used to generate migration files
# file_template = %%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library that can be
# installed by adding "alembic[tz]" to the pip requirements
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version number format (defaults to 4-digit zero-padded)
# version_num_format = %04d

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses
# os.pathsep. If this key is omitted entirely, it falls back to the legacy
# behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = postgresql://postgres:password@localhost:5432/${service/-/_}_db


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF

    # Create env.py
    cat > "$migrations_dir/env.py" << 'EOF'
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# Import all models for the service
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    # Try to import the service's database models
    service_name = os.path.basename(os.path.dirname(os.path.dirname(__file__)))
    if 'audit' in service_name:
        from src.audit_service.infrastructure.database import Base
    elif 'customer' in service_name:
        from src.customer_service.infrastructure.database import Base
    elif 'loan' in service_name:
        from src.loan_service.infrastructure.database import Base
    elif 'notification' in service_name:
        from src.notification_service.infrastructure.database import Base
    elif 'payment' in service_name:
        from src.payment_service.infrastructure.database import Base
    elif 'transaction' in service_name:
        from src.transaction_service.infrastructure.database import Base
    elif 'account' in service_name:
        from src.account_service.infrastructure.database import Base
    else:
        # Fallback - create empty Base
        from sqlalchemy.ext.declarative import declarative_base
        Base = declarative_base()
    
    target_metadata = Base.metadata
except ImportError:
    # Fallback if models can't be imported
    target_metadata = None

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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

    # Create script.py.mako
    cat > "$migrations_dir/script.py.mako" << 'EOF'
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
EOF

    echo "✅ Migration setup completed for $service"
}

# Setup migrations for each service
for service in "${SERVICES[@]}"; do
    if [ -d "$SERVICES_DIR/$service" ]; then
        setup_service_migration "$service"
    else
        echo "⚠️  Service directory not found: $service"
    fi
done

echo ""
echo "🎯 Database migration setup completed for all services!"
echo ""
echo "📋 Next steps:"
echo "   1. Install Alembic: pip install alembic"
echo "   2. Generate initial migrations for each service:"
echo "      cd services/[service-name] && alembic revision --autogenerate -m 'Initial migration'"
echo "   3. Run migrations: alembic upgrade head"
echo ""
echo "🔧 Migration commands for each service:"
for service in "${SERVICES[@]}"; do
    if [ -d "$SERVICES_DIR/$service" ]; then
        echo "   cd services/$service && alembic revision --autogenerate -m 'Initial migration'"
    fi
done

echo ""
echo "✨ CBS_PYTHON V2.0 Database Migration Setup Complete!"
