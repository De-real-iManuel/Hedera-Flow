-- Hedera Flow MVP - PostgreSQL Database Schema
-- Version: 1.0
-- Created: February 19, 2026

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- NULL if wallet-only auth
    country_code CHAR(2) NOT NULL CHECK (country_code IN ('ES', 'US', 'IN', 'BR', 'NG')),
    hedera_account_id VARCHAR(50) UNIQUE,
    wallet_type VARCHAR(20) DEFAULT 'hashpack',  -- 'hashpack', 'system_generated'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_hedera_account ON users(hedera_account_id);
CREATE INDEX idx_users_country ON users(country_code);

-- ============================================================================
-- METERS TABLE
-- ============================================================================
CREATE TABLE meters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    meter_id VARCHAR(50) NOT NULL,
    utility_provider VARCHAR(100) NOT NULL,
    meter_type VARCHAR(20) CHECK (meter_type IN ('prepaid', 'postpaid')),
    band_classification VARCHAR(10),  -- For Nigeria: 'A', 'B', 'C', 'D', 'E'
    address TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, meter_id)
);

-- Indexes for meters table
CREATE INDEX idx_meters_user_id ON meters(user_id);
CREATE INDEX idx_meters_meter_id ON meters(meter_id);

-- ============================================================================
-- TARIFFS TABLE
-- ============================================================================
CREATE TABLE tariffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code CHAR(2) NOT NULL,
    region VARCHAR(100),
    utility_provider VARCHAR(100) NOT NULL,
    currency CHAR(3) NOT NULL,
    
    -- Rate Structure (JSONB)
    -- Example for Spain:
    -- {
    --   "type": "time_of_use",
    --   "periods": [
    --     {"name": "peak", "hours": [10,11,12,13,14,18,19,20,21], "price": 0.40},
    --     {"name": "standard", "hours": [8,9,15,16,17,22,23], "price": 0.25},
    --     {"name": "off_peak", "hours": [0,1,2,3,4,5,6,7], "price": 0.15}
    --   ]
    -- }
    -- Example for Nigeria:
    -- {
    --   "type": "band_based",
    --   "bands": [
    --     {"name": "A", "hours_min": 20, "price": 225.00},
    --     {"name": "B", "hours_min": 16, "price": 63.30},
    --     {"name": "C", "hours_min": 12, "price": 50.00},
    --     {"name": "D", "hours_min": 8, "price": 43.00},
    --     {"name": "E", "hours_min": 0, "price": 40.00}
    --   ]
    -- }
    rate_structure JSONB NOT NULL,
    
    -- Taxes and Fees (JSONB)
    -- Example:
    -- {
    --   "vat": 0.21,
    --   "distribution_charge": 0.045,
    --   "service_charge": 1000
    -- }
    taxes_and_fees JSONB,
    
    -- Subsidies (JSONB)
    subsidies JSONB,
    
    -- Validity
    valid_from DATE NOT NULL,
    valid_until DATE,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for tariffs table
CREATE INDEX idx_tariffs_country_provider ON tariffs(country_code, utility_provider);
CREATE INDEX idx_tariffs_active ON tariffs(is_active, valid_from, valid_until);

-- ============================================================================
-- VERIFICATIONS TABLE
-- ============================================================================
CREATE TABLE verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    meter_id UUID REFERENCES meters(id) ON DELETE CASCADE,
    
    -- Reading Data
    reading_value DECIMAL(12, 2) NOT NULL,
    previous_reading DECIMAL(12, 2),
    consumption_kwh DECIMAL(12, 2),
    
    -- OCR Data
    image_ipfs_hash VARCHAR(100),
    ocr_engine VARCHAR(20),  -- 'tesseract', 'google_vision'
    confidence DECIMAL(5, 2),  -- 0.00 to 1.00
    raw_ocr_text TEXT,
    
    -- Fraud Detection
    fraud_score DECIMAL(5, 2),  -- 0.00 to 1.00
    fraud_flags JSONB,  -- Array of detected issues
    
    -- Utility Cross-Check
    utility_reading DECIMAL(12, 2),
    utility_api_response JSONB,
    
    -- Status
    status VARCHAR(20) CHECK (status IN ('VERIFIED', 'WARNING', 'DISCREPANCY', 'FRAUD_DETECTED')),
    
    -- Blockchain
    hcs_topic_id VARCHAR(50),
    hcs_sequence_number BIGINT,
    hcs_timestamp TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for verifications table
CREATE INDEX idx_verifications_user_id ON verifications(user_id);
CREATE INDEX idx_verifications_meter_id ON verifications(meter_id);
CREATE INDEX idx_verifications_status ON verifications(status);
CREATE INDEX idx_verifications_created_at ON verifications(created_at DESC);

