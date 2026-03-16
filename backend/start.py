#!/usr/bin/env python3
import os
import subprocess
import sys

def run_migrations():
    """Run database migrations on startup"""
    print("🚀 Running database migrations...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'alembic', 'upgrade', 'head'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully!")
            return True
        else:
            print("❌ Migration failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

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