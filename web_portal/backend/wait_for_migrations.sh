#!/bin/bash
# Script to wait for migrations to complete before starting the application

set -e

echo "Waiting for database migrations to complete..."

# Wait for the migrations container to finish
# This is a simple wait loop that checks if the database has the alembic_version table
while ! python -c "
import os
import sys
from sqlalchemy import create_engine, inspect

try:
    database_url = os.getenv('DATABASE_URL')
    engine = create_engine(database_url)
    inspector = inspect(engine)

    # Check if alembic_version table exists (migrations have run)
    if 'alembic_version' in inspector.get_table_names():
        print('Migrations table found. Database is ready.')
        sys.exit(0)
    else:
        print('Migrations table not found. Waiting...')
        sys.exit(1)
except Exception as e:
    print(f'Error checking migrations: {e}')
    sys.exit(1)
"; do
    echo "Waiting for migrations to complete..."
    sleep 2
done

echo "Migrations complete! Starting application..."
exec "$@"
