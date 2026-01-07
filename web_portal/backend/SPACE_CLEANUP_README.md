# Database Space Cleanup Documentation

## Overview

This module provides tools to clean up leading and trailing spaces in PostgreSQL table column values. Leading/trailing spaces can cause data matching issues and inconsistencies in vehicle valuation queries.

## Problem

CSV files may contain data with leading or trailing spaces in string columns:
- ` TOYOTA` (leading space)
- `AXIO ` (trailing space)
- ` PETROL ` (both)

This causes:
- **Query mismatches**: `manufacturer = 'TOYOTA'` won't match ` TOYOTA`
- **Duplicate entries**: System treats `TOYOTA` and ` TOYOTA` as different
- **Data inconsistency**: Unreliable searches and price predictions

## Solution

Two-pronged approach:

### 1. Automatic Cleanup During Migration

The `run_migrations.py` script now:
- **Strips spaces during CSV import** (prevents issue at source)
- **Runs cleanup after data loading** (ensures consistency)

**Affected tables and columns:**
```python
erp_model_mapping:
  - manufacturer
  - erp_name
  - mapped_name

fast_moving_vehicles:
  - type
  - manufacturer
  - model

scraped_vehicles:
  - manufacturer
  - type
  - model
  - transmission
  - fuel_type
```

### 2. Standalone Cleanup Script

For production databases that already have data with spaces.

## Usage

### Option 1: Run with Migrations (Automatic)

When you run migrations, space cleanup happens automatically:

```bash
# Docker environment
docker-compose -f docker-compose.prod.yml up db_migrations

# Local development
cd web_portal/backend
python run_migrations.py
```

**Output:**
```
==================================================
Loading CSV data into database...
==================================================
...
✓ CSV data loading complete!

==================================================
Cleaning up leading/trailing spaces...
==================================================

Cleaning table: erp_model_mapping
  ✓ Cleaned 45 rows in column 'manufacturer'
  ✓ Cleaned 12 rows in column 'erp_name'
  - No spaces found in column 'mapped_name'

Cleaning table: fast_moving_vehicles
  ✓ Cleaned 234 rows in column 'manufacturer'
  ✓ Cleaned 156 rows in column 'model'
  - No spaces found in column 'type'

Cleaning table: scraped_vehicles
  ✓ Cleaned 1,523 rows in column 'manufacturer'
  ✓ Cleaned 892 rows in column 'model'
  ✓ Cleaned 45 rows in column 'transmission'

==================================================
✓ Space cleanup complete!
Total rows updated: 2,907
==================================================
```

### Option 2: Standalone Cleanup (Production)

For existing databases without reloading data:

```bash
# Local environment
cd web_portal/backend
python cleanup_spaces.py

# Docker environment
docker exec -it cdb_backend python cleanup_spaces.py
```

**Interactive confirmation:**
```
======================================================================
PostgreSQL Space Cleanup Tool
======================================================================

Database: postgres:5432/cdb_valuation_db

Testing database connection...
✓ Database connection successful!

This script will update string columns in the following tables:
  - erp_model_mapping
  - fast_moving_vehicles
  - scraped_vehicles

Do you want to continue? (yes/no): yes
```

## How It Works

### During CSV Import

```python
# Before (old code)
df_to_load = df[['manufacturer', 'model']].copy()

# After (new code with cleanup)
df_to_load = df[['manufacturer', 'model']].copy()

# Strip spaces from string columns
string_columns = ['manufacturer', 'model']
for col in string_columns:
    df_to_load[col] = df_to_load[col].astype(str).str.strip()
```

### Database Cleanup

```sql
-- For each table and column, run:
UPDATE erp_model_mapping
SET manufacturer = TRIM(manufacturer)
WHERE manufacturer != TRIM(manufacturer)
   OR manufacturer IS NOT NULL
   AND (manufacturer LIKE ' %' OR manufacturer LIKE '% ')
```

## Testing

### Verify Cleanup

