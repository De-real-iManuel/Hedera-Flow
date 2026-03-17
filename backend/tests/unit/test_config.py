"""
Test config loading
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

print("Testing configuration loading...\n")

# Load config
from config import settings

print(f"DATABASE_URL: {settings.database_url}")
print(f"REDIS_URL: {settings.redis_url}")
print(f"Environment: {settings.environment}")

# Test database connection
print("\nTesting database connection...")
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("[OK] Database connection successful!")
except Exception as e:
    print(f"[FAIL] Database connection failed: {e}")
