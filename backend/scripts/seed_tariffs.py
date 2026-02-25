"""
Seed tariff data for Spain, USA, India, Brazil, and Nigeria
Based on requirements from .kiro/specs/hedera-flow-mvp/requirements.md
"""
import os
import sys
from datetime import date
import psycopg2
from psycopg2.extras import Json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings


def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(settings.database_url)


def seed_tariffs():
    """Seed tariff data for all 5 regions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Spain (Iberdrola) - Time-of-Use
        spain_tariff = {
            "country_code": "ES",
            "region": "National",
            "utility_provider": "Iberdrola",
            "currency": "EUR",
            "rate_structure": {
                "type": "time_of_use",
                "periods": [
                    {
                        "name": "peak",
                        "hours": [10, 11, 12, 13, 14, 18, 19, 20, 21],
                        "price": 0.40
                    },
                    {
                        "name": "standard",
                        "hours": [8, 9, 15, 16, 17, 22, 23],
                        "price": 0.25
                    },
                    {
                        "name": "off_peak",
                        "hours": [0, 1, 2, 3, 4, 5, 6, 7],
                        "price": 0.15
                    }
                ]
            },
            "taxes_and_fees": {
                "vat": 0.21,
                "distribution_charge": 0.045
            },
            "subsidies": {},
            "valid_from": date(2024, 1, 1),
            "valid_until": None,
            "is_active": True
        }
        
        # USA (PG&E California) - Tiered
        usa_tariff = {
            "country_code": "US",
            "region": "California",
            "utility_provider": "PG&E",
            "currency": "USD",
            "rate_structure": {
                "type": "tiered",
                "tiers": [
                    {
                        "name": "tier1",
                        "min_kwh": 0,
                        "max_kwh": 400,
                        "price": 0.32
                    },
                    {
                        "name": "tier2",
                        "min_kwh": 401,
                        "max_kwh": 800,
                        "price": 0.40
                    },
                    {
                        "name": "tier3",
                        "min_kwh": 801,
                        "max_kwh": None,
                        "price": 0.50
                    }
                ]
            },
            "taxes_and_fees": {
                "sales_tax": 0.0725,
                "fixed_monthly_fee": 10.00
            },
            "subsidies": {},
            "valid_from": date(2024, 1, 1),
            "valid_until": None,
            "is_active": True
        }
        
        # India (Tata Power) - Tiered
        india_tariff = {
            "country_code": "IN",
            "region": "National",
            "utility_provider": "Tata Power",
            "currency": "INR",
            "rate_structure": {
                "type": "tiered",
                "tiers": [
                    {
                        "name": "tier1",
                        "min_kwh": 0,
                        "max_kwh": 100,
                        "price": 4.50
                    },
                    {
                        "name": "tier2",
                        "min_kwh": 101,
                        "max_kwh": 300,
                        "price": 6.00
                    },
                    {
                        "name": "tier3",
                        "min_kwh": 301,
                        "max_kwh": None,
                        "price": 7.50
                    }
                ]
            },
            "taxes_and_fees": {
                "vat": 0.18
            },
            "subsidies": {},
            "valid_from": date(2024, 1, 1),
            "valid_until": None,
            "is_active": True
        }
        
        # Brazil (Regional) - Tiered
        brazil_tariff = {
            "country_code": "BR",
            "region": "National",
            "utility_provider": "Regional Provider",
            "currency": "BRL",
            "rate_structure": {
                "type": "tiered",
                "tiers": [
                    {
                        "name": "tier1",
                        "min_kwh": 0,
                        "max_kwh": 100,
                        "price": 0.50
                    },
                    {
                        "name": "tier2",
                        "min_kwh": 101,
                        "max_kwh": 300,
                        "price": 0.70
                    },
                    {
                        "name": "tier3",
                        "min_kwh": 301,
                        "max_kwh": None,
                        "price": 0.90
                    }
                ]
            },
            "taxes_and_fees": {
                "icms_tax": 0.20
            },
            "subsidies": {},
            "valid_from": date(2024, 1, 1),
            "valid_until": None,
            "is_active": True
        }
        
        # Nigeria (EKEDC/IKEDC) - Band-Based Tiered
        nigeria_tariff = {
            "country_code": "NG",
            "region": "National",
            "utility_provider": "EKEDC",
            "currency": "NGN",
            "rate_structure": {
                "type": "band_based",
                "bands": [
                    {
                        "name": "A",
                        "hours_min": 20,
                        "price": 225.00
                    },
                    {
                        "name": "B",
                        "hours_min": 16,
                        "price": 63.30
                    },
                    {
                        "name": "C",
                        "hours_min": 12,
                        "price": 50.00
                    },
                    {
                        "name": "D",
                        "hours_min": 8,
                        "price": 43.00
                    },
                    {
                        "name": "E",
                        "hours_min": 0,
                        "price": 40.00
                    }
                ]
            },
            "taxes_and_fees": {
                "vat": 0.075,
                "service_charge": 1500
            },
            "subsidies": {},
            "valid_from": date(2024, 1, 1),
            "valid_until": None,
            "is_active": True
        }
        
        # Insert all tariffs
        tariffs = [spain_tariff, usa_tariff, india_tariff, brazil_tariff, nigeria_tariff]
        
        for tariff in tariffs:
            cursor.execute("""
                INSERT INTO tariffs (
                    country_code, region, utility_provider, currency,
                    rate_structure, taxes_and_fees, subsidies,
                    valid_from, valid_until, is_active
                ) VALUES (
                    %(country_code)s, %(region)s, %(utility_provider)s, %(currency)s,
                    %(rate_structure)s, %(taxes_and_fees)s, %(subsidies)s,
                    %(valid_from)s, %(valid_until)s, %(is_active)s
                )
            """, {
                "country_code": tariff["country_code"],
                "region": tariff["region"],
                "utility_provider": tariff["utility_provider"],
                "currency": tariff["currency"],
                "rate_structure": Json(tariff["rate_structure"]),
                "taxes_and_fees": Json(tariff["taxes_and_fees"]),
                "subsidies": Json(tariff["subsidies"]),
                "valid_from": tariff["valid_from"],
                "valid_until": tariff["valid_until"],
                "is_active": tariff["is_active"]
            })
            
            print(f"✓ Seeded tariff for {tariff['country_code']} - {tariff['utility_provider']}")
        
        conn.commit()
        print(f"\n✓ Successfully seeded {len(tariffs)} tariffs!")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error seeding tariffs: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("Seeding tariff data for Spain, USA, India, Brazil, and Nigeria...")
    print("=" * 70)
    seed_tariffs()
