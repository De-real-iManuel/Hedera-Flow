"""
Initialize Supabase database with schema
Run this script after creating your Supabase project
"""
import sys
import psycopg2
from psycopg2 import OperationalError
from config import settings


def init_database():
    """Initialize database schema from init.sql"""
    print("🚀 Initializing Supabase database...")
    print(f"   Database: {settings.database_url.split('@')[1].split('/')[0] if '@' in settings.database_url else 'localhost'}")
    
    try:
        # Connect to database
        conn = psycopg2.connect(settings.database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to database")
        
        # Read init.sql file
        print("📖 Reading init.sql...")
        with open('init.sql', 'r') as f:
            sql_script = f.read()
        
        # Execute SQL script
        print("⚙️  Executing SQL script...")
        cursor.execute(sql_script)
        
        print("✅ Schema created successfully")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print(f"✅ Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Database initialization complete!")
        return True
        
    except FileNotFoundError:
        print("❌ Error: init.sql file not found")
        print("   Make sure you're running this script from the backend/ directory")
        return False
    except OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Check DATABASE_URL in .env file")
        print("   2. Verify Supabase project is running")
        print("   3. Check your internet connection")
        print("   4. Ensure password is correct")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def seed_tariff_data():
    """Seed initial tariff data for 5 regions"""
    print("\n🌱 Seeding tariff data...")
    
    try:
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        
        # Spain tariff (Time-of-use)
        cursor.execute("""
            INSERT INTO tariffs (country_code, region, utility_provider, currency, rate_structure, taxes_and_fees, valid_from, is_active)
            VALUES (
                'ES',
                'National',
                'Iberdrola',
                'EUR',
                '{"type": "time_of_use", "periods": [
                    {"name": "peak", "hours": [10,11,12,13,14,18,19,20,21], "price": 0.40},
                    {"name": "standard", "hours": [8,9,15,16,17,22,23], "price": 0.25},
                    {"name": "off_peak", "hours": [0,1,2,3,4,5,6,7], "price": 0.15}
                ]}'::jsonb,
                '{"vat": 0.21, "distribution_charge": 0.045}'::jsonb,
                CURRENT_DATE,
                true
            )
            ON CONFLICT DO NOTHING
        """)
        
        # USA tariff (Tiered)
        cursor.execute("""
            INSERT INTO tariffs (country_code, region, utility_provider, currency, rate_structure, taxes_and_fees, valid_from, is_active)
            VALUES (
                'US',
                'California',
                'PG&E',
                'USD',
                '{"type": "tiered", "tiers": [
                    {"name": "tier1", "max_kwh": 400, "price": 0.32},
                    {"name": "tier2", "max_kwh": 800, "price": 0.40},
                    {"name": "tier3", "max_kwh": null, "price": 0.50}
                ]}'::jsonb,
                '{"sales_tax": 0.0725, "fixed_monthly_fee": 10.00}'::jsonb,
                CURRENT_DATE,
                true
            )
            ON CONFLICT DO NOTHING
        """)
        
        # India tariff (Tiered)
        cursor.execute("""
            INSERT INTO tariffs (country_code, region, utility_provider, currency, rate_structure, taxes_and_fees, valid_from, is_active)
            VALUES (
                'IN',
                'Maharashtra',
                'Tata Power',
                'INR',
                '{"type": "tiered", "tiers": [
                    {"name": "tier1", "max_kwh": 100, "price": 4.50},
                    {"name": "tier2", "max_kwh": 300, "price": 6.00},
                    {"name": "tier3", "max_kwh": null, "price": 7.50}
                ]}'::jsonb,
                '{"vat": 0.18}'::jsonb,
                CURRENT_DATE,
                true
            )
            ON CONFLICT DO NOTHING
        """)
        
        # Brazil tariff (Tiered)
        cursor.execute("""
            INSERT INTO tariffs (country_code, region, utility_provider, currency, rate_structure, taxes_and_fees, valid_from, is_active)
            VALUES (
                'BR',
                'São Paulo',
                'Enel',
                'BRL',
                '{"type": "tiered", "tiers": [
                    {"name": "tier1", "max_kwh": 100, "price": 0.50},
                    {"name": "tier2", "max_kwh": 300, "price": 0.70},
                    {"name": "tier3", "max_kwh": null, "price": 0.90}
                ]}'::jsonb,
                '{"icms_tax": 0.18}'::jsonb,
                CURRENT_DATE,
                true
            )
            ON CONFLICT DO NOTHING
        """)
        
        # Nigeria tariff (Band-based)
        cursor.execute("""
            INSERT INTO tariffs (country_code, region, utility_provider, currency, rate_structure, taxes_and_fees, valid_from, is_active)
            VALUES (
                'NG',
                'Lagos',
                'EKEDC',
                'NGN',
                '{"type": "band_based", "bands": [
                    {"name": "A", "hours_min": 20, "price": 225.00},
                    {"name": "B", "hours_min": 16, "price": 63.30},
                    {"name": "C", "hours_min": 12, "price": 50.00},
                    {"name": "D", "hours_min": 8, "price": 43.00},
                    {"name": "E", "hours_min": 0, "price": 40.00}
                ]}'::jsonb,
                '{"vat": 0.075, "service_charge": 1500}'::jsonb,
                CURRENT_DATE,
                true
            )
            ON CONFLICT DO NOTHING
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Tariff data seeded successfully")
        print("   - Spain (Iberdrola)")
        print("   - USA (PG&E)")
        print("   - India (Tata Power)")
        print("   - Brazil (Enel)")
        print("   - Nigeria (EKEDC)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error seeding tariff data: {e}")
        return False


def main():
    """Main initialization function"""
    print("=" * 60)
    print("Hedera Flow - Supabase Database Initialization")
    print("=" * 60)
    
    # Initialize schema
    schema_success = init_database()
    
    if not schema_success:
        print("\n❌ Schema initialization failed. Aborting.")
        sys.exit(1)
    
    # Seed tariff data
    seed_success = seed_tariff_data()
    
    print("\n" + "=" * 60)
    print("Initialization Summary")
    print("=" * 60)
    print(f"Schema:  {'✅ SUCCESS' if schema_success else '❌ FAILED'}")
    print(f"Tariffs: {'✅ SUCCESS' if seed_success else '❌ FAILED'}")
    print("=" * 60)
    
    if schema_success and seed_success:
        print("\n🎉 Supabase database is ready!")
        print("\nNext steps:")
        print("   1. Run: python test_supabase_connection.py")
        print("   2. Continue to Task 1.6: Configure environment variables")
        sys.exit(0)
    else:
        print("\n⚠️  Initialization completed with errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
