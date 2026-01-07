# Database Setup Instructions

This guide will help you set up the database and import data.

## Option 1: Fresh Database Setup (Recommended)

If you're starting fresh or want to recreate the database:

1. **Drop existing tables** (if any):
   ```bash
   # Connect to PostgreSQL and drop the database
   psql -U postgres
   DROP DATABASE vehicle_valuation;
   CREATE DATABASE vehicle_valuation;
   \q
   ```

2. **Run the initialization script**:
   ```bash
   cd backend
   python init_db.py
   ```

This will create all tables with the correct schema and populate them with data.

## Option 2: Migrate Existing Database

If you have existing data and want to update the schema:

1. **Run the migration script first**:
   ```bash
   cd backend
   python migrate_price_precision.py
   ```

2. **Then run the initialization script**:
   ```bash
   python init_db.py
   ```

## What Changed

The price field precision was increased from `DECIMAL(12, 2)` to `DECIMAL(15, 2)` to support larger vehicle prices:

- **Old maximum**: 9,999,999,999.99 (< 10 billion)
- **New maximum**: 999,999,999,999.99 (< 1 trillion)

This allows the system to handle luxury and commercial vehicle prices that may exceed 10 billion in local currency.

## Troubleshooting

### Error: "numeric field overflow"

This error occurs when trying to insert price values that exceed the column's precision. Solutions:

1. Run the migration script: `python migrate_price_precision.py`
2. Or drop and recreate the database using Option 1 above

### Error: "CSV file not found"

Make sure the following CSV files exist:
- `backend/postgres/fast_moving_vehicles.csv`
- `backend/postgres/master_table_scraped.csv`

### Database Connection Issues

Check your `.env` file has the correct database configuration:
```
DATABASE_URL=postgresql://username:password@localhost:5432/vehicle_valuation
```
