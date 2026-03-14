#!/usr/bin/env python3
"""
Check the actual bills table schema
"""
import sys
sys.path.append('.')

from app.core.database import get_db
from sqlalchemy import text

def check_bills_schema():
    """Check what columns exist in the bills table"""
    
    db = next(get_db())
    
    try:
        # Get table schema
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'bills' 
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        
        print("📋 Bills Table Schema:")
        print("=" * 50)
        
        for col in columns:
            nullable = "NULL" if col[2] == "YES" else "NOT NULL"
            print(f"  {col[0]:<25} {col[1]:<20} {nullable}")
        
        print(f"\n📊 Total columns: {len(columns)}")
        
        # Check if we have any bills
        result = db.execute(text("SELECT COUNT(*) FROM bills"))
        count = result.scalar()
        print(f"📈 Total bills: {count}")
        
        if count > 0:
            # Show sample bill
            result = db.execute(text("SELECT * FROM bills LIMIT 1"))
            bill = result.fetchone()
            print(f"\n📄 Sample bill columns:")
            for i, col_name in enumerate(result.keys()):
                print(f"  {col_name}: {bill[i]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_bills_schema()