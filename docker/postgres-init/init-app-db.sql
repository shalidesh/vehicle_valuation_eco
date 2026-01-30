-- This script runs on first PostgreSQL container initialization.
-- The Airflow database is created automatically via POSTGRES_DB env var.
-- This script creates the application database for other services.
--
-- IMPORTANT: If you change APP_DB_NAME in .env.prod, update the name below to match.

CREATE DATABASE cdb_valuation_db;
