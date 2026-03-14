#!/usr/bin/env python3
"""
Add missing columns to bills table to match the model
"""
import sys
sys.path.append('.')

from app.core.database import get_db
from sqlalchemy import text

def fix_bills_schema():
    """Add missing columns to bills table"""
    
    db = next(get_db())
    
    try:
        print("🔧 Adding missing columns to bills table...")
        
        # Add missing columns
        missing_columns = [
            "ALTER TABLE bills ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20) DEFAULT 'hbar'",
            "ALTER TABLE bills ADD COLUMN IF NOT EXISTS amount_usdc DECIMAL(20, 6)",
            "ALTER TABLE bills ADD COLUMN IF NOT EXISTS usdc_token_id VARCHAR(100)",
            "ALTER TABLE bills ADD COLUMN IF NOT EXISTS payment_network VARCHAR(20)",
            "ALTER TABLE bills ADD COLUMN IF NOT EXISTS ethereum_tx_hash VARCHAR(66)"
        ]
        
        for sql in missing_columns:
            print(f"   Executing: {sql}")
            db.execute(text(sql))
        
        db.commit()
        print("✅ Bills table schema updated successfully!")
        
        # Verify the changes
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bills' 
            ORDER BY ordinal_position
        """))
        
        columns = [row[0] for row in result.fetchall()]
        print(f"\n📋 Updated bills table columns ({len(columns)} total):")
        for col in columns:
            print(f"   - {col}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_bills_schema()