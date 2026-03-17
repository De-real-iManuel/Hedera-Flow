"""Test if we can import the main app"""
import sys
sys.path.insert(0, '.')

print("Step 1: Importing pytest...")
import pytest
print("[OK] pytest imported")

print("\nStep 2: Importing SQLAlchemy...")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
print("[OK] SQLAlchemy imported")

print("\nStep 3: Importing app components...")
try:
    from app.core.database import Base, get_db
    print("[OK] Database imported")
except Exception as e:
    print(f"[FAIL] Database import failed: {e}")

try:
    from app.models.user import User, CountryCodeEnum
    print("[OK] User model imported")
except Exception as e:
    print(f"[FAIL] User model import failed: {e}")

try:
    from app.models.meter import Meter, MeterTypeEnum
    print("[OK] Meter model imported")
except Exception as e:
    print(f"[FAIL] Meter model import failed: {e}")

try:
    from app.models.utility_provider import UtilityProvider
    print("[OK] Utility provider model imported")
except Exception as e:
    print(f"[FAIL] Utility provider model import failed: {e}")

try:
    from app.utils.auth import hash_password, create_access_token
    print("[OK] Auth utils imported")
except Exception as e:
    print(f"[FAIL] Auth utils import failed: {e}")

print("\nStep 4: Importing main app...")
try:
    from main import app
    print("[OK] Main app imported")
except Exception as e:
    print(f"[FAIL] Main app import failed: {e}")
    import traceback
    traceback.print_exc()

print("\nAll imports successful!")
