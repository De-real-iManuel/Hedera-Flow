-- Migration: Add Email Verification Fields
-- Description: Adds email verification columns to users table
-- Date: 2026-02-24

-- Add email verification columns
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255) UNIQUE,
ADD COLUMN IF NOT EXISTS email_verification_expires TIMESTAMP WITH TIME ZONE;

-- Create index on verification token for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email_verification_token 
ON users(email_verification_token) 
WHERE email_verification_token IS NOT NULL;

-- Update existing users to be verified (for MVP/development)
-- In production, you might want to require verification
UPDATE users 
SET is_email_verified = TRUE 
WHERE is_email_verified IS NULL OR is_email_verified = FALSE;

-- Add comment
COMMENT ON COLUMN users.is_email_verified IS 'Whether user has verified their email address';
COMMENT ON COLUMN users.email_verification_token IS 'Token for email verification (expires after 24 hours)';
COMMENT ON COLUMN users.email_verification_expires IS 'Expiration timestamp for verification token';
