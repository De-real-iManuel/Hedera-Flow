"""
Seed Utility Providers Table
Populates utility_providers table with data for all 5 regions
Requirements: US-2, FR-4.1
"""
import os
import sys
import psycopg2
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


# Utility providers data for all regions
UTILITY_PROVIDERS = [
    # ========== SPAIN (ES) ==========
    {"country": "ES", "state": "Madrid", "name": "i-DE (Iberdrola)", "code": "IDE_IBERDROLA", "areas": ["Madrid City", "Alcalá de Henares", "Getafe"]},
    {"country": "ES", "state": "Madrid", "name": "UFD (Naturgy)", "code": "UFD_NATURGY", "areas": ["Madrid North", "Alcobendas"]},
    {"country": "ES", "state": "Madrid", "name": "E-Redes (EDP)", "code": "EREDES_EDP", "areas": ["Madrid East"]},
    {"country": "ES", "state": "Valencia", "name": "i-DE (Iberdrola)", "code": "IDE_IBERDROLA", "areas": ["Valencia City", "Alicante", "Castellón"]},
    {"country": "ES", "state": "Catalonia", "name": "e-distribución (Endesa)", "code": "EDISTRIBUCION", "areas": ["Barcelona", "Tarragona", "Girona", "Lleida"]},
    {"country": "ES", "state": "Andalusia", "name": "e-distribución (Endesa)", "code": "EDISTRIBUCION", "areas": ["Seville", "Málaga", "Granada", "Córdoba"]},
    {"country": "ES", "state": "Basque Country", "name": "i-DE (Iberdrola)", "code": "IDE_IBERDROLA", "areas": ["Bilbao", "San Sebastián", "Vitoria"]},
    {"country": "ES", "state": "Galicia", "name": "UFD (Naturgy)", "code": "UFD_NATURGY", "areas": ["A Coruña", "Vigo", "Santiago"]},
    {"country": "ES", "state": "Asturias", "name": "Viesgo", "code": "VIESGO", "areas": ["Oviedo", "Gijón"]},
    {"country": "ES", "state": "Asturias", "name": "E-Redes (EDP)", "code": "EREDES_EDP", "areas": ["Avilés"]},
    {"country": "ES", "state": "Cantabria", "name": "Viesgo", "code": "VIESGO", "areas": ["Santander", "Torrelavega"]},
    
    # ========== NIGERIA (NG) ==========
    {"country": "NG", "state": "Lagos", "name": "Ikeja Electric (IKEDP)", "code": "IKEDP", "areas": ["Ikeja", "Agege", "Mushin", "Oshodi"]},
    {"country": "NG", "state": "Lagos", "name": "Eko Electricity (EKEDP)", "code": "EKEDP", "areas": ["Lagos Island", "Victoria Island", "Lekki", "Ikoyi"]},
    {"country": "NG", "state": "FCT", "name": "Abuja Electricity (AEDC)", "code": "AEDC", "areas": ["Abuja", "Gwagwalada", "Kuje"]},
    {"country": "NG", "state": "Kano", "name": "Kano Electricity (KEDCO)", "code": "KEDCO", "areas": ["Kano City", "Kumbotso"]},
    {"country": "NG", "state": "Rivers", "name": "Port Harcourt Electricity (PHED)", "code": "PHED", "areas": ["Port Harcourt", "Obio-Akpor"]},
    {"country": "NG", "state": "Oyo", "name": "Ibadan Electricity (IBEDC)", "code": "IBEDC", "areas": ["Ibadan", "Ogbomoso"]},
    {"country": "NG", "state": "Edo", "name": "Benin Electricity (BEDC)", "code": "BEDC", "areas": ["Benin City", "Auchi"]},
    {"country": "NG", "state": "Enugu", "name": "Enugu Electricity (EEDC)", "code": "EEDC", "areas": ["Enugu", "Nsukka"]},
    {"country": "NG", "state": "Kaduna", "name": "Kaduna Electricity (KAEDCO)", "code": "KAEDCO", "areas": ["Kaduna", "Zaria"]},
    {"country": "NG", "state": "Plateau", "name": "Jos Electricity (JEDC)", "code": "JEDC", "areas": ["Jos", "Bukuru"]},
    {"country": "NG", "state": "Adamawa", "name": "Yola Electricity (YEDC)", "code": "YEDC", "areas": ["Yola", "Jimeta"]},
    
    # ========== USA (US) ==========
    {"country": "US", "state": "California", "name": "Pacific Gas & Electric (PG&E)", "code": "PGE", "areas": ["San Francisco", "Oakland", "San Jose", "Sacramento"]},
    {"country": "US", "state": "California", "name": "Southern California Edison (SCE)", "code": "SCE", "areas": ["Los Angeles", "Orange County", "Riverside"]},
    {"country": "US", "state": "California", "name": "San Diego Gas & Electric (SDG&E)", "code": "SDGE", "areas": ["San Diego", "Imperial County"]},
    {"country": "US", "state": "Texas", "name": "Oncor Electric Delivery", "code": "ONCOR", "areas": ["Dallas", "Fort Worth", "Arlington"]},
    {"country": "US", "state": "Texas", "name": "CenterPoint Energy", "code": "CENTERPOINT", "areas": ["Houston", "Galveston"]},
    {"country": "US", "state": "Texas", "name": "AEP Texas", "code": "AEP_TEXAS", "areas": ["Corpus Christi", "Laredo"]},
    {"country": "US", "state": "New York", "name": "Consolidated Edison (ConEd)", "code": "CONED", "areas": ["Manhattan", "Bronx", "Queens", "Brooklyn"]},
    {"country": "US", "state": "New York", "name": "National Grid", "code": "NATIONAL_GRID", "areas": ["Buffalo", "Syracuse", "Rochester"]},
    {"country": "US", "state": "Florida", "name": "Florida Power & Light (FPL)", "code": "FPL", "areas": ["Miami", "Fort Lauderdale", "West Palm Beach"]},
    {"country": "US", "state": "Florida", "name": "Duke Energy Florida", "code": "DUKE_FL", "areas": ["Tampa", "St. Petersburg", "Clearwater"]},
    {"country": "US", "state": "Illinois", "name": "Commonwealth Edison (ComEd)", "code": "COMED", "areas": ["Chicago", "Naperville", "Aurora"]},
    
    # ========== INDIA (IN) ==========
    {"country": "IN", "state": "Delhi", "name": "Tata Power Delhi Distribution (TPDDL)", "code": "TPDDL", "areas": ["North Delhi", "Central Delhi"]},
    {"country": "IN", "state": "Delhi", "name": "BSES Rajdhani Power (BRPL)", "code": "BRPL", "areas": ["South Delhi", "West Delhi"]},
    {"country": "IN", "state": "Delhi", "name": "BSES Yamuna Power (BYPL)", "code": "BYPL", "areas": ["East Delhi", "Central Delhi"]},
    {"country": "IN", "state": "Maharashtra", "name": "Maharashtra State Electricity Distribution (MSEDCL)", "code": "MSEDCL", "areas": ["Pune", "Nagpur", "Nashik"]},
    {"country": "IN", "state": "Maharashtra", "name": "Tata Power", "code": "TATA_POWER_MH", "areas": ["Mumbai Suburbs"]},
    {"country": "IN", "state": "Maharashtra", "name": "Adani Electricity Mumbai", "code": "ADANI_MUMBAI", "areas": ["Mumbai City"]},
    {"country": "IN", "state": "Karnataka", "name": "Bangalore Electricity Supply Company (BESCOM)", "code": "BESCOM", "areas": ["Bangalore", "Bangalore Rural"]},
    {"country": "IN", "state": "Karnataka", "name": "Hubli Electricity Supply Company (HESCOM)", "code": "HESCOM", "areas": ["Hubli", "Dharwad"]},
    {"country": "IN", "state": "Gujarat", "name": "Dakshin Gujarat Vij Company (DGVCL)", "code": "DGVCL", "areas": ["Surat", "Valsad"]},
    {"country": "IN", "state": "Gujarat", "name": "Torrent Power", "code": "TORRENT_POWER", "areas": ["Ahmedabad", "Gandhinagar"]},
    {"country": "IN", "state": "Tamil Nadu", "name": "Tamil Nadu Generation and Distribution Corporation (TANGEDCO)", "code": "TANGEDCO", "areas": ["Chennai", "Coimbatore", "Madurai"]},
    
    # ========== BRAZIL (BR) ==========
    {"country": "BR", "state": "São Paulo", "name": "Enel São Paulo", "code": "ENEL_SP", "areas": ["São Paulo City", "Guarulhos", "Osasco"]},
    {"country": "BR", "state": "São Paulo", "name": "CPFL Paulista", "code": "CPFL_PAULISTA", "areas": ["Campinas", "Piracicaba", "Ribeirão Preto"]},
    {"country": "BR", "state": "Rio de Janeiro", "name": "Enel Rio", "code": "ENEL_RJ", "areas": ["Rio de Janeiro City", "Niterói"]},
    {"country": "BR", "state": "Minas Gerais", "name": "Cemig", "code": "CEMIG", "areas": ["Belo Horizonte", "Uberlândia", "Juiz de Fora"]},
    {"country": "BR", "state": "Bahia", "name": "Coelba (Neoenergia)", "code": "COELBA", "areas": ["Salvador", "Feira de Santana"]},
    {"country": "BR", "state": "Pernambuco", "name": "Celpe (Neoenergia)", "code": "CELPE", "areas": ["Recife", "Olinda", "Jaboatão"]},
    {"country": "BR", "state": "Ceará", "name": "Enel Ceará", "code": "ENEL_CE", "areas": ["Fortaleza", "Caucaia"]},
    {"country": "BR", "state": "Paraná", "name": "Copel", "code": "COPEL", "areas": ["Curitiba", "Londrina", "Maringá"]},
    {"country": "BR", "state": "Rio Grande do Sul", "name": "RGE Sul (CPFL)", "code": "RGE_SUL", "areas": ["Porto Alegre", "Caxias do Sul"]},
    {"country": "BR", "state": "Santa Catarina", "name": "Celesc", "code": "CELESC", "areas": ["Florianópolis", "Joinville", "Blumenau"]},
]


