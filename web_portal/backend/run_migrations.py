"""
Migration runner script for automatic database migrations.
This script should be run in a separate container before starting the main application.
Also loads initial data from CSV files into the database.
"""
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
import pandas as pd
from passlib.context import CryptContext

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import models after adding to path
from app.models.user import User, UserRole

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def wait_for_db(database_url: str, max_retries: int = 30, retry_interval: int = 2):
    """Wait for database to be ready."""
    print("Waiting for database to be ready...")
    engine = create_engine(database_url)

    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database is ready!")
            return True
        except OperationalError as e:
            print(f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
            else:
                print("Max retries reached. Database is not available.")
                return False

    return False


def load_erp_model_mapping(engine, csv_path):
    """Load ERP model mapping data from CSV."""
    print("\nLoading ERP Model Mapping data...")

    df = pd.read_csv(csv_path)
    print(f"  Found {len(df)} records in {csv_path.name}")

    # Clear existing data
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE erp_model_mapping RESTART IDENTITY CASCADE"))
        conn.commit()

    # Prepare and load data
    df_to_load = df[['manufacturer', 'erp_name', 'mapped_name']].copy()

    # Clean up leading/trailing spaces from string columns
    string_columns = ['manufacturer', 'erp_name', 'mapped_name']
    for col in string_columns:
        if col in df_to_load.columns:
            df_to_load[col] = df_to_load[col].astype(str).str.strip()

    # Remove duplicates based on (manufacturer, erp_name) - keep first occurrence
    duplicates_count = len(df_to_load) - df_to_load.drop_duplicates(subset=['manufacturer', 'erp_name'], keep='first').shape[0]
    if duplicates_count > 0:
        print(f"  Warning: Found {duplicates_count} duplicate records, removing duplicates...")
        df_to_load = df_to_load.drop_duplicates(subset=['manufacturer', 'erp_name'], keep='first')

    # Pass engine directly to to_sql for pandas compatibility
    df_to_load.to_sql('erp_model_mapping', engine, if_exists='append', index=False, method='multi', chunksize=1000)

    print(f"  ✓ Loaded {len(df_to_load)} unique records into erp_model_mapping")
    return len(df_to_load)


def load_fast_moving_vehicles(engine, csv_path):
    """Load fast moving vehicles data from CSV."""
    print("\nLoading Fast Moving Vehicles data...")

    df = pd.read_csv(csv_path)
    print(f"  Found {len(df)} records in {csv_path.name}")

    # Clear existing data
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE fast_moving_vehicles RESTART IDENTITY CASCADE"))
        conn.commit()

    # Prepare data - convert date to datetime
    df_to_load = df[['type', 'manufacturer', 'model', 'yom', 'price', 'date']].copy()
    df_to_load = df_to_load.drop_duplicates(subset=["type","manufacturer","model","yom","date"])

    # Clean up leading/trailing spaces from string columns
    string_columns = ['type', 'manufacturer', 'model']
    for col in string_columns:
        if col in df_to_load.columns:
            df_to_load[col] = df_to_load[col].astype(str).str.strip()

    df_to_load['date'] = pd.to_datetime(df_to_load['date'])

    # Pass engine directly to to_sql for pandas compatibility
    df_to_load.to_sql('fast_moving_vehicles', engine, if_exists='append', index=False, method='multi', chunksize=1000)

    print(f"  ✓ Loaded {len(df_to_load)} records into fast_moving_vehicles")
    return len(df_to_load)


def load_scraped_vehicles(engine, csv_path):
    """Load scraped vehicles data from CSV."""
    print("\nLoading Scraped Vehicles data...")

    df = pd.read_csv(csv_path)
    print(f"  Found {len(df)} records in {csv_path.name}")

    # Clear existing data
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE scraped_vehicles RESTART IDENTITY CASCADE"))
        conn.commit()

    # Prepare data
    df_to_load = df[['manufacturer', 'type', 'model', 'yom', 'transmission', 'fuel_type', 'mileage', 'price']].copy()

    # Clean up leading/trailing spaces from string columns
    string_columns = ['manufacturer', 'type', 'model', 'transmission', 'fuel_type']
    for col in string_columns:
        if col in df_to_load.columns:
            df_to_load[col] = df_to_load[col].astype(str).str.strip()

    # Convert date_posted to updated_date if exists
    if 'date_posted' in df.columns:
        df['updated_date'] = pd.to_datetime(df['date_posted'])
        df_to_load['updated_date'] = df['updated_date']

    # Clean up data
    df_to_load['mileage'] = df_to_load['mileage'].fillna(0).astype(int)

    # Pass engine directly to to_sql for pandas compatibility
    df_to_load.to_sql('scraped_vehicles', engine, if_exists='append', index=False, method='multi', chunksize=1000)

    print(f"  ✓ Loaded {len(df_to_load)} records into scraped_vehicles")
    return len(df_to_load)


def load_default_users(engine):
    """Load default users into the database."""
    print("\nLoading default users...")

    users = [
        {
            "username": "admin1",
            "email": "admin1@cdb.com",
            "password": "admin123",
            "role": UserRole.admin,
        },
        {
            "username": "admin2",
            "email": "admin2@cdb.com",
            "password": "admin123",
            "role": UserRole.admin,
        },
        {
            "username": "manager1",
            "email": "manager1@cdb.com",
            "password": "manager123",
            "role": UserRole.manager,
        },
        {
            "username": "manager2",
            "email": "manager2@cdb.com",
            "password": "manager123",
            "role": UserRole.manager,
        },
        {
            "username": "manager3",
            "email": "manager3@cdb.com",
            "password": "manager123",
            "role": UserRole.manager,
        },
    ]

    with Session(engine) as session:
        # Clear existing users
        session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        session.commit()

        # Create users with hashed passwords
        for user_data in users:
            password = user_data.pop("password")
            password_hash = pwd_context.hash(password)

            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=password_hash,
                role=user_data["role"]
            )
            session.add(user)

        session.commit()
        print(f"  ✓ Loaded {len(users)} default users")

    return len(users)


