-- Hedera Flow MVP - Database Initialization Script
-- This script runs automatically when PostgreSQL container starts for the first time

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    country_code CHAR(2) NOT NULL CHECK (country_code IN ('ES', 'US', 'IN', 'BR', 'NG')),
    hedera_account_id VARCHAR(50) UNIQUE,
    wallet_type VARCHAR(20) DEFAULT 'hashpack',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_hedera_account ON users(hedera_account_id);
CREATE INDEX IF NOT EXISTS idx_users_country ON users(country_code);

-- Create meters table
CREATE TABLE IF NOT EXISTS meters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    meter_id VARCHAR(50) NOT NULL,
    utility_provider VARCHAR(100) NOT NULL,
    meter_type VARCHAR(20) CHECK (meter_type IN ('prepaid', 'postpaid')),
    band_classification VARCHAR(10),
    address TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, meter_id)
);

-- Create indexes for meters table
CREATE INDEX IF NOT EXISTS idx_meters_user_id ON meters(user_id);
CREATE INDEX IF NOT EXISTS idx_meters_meter_id ON meters(meter_id);

-- Create verifications table
CREATE TABLE IF NOT EXISTS verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    meter_id UUID REFERENCES meters(id) ON DELETE CASCADE,
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
    status VARCHAR(20) CHECK (status IN ('VERIFIED', 'WARNING', 'DISCREPANCY', 'FRAUD_DETECTED')),
    hcs_topic_id VARCHAR(50),
    hcs_sequence_number BIGINT,
    hcs_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for verifications table
CREATE INDEX IF NOT EXISTS idx_verifications_user_id ON verifications(user_id);
CREATE INDEX IF NOT EXISTS idx_verifications_meter_id ON verifications(meter_id);
CREATE INDEX IF NOT EXISTS idx_verifications_status ON verifications(status);
CREATE INDEX IF NOT EXISTS idx_verifications_created_at ON verifications(created_at DESC);

-- Create tariffs table
CREATE TABLE IF NOT EXISTS tariffs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    country_code CHAR(2) NOT NULL,
    region VARCHAR(100),
    utility_provider VARCHAR(100) NOT NULL,
    currency CHAR(3) NOT NULL,
    rate_structure JSONB NOT NULL,
    taxes_and_fees JSONB,
    subsidies JSONB,
    valid_from DATE NOT NULL,
    valid_until DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for tariffs table
CREATE INDEX IF NOT EXISTS idx_tariffs_country_provider ON tariffs(country_code, utility_provider);
CREATE INDEX IF NOT EXISTS idx_tariffs_active ON tariffs(is_active, valid_from, valid_until);

-- Create bills table
CREATE TABLE IF NOT EXISTS bills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    meter_id UUID REFERENCES meters(id) ON DELETE CASCADE,
    verification_id UUID REFERENCES verifications(id),
    consumption_kwh DECIMAL(12, 2) NOT NULL,
    base_charge DECIMAL(12, 2) NOT NULL,
    taxes DECIMAL(12, 2) NOT NULL,
    subsidies DECIMAL(12, 2) DEFAULT 0,
    total_fiat DECIMAL(12, 2) NOT NULL,
    currency CHAR(3) NOT NULL,
    tariff_id UUID REFERENCES tariffs(id),
    tariff_snapshot JSONB,
    amount_hbar DECIMAL(18, 8),
    exchange_rate DECIMAL(12, 6),
    exchange_rate_timestamp TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'disputed', 'refunded')),
    hedera_tx_id VARCHAR(100),
    hedera_consensus_timestamp TIMESTAMP,
    hcs_topic_id VARCHAR(50),
    hcs_sequence_number BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    paid_at TIMESTAMP
);

-- Create indexes for bills table
CREATE INDEX IF NOT EXISTS idx_bills_user_id ON bills(user_id);
CREATE INDEX IF NOT EXISTS idx_bills_meter_id ON bills(meter_id);
CREATE INDEX IF NOT EXISTS idx_bills_status ON bills(status);
CREATE INDEX IF NOT EXISTS idx_bills_created_at ON bills(created_at DESC);

-- Create disputes table
CREATE TABLE IF NOT EXISTS disputes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dispute_id VARCHAR(50) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    bill_id UUID REFERENCES bills(id) ON DELETE CASCADE,
    reason VARCHAR(50) CHECK (reason IN ('OVERCHARGE', 'METER_ERROR', 'TARIFF_ERROR', 'OTHER')),
    description TEXT,
    evidence_ipfs_hashes TEXT[],
    escrow_amount_hbar DECIMAL(18, 8),
    escrow_amount_fiat DECIMAL(12, 2),
    escrow_currency CHAR(3),
    escrow_tx_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'under_review', 'resolved_user', 'resolved_utility', 'cancelled')),
    resolution_notes TEXT,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP,
    hcs_topic_id VARCHAR(50),
    hcs_sequence_number BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for disputes table
CREATE INDEX IF NOT EXISTS idx_disputes_user_id ON disputes(user_id);
CREATE INDEX IF NOT EXISTS idx_disputes_bill_id ON disputes(bill_id);
CREATE INDEX IF NOT EXISTS idx_disputes_status ON disputes(status);
CREATE INDEX IF NOT EXISTS idx_disputes_created_at ON disputes(created_at DESC);

-- Create exchange_rates table
CREATE TABLE IF NOT EXISTS exchange_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    currency CHAR(3) NOT NULL,
    hbar_price DECIMAL(12, 6) NOT NULL,
    source VARCHAR(50) NOT NULL,
    fetched_at TIMESTAMP DEFAULT NOW()
);

-- Create index for exchange_rates table
CREATE INDEX IF NOT EXISTS idx_exchange_rates_currency_time ON exchange_rates(currency, fetched_at DESC);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for audit_logs table
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action, created_at DESC);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Hedera Flow database initialized successfully!';
END $$;