def seed_utility_providers():
    """Seed utility providers for all regions"""
    conn = psycopg2.connect(settings.database_url)
    cursor = conn.cursor()
    
    try:
        print(f"\nSeeding {len(UTILITY_PROVIDERS)} utility providers...")
        print("=" * 70)
        
        inserted_count = 0
        skipped_count = 0
        
        for provider in UTILITY_PROVIDERS:
            # Check if provider already exists
            cursor.execute("""
                SELECT id FROM utility_providers 
                WHERE country_code = %s AND state_province = %s AND provider_code = %s
            """, (provider["country"], provider["state"], provider["code"]))
            
            if cursor.fetchone():
                skipped_count += 1
                print(f"[SKIP] {provider['country']} - {provider['state']}: {provider['name']}")
                continue
            
            # Insert provider
            cursor.execute("""
                INSERT INTO utility_providers 
                (country_code, state_province, provider_name, provider_code, service_areas, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                provider["country"],
                provider["state"],
                provider["name"],
                provider["code"],
                provider["areas"],
                True
            ))
            
            inserted_count += 1
            print(f"[OK] {provider['country']} - {provider['state']}: {provider['name']}")
        
        conn.commit()
        print("=" * 70)
        print(f"✓ Successfully seeded {inserted_count} utility providers!")
        print(f"  Skipped {skipped_count} existing providers")
        print(f"  Total: {inserted_count + skipped_count} providers in database")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error seeding utility providers: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    seed_utility_providers()
