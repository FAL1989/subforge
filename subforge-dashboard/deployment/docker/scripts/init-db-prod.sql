-- Production Database Initialization Script
-- This script runs automatically when the PostgreSQL container starts in production

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create production schemas
CREATE SCHEMA IF NOT EXISTS subforge;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS audit;

-- Set default search path
ALTER DATABASE subforge SET search_path TO subforge, public;

-- Create application users with limited privileges
CREATE ROLE subforge_app;
GRANT CONNECT ON DATABASE subforge TO subforge_app;
GRANT USAGE ON SCHEMA subforge TO subforge_app;
GRANT USAGE ON SCHEMA analytics TO subforge_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA subforge TO subforge_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analytics TO subforge_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA subforge TO subforge_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA analytics TO subforge_app;

-- Create read-only user for reporting and monitoring
CREATE ROLE subforge_readonly;
GRANT CONNECT ON DATABASE subforge TO subforge_readonly;
GRANT USAGE ON SCHEMA subforge TO subforge_readonly;
GRANT USAGE ON SCHEMA analytics TO subforge_readonly;
GRANT USAGE ON SCHEMA audit TO subforge_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA subforge TO subforge_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO subforge_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA audit TO subforge_readonly;

-- Create audit user with limited write access to audit schema
CREATE ROLE subforge_auditor;
GRANT CONNECT ON DATABASE subforge TO subforge_auditor;
GRANT USAGE ON SCHEMA audit TO subforge_auditor;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA audit TO subforge_auditor;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA audit TO subforge_auditor;

-- Production-specific security settings
ALTER SYSTEM SET ssl = 'on';
ALTER SYSTEM SET log_connections = 'on';
ALTER SYSTEM SET log_disconnections = 'on';
ALTER SYSTEM SET log_min_duration_statement = 5000;
ALTER SYSTEM SET log_statement = 'ddl';
ALTER SYSTEM SET log_lock_waits = 'on';

-- Performance tuning for production
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Security hardening
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activities = 'on';
ALTER SYSTEM SET track_counts = 'on';
ALTER SYSTEM SET track_io_timing = 'on';

-- Create function to revoke dangerous permissions
CREATE OR REPLACE FUNCTION revoke_dangerous_permissions()
RETURNS void AS $$
BEGIN
    -- Revoke dangerous default public permissions
    REVOKE ALL ON SCHEMA public FROM PUBLIC;
    REVOKE CREATE ON SCHEMA public FROM PUBLIC;
    
    -- Only allow specific roles to create objects
    GRANT USAGE ON SCHEMA public TO subforge_app, subforge_readonly, subforge_auditor;
END;
$$ LANGUAGE plpgsql;

-- Execute security function
SELECT revoke_dangerous_permissions();

-- Create audit table for security monitoring
CREATE TABLE IF NOT EXISTS audit.connection_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    username TEXT,
    database_name TEXT,
    client_addr INET,
    connection_type TEXT
);

-- Create function to log connections (will be called by triggers)
CREATE OR REPLACE FUNCTION audit.log_connection()
RETURNS void AS $$
BEGIN
    INSERT INTO audit.connection_log (username, database_name, client_addr, connection_type)
    VALUES (current_user, current_database(), inet_client_addr(), 'connect');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;