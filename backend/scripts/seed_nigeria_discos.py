"""
Seed all 11 Nigerian Distribution Companies (DisCos) with state coverage
Task 2.3.1: Nigeria DisCos Implementation
Requirements: US-2, FR-4.1
"""
import os
import sys
from datetime import date
import psycopg2
from psycopg2.extras import Json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


def get_db_connection():
    return psycopg2.connect(settings.database_url)


# Nigeria DisCos with state coverage and band-based tariffs
NIGERIA_DISCOS = [
    {
        "code": "AEDC",
        "name": "Abuja Electricity Distribution Company",
        "states": ["FCT", "Kogi", "Nasarawa", "Niger"],
        "bands": {
            "A": {"hours": 20, "price": 225.00},
            "B": {"hours": 16, "price": 63.30},
            "C": {"hours": 12, "price": 50.00},
            "D": {"hours": 8, "price": 43.00},
            "E": {"hours": 4, "price": 40.00}
        }
    },
    {
        "code": "BEDC",
        "name": "Benin Electricity Distribution Company",
        "states": ["Edo", "Delta", "Ondo", "Ekiti"],
        "bands": {
            "A": {"hours": 20, "price": 225.00},
            "B": {"hours": 16, "price": 63.30},
            "C": {"hours": 12, "price": 50.00},
            "D": {"hours": 8, "price": 43.00},
            "E": {"hours": 4, "price": 40.00}
        }
    },
    {
        "code": "EKEDP",
        "name": "Eko Electricity Distribution Company",
        "states": ["Lagos (Mainland)"],
        "bands": {
            "A": {"hours": 20, "price": 225.00},
            "B": {"hours": 16, "price": 63.30},
            "C": {"hours": 12, "price": 50.00},
            "D": {"hours": 8, "price": 43.00},
            "E": {"hours": 4, "price": 40.00}
        }
    },
    {
        "code": "EEDC",
        "name": "Enugu Electricity Distribution Company",
        "states": ["Enugu", "Abia", "Anambra", "Ebonyi", "Imo"],
        "bands": {
            "A": {"hours": 20, "price": 225.00},
            "B": {"hours": 16, "price": 63.30},
            "C": {"hours": 12, "price": 50.00},
            "D": {"hours": 8, "price": 43.00},
            "E": {"hours": 4, "price": 40.00}
        }
    },
    {
        "code": "IBEDC",
        "name": "Ibadan Electricity Distribution Company",
        "states": ["Oyo", "Osun", "Ogun", "Kwara"],
        "bands": {
            "A": {"hours": 20, "price": 225.00},
            "B": {"hours": 16, "price": 63.30},
            "C": {"hours": 12, "price": 50.00},
            "D": {"hours": 8, "price": 43.00},
            "E": {"hours": 4, "price": 40.00}
        }
    },
    {
        "code": "IKEDC",
        "name": "Ikeja Electricity Distribution Company",
        "states": ["Lagos (Island & Ikeja)"],
        "bands": {
            "A": {"hours": 20, "price": 225.00},
            "B": {"hours": 16, "price": 63.30},
            "C": {"hours": 12, "price": 50.00},
            "D": {"hours": 8, "price": 43.00},
            "E": {"hours": 4, "price": 40.00}
        }
    },
    {
        "code": "JEDC",
        "name": "Jos Electricity Distribution Company",
        "states": ["Plateau", "Bauchi", "Gombe", "Benue"],
        "bands": {
            "A": {"hours": 20, "price": 225.00},
            "B": {"hours": 16, "price": 63.30},
            "C": {"hours": 12, "price": 50.00},
            "D": {"hours": 8, "price": 43.00},
            "E": {"hours": 4, "price": 40.00}
        }
    },
    {
        "code": "KAEDCO",
        "name": "Kaduna Electricity Distribution Company",
        "states": ["Kaduna", "Kebbi", "Sokoto", "Zamfara"],
        "bands": {
            "A": {"hours": 20, "price": 225.00},
            "B": {"hours": 16, "price": 63.30},
            "C": {"hours": 12, "price": 50.00},
            "D": {"hours": 8, "price": 43.00},
            "E": {"hours": 4, "price": 40.00}
        }
    },
    {
        "code": "KEDCO",
        "name": "Kano Electricity Distribution Company",
        "states": ["Kano", "Jigawa", "Katsina"],
        "bands": {
            "A": {"hours": 20, "price": 225.00},
            "B": {"hours": 16, "price": 63.30},
            "C": {"hours": 12, "price": 50.00},
            "D": {"hours": 8, "price": 43.00},
            "E": {"hours": 4, "price": 40.00}
        }
    },
    {
        "code": "PHED",
        "name": "Port Harcourt Electricity Distribution Company",
        "states": ["Rivers", "Bayelsa", "Cross River", "Akwa Ibom"],
        "bands": {
            "A": {"hours": 20, "price": 225.00},
            "B": {"hours": 16, "price": 63.30},
            "C": {"hours": 12, "price": 50.00},
            "D": {"hours": 8, "price": 43.00},
            "E": {"hours": 4, "price": 40.00}
        }
    },
    {
        "code": "YEDC",
        "name": "Yola Electricity Distribution Company",
        "states": ["Adamawa", "Borno", "Taraba", "Yobe"],
        "bands": {
            "A": {"hours": 20, "price": 225.00},
            "B": {"hours": 16, "price": 63.30},
            "C": {"hours": 12, "price": 50.00},
            "D": {"hours": 8, "price": 43.00},
            "E": {"hours": 4, "price": 40.00}
        }
    }
]


def seed_nigeria_discos():
    """Seed all 11 Nigerian DisCos with state coverage"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print(f"Seeding {len(NIGERIA_DISCOS)} Nigerian DisCos...")
        print("=" * 70)
        
        for disco in NIGERIA_DISCOS:
            # Build rate structure
            rate_structure = {
                "type": "band_based",
                "bands": [
                    {
                        "name": band_name,
                        "hours_min": band_data["hours"],
                        "price": band_data["price"]
                    }
                    for band_name, band_data in disco["bands"].items()
                ]
            }
            
            # Build region string from states
            region = ", ".join(disco["states"])
            
            tariff = {
                "country_code": "NG",
                "region": region,
                "utility_provider": disco["code"],
                "utility_provider_name": disco["name"],
                "currency": "NGN",
                "rate_structure": rate_structure,
                "taxes_and_fees": {
                    "vat": 0.075,
                    "service_charge": 1500
                },
                "subsidies": {},
                "valid_from": date(2024, 1, 1),
                "valid_until": None,
                "is_active": True
            }
            
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
                ON CONFLICT DO NOTHING
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
            
            print(f"[OK] {disco['code']}: {disco['name']}")
            print(f"  States: {region}")
        
        conn.commit()
        print("=" * 70)
        print(f"[OK] Successfully seeded {len(NIGERIA_DISCOS)} Nigerian DisCos!")
        
    except Exception as e:
        conn.rollback()
        print(f"[FAIL] Error seeding DisCos: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    seed_nigeria_discos()
