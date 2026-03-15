-- Migration 004: Add hedera_account_id to utility_providers table
-- This migration adds the hedera_account_id field to utility providers
-- so that payments can be sent directly to utility providers (FR-6.6, US-7)

-- Add hedera_account_id column to utility_providers table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'utility_providers' AND column_name = 'hedera_account_id'
    ) THEN
        ALTER TABLE utility_providers ADD COLUMN hedera_account_id VARCHAR(50);
    END IF;
END $$;

-- Create index for hedera_account_id lookups (non-unique for MVP)
CREATE INDEX IF NOT EXISTS idx_utility_providers_hedera_account ON utility_providers(hedera_account_id);

-- Add comment
COMMENT ON COLUMN utility_providers.hedera_account_id IS 'Hedera account ID for receiving bill payments (0.0.xxxxx format)';

-- For MVP/testnet, we'll use the treasury account as a placeholder for all utility providers
-- In production, each utility provider would have their own Hedera account
-- Update existing providers with treasury account (can be updated later per provider)
UPDATE utility_providers 
SET hedera_account_id = '0.0.7942957'  -- Treasury account as default
WHERE hedera_account_id IS NULL;
