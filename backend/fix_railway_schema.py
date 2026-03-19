#!/usr/bin/env python3
"""
Fix Railway DB schema — adds all missing columns to users table.
Run with: railway run python fix_railway_schema.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

migrations = [
    # Add missing user profile columns
    """
    ALTER TABLE users
        ADD COLUMN IF NOT EXISTS first_name VARCHAR(100),
        ADD COLUMN IF NOT EXISTS last_name VARCHAR(100),
        ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255),
        ADD COLUMN IF NOT EXISTS email_verification_expires TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS subsidy_eligible BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS subsidy_type VARCHAR(50),
        ADD COLUMN IF NOT EXISTS subsidy_verified_at TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS subsidy_expires_at TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS preferences JSONB,
        ADD COLUMN IF NOT EXISTS security_settings JSONB;
    """,
    # Add unique constraint on email_verification_token if not exists
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'users_email_verification_token_key'
        ) THEN
            ALTER TABLE users
                ADD CONSTRAINT users_email_verification_token_key
                UNIQUE (email_verification_token);
        END IF;
    END $$;
    """,
    # Add indexes
    """
    CREATE INDEX IF NOT EXISTS idx_users_first_name ON users(first_name);
    CREATE INDEX IF NOT EXISTS idx_users_last_name ON users(last_name);
    """,
]

print("Running Railway schema fix...")
try:
    with engine.connect() as conn:
        for i, sql in enumerate(migrations, 1):
            print(f"  Step {i}/{len(migrations)}...")
            conn.execute(text(sql))
        conn.commit()
    print("Schema fix complete.")

    # Verify
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """))
        cols = [r[0] for r in result]
        print(f"Users table columns: {cols}")

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
