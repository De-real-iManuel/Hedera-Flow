#!/usr/bin/env python3
"""Add Port Harcourt Electricity Distribution Company tariff"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from sqlalchemy import text
import uuid
from datetime import datetime, date
import json

db = SessionLocal()
try:
    # Port Harcourt tariff with band-based pricing (NGN per kWh)
    tariff_data = {
        'id': str(uuid.uuid4()),
        'country_code': 'NG',
        'utility_provider': 'Port Harcourt Electricity Distribution Company',
        'rate_structure': {
            'type': 'band_based',
            'bands': [
                {'band': 'A', 'price': 209.50, 'description': 'Band A (20+ hours supply)'},
                {'band': 'B', 'price': 68.96, 'description': 'Band B (16-20 hours)'},
                {'band': 'C', 'price': 56.38, 'description': 'Band C (12-16 hours)'},
                {'band': 'D', 'price': 55.43, 'description': 'Band D (8-12 hours)'},
                {'band': 'E', 'price': 39.44, 'description': 'Band E (<8 hours)'}
            ]
        },
        'currency': 'NGN',
        'valid_from': date.today(),
        'is_active': True
    }
    
    # Check if tariff already exists
    check_query = text("""
        SELECT id FROM tariffs 
        WHERE country_code = 'NG' 
        AND utility_provider = 'Port Harcourt Electricity Distribution Company'
        AND is_active = true
    """)
    
    existing = db.execute(check_query).fetchone()
    
    if existing:
        print("Tariff already exists. Updating...")
        update_query = text("""
            UPDATE tariffs 
            SET rate_structure = CAST(:rate_structure AS jsonb),
                currency = :currency,
                valid_from = :valid_from,
                updated_at = NOW()
            WHERE country_code = 'NG' 
            AND utility_provider = 'Port Harcourt Electricity Distribution Company'
            AND is_active = true
        """)
        
        db.execute(update_query, {
            'rate_structure': json.dumps(tariff_data['rate_structure']),
            'currency': tariff_data['currency'],
            'valid_from': tariff_data['valid_from']
        })
        print("✓ Tariff updated successfully")
    else:
        print("Creating new tariff...")
        insert_query = text("""
            INSERT INTO tariffs (
                id, country_code, utility_provider, 
                rate_structure, currency, valid_from, is_active
            ) VALUES (
                :id, :country_code, :utility_provider,
                CAST(:rate_structure AS jsonb), :currency, :valid_from, :is_active
            )
        """)
        
        db.execute(insert_query, {
            'id': tariff_data['id'],
            'country_code': tariff_data['country_code'],
            'utility_provider': tariff_data['utility_provider'],
            'rate_structure': json.dumps(tariff_data['rate_structure']),
            'currency': tariff_data['currency'],
            'valid_from': tariff_data['valid_from'],
            'is_active': tariff_data['is_active']
        })
        print("✓ Tariff created successfully")
    
    db.commit()
    
    # Verify
    verify_query = text("""
        SELECT id, utility_provider, rate_structure, currency, is_active
        FROM tariffs
        WHERE country_code = 'NG' 
        AND utility_provider = 'Port Harcourt Electricity Distribution Company'
    """)
    
    result = db.execute(verify_query).fetchone()
    if result:
        print(f"\nVerified tariff:")
        print(f"  Provider: {result[1]}")
        print(f"  Currency: {result[3]}")
        print(f"  Active: {result[4]}")
        print(f"  Rate Structure: {result[2]}")
    
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
