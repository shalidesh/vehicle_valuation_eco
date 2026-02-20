"""
Standalone script to clean up leading/trailing spaces in PostgreSQL database.
This script can be run independently to clean existing data without reloading CSV files.

Usage:
    python cleanup_spaces.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


def cleanup_trailing_spaces(engine):
    """
    Clean up leading/trailing spaces from all string columns in database tables.
    This ensures data consistency and prevents matching issues.
    """
    print("\n" + "=" * 70)
    print("PostgreSQL Database - Trailing/Leading Spaces Cleanup")
    print("=" * 70)

    # Define tables and their string columns that need cleanup
    tables_to_clean = {
        'erp_model_mapping': ['manufacturer', 'erp_name', 'mapped_name'],
        'fast_moving_vehicles': ['type', 'manufacturer', 'model'],
    }

    total_updates = 0
    table_stats = {}

    try:
        with engine.connect() as conn:
            for table_name, columns in tables_to_clean.items():
                print(f"\n[{table_name}]")
                print("-" * 70)

                table_updates = 0

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
                        print(f"  ✓ {column:20s} - Cleaned {rows_updated:5d} rows")
                        total_updates += rows_updated
                        table_updates += rows_updated
                    else:
                        print(f"  - {column:20s} - No spaces found")

                conn.commit()
                table_stats[table_name] = table_updates

        # Print summary
        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)

        for table_name, updates in table_stats.items():
            status = "✓" if updates > 0 else "-"
            print(f"{status} {table_name:30s} - {updates:5d} rows updated")

        print("-" * 70)
        print(f"Total rows updated: {total_updates}")
        print("=" * 70 + "\n")

        if total_updates > 0:
            print("✓ Space cleanup completed successfully!")
        else:
            print("✓ No trailing/leading spaces found. Database is clean!")

        return total_updates

    except Exception as e:
        print(f"\n✗ ERROR during space cleanup: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_connection(database_url):
    """Test database connection."""
    print("Testing database connection...")

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Database connection successful!\n")
        return engine
    except OperationalError as e:
        print(f"✗ Database connection failed: {e}")
        sys.exit(1)


def main():
    """Main function to run the cleanup."""
    print("\n" + "=" * 70)
    print("PostgreSQL Space Cleanup Tool")
    print("=" * 70)
    print()

    # Get database URL
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set!")
        print("\nPlease set DATABASE_URL in your .env file:")
        print("DATABASE_URL=postgresql+psycopg2://user:password@host:port/database")
        sys.exit(1)

    # Hide password in output
    safe_url = database_url.split('@')[1] if '@' in database_url else database_url
    print(f"Database: {safe_url}\n")

    # Test connection
    engine = test_connection(database_url)

    # Ask for confirmation
    print("This script will update string columns in the following tables:")
    print("  - erp_model_mapping")
    print("  - fast_moving_vehicles")
    print()

    confirm = input("Do you want to continue? (yes/no): ").strip().lower()

    if confirm not in ['yes', 'y']:
        print("\nOperation cancelled by user.")
        sys.exit(0)

    # Run cleanup
    try:
        cleanup_trailing_spaces(engine)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
