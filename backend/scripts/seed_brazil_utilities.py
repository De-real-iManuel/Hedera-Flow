"""
Seed Brazil Regional Distributors
Task 2.3.4: Brazil utilities implementation
Requirements: US-2, FR-4.1
"""
import os
import sys
from datetime import date
import psycopg2
from psycopg2.extras import Json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

BRAZIL_UTILITIES = [
    # Enel Group
    {"code": "ENEL_SP", "name": "Enel São Paulo", "state": "São Paulo", "tiers": [{"min": 0, "max": 100, "price": 0.50}, {"min": 101, "max": 300, "price": 0.70}, {"min": 301, "max": None, "price": 0.90}]},
    {"code": "ENEL_RJ", "name": "Enel Rio", "state": "Rio de Janeiro", "tiers": [{"min": 0, "max": 100, "price": 0.52}, {"min": 101, "max": 300, "price": 0.72}, {"min": 301, "max": None, "price": 0.92}]},
    {"code": "ENEL_CE", "name": "Enel Ceará", "state": "Ceará", "tiers": [{"min": 0, "max": 100, "price": 0.48}, {"min": 101, "max": 300, "price": 0.68}, {"min": 301, "max": None, "price": 0.88}]},
    # Equatorial Group
    {"code": "EQUATORIAL_MA", "name": "Equatorial Maranhão", "state": "Maranhão", "tiers": [{"min": 0, "max": 100, "price": 0.45}, {"min": 101, "max": 300, "price": 0.65}, {"min": 301, "max": None, "price": 0.85}]},
    {"code": "EQUATORIAL_PA", "name": "Equatorial Pará", "state": "Pará", "tiers": [{"min": 0, "max": 100, "price": 0.46}, {"min": 101, "max": 300, "price": 0.66}, {"min": 301, "max": None, "price": 0.86}]},
    {"code": "EQUATORIAL_PI", "name": "Equatorial Piauí", "state": "Piauí", "tiers": [{"min": 0, "max": 100, "price": 0.44}, {"min": 101, "max": 300, "price": 0.64}, {"min": 301, "max": None, "price": 0.84}]},
    {"code": "EQUATORIAL_AL", "name": "Equatorial Alagoas", "state": "Alagoas", "tiers": [{"min": 0, "max": 100, "price": 0.47}, {"min": 101, "max": 300, "price": 0.67}, {"min": 301, "max": None, "price": 0.87}]},
    {"code": "EQUATORIAL_RS", "name": "Equatorial Rio Grande do Sul", "state": "Rio Grande do Sul", "tiers": [{"min": 0, "max": 100, "price": 0.49}, {"min": 101, "max": 300, "price": 0.69}, {"min": 301, "max": None, "price": 0.89}]},
    {"code": "EQUATORIAL_GO", "name": "Equatorial Goiás", "state": "Goiás", "tiers": [{"min": 0, "max": 100, "price": 0.48}, {"min": 101, "max": 300, "price": 0.68}, {"min": 301, "max": None, "price": 0.88}]},
    # Neoenergia Group
    {"code": "COELBA", "name": "Coelba (Bahia)", "state": "Bahia", "tiers": [{"min": 0, "max": 100, "price": 0.51}, {"min": 101, "max": 300, "price": 0.71}, {"min": 301, "max": None, "price": 0.91}]},
    {"code": "CELPE", "name": "Celpe (Pernambuco)", "state": "Pernambuco", "tiers": [{"min": 0, "max": 100, "price": 0.50}, {"min": 101, "max": 300, "price": 0.70}, {"min": 301, "max": None, "price": 0.90}]},
    {"code": "COSERN", "name": "Cosern (Rio Grande do Norte)", "state": "Rio Grande do Norte", "tiers": [{"min": 0, "max": 100, "price": 0.49}, {"min": 101, "max": 300, "price": 0.69}, {"min": 301, "max": None, "price": 0.89}]},
    {"code": "ELEKTRO", "name": "Elektro (SP/MS)", "state": "São Paulo/Mato Grosso do Sul", "tiers": [{"min": 0, "max": 100, "price": 0.52}, {"min": 101, "max": 300, "price": 0.72}, {"min": 301, "max": None, "price": 0.92}]},
    # CPFL Energia
    {"code": "CPFL_PAULISTA", "name": "CPFL Paulista", "state": "São Paulo", "tiers": [{"min": 0, "max": 100, "price": 0.53}, {"min": 101, "max": 300, "price": 0.73}, {"min": 301, "max": None, "price": 0.93}]},
    {"code": "CPFL_PIRATININGA", "name": "CPFL Piratininga", "state": "São Paulo", "tiers": [{"min": 0, "max": 100, "price": 0.54}, {"min": 101, "max": 300, "price": 0.74}, {"min": 301, "max": None, "price": 0.94}]},
    {"code": "RGE", "name": "RGE (Rio Grande do Sul)", "state": "Rio Grande do Sul", "tiers": [{"min": 0, "max": 100, "price": 0.50}, {"min": 101, "max": 300, "price": 0.70}, {"min": 301, "max": None, "price": 0.90}]},
    # State-Owned
    {"code": "CEMIG", "name": "Cemig (Minas Gerais)", "state": "Minas Gerais", "tiers": [{"min": 0, "max": 100, "price": 0.55}, {"min": 101, "max": 300, "price": 0.75}, {"min": 301, "max": None, "price": 0.95}]},
    {"code": "COPEL", "name": "Copel (Paraná)", "state": "Paraná", "tiers": [{"min": 0, "max": 100, "price": 0.51}, {"min": 101, "max": 300, "price": 0.71}, {"min": 301, "max": None, "price": 0.91}]},
    {"code": "CELESC", "name": "Celesc (Santa Catarina)", "state": "Santa Catarina", "tiers": [{"min": 0, "max": 100, "price": 0.52}, {"min": 101, "max": 300, "price": 0.72}, {"min": 301, "max": None, "price": 0.92}]},
    {"code": "LIGHT", "name": "Light (Rio de Janeiro)", "state": "Rio de Janeiro", "tiers": [{"min": 0, "max": 100, "price": 0.56}, {"min": 101, "max": 300, "price": 0.76}, {"min": 301, "max": None, "price": 0.96}]}
]

def seed_brazil_utilities():
    conn = psycopg2.connect(settings.database_url)
    cursor = conn.cursor()
    
    try:
        print(f"Seeding {len(BRAZIL_UTILITIES)} Brazil utilities...")
        print("=" * 70)
        
        for util in BRAZIL_UTILITIES:
            rate_structure = {
                "type": "tiered",
                "tiers": [{"name": f"tier{i+1}", "min_kwh": t["min"], "max_kwh": t["max"], "price": t["price"]} for i, t in enumerate(util["tiers"])]
            }
            
            cursor.execute("""
                INSERT INTO tariffs (country_code, region, utility_provider, currency, rate_structure, taxes_and_fees, subsidies, valid_from, valid_until, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
            """, ("BR", util["state"], util["code"], "BRL", Json(rate_structure), Json({"icms_tax": 0.20}), Json({}), date(2024, 1, 1), None, True))
            
            print(f"[OK] {util['code']}: {util['name']} ({util['state']})")
        
        conn.commit()
        print("=" * 70)
        print(f"[OK] Successfully seeded {len(BRAZIL_UTILITIES)} Brazil utilities!")
    except Exception as e:
        conn.rollback()
        print(f"[FAIL] Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    seed_brazil_utilities()
