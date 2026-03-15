-- Migration: Add user preferences and security settings
-- Description: Adds JSON columns for user preferences and security settings

-- Add preferences column
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}'::jsonb;

-- Add security_settings column
ALTER TABLE users ADD COLUMN IF NOT EXISTS security_settings JSONB DEFAULT '{}'::jsonb;

-- Add comment
COMMENT ON COLUMN users.preferences IS 'User preferences including theme, language, and notification settings';
COMMENT ON COLUMN users.security_settings IS 'Security settings including biometric, PIN, and 2FA preferences';
