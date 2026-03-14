#!/usr/bin/env python3
"""Check tariffs in database"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Check for Nigeria tariffs
    query = text("""
        SELECT id, country_code, utility_provider, rate_structure, is_active
        FROM tariffs
        WHERE country_code = 'NG'
        ORDER BY created_at DESC
        LIMIT 5
    """)
    
    result = db.execute(query).fetchall()
    
    print(f"Found {len(result)} Nigeria tariff(s):")
    for row in result:
        print(f"  - Provider: {row[2]}, Active: {row[4]}")
        print(f"    Rate Structure: {row[3]}")
        
    # Check for Port Harcourt specifically
    query2 = text("""
        SELECT id, utility_provider, rate_structure, is_active
        FROM tariffs
        WHERE country_code = 'NG' 
        AND utility_provider LIKE '%Port Harcourt%'
    """)
    
    result2 = db.execute(query2).fetchall()
    print(f"\nPort Harcourt tariffs: {len(result2)}")
    for row in result2:
        print(f"  - {row[1]}, Active: {row[3]}")
        
finally:
    db.close()
