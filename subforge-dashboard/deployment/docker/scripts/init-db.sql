-- Development Database Initialization Script
-- This script runs automatically when the PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create development schemas if they don't exist
CREATE SCHEMA IF NOT EXISTS subforge;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Set default search path
ALTER DATABASE subforge_dev SET search_path TO subforge, public;

-- Create a read-only user for reporting
CREATE ROLE subforge_readonly;
GRANT CONNECT ON DATABASE subforge_dev TO subforge_readonly;
GRANT USAGE ON SCHEMA subforge TO subforge_readonly;
GRANT USAGE ON SCHEMA analytics TO subforge_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA subforge TO subforge_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO subforge_readonly;

-- Create application-specific configuration
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Development-specific settings
ALTER SYSTEM SET log_connections = 'on';
ALTER SYSTEM SET log_disconnections = 'on';
ALTER SYSTEM SET log_lock_waits = 'on';

-- Create indexes for common queries (will be created by Alembic migrations)
-- This is just a placeholder for any additional development-specific indexes