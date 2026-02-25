#!/usr/bin/env python3
"""
Test script to verify migration system is working correctly

This script:
1. Checks if Alembic is properly configured
2. Verifies database connection
3. Tests migration commands
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from config import settings


def test_alembic_config():
    """Test if Alembic configuration is valid"""
    print("1. Testing Alembic configuration...")
    
    backend_dir = Path(__file__).resolve().parent.parent
    alembic_ini = backend_dir / "alembic.ini"
    
    if not alembic_ini.exists():
        print("   ✗ alembic.ini not found")
        return False
    
    try:
        config = Config(str(alembic_ini))
        config.set_main_option("script_location", str(backend_dir / "migrations"))
        print("   ✓ Alembic configuration valid")
        return True
    except Exception as e:
        print(f"   ✗ Error loading Alembic config: {e}")
        return False


def test_database_connection():
    """Test database connection"""
    print("\n2. Testing database connection...")
    
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("   ✓ Database connection successful")
        return True
    except Exception as e:
        print(f"   ✗ Database connection failed: {e}")
        return False


def test_migration_files():
    """Test if migration files exist and are valid"""
    print("\n3. Testing migration files...")
    
    backend_dir = Path(__file__).resolve().parent.parent
    migrations_dir = backend_dir / "migrations"
    versions_dir = migrations_dir / "versions"
    
    # Check directories exist
    if not migrations_dir.exists():
        print("   ✗ migrations/ directory not found")
        return False
    
    if not versions_dir.exists():
        print("   ✗ migrations/versions/ directory not found")
        return False
    
    # Check required files
    required_files = [
        migrations_dir / "env.py",
        migrations_dir / "script.py.mako"
    ]
    
    for file in required_files:
        if not file.exists():
            print(f"   ✗ Required file not found: {file.name}")
            return False
    
    # Check for migration files
    migration_files = list(versions_dir.glob("*.py"))
    migration_files = [f for f in migration_files if f.name != "__pycache__" and f.name != ".gitkeep"]
    
    if not migration_files:
        print("   ⚠ No migration files found in versions/")
        print("   ℹ This is OK for a fresh setup")
    else:
        print(f"   ✓ Found {len(migration_files)} migration file(s)")
        for mf in migration_files:
            print(f"     - {mf.name}")
    
    print("   ✓ Migration structure valid")
    return True


def test_migration_history():
    """Test if we can read migration history"""
    print("\n4. Testing migration history...")
    
    try:
        backend_dir = Path(__file__).resolve().parent.parent
        alembic_ini = backend_dir / "alembic.ini"
        
        config = Config(str(alembic_ini))
        config.set_main_option("script_location", str(backend_dir / "migrations"))
        
        script = ScriptDirectory.from_config(config)
        revisions = list(script.walk_revisions())
        
        if not revisions:
            print("   ⚠ No migrations in history")
            print("   ℹ This is OK for a fresh setup")
        else:
            print(f"   ✓ Found {len(revisions)} migration(s) in history")
            for rev in revisions:
                print(f"     - {rev.revision}: {rev.doc}")
        
        return True
    except Exception as e:
        print(f"   ✗ Error reading migration history: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Hedera Flow - Migration System Test")
    print("=" * 60)
    
    tests = [
        test_alembic_config,
        test_database_connection,
        test_migration_files,
        test_migration_history
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ✗ Unexpected error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All tests passed ({passed}/{total})")
        print("\nMigration system is ready to use!")
        print("\nNext steps:")
        print("  1. Run migrations: python scripts/migrate.py upgrade head")
        print("  2. Check status: python scripts/migrate.py current")
        return 0
    else:
        print(f"✗ Some tests failed ({passed}/{total} passed)")
        print("\nPlease fix the issues above before using migrations.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
