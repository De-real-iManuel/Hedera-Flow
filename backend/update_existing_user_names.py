#!/usr/bin/env python3
"""
Update existing users with placeholder names if they don't have first_name/last_name
This is for users created before the migration
"""
from sqlalchemy import text
from app.core.database import engine

sql = """
-- Update users without names to have placeholder values
UPDATE users 
SET 
    first_name = COALESCE(first_name, 'User'),
    last_name = COALESCE(last_name, split_part(email, '@', 1))
WHERE first_name IS NULL OR last_name IS NULL;
"""

print("Updating existing users with placeholder names...")
with engine.connect() as conn:
    result = conn.execute(text(sql))
    conn.commit()
    print(f"✅ Updated {result.rowcount} users")
