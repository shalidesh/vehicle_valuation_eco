"""
Database initialization and seed data script.
Run this script to create the database schema and populate with sample data.
"""
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent))

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.vehicle import FastMovingVehicle
from app.models.mapping import ERPModelMapping
from app.services.auth import get_password_hash
from decimal import Decimal
from datetime import datetime, timedelta
import random
import csv


def create_tables():
    """
    DEPRECATED: Table creation is now handled by Alembic migrations.
    This function is kept for backwards compatibility but does nothing.
    """
    print("Table creation is now handled by Alembic migrations.")
    print("Skipping Base.metadata.create_all()...")


def seed_users(db):
    """Create sample users."""
    print("Creating users...")

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

    created_users = []
    for user_data in users:
        existing_user = db.query(User).filter(User.username == user_data["username"]).first()
        if not existing_user:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=get_password_hash(user_data["password"]),
                role=user_data["role"],
            )
            db.add(user)
            created_users.append(user)

    db.commit()
    print(f"Created {len(created_users)} users")
    return created_users


def parse_date(date_str):
    """Parse date string from CSV in format M/D/YYYY"""
    try:
        return datetime.strptime(date_str, "%m/%d/%Y")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            print(f"Error parsing date: {date_str}")
            return None


def seed_fast_moving_vehicles(db):
    """Import fast moving vehicle records from CSV file."""
    print("Importing fast moving vehicles from CSV...")

    csv_path = "postgres/fast_moving_vehicles.csv"

    # Check if file exists
    if not Path(csv_path).exists():
        print(f"Warning: CSV file not found at {csv_path}")
        print("Skipping fast moving vehicles import.")
        return 

    vehicles_added = 0
    vehicles_skipped = 0

    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)

            for row in csv_reader:
                try:
                    # Parse date
                    date_obj = parse_date(row['date'])
                    if not date_obj:
                        vehicles_skipped += 1
                        continue

                    # Parse price
                    price = float(row['price']) if row['price'] else None

                    # Create vehicle record
                    vehicle = FastMovingVehicle(
                        type=row['type'],
                        manufacturer=row['manufacturer'],
                        model=row['model'],
                        yom=int(row['yom']),
                        price=Decimal(str(price)) if price else None,
                        date=date_obj
                    )

                    db.add(vehicle)
                    vehicles_added += 1

                    # Commit in batches of 1000 for better performance
                    if vehicles_added % 1000 == 0:
                        db.commit()
                        print(f"  Committed {vehicles_added} records...")

                except Exception as e:
                    print(f"  Error processing row: {row}")
                    print(f"  Error: {e}")
                    vehicles_skipped += 1
                    continue

            # Commit remaining records
            db.commit()

        print(f"Imported {vehicles_added} fast moving vehicles from CSV")
        if vehicles_skipped > 0:
            print(f"Skipped {vehicles_skipped} records due to errors")

    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_path}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        db.rollback()


def seed_erp_mappings(db):
    """Create sample ERP model mappings."""
    print("Creating ERP mappings...")

    mappings = [
        {"manufacturer": "Toyota", "erp_name": "CRL", "mapped_name": "Corolla"},
        {"manufacturer": "Toyota", "erp_name": "PRS", "mapped_name": "Prius"},
        {"manufacturer": "Toyota", "erp_name": "AQA", "mapped_name": "Aqua"},
        {"manufacturer": "Toyota", "erp_name": "VTZ", "mapped_name": "Vitz"},
        {"manufacturer": "Honda", "erp_name": "CVC", "mapped_name": "Civic"},
        {"manufacturer": "Honda", "erp_name": "FIT", "mapped_name": "Fit"},
        {"manufacturer": "Honda", "erp_name": "VZL", "mapped_name": "Vezel"},
        {"manufacturer": "Nissan", "erp_name": "MRC", "mapped_name": "March"},
        {"manufacturer": "Nissan", "erp_name": "NTE", "mapped_name": "Note"},
        {"manufacturer": "Nissan", "erp_name": "LF", "mapped_name": "Leaf"},
        {"manufacturer": "Suzuki", "erp_name": "SWT", "mapped_name": "Swift"},
        {"manufacturer": "Suzuki", "erp_name": "ALT", "mapped_name": "Alto"},
        {"manufacturer": "Suzuki", "erp_name": "WGR", "mapped_name": "Wagon R"},
        {"manufacturer": "Mitsubishi", "erp_name": "RVR", "mapped_name": "RVR"},
        {"manufacturer": "Mitsubishi", "erp_name": "LNC", "mapped_name": "Lancer"},
        {"manufacturer": "BMW", "erp_name": "3SR", "mapped_name": "3 Series"},
        {"manufacturer": "BMW", "erp_name": "5SR", "mapped_name": "5 Series"},
        {"manufacturer": "Mercedes-Benz", "erp_name": "C-CLS", "mapped_name": "C-Class"},
        {"manufacturer": "Mercedes-Benz", "erp_name": "E-CLS", "mapped_name": "E-Class"},
    ]

    admin_user = db.query(User).filter(User.role == UserRole.admin).first()

    mappings_created = 0
    for mapping_data in mappings:
        existing = (
            db.query(ERPModelMapping)
            .filter(
                ERPModelMapping.manufacturer == mapping_data["manufacturer"],
                ERPModelMapping.erp_name == mapping_data["erp_name"],
            )
            .first()
        )

        if not existing:
            mapping = ERPModelMapping(
                manufacturer=mapping_data["manufacturer"],
                erp_name=mapping_data["erp_name"],
                mapped_name=mapping_data["mapped_name"],
                updated_by=admin_user.id if admin_user else None,
            )
            db.add(mapping)
            mappings_created += 1

    db.commit()
    print(f"Created {mappings_created} ERP mappings")


def main():
    """Main function to initialize database and seed data."""
    print("Starting database initialization...")

    # Create tables
    create_tables()

    # Create database session
    db = SessionLocal()

    try:
        # Seed data
        seed_users(db)
        seed_fast_moving_vehicles(db)
        seed_erp_mappings(db)

        print("\n" + "=" * 50)
        print("Database initialization completed successfully!")
        print("=" * 50)
        print("\nDefault Users Created:")
        print("  Admin 1: admin1 / admin123")
        print("  Admin 2: admin2 / admin123")
        print("  Manager 1: manager1 / manager123")
        print("  Manager 2: manager2 / manager123")
        print("  Manager 3: manager3 / manager123")
        print("=" * 50)

    except Exception as e:
        print(f"Error during initialization: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
