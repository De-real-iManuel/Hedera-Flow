-- ============================================================================
-- HEDERA FLOW - COMPLETE DATABASE MIGRATION FOR SUPABASE
-- ============================================================================
-- This file contains all migrations to create the complete schema
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard → SQL Editor
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- MIGRATION 001: INITIAL SCHEMA
-- ============================================================================

-- USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    country_code CHAR(2) NOT NULL,
    hedera_account_id VARCHAR(50) UNIQUE,
    wallet_type VARCHAR(20) DEFAULT 'hashpack',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    subsidy_eligible BOOLEAN DEFAULT false,
    subsidy_type VARCHAR(50),
    subsidy_verified_at TIMESTAMP,
    subsidy_expires_at TIMESTAMP,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_email_verified BOOLEAN DEFAULT false,
    email_verification_token VARCHAR(255),
    email_verification_expires TIMESTAMP,
    preferences JSONB,
    security_settings JSONB,
    evm_address VARCHAR(42),
    kms_key_id VARCHAR(255),
    CONSTRAINT users_country_code_check CHECK (country_code IN ('ES', 'US', 'IN', 'BR', 'NG'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_hedera_account ON users(hedera_account_id);
CREATE INDEX IF NOT EXISTS idx_users_country ON users(country_code);
CREATE INDEX IF NOT EXISTS idx_users_evm_address ON users(evm_address);
CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(is_email_verified);
CREATE INDEX IF NOT EXISTS idx_users_subsidy_eligible ON users(subsidy_eligible);
CREATE INDEX IF NOT EXISTS idx_users_subsidy_expires ON users(subsidy_expires_at);

-- METERS TABLE
CREATE TABLE IF NOT EXISTS meters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meter_id VARCHAR(50) NOT NULL,
    utility_provider VARCHAR(100) NOT NULL,
    meter_type VARCHAR(20),
    band_classification VARCHAR(10),
    address TEXT,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT meters_meter_type_check CHECK (meter_type IN ('prepaid', 'postpaid')),
    CONSTRAINT meters_user_id_meter_id_key UNIQUE (user_id, meter_id)
);

CREATE INDEX IF NOT EXISTS idx_meters_user_id ON meters(user_id);
CREATE INDEX IF NOT EXISTS idx_meters_meter_id ON meters(meter_id);

-- TARIFFS TABLE
CREATE TABLE IF NOT EXISTS tariffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code CHAR(2) NOT NULL,
    region VARCHAR(100),
    utility_provider VARCHAR(100) NOT NULL,
    currency CHAR(3) NOT NULL,
    rate_structure JSONB NOT NULL,
    taxes_and_fees JSONB,
    subsidies JSONB,
    valid_from DATE NOT NULL,
    valid_until DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tariffs_country_provider ON tariffs(country_code, utility_provider);
CREATE INDEX IF NOT EXISTS idx_tariffs_active ON tariffs(is_active, valid_from, valid_until);

-- VERIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meter_id UUID NOT NULL REFERENCES meters(id) ON DELETE CASCADE,
    reading_value DECIMAL(12, 2) NOT NULL,
    previous_reading DECIMAL(12, 2),
    consumption_kwh DECIMAL(12, 2),
    image_ipfs_hash VARCHAR(100),
    ocr_engine VARCHAR(20),
    confidence DECIMAL(5, 2),
    raw_ocr_text TEXT,
    fraud_score DECIMAL(5, 2),
    fraud_flags JSONB,
    utility_reading DECIMAL(12, 2),
    utility_api_response JSONB,
    status VARCHAR(20),
    hcs_topic_id VARCHAR(50),
    hcs_sequence_number BIGINT,
    hcs_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT verifications_status_check CHECK (status IN ('VERIFIED', 'WARNING', 'DISCREPANCY', 'FRAUD_DETECTED'))
);

CREATE INDEX IF NOT EXISTS idx_verifications_user_id ON verifications(user_id);
CREATE INDEX IF NOT EXISTS idx_verifications_meter_id ON verifications(meter_id);
CREATE INDEX IF NOT EXISTS idx_verifications_status ON verifications(status);
CREATE INDEX IF NOT EXISTS idx_verifications_created_at ON verifications(created_at DESC);

