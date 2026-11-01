-- =============================================================================
-- KGP LIST - Database Initialization Script
-- Executed on PostgreSQL container creation
-- =============================================================================

-- Ensure UTF-8 client encoding
SET client_encoding = 'UTF8';

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verification comment
COMMENT ON DATABASE kgp_db IS 'KGP LIST Spare-Parts Platform Database';