```sql
-- Check for remaining spaces
SELECT
    manufacturer,
    LENGTH(manufacturer) as len,
    TRIM(manufacturer) as trimmed,
    LENGTH(TRIM(manufacturer)) as trimmed_len
FROM erp_model_mapping
WHERE manufacturer != TRIM(manufacturer);

-- Should return 0 rows after cleanup
```

### Before/After Example

```sql
-- Before cleanup
SELECT DISTINCT manufacturer FROM fast_moving_vehicles;
-- Results:
-- TOYOTA
--  TOYOTA
-- TOYOTA

-- After cleanup
SELECT DISTINCT manufacturer FROM fast_moving_vehicles;
-- Results:
-- TOYOTA
```

## Integration with Migrations

The cleanup is integrated into the migration workflow:

```
1. Run Alembic migrations (schema changes)
   ↓
2. Load CSV data
   ├─ Strip spaces during pandas import
   ↓
3. Run space cleanup (SQL TRIM)
   ├─ Double-check and clean any missed data
   ↓
4. Database ready with clean data
```

## Environment Variables

Required in `.env`:
```env
DATABASE_URL=postgresql+psycopg2://user:password@host:port/database
```

## Files Modified

1. **`run_migrations.py`**:
   - Added `cleanup_trailing_spaces()` function
   - Updated all CSV loading functions to strip spaces
   - Integrated cleanup into migration workflow

2. **`cleanup_spaces.py`** (new):
   - Standalone cleanup script
   - Interactive confirmation
   - Detailed reporting

## Error Handling

The cleanup script:
- ✓ Tests database connection before starting
- ✓ Commits changes per table (partial success possible)
- ✓ Provides detailed error messages with stack traces
- ✓ Requires explicit user confirmation
- ✓ Shows summary of all changes

## Performance

- **Bulk updates**: Uses SQL UPDATE with WHERE clause
- **Only updates affected rows**: Checks before updating
- **Batch processing**: Processes by table, commits per table
- **Typical runtime**: < 30 seconds for 100K rows

## Maintenance

### Adding New Tables

To include new tables in cleanup:

1. **In `run_migrations.py`:**
```python
def cleanup_trailing_spaces(engine):
    tables_to_clean = {
        # Add your table here
        'your_table_name': ['column1', 'column2'],
    }
```

2. **In `cleanup_spaces.py`:**
```python
def cleanup_trailing_spaces(engine):
    tables_to_clean = {
        # Add your table here
        'your_table_name': ['column1', 'column2'],
    }
```

### Adding New Columns

Update the column list for the relevant table in both scripts.

## Troubleshooting

### Issue: Script says "No spaces found" but data has spaces

**Solution**: Check if spaces are in columns not included in cleanup list.

```sql
-- Find columns with spaces
SELECT column_name, COUNT(*)
FROM information_schema.columns c
JOIN your_table t ON true
WHERE c.table_name = 'your_table'
  AND t[column_name] != TRIM(t[column_name])
GROUP BY column_name;
```

### Issue: Permission denied

**Solution**: Ensure database user has UPDATE permissions.

```sql
GRANT UPDATE ON ALL TABLES IN SCHEMA public TO your_user;
```

### Issue: Script hangs

**Solution**: Check for table locks.

```sql
SELECT * FROM pg_stat_activity
WHERE state = 'active' AND query LIKE '%UPDATE%';
```

## Best Practices

1. **Always backup before running cleanup** in production
2. **Test on staging first** with production data copy
3. **Run during maintenance window** to avoid locking issues
4. **Monitor CSV sources** to prevent spaces at source
5. **Add validation** in data import pipelines

## Future Enhancements

- [ ] Add logging to file
- [ ] Support for dry-run mode (preview changes)
- [ ] Email notifications on completion
- [ ] Integration with data quality monitoring
- [ ] Automatic scheduling (cron job)
- [ ] Support for other whitespace characters (tabs, newlines)

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review database connection settings
3. Verify table and column names match models
4. Contact development team

---

**Version**: 1.0
**Last Updated**: 2025-12-29
**Author**: CDB Development Team