-- BILLS TABLE
CREATE TABLE IF NOT EXISTS bills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meter_id UUID NOT NULL REFERENCES meters(id) ON DELETE CASCADE,
    verification_id UUID REFERENCES verifications(id),
    consumption_kwh DECIMAL(12, 2) NOT NULL,
    base_charge DECIMAL(12, 2) NOT NULL,
    taxes DECIMAL(12, 2) NOT NULL,
    subsidies DECIMAL(12, 2) DEFAULT 0,
    total_fiat DECIMAL(12, 2) NOT NULL,
    currency CHAR(3) NOT NULL,
    tariff_id UUID REFERENCES tariffs(id),
    tariff_snapshot JSONB,
    payment_method VARCHAR(20) DEFAULT 'hbar' NOT NULL,
    amount_hbar DECIMAL(18, 8),
    amount_usdc DECIMAL(20, 6),
    exchange_rate DECIMAL(12, 6),
    exchange_rate_timestamp TIMESTAMP,
    usdc_token_id VARCHAR(100),
    payment_network VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending',
    hedera_tx_id VARCHAR(100),
    ethereum_tx_hash VARCHAR(66),
    hedera_consensus_timestamp TIMESTAMP,
    hcs_topic_id VARCHAR(50),
    hcs_sequence_number BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    paid_at TIMESTAMP,
    CONSTRAINT bills_status_check CHECK (status IN ('pending', 'paid', 'disputed', 'refunded')),
    CONSTRAINT check_payment_method CHECK (payment_method IN ('hbar', 'usdc_hedera', 'usdc_ethereum')),
    CONSTRAINT check_payment_network CHECK (payment_network IS NULL OR payment_network IN ('hedera', 'ethereum'))
);

CREATE INDEX IF NOT EXISTS idx_bills_user_id ON bills(user_id);
CREATE INDEX IF NOT EXISTS idx_bills_meter_id ON bills(meter_id);
CREATE INDEX IF NOT EXISTS idx_bills_status ON bills(status);
CREATE INDEX IF NOT EXISTS idx_bills_created_at ON bills(created_at DESC);

-- DISPUTES TABLE
CREATE TABLE IF NOT EXISTS disputes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_id VARCHAR(50) NOT NULL UNIQUE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bill_id UUID NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
    reason VARCHAR(50),
    description TEXT,
    evidence_ipfs_hashes TEXT[],
    escrow_amount_hbar DECIMAL(18, 8),
    escrow_amount_fiat DECIMAL(12, 2),
    escrow_currency CHAR(3),
    escrow_tx_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    resolution_notes TEXT,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP,
    hcs_topic_id VARCHAR(50),
    hcs_sequence_number BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT disputes_reason_check CHECK (reason IN ('OVERCHARGE', 'METER_ERROR', 'TARIFF_ERROR', 'OTHER')),
    CONSTRAINT disputes_status_check CHECK (status IN ('pending', 'under_review', 'resolved_user', 'resolved_utility', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_disputes_user_id ON disputes(user_id);
CREATE INDEX IF NOT EXISTS idx_disputes_bill_id ON disputes(bill_id);
CREATE INDEX IF NOT EXISTS idx_disputes_status ON disputes(status);
CREATE INDEX IF NOT EXISTS idx_disputes_created_at ON disputes(created_at DESC);

-- EXCHANGE RATES TABLE
CREATE TABLE IF NOT EXISTS exchange_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    currency CHAR(3) NOT NULL,
    hbar_price DECIMAL(12, 6) NOT NULL,
    source VARCHAR(50) NOT NULL,
    fetched_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exchange_rates_currency_time ON exchange_rates(currency, fetched_at DESC);

-- AUDIT LOGS TABLE
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action, created_at DESC);

-- ============================================================================
-- MIGRATION 002: PERFORMANCE INDEXES
-- ============================================================================

-- Users performance indexes
CREATE INDEX IF NOT EXISTS idx_users_active_country ON users(is_active, country_code) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login DESC) WHERE last_login IS NOT NULL;

