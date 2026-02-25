#!/usr/bin/env python3
"""
Validate migration setup without requiring Alembic to be installed

This script checks:
1. Migration directory structure
2. Configuration files
3. Migration files
"""
import sys
from pathlib import Path


def check_directory_structure():
    """Check if migration directories exist"""
    print("1. Checking directory structure...")
    
    backend_dir = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        backend_dir / "migrations",
        backend_dir / "migrations" / "versions",
        backend_dir / "scripts"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"   ✓ {dir_path.relative_to(backend_dir)}")
        else:
            print(f"   ✗ {dir_path.relative_to(backend_dir)} - NOT FOUND")
            all_exist = False
    
    return all_exist


def check_configuration_files():
    """Check if configuration files exist"""
    print("\n2. Checking configuration files...")
    
    backend_dir = Path(__file__).resolve().parent.parent
    
    required_files = [
        backend_dir / "alembic.ini",
        backend_dir / "migrations" / "env.py",
        backend_dir / "migrations" / "script.py.mako"
    ]
    
    all_exist = True
    for file_path in required_files:
        if file_path.exists():
            print(f"   ✓ {file_path.relative_to(backend_dir)}")
        else:
            print(f"   ✗ {file_path.relative_to(backend_dir)} - NOT FOUND")
            all_exist = False
    
    return all_exist


def check_migration_files():
    """Check migration files"""
    print("\n3. Checking migration files...")
    
    backend_dir = Path(__file__).resolve().parent.parent
    versions_dir = backend_dir / "migrations" / "versions"
    
    if not versions_dir.exists():
        print("   ✗ versions/ directory not found")
        return False
    
    migration_files = list(versions_dir.glob("*.py"))
    migration_files = [f for f in migration_files if f.name not in ["__pycache__", "__init__.py"]]
    
    if not migration_files:
        print("   ⚠ No migration files found")
        print("   ℹ This is OK - migrations will be created as needed")
    else:
        print(f"   ✓ Found {len(migration_files)} migration file(s):")
        for mf in migration_files:
            print(f"     - {mf.name}")
    
    return True


def check_documentation():
    """Check if documentation exists"""
    print("\n4. Checking documentation...")
    
    backend_dir = Path(__file__).resolve().parent.parent
    
    doc_files = [
        backend_dir / "MIGRATIONS.md",
        backend_dir / "MIGRATION_QUICK_REFERENCE.md"
    ]
    
    all_exist = True
    for file_path in doc_files:
        if file_path.exists():
            print(f"   ✓ {file_path.relative_to(backend_dir)}")
        else:
            print(f"   ⚠ {file_path.relative_to(backend_dir)} - NOT FOUND")
            all_exist = False
    
    return all_exist


def check_requirements():
    """Check if Alembic is in requirements.txt"""
    print("\n5. Checking requirements.txt...")
    
    backend_dir = Path(__file__).resolve().parent.parent
    requirements_file = backend_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print("   ✗ requirements.txt not found")
        return False
    
    content = requirements_file.read_text()
    
    if "alembic" in content.lower():
        print("   ✓ Alembic found in requirements.txt")
        return True
    else:
        print("   ✗ Alembic NOT found in requirements.txt")
        return False


def main():
    """Run all validation checks"""
    print("=" * 60)
    print("Migration Setup Validation")
    print("=" * 60)
    print()
    
    checks = [
        check_directory_structure,
        check_configuration_files,
        check_migration_files,
        check_documentation,
        check_requirements
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"   ✗ Unexpected error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Validation Results")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All checks passed ({passed}/{total})")
        print("\nMigration system is properly set up!")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Test migrations: python scripts/test_migrations.py")
        print("  3. Run migrations: python scripts/migrate.py upgrade head")
        print("\nSee MIGRATIONS.md for complete guide.")
        return 0
    else:
        print(f"⚠ Some checks failed ({passed}/{total} passed)")
        print("\nPlease review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
