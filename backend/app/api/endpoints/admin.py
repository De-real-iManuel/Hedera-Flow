"""
Admin endpoints for database management
"""
import subprocess
import sys
from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, text
from config import settings

router = APIRouter()

@router.post("/migrate")
async def run_migrations():
    """Run database migrations"""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'alembic', 'upgrade', 'head'
        ], capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": "Migrations completed successfully",
                "output": result.stdout
            }
        else:
            return {
                "success": False,
                "message": "Migration failed",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running migrations: {str(e)}")

@router.post("/seed")
async def seed_database():
    """Seed database with basic data"""
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Check if data already exists
            result = conn.execute(text("SELECT COUNT(*) FROM utility_providers"))
            count = result.scalar()
            
            if count > 0:
                return {
                    "success": True,
                    "message": f"Data already exists ({count} utility providers found)",
                    "seeded": False
                }
            
            # Add basic utility providers
            providers_sql = """
            INSERT INTO utility_providers (
                provider_name, provider_code, country_code, state_province, 
                service_areas, is_active, created_at
            ) VALUES 
            ('Eko Electricity Distribution Company', 'EKEDC', 'NG', 'Lagos', ARRAY['Lagos Island', 'Victoria Island'], true, NOW()),
            ('Pacific Gas & Electric', 'PGE', 'US', 'California', ARRAY['San Francisco', 'Oakland'], true, NOW()),
            ('Iberdrola', 'IBE', 'ES', 'Madrid', ARRAY['Madrid', 'Toledo'], true, NOW());
            """
            conn.execute(text(providers_sql))
            
            # Add basic tariffs
            tariffs_sql = """
            INSERT INTO tariffs (
                country_code, region, utility_provider, currency,
                rate_structure, taxes_and_fees, subsidies,
                valid_from, valid_until, is_active,
                created_at, updated_at
            ) VALUES 
            (
                'NG', 'Lagos', 'EKEDC', 'NGN',
                '{"type": "band_based", "bands": [{"name": "A", "hours_min": 20, "price": 225.00}]}',
                '{"vat": 7.5}',
                '{}',
                '2024-01-01', '2024-12-31', true,
                NOW(), NOW()
            ),
            (
                'US', 'California', 'PG&E', 'USD',
                '{"type": "tiered", "tiers": [{"threshold": 300, "price": 0.25}]}',
                '{"delivery_charge": 0.05}',
                '{}',
                '2024-01-01', '2024-12-31', true,
                NOW(), NOW()
            );
            """
            conn.execute(text(tariffs_sql))
            conn.commit()
            
            return {
                "success": True,
                "message": "Database seeded successfully",
                "seeded": True
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error seeding database: {str(e)}")

@router.get("/status")
async def database_status():
    """Check database status"""
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Check if tables exist
            tables_result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in tables_result]
            
            # Count records in main tables
            counts = {}
            for table in ['users', 'utility_providers', 'tariffs', 'meters', 'bills']:
                if table in tables:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        counts[table] = result.scalar()
                    except:
                        counts[table] = "error"
                else:
                    counts[table] = "table not found"
            
            return {
                "success": True,
                "tables": tables,
                "record_counts": counts
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking database status: {str(e)}")