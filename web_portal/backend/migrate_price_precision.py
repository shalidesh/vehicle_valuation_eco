"""
Migration script to increase price field precision from DECIMAL(12,2) to DECIMAL(15,2)
Run this script before running init_db.py if you have existing data.
"""
from sqlalchemy import text
from app.database import engine

def migrate_price_precision():
    """Alter price columns to support larger values."""
    print("Starting migration to increase price field precision...")

    migrations = [
        {
            "table": "fast_moving_vehicles",
            "query": "ALTER TABLE fast_moving_vehicles ALTER COLUMN price TYPE NUMERIC(15, 2);"
        },
        {
            "table": "scraped_vehicles",
            "query": "ALTER TABLE scraped_vehicles ALTER COLUMN price TYPE NUMERIC(15, 2);"
        }
    ]

    with engine.connect() as conn:
        for migration in migrations:
            try:
                print(f"Updating {migration['table']}...")
                conn.execute(text(migration['query']))
                conn.commit()
                print(f"✓ Successfully updated {migration['table']}")
            except Exception as e:
                print(f"✗ Error updating {migration['table']}: {e}")
                print(f"  (This is normal if the table doesn't exist yet)")
                conn.rollback()

    print("\nMigration completed!")
    print("You can now run init_db.py to populate the data.")

if __name__ == "__main__":
    migrate_price_precision()