-- Meters performance indexes
CREATE INDEX IF NOT EXISTS idx_meters_user_primary ON meters(user_id, is_primary) WHERE is_primary = true;
CREATE INDEX IF NOT EXISTS idx_meters_utility_provider ON meters(utility_provider);
CREATE INDEX IF NOT EXISTS idx_meters_band_classification ON meters(utility_provider, band_classification) WHERE band_classification IS NOT NULL;

-- Tariffs performance indexes
CREATE INDEX IF NOT EXISTS idx_tariffs_region_active ON tariffs(country_code, region, utility_provider, is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_tariffs_validity_dates ON tariffs(valid_from, valid_until);

-- Verifications performance indexes
CREATE INDEX IF NOT EXISTS idx_verifications_user_recent ON verifications(user_id, created_at DESC) INCLUDE (status, reading_value, confidence);
CREATE INDEX IF NOT EXISTS idx_verifications_meter_history ON verifications(meter_id, created_at DESC) INCLUDE (reading_value, consumption_kwh);
CREATE INDEX IF NOT EXISTS idx_verifications_fraud_score ON verifications(fraud_score) WHERE fraud_score > 0.4;
CREATE INDEX IF NOT EXISTS idx_verifications_hcs ON verifications(hcs_topic_id, hcs_sequence_number);
CREATE INDEX IF NOT EXISTS idx_verifications_status_date ON verifications(status, created_at DESC);

-- Bills performance indexes
CREATE INDEX IF NOT EXISTS idx_bills_user_status ON bills(user_id, status, created_at DESC) INCLUDE (total_fiat, currency);
CREATE INDEX IF NOT EXISTS idx_bills_pending ON bills(created_at DESC) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_bills_paid_date ON bills(paid_at DESC) WHERE status = 'paid' AND paid_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_bills_hedera_tx ON bills(hedera_tx_id) WHERE hedera_tx_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_bills_verification ON bills(verification_id, status);
CREATE INDEX IF NOT EXISTS idx_bills_tariff ON bills(tariff_id, created_at DESC);

-- Disputes performance indexes
CREATE INDEX IF NOT EXISTS idx_disputes_user_status ON disputes(user_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_disputes_pending ON disputes(created_at DESC) WHERE status IN ('pending', 'under_review');
CREATE INDEX IF NOT EXISTS idx_disputes_resolved ON disputes(resolved_by, resolved_at DESC) WHERE resolved_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_disputes_reason ON disputes(reason, status);

-- Exchange rates performance indexes
CREATE INDEX IF NOT EXISTS idx_exchange_rates_latest ON exchange_rates(currency, fetched_at DESC) INCLUDE (hbar_price, source);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_source ON exchange_rates(source, fetched_at DESC);

-- Audit logs performance indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_ip ON audit_logs(ip_address, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action ON audit_logs(user_id, action, created_at DESC);

-- ============================================================================
-- MIGRATION 003: UTILITY PROVIDERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS utility_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code CHAR(2) NOT NULL,
    state_province VARCHAR(100) NOT NULL,
    provider_name VARCHAR(100) NOT NULL,
    provider_code VARCHAR(20) NOT NULL,
    service_areas TEXT[],
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    CONSTRAINT utility_providers_country_code_check CHECK (country_code IN ('ES', 'US', 'IN', 'BR', 'NG')),
    CONSTRAINT utility_providers_country_state_code_key UNIQUE (country_code, state_province, provider_code)
);

CREATE INDEX IF NOT EXISTS idx_utility_providers_country ON utility_providers(country_code);
CREATE INDEX IF NOT EXISTS idx_utility_providers_state ON utility_providers(state_province);
CREATE INDEX IF NOT EXISTS idx_utility_providers_country_state ON utility_providers(country_code, state_province);
CREATE INDEX IF NOT EXISTS idx_utility_providers_code ON utility_providers(provider_code);
CREATE INDEX IF NOT EXISTS idx_utility_providers_active ON utility_providers(is_active);

-- Add utility_provider_id and hedera_account_id to utility_providers
ALTER TABLE utility_providers ADD COLUMN IF NOT EXISTS hedera_account_id VARCHAR(50);
CREATE INDEX IF NOT EXISTS idx_utility_providers_hedera_account ON utility_providers(hedera_account_id);

-- Add utility_provider_id to meters
ALTER TABLE meters ADD COLUMN IF NOT EXISTS utility_provider_id UUID REFERENCES utility_providers(id);
ALTER TABLE meters ADD COLUMN IF NOT EXISTS state_province VARCHAR(100);
CREATE INDEX IF NOT EXISTS idx_meters_utility_provider_id ON meters(utility_provider_id);

-- ============================================================================
-- MIGRATION 004: SUBSIDY ELIGIBILITY
-- ============================================================================

-- Subsidy columns already added in users table creation above
-- This section kept for migration tracking purposes only

-- ============================================================================
-- MIGRATION 005: PREPAID TOKENS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS prepaid_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_id VARCHAR(50) NOT NULL UNIQUE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meter_id UUID NOT NULL REFERENCES meters(id) ON DELETE CASCADE,
    units_purchased DECIMAL(12, 2) NOT NULL,
    units_remaining DECIMAL(12, 2) NOT NULL,
    amount_paid_hbar DECIMAL(18, 8),
    amount_paid_usdc DECIMAL(18, 6),
    amount_paid_fiat DECIMAL(12, 2) NOT NULL,
    currency CHAR(3) NOT NULL,
    exchange_rate DECIMAL(12, 6) NOT NULL,
    tariff_rate DECIMAL(12, 6) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    hedera_tx_id VARCHAR(100),
    hedera_consensus_timestamp TIMESTAMP,
    hcs_topic_id VARCHAR(50),
    hcs_sequence_number BIGINT,
    issued_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    depleted_at TIMESTAMP,
    CONSTRAINT check_prepaid_token_status CHECK (status IN ('pending', 'active', 'depleted', 'expired', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_prepaid_tokens_user_id ON prepaid_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_prepaid_tokens_meter_id ON prepaid_tokens(meter_id);
CREATE INDEX IF NOT EXISTS idx_prepaid_tokens_status ON prepaid_tokens(status);
CREATE INDEX IF NOT EXISTS idx_prepaid_tokens_issued_at ON prepaid_tokens(issued_at);

-- ============================================================================
-- MIGRATION 006: SMART METER KEYS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS smart_meter_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meter_id UUID NOT NULL UNIQUE REFERENCES meters(id) ON DELETE CASCADE,
    public_key TEXT NOT NULL,
    private_key_encrypted TEXT,
    encryption_iv TEXT,
    kms_key_id VARCHAR(255),
    algorithm VARCHAR(20) NOT NULL DEFAULT 'ED25519',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_smart_meter_keys_meter_id ON smart_meter_keys(meter_id);

-- ============================================================================
-- MIGRATION 007: CONSUMPTION LOGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS consumption_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meter_id UUID NOT NULL REFERENCES meters(id) ON DELETE CASCADE,
    token_id UUID REFERENCES prepaid_tokens(id),
    consumption_kwh DECIMAL(12, 2) NOT NULL,
    reading_before DECIMAL(12, 2),
    reading_after DECIMAL(12, 2),
    timestamp BIGINT NOT NULL,
    signature TEXT NOT NULL,
    public_key TEXT NOT NULL,
    signature_valid BOOLEAN NOT NULL,
    units_deducted DECIMAL(12, 2),
    units_remaining DECIMAL(12, 2),
    hcs_topic_id VARCHAR(50),
    hcs_sequence_number BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_consumption_logs_meter_created ON consumption_logs(meter_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_consumption_logs_token ON consumption_logs(token_id);
CREATE INDEX IF NOT EXISTS idx_consumption_logs_timestamp ON consumption_logs(timestamp DESC);

-- ============================================================================
-- MIGRATION 009: STS TOKEN FIELD
-- ============================================================================

ALTER TABLE prepaid_tokens ADD COLUMN IF NOT EXISTS sts_token VARCHAR(25);
CREATE INDEX IF NOT EXISTS ix_prepaid_tokens_sts_token ON prepaid_tokens(sts_token);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify all tables were created
SELECT 
    schemaname,
    tablename
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
