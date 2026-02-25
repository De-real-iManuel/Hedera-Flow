"""
Seed Spain Regional Distributors
Task 2.3.5: Spain utilities implementation
Requirements: US-2, FR-4.1
"""
import os
import sys
from datetime import date
import psycopg2
from psycopg2.extras import Json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

SPAIN_UTILITIES = [
    {"code": "IDE_IBERDROLA", "name": "i-DE (Iberdrola)", "regions": "Madrid, Valencia, Castile and León, Basque Country", "periods": [{"name": "peak", "hours": [10,11,12,13,14,18,19,20,21], "price": 0.40}, {"name": "standard", "hours": [8,9,15,16,17,22,23], "price": 0.25}, {"name": "off_peak", "hours": [0,1,2,3,4,5,6,7], "price": 0.15}]},
    {"code": "EDISTRIBUCION", "name": "e-distribución (Endesa)", "regions": "Andalusia, Aragon, Balearic Islands, Canary Islands, Catalonia, Extremadura", "periods": [{"name": "peak", "hours": [10,11,12,13,14,18,19,20,21], "price": 0.38}, {"name": "standard", "hours": [8,9,15,16,17,22,23], "price": 0.24}, {"name": "off_peak", "hours": [0,1,2,3,4,5,6,7], "price": 0.14}]},
    {"code": "UFD_NATURGY", "name": "UFD (Naturgy)", "regions": "Galicia, Madrid, Castile-La Mancha", "periods": [{"name": "peak", "hours": [10,11,12,13,14,18,19,20,21], "price": 0.39}, {"name": "standard", "hours": [8,9,15,16,17,22,23], "price": 0.26}, {"name": "off_peak", "hours": [0,1,2,3,4,5,6,7], "price": 0.16}]},
    {"code": "EREDES_EDP", "name": "E-Redes (EDP)", "regions": "Asturias, Madrid, Aragon", "periods": [{"name": "peak", "hours": [10,11,12,13,14,18,19,20,21], "price": 0.37}, {"name": "standard", "hours": [8,9,15,16,17,22,23], "price": 0.23}, {"name": "off_peak", "hours": [0,1,2,3,4,5,6,7], "price": 0.13}]},
    {"code": "VIESGO", "name": "Viesgo", "regions": "Cantabria, Asturias", "periods": [{"name": "peak", "hours": [10,11,12,13,14,18,19,20,21], "price": 0.41}, {"name": "standard", "hours": [8,9,15,16,17,22,23], "price": 0.27}, {"name": "off_peak", "hours": [0,1,2,3,4,5,6,7], "price": 0.17}]}
]

def seed_spain_utilities():
    conn = psycopg2.connect(settings.database_url)
    cursor = conn.cursor()
    
    try:
        print(f"Seeding {len(SPAIN_UTILITIES)} Spain utilities...")
        print("=" * 70)
        
        for util in SPAIN_UTILITIES:
            rate_structure = {"type": "time_of_use", "periods": util["periods"]}
            
            cursor.execute("""
                INSERT INTO tariffs (country_code, region, utility_provider, currency, rate_structure, taxes_and_fees, subsidies, valid_from, valid_until, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
            """, ("ES", util["regions"], util["code"], "EUR", Json(rate_structure), Json({"vat": 0.21, "distribution_charge": 0.045}), Json({}), date(2024, 1, 1), None, True))
            
            print(f"[OK] {util['code']}: {util['name']}")
            print(f"  Regions: {util['regions']}")
        
        conn.commit()
        print("=" * 70)
        print(f"[OK] Successfully seeded {len(SPAIN_UTILITIES)} Spain utilities!")
    except Exception as e:
        conn.rollback()
        print(f"[FAIL] Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    seed_spain_utilities()
