#!/usr/bin/env python3
"""Check tariffs table schema"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Get table columns
    query = text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'tariffs'
        ORDER BY ordinal_position
    """)
    
    result = db.execute(query).fetchall()
    
    print("Tariffs table columns:")
    for row in result:
        print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
        
finally:
    db.close()
