-- Migration: Add USDC Payment Support
-- Date: March 2026
-- Description: Add columns to support USDC payments on both Hedera and Ethereum networks

-- Add payment method column
ALTER TABLE bills 
ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20) DEFAULT 'hbar';

-- Add USDC amount column
ALTER TABLE bills 
ADD COLUMN IF NOT EXISTS amount_usdc DECIMAL(20, 6);

-- Add USDC token ID/address column
ALTER TABLE bills 
ADD COLUMN IF NOT EXISTS usdc_token_id VARCHAR(100);

-- Add payment network column
ALTER TABLE bills 
ADD COLUMN IF NOT EXISTS payment_network VARCHAR(20);

-- Add Ethereum transaction hash column
ALTER TABLE bills 
ADD COLUMN IF NOT EXISTS ethereum_tx_hash VARCHAR(66);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_bills_payment_method ON bills(payment_method);
CREATE INDEX IF NOT EXISTS idx_bills_payment_network ON bills(payment_network);
CREATE INDEX IF NOT EXISTS idx_bills_ethereum_tx_hash ON bills(ethereum_tx_hash);

-- Add check constraint for payment method
ALTER TABLE bills 
ADD CONSTRAINT chk_payment_method 
CHECK (payment_method IN ('hbar', 'usdc_hedera', 'usdc_ethereum'));

-- Add check constraint for payment network
ALTER TABLE bills 
ADD CONSTRAINT chk_payment_network 
CHECK (payment_network IS NULL OR payment_network IN ('hedera', 'ethereum'));

-- Add comment to document the changes
COMMENT ON COLUMN bills.payment_method IS 'Payment method used: hbar, usdc_hedera, or usdc_ethereum';
COMMENT ON COLUMN bills.amount_usdc IS 'Payment amount in USDC (6 decimal places)';
COMMENT ON COLUMN bills.usdc_token_id IS 'USDC token ID (Hedera) or contract address (Ethereum)';
COMMENT ON COLUMN bills.payment_network IS 'Network used for payment: hedera or ethereum';
COMMENT ON COLUMN bills.ethereum_tx_hash IS 'Ethereum transaction hash for USDC payments on Ethereum';
