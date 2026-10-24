-- MONY backend initial schema
-- Run against your Supabase Postgres database

-- Users table: one row per wallet address
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address         TEXT NOT NULL UNIQUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_address ON users (address);

-- Scans table: records every verification attempt
CREATE TABLE IF NOT EXISTS scans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      TEXT NOT NULL UNIQUE,
    user_address    TEXT NOT NULL,
    decision        TEXT NOT NULL,          -- ACCEPT | REJECT | RESCAN
    score           NUMERIC(6, 4) NOT NULL,
    reason_code     TEXT NOT NULL,
    layer_scores    JSONB NOT NULL DEFAULT '{}',
    note_hash       TEXT,                   -- populated on ACCEPT
    denomination    INTEGER,
    amount_mon      NUMERIC(28, 18),
    amount_wei      TEXT,
    voucher_json    JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scans_user_address ON scans (user_address);
CREATE INDEX IF NOT EXISTS idx_scans_note_hash ON scans (note_hash) WHERE note_hash IS NOT NULL;

-- Notes table: de-duplication registry (unique per note_hash)
CREATE TABLE IF NOT EXISTS notes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note_hash       TEXT NOT NULL UNIQUE,
    phash           TEXT NOT NULL,
    denomination    INTEGER NOT NULL,
    user_address    TEXT NOT NULL,
    scan_id         UUID NOT NULL REFERENCES scans (id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notes_phash ON notes (phash);
CREATE INDEX IF NOT EXISTS idx_notes_user_address ON notes (user_address);

-- Deposits table: tracks on-chain redeem calls
CREATE TABLE IF NOT EXISTS deposits (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id         UUID NOT NULL REFERENCES scans (id),
    user_address    TEXT NOT NULL,
    mode            TEXT NOT NULL DEFAULT 'manual',  -- manual | automated
    tx_hash         TEXT,
    status          TEXT NOT NULL DEFAULT 'pending', -- pending | confirmed | failed
    amount_wei      TEXT NOT NULL,
    amount_mon      NUMERIC(28, 18),
    denomination    INTEGER,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    confirmed_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_deposits_user_address ON deposits (user_address);
CREATE INDEX IF NOT EXISTS idx_deposits_tx_hash ON deposits (tx_hash) WHERE tx_hash IS NOT NULL;

-- Quotes table: rate lock records
CREATE TABLE IF NOT EXISTS quotes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_address    TEXT NOT NULL,
    denomination    INTEGER NOT NULL,
    rate_inr_per_mon NUMERIC(20, 8) NOT NULL,
    amount_mon      NUMERIC(28, 18) NOT NULL,
    locked_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ NOT NULL,
    used            BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_quotes_user_address ON quotes (user_address);

-- Invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_address    TEXT NOT NULL,
    invoice_number  TEXT NOT NULL UNIQUE,
    amount_inr      NUMERIC(20, 4) NOT NULL,
    amount_mon      NUMERIC(28, 18),
    recipient_name  TEXT,
    description     TEXT,
    status          TEXT NOT NULL DEFAULT 'draft', -- draft | issued | paid
    pdf_data        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    issued_at       TIMESTAMPTZ,
    paid_at         TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_invoices_user_address ON invoices (user_address);

-- Rate cache table: persisted exchange rate snapshots
CREATE TABLE IF NOT EXISTS rate_cache (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key       TEXT NOT NULL UNIQUE,
    payload         JSONB NOT NULL,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rate_cache_key ON rate_cache (cache_key);
CREATE INDEX IF NOT EXISTS idx_rate_cache_expires ON rate_cache (expires_at);
