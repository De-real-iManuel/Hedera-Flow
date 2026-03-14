"""
Add tariffs for all supported countries and utility providers
Run this to populate tariff data for MVP testing
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import date
import json
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings

# Create engine and session using settings
engine = create_engine(settings.database_url)
Session = sessionmaker(bind=engine)

# Tariff configurations for all countries
TARIFFS = [
    {
        'country_code': 'ES',
        'utility_provider': 'Iberdrola',
        'currency': 'EUR',
        'rate_structure': {
            'type': 'flat',
            'rate': 0.15
        },
        'taxes_and_fees': {
            'vat': 0.21,
            'fixed_charge': 5.0
        }
    },
    {
        'country_code': 'US',
        'utility_provider': 'ConEd',
        'currency': 'USD',
        'rate_structure': {
            'type': 'flat',
            'rate': 0.17
        },
        'taxes_and_fees': {
            'sales_tax': 0.08,
            'fixed_charge': 10.0
        }
    },
    {
        'country_code': 'IN',
        'utility_provider': 'TATA Power',
        'currency': 'INR',
        'rate_structure': {
            'type': 'flat',
            'rate': 8.0
        },
        'taxes_and_fees': {
            'electricity_duty': 0.16,
            'fixed_charge': 50.0
        }
    },
    {
        'country_code': 'BR',
        'utility_provider': 'Eletrobras',
        'currency': 'BRL',
        'rate_structure': {
            'type': 'flat',
            'rate': 0.65
        },
        'taxes_and_fees': {
            'icms': 0.25,
            'pis_cofins': 0.0465,
            'fixed_charge': 20.0
        }
    },
    {
        'country_code': 'NG',
        'utility_provider': 'Port Harcourt Electricity Distribution Company',
        'currency': 'NGN',
        'rate_structure': {
            'type': 'band_based',
            'bands': [
                {'band': 'A', 'price': 209.5, 'description': 'Band A (20+ hours supply)'},
                {'band': 'B', 'price': 68.96, 'description': 'Band B (16-20 hours)'},
                {'band': 'C', 'price': 56.38, 'description': 'Band C (12-16 hours)'},
                {'band': 'D', 'price': 55.43, 'description': 'Band D (8-12 hours)'},
                {'band': 'E', 'price': 39.44, 'description': 'Band E (<8 hours)'}
            ]
        },
        'taxes_and_fees': {
            'vat': 0.075
        }
    }
]


def add_or_update_tariff(session, tariff_config):
    """Add or update a tariff in the database"""
    
    country_code = tariff_config['country_code']
    utility_provider = tariff_config['utility_provider']
    
    # Check if tariff exists
    check_query = text("""
        SELECT id FROM tariffs
        WHERE country_code = :country_code
        AND utility_provider = :utility_provider
        AND is_active = true
    """)
    
    result = session.execute(check_query, {
        'country_code': country_code,
        'utility_provider': utility_provider
    }).fetchone()
    
    if result:
        # Update existing tariff
        print(f"Updating tariff: {country_code}/{utility_provider}")
        
        update_query = text("""
            UPDATE tariffs
            SET rate_structure = CAST(:rate_structure AS jsonb),
                taxes_and_fees = CAST(:taxes_and_fees AS jsonb),
                currency = :currency,
                valid_from = :valid_from,
                updated_at = NOW()
            WHERE country_code = :country_code
            AND utility_provider = :utility_provider
            AND is_active = true
        """)
        
        session.execute(update_query, {
            'country_code': country_code,
            'utility_provider': utility_provider,
            'rate_structure': json.dumps(tariff_config['rate_structure']),
            'taxes_and_fees': json.dumps(tariff_config.get('taxes_and_fees', {})),
            'currency': tariff_config['currency'],
            'valid_from': date.today()
        })
        
        print(f"  ✓ Updated successfully")
        
    else:
        # Insert new tariff
        print(f"Creating tariff: {country_code}/{utility_provider}")
        
        insert_query = text("""
            INSERT INTO tariffs (
                id,
                country_code,
                utility_provider,
                currency,
                rate_structure,
                taxes_and_fees,
                subsidies,
                valid_from,
                valid_until,
                is_active,
                created_at,
                updated_at
            ) VALUES (
                gen_random_uuid(),
                :country_code,
                :utility_provider,
                :currency,
                CAST(:rate_structure AS jsonb),
                CAST(:taxes_and_fees AS jsonb),
                '{}'::jsonb,
                :valid_from,
                NULL,
                true,
                NOW(),
                NOW()
            )
        """)
        
        session.execute(insert_query, {
            'country_code': country_code,
            'utility_provider': utility_provider,
            'currency': tariff_config['currency'],
            'rate_structure': json.dumps(tariff_config['rate_structure']),
            'taxes_and_fees': json.dumps(tariff_config.get('taxes_and_fees', {})),
            'valid_from': date.today()
        })
        
        print(f"  ✓ Created successfully")


def main():
    """Add all tariffs"""
    print("=" * 60)
    print("Adding Tariffs for All Countries")
    print("=" * 60)
    print()
    
    session = Session()
    
    try:
        for tariff_config in TARIFFS:
            add_or_update_tariff(session, tariff_config)
            print()
        
        session.commit()
        print("=" * 60)
        print("✓ All tariffs added/updated successfully!")
        print("=" * 60)
        print()
        
        # Verify
        print("Verifying tariffs:")
        print("-" * 60)
        
        verify_query = text("""
            SELECT country_code, utility_provider, currency, is_active
            FROM tariffs
            ORDER BY country_code
        """)
        
        results = session.execute(verify_query).fetchall()
        
        for row in results:
            status = "✓ Active" if row[3] else "✗ Inactive"
            print(f"{row[0]:3} | {row[1]:50} | {row[2]:3} | {status}")
        
        print()
        print(f"Total tariffs: {len(results)}")
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
