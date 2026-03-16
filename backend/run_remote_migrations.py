#!/usr/bin/env python3
"""
Run Alembic migrations on Railway database
"""
import os
import subprocess
import sys

def run_remote_migrations():
    """Run migrations on Railway database"""
    print("🚀 Running migrations on Railway database...")
    
    # Set the database URL to Railway's PostgreSQL
    railway_db_url = "postgresql://postgres:IZbQWHVADRGAUImDKSJVYwQAKORTDums@postgres.railway.internal:5432/railway"
    
    # Set environment variable for Alembic
    env = os.environ.copy()
    env['DATABASE_URL'] = railway_db_url
    
    try:
        # Run Alembic upgrade
        result = subprocess.run(
            [sys.executable, '-m', 'alembic', 'upgrade', 'head'],
            env=env,
            capture_output=True,
            text=True,
            cwd='.'
        )
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully!")
            print(result.stdout)
            return True
        else:
            print("❌ Migration failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

if __name__ == "__main__":
    success = run_remote_migrations()
    sys.exit(0 if success else 1)