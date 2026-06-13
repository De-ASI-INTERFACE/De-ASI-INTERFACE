-- db_migrations.sql
-- De-ASI-INTERFACE v1.0.0-secure
-- Owner/Creator: Richard Patterson
-- © 2026 Richard Patterson. All Rights Reserved.
--
-- Run against your PostgreSQL instance (Railway Postgres plugin):
--   psql $DATABASE_URL -f src/api/auth/db_migrations.sql
--
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username            VARCHAR(64)  NOT NULL UNIQUE,
    email               VARCHAR(255) NOT NULL UNIQUE,
    password_hash       TEXT         NOT NULL,
    role                VARCHAR(16)  NOT NULL DEFAULT 'trader'
                            CHECK (role IN ('admin', 'trader', 'viewer')),
    status              VARCHAR(16)  NOT NULL DEFAULT 'pending_2fa'
                            CHECK (status IN ('active', 'suspended', 'pending_2fa')),
    totp_secret_enc     TEXT,
    totp_enabled        BOOLEAN      NOT NULL DEFAULT FALSE,
    backup_code_hashes  TEXT[]       NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_login_at       TIMESTAMPTZ,
    failed_login_count  INTEGER      NOT NULL DEFAULT 0,
    locked_until        TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_username    ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_email       ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_status      ON users (status);
CREATE INDEX IF NOT EXISTS idx_users_locked      ON users (locked_until)
    WHERE locked_until IS NOT NULL;

-- Auto-update updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Audit log table (immutable append-only)
CREATE TABLE IF NOT EXISTS auth_audit_log (
    id           BIGSERIAL    PRIMARY KEY,
    event_time   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    username     VARCHAR(64),
    event_type   VARCHAR(32)  NOT NULL,
    ip_address   INET,
    success      BOOLEAN      NOT NULL,
    detail       TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_username   ON auth_audit_log (username);
CREATE INDEX IF NOT EXISTS idx_audit_event_time ON auth_audit_log (event_time DESC);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON auth_audit_log (event_type);

-- Revoke DELETE on audit_log (enforce immutability at DB level)
REVOKE DELETE ON auth_audit_log FROM PUBLIC;