-- ============================================================================
-- BILLS TABLE
-- ============================================================================
CREATE TABLE bills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    meter_id UUID REFERENCES meters(id) ON DELETE CASCADE,
    verification_id UUID REFERENCES verifications(id),
    
    -- Billing Data
    consumption_kwh DECIMAL(12, 2) NOT NULL,
    base_charge DECIMAL(12, 2) NOT NULL,
    taxes DECIMAL(12, 2) NOT NULL,
    subsidies DECIMAL(12, 2) DEFAULT 0,
    total_fiat DECIMAL(12, 2) NOT NULL,
    currency CHAR(3) NOT NULL,  -- 'EUR', 'USD', 'INR', 'BRL', 'NGN'
    
    -- Tariff Used
    tariff_id UUID REFERENCES tariffs(id),
    tariff_snapshot JSONB,  -- Full tariff at time of calculation
    
    -- Payment Data
    amount_hbar DECIMAL(18, 8),  -- HBAR amount
    exchange_rate DECIMAL(12, 6),  -- HBAR/fiat rate used
    exchange_rate_timestamp TIMESTAMP,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'disputed', 'refunded')),
    
    -- Hedera Transaction
    hedera_tx_id VARCHAR(100),
    hedera_consensus_timestamp TIMESTAMP,
    
    -- Blockchain Logging
    hcs_topic_id VARCHAR(50),
    hcs_sequence_number BIGINT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    paid_at TIMESTAMP
);

-- Indexes for bills table
CREATE INDEX idx_bills_user_id ON bills(user_id);
CREATE INDEX idx_bills_meter_id ON bills(meter_id);
CREATE INDEX idx_bills_status ON bills(status);
CREATE INDEX idx_bills_created_at ON bills(created_at DESC);

-- ============================================================================
-- DISPUTES TABLE
-- ============================================================================
CREATE TABLE disputes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_id VARCHAR(50) UNIQUE NOT NULL,  -- DISP-{COUNTRY}-{YEAR}-{ID}
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    bill_id UUID REFERENCES bills(id) ON DELETE CASCADE,
    
    -- Dispute Details
    reason VARCHAR(50) CHECK (reason IN ('OVERCHARGE', 'METER_ERROR', 'TARIFF_ERROR', 'OTHER')),
    description TEXT,
    evidence_ipfs_hashes TEXT[],  -- Array of IPFS hashes
    
    -- Escrow
    escrow_amount_hbar DECIMAL(18, 8),
    escrow_amount_fiat DECIMAL(12, 2),
    escrow_currency CHAR(3),
    escrow_tx_id VARCHAR(100),
    
    -- Resolution
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'under_review', 'resolved_user', 'resolved_utility', 'cancelled')),
    resolution_notes TEXT,
    resolved_by UUID REFERENCES users(id),  -- Admin user
    resolved_at TIMESTAMP,
    
    -- Blockchain
    hcs_topic_id VARCHAR(50),
    hcs_sequence_number BIGINT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for disputes table
CREATE INDEX idx_disputes_user_id ON disputes(user_id);
CREATE INDEX idx_disputes_bill_id ON disputes(bill_id);
CREATE INDEX idx_disputes_status ON disputes(status);
CREATE INDEX idx_disputes_created_at ON disputes(created_at DESC);

-- ============================================================================
-- EXCHANGE RATES CACHE TABLE
-- ============================================================================
CREATE TABLE exchange_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    currency CHAR(3) NOT NULL,  -- 'EUR', 'USD', 'INR', 'BRL', 'NGN'
    hbar_price DECIMAL(12, 6) NOT NULL,  -- Price of 1 HBAR in fiat
    source VARCHAR(50) NOT NULL,  -- 'coingecko', 'coinmarketcap'
    fetched_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for exchange_rates table
CREATE INDEX idx_exchange_rates_currency_time ON exchange_rates(currency, fetched_at DESC);

-- ============================================================================
-- AUDIT LOGS TABLE
-- ============================================================================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,  -- 'login', 'verification', 'payment', 'dispute'
    entity_type VARCHAR(50),  -- 'user', 'bill', 'dispute'
    entity_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for audit_logs table
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, created_at DESC);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE users IS 'User accounts with email/password or wallet authentication';
COMMENT ON TABLE meters IS 'Registered electricity meters for users';
COMMENT ON TABLE tariffs IS 'Regional electricity tariffs and pricing structures';
COMMENT ON TABLE verifications IS 'Meter reading verifications with OCR and fraud detection';
COMMENT ON TABLE bills IS 'Calculated bills with HBAR payment tracking';
COMMENT ON TABLE disputes IS 'Bill disputes with escrow and resolution tracking';
COMMENT ON TABLE exchange_rates IS 'Cached HBAR exchange rates for fiat currencies';
COMMENT ON TABLE audit_logs IS 'Audit trail for all user actions';

-- ============================================================================
-- INITIAL DATA (Optional - for development)
-- ============================================================================

-- Note: Seed data for tariffs should be added separately via migration scripts
-- This ensures production data is managed properly
