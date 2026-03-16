#!/usr/bin/env python3
"""
Seed basic data for Hedera Flow
"""
import sys
from sqlalchemy import create_engine, text
from config import settings

def seed_basic_data():
    """Seed basic utility providers and tariffs"""
    print("🌱 Seeding basic data...")
    
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            # Insert basic utility providers
            print("Adding utility providers...")
            
            providers_sql = """
            INSERT INTO utility_providers (
                provider_name, provider_code, country_code, state_province, 
                service_areas, is_active, created_at
            ) VALUES 
            ('Eko Electricity Distribution Company', 'EKEDC', 'NG', 'Lagos', ARRAY['Lagos Island', 'Victoria Island', 'Ikoyi'], true, NOW()),
            ('Iberdrola', 'IBE', 'ES', 'Madrid', ARRAY['Madrid', 'Toledo', 'Guadalajara'], true, NOW()),
            ('Pacific Gas & Electric', 'PGE', 'US', 'California', ARRAY['San Francisco', 'Oakland', 'San Jose'], true, NOW()),
            ('Tata Power', 'TATA', 'IN', 'Maharashtra', ARRAY['Mumbai', 'Pune', 'Nashik'], true, NOW()),
            ('CEMIG', 'CEMIG', 'BR', 'Minas Gerais', ARRAY['Belo Horizonte', 'Uberlandia'], true, NOW());
            """
            
            conn.execute(text(providers_sql))
            
            # Insert basic tariffs
            print("Adding tariffs...")
            
            tariffs_sql = """
            INSERT INTO tariffs (
                country_code, region, utility_provider, currency,
                rate_structure, taxes_and_fees, subsidies,
                valid_from, valid_until, is_active,
                created_at, updated_at
            ) VALUES 
            (
                'NG', 'Lagos', 'EKEDC', 'NGN',
                '{"type": "band_based", "bands": [{"name": "A", "hours_min": 20, "price": 225.00}, {"name": "B", "hours_min": 16, "price": 63.00}]}',
                '{"vat": 7.5, "service_charge": 5.0}',
                '{"lifeline": {"threshold": 50, "discount": 50}}',
                '2024-01-01', '2024-12-31', true,
                NOW(), NOW()
            ),
            (
                'ES', 'Madrid', 'Iberdrola', 'EUR',
                '{"type": "time_of_use", "periods": [{"name": "peak", "hours": "18-22", "price": 0.25}, {"name": "off_peak", "hours": "22-18", "price": 0.15}]}',
                '{"iva": 21.0, "electricity_tax": 5.11}',
                '{}',
                '2024-01-01', '2024-12-31', true,
                NOW(), NOW()
            ),
            (
                'US', 'California', 'PG&E', 'USD',
                '{"type": "tiered", "tiers": [{"threshold": 300, "price": 0.25}, {"threshold": 600, "price": 0.35}]}',
                '{"delivery_charge": 0.05, "public_purpose": 0.02}',
                '{"care": {"discount": 20}}',
                '2024-01-01', '2024-12-31', true,
                NOW(), NOW()
            );
            """
            
            conn.execute(text(tariffs_sql))
            conn.commit()
            
            print("✅ Basic data seeded successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        return False

if __name__ == "__main__":
    success = seed_basic_data()
    sys.exit(0 if success else 1)