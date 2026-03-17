#!/usr/bin/env python3
import os
import subprocess
import sys

def run_migrations():
    """Run database migrations on startup"""
    print("🚀 Running database migrations...")
    
    # First run raw SQL migrations to ensure schema is up to date
    try:
        from sqlalchemy import create_engine, text
        from config import settings
        
        if not settings.database_url:
            print("⚠️  No DATABASE_URL - skipping migrations")
            return True
            
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            sql_migrations = [
                ("add_first_last_name", "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(100)"),
                ("add_last_name", "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(100)"),
                ("add_is_email_verified", "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT FALSE"),
                ("add_email_verification_token", "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255)"),
                ("add_email_verification_expires", "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_expires TIMESTAMP WITH TIME ZONE"),
                ("add_preferences", "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}'::jsonb"),
                ("add_security_settings", "ALTER TABLE users ADD COLUMN IF NOT EXISTS security_settings JSONB DEFAULT '{}'::jsonb"),
                ("add_subsidy_eligible", "ALTER TABLE users ADD COLUMN IF NOT EXISTS subsidy_eligible BOOLEAN DEFAULT FALSE"),
                ("add_subsidy_type", "ALTER TABLE users ADD COLUMN IF NOT EXISTS subsidy_type VARCHAR(50)"),
                ("add_subsidy_verified_at", "ALTER TABLE users ADD COLUMN IF NOT EXISTS subsidy_verified_at TIMESTAMP WITH TIME ZONE"),
                ("add_subsidy_expires_at", "ALTER TABLE users ADD COLUMN IF NOT EXISTS subsidy_expires_at TIMESTAMP WITH TIME ZONE"),
            ]
            for name, sql in sql_migrations:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"  ✅ {name}")
                except Exception as e:
                    conn.rollback()
                    print(f"  ⚠️  {name}: {e}")
            
            print("✅ Schema migrations complete")
    except Exception as e:
        print(f"⚠️  Schema migration error: {e}")
    
    # Then run alembic
    try:
        result = subprocess.run([
            sys.executable, '-m', 'alembic', 'upgrade', 'head'
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Alembic migrations completed!")
        else:
            print(f"⚠️  Alembic migration skipped: {result.stderr[:200]}")
    except Exception as e:
        print(f"⚠️  Alembic error (non-fatal): {e}")
    
    return True

def seed_basic_data():
    """Seed basic data if needed"""
    print("🌱 Checking if seeding is needed...")
    try:
        from sqlalchemy import create_engine, text
        from config import settings
        
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            # Check if data already exists
            result = conn.execute(text("SELECT COUNT(*) FROM utility_providers"))
            count = result.scalar()
            
            if count > 0:
                print(f"✅ Data already exists ({count} utility providers found)")
                return True
            
            print("Adding basic seed data...")
            # Add basic utility providers
            providers_sql = """
            INSERT INTO utility_providers (
                provider_name, provider_code, country_code, state_province, 
                service_areas, is_active, created_at
            ) VALUES 
            ('Eko Electricity Distribution Company', 'EKEDC', 'NG', 'Lagos', ARRAY['Lagos Island', 'Victoria Island'], true, NOW()),
            ('Pacific Gas & Electric', 'PGE', 'US', 'California', ARRAY['San Francisco', 'Oakland'], true, NOW());
            """
            conn.execute(text(providers_sql))
            conn.commit()
            print("✅ Basic data seeded successfully!")
            return True
            
    except Exception as e:
        print(f"⚠️  Seeding failed (will continue): {e}")
        return False

# Get the port from environment variable, default to 8000
port = os.environ.get('PORT', '8000')
print(f"PORT environment variable: {os.environ.get('PORT', 'Not set')}")
print(f"Starting server on port {port}")

# Run migrations first
if not run_migrations():
    print("⚠️  Migrations failed, but continuing to start server...")

# Try to seed data
seed_basic_data()

# Start uvicorn with the correct port
cmd = [
    'uvicorn', 
    'app.core.app:app', 
    '--host', '0.0.0.0', 
    '--port', port
]

print(f"Running command: {' '.join(cmd)}")
subprocess.run(cmd)