def cleanup_trailing_spaces(engine):
    """
    Clean up leading/trailing spaces from all string columns in database tables.
    This ensures data consistency and prevents matching issues.
    """
    print("\n" + "=" * 50)
    print("Cleaning up leading/trailing spaces...")
    print("=" * 50)

    # Define tables and their string columns that need cleanup
    tables_to_clean = {
        'erp_model_mapping': ['manufacturer', 'erp_name', 'mapped_name'],
        'fast_moving_vehicles': ['type', 'manufacturer', 'model'],
        'scraped_vehicles': ['manufacturer', 'type', 'model', 'transmission', 'fuel_type']
    }

    total_updates = 0

    try:
        with engine.connect() as conn:
            for table_name, columns in tables_to_clean.items():
                print(f"\nCleaning table: {table_name}")

                for column in columns:
                    # Update query to trim leading and trailing spaces
                    update_query = text(f"""
                        UPDATE {table_name}
                        SET {column} = TRIM({column})
                        WHERE {column} != TRIM({column})
                        OR {column} IS NOT NULL AND ({column} LIKE ' %' OR {column} LIKE '% ')
                    """)

                    result = conn.execute(update_query)
                    rows_updated = result.rowcount

                    if rows_updated > 0:
                        print(f"  ✓ Cleaned {rows_updated} rows in column '{column}'")
                        total_updates += rows_updated
                    else:
                        print(f"  - No spaces found in column '{column}'")

                conn.commit()

        print("\n" + "=" * 50)
        print(f"✓ Space cleanup complete!")
        print(f"Total rows updated: {total_updates}")
        print("=" * 50 + "\n")

        return total_updates

    except Exception as e:
        print(f"\n✗ ERROR during space cleanup: {e}")
        import traceback
        traceback.print_exc()
        raise


def load_csv_data(database_url):
    """Load data from CSV files into database tables."""
    print("\n" + "=" * 50)
    print("Loading CSV data into database...")
    print("=" * 50)

    engine = create_engine(database_url)
    base_path = Path(__file__).parent / 'postgres'

    csv_files = {
        'erp_model_mapping': base_path / 'model_mapped.csv',
        'fast_moving_vehicles': base_path / 'vehicle_fast_moving_update.csv',
        'scraped_vehicles': base_path / 'master_table_scraped.csv'
    }
    print(f"CSV file paths: {csv_files}")

    total_records = 0

    try:
        # Load default users first
        total_records += load_default_users(engine)

        # Load each dataset if file exists
        if csv_files['erp_model_mapping'].exists():
            total_records += load_erp_model_mapping(engine, csv_files['erp_model_mapping'])
        else:
            print(f"\n  WARNING: {csv_files['erp_model_mapping'].name} not found, skipping")

        if csv_files['fast_moving_vehicles'].exists():
            total_records += load_fast_moving_vehicles(engine, csv_files['fast_moving_vehicles'])
        else:
            print(f"\n  WARNING: {csv_files['fast_moving_vehicles'].name} not found, skipping")

        if csv_files['scraped_vehicles'].exists():
            total_records += load_scraped_vehicles(engine, csv_files['scraped_vehicles'])
        else:
            print(f"\n  WARNING: {csv_files['scraped_vehicles'].name} not found, skipping")

        print("\n" + "=" * 50)
        print(f"✓ CSV data loading complete!")
        print(f"Total records loaded: {total_records}")
        print("=" * 50 + "\n")

        # Clean up trailing spaces after loading data
        cleanup_trailing_spaces(engine)

    except Exception as e:
        print(f"\n✗ ERROR during CSV data loading: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        engine.dispose()


def run_migrations():
    """Run Alembic migrations to upgrade database to latest version."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set!")
        sys.exit(1)

    print(f"Database URL: {database_url.split('@')[1] if '@' in database_url else database_url}")

    # Wait for database to be ready
    if not wait_for_db(database_url):
        print("ERROR: Could not connect to database!")
        sys.exit(1)

    # Configure Alembic
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    try:
        print("\n" + "=" * 50)
        print("Running database migrations...")
        print("=" * 50 + "\n")

        # Run migrations
        command.upgrade(alembic_cfg, "head")

        print("\n" + "=" * 50)
        print("Migrations completed successfully!")
        print("=" * 50 + "\n")

        # Load CSV data after successful migration
        load_csv_data(database_url)

    except Exception as e:
        print(f"\nERROR during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_migrations()
