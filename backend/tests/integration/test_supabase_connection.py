"""
Test script to verify Supabase database connection
Run this after setting up your Supabase project
"""
import sys
import psycopg2
from psycopg2 import OperationalError
from config import settings


def test_database_connection():
    """Test PostgreSQL connection to Supabase"""
    print("Testing Supabase PostgreSQL connection...")
    print(f"   Host: {settings.database_url.split('@')[1].split('/')[0] if '@' in settings.database_url else 'localhost'}")
    
    try:
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"[OK] Connected to PostgreSQL")
        print(f"   Version: {version[0][:50]}...")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"[OK] Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("[WARN] No tables found. Run init.sql to create schema.")
        
        # Check database size
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
        size = cursor.fetchone()
        print(f"Database size: {size[0]}")
        
        # Check active connections
        cursor.execute("SELECT count(*) FROM pg_stat_activity;")
        connections = cursor.fetchone()
        print(f"Active connections: {connections[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n[OK] Supabase PostgreSQL connection test PASSED")
        return True
        
    except OperationalError as e:
        print(f"\n[FAIL] Connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("   1. Check DATABASE_URL in .env file")
        print("   2. Verify Supabase project is running")
        print("   3. Check your internet connection")
        print("   4. Ensure password is correct")
        return False
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        return False


def test_redis_connection():
    """Test Redis connection (Upstash)"""
    print("\nTesting Redis connection...")
    
    try:
        import redis
        
        # Parse Redis URL
        r = redis.from_url(settings.redis_url, decode_responses=True)
        
        # Test ping
        r.ping()
        print("[OK] Connected to Redis")
        
        # Test set/get
        r.set("test_key", "test_value", ex=10)
        value = r.get("test_key")
        
        if value == "test_value":
            print("[OK] Redis read/write test PASSED")
        else:
            print("[WARN] Redis read/write test FAILED")
        
        # Clean up
        r.delete("test_key")
        
        # Get info
        info = r.info()
        print(f"Redis version: {info.get('redis_version', 'unknown')}")
        print(f"Connected clients: {info.get('connected_clients', 0)}")
        
        print("\n[OK] Redis connection test PASSED")
        return True
        
    except ImportError:
        print("[WARN] Redis library not installed. Run: pip install redis")
        return False
    except Exception as e:
        print(f"[FAIL] Redis connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("   1. Check REDIS_URL in .env file")
        print("   2. Verify Upstash Redis is configured")
        print("   3. Check if Redis password is correct")
        return False


def main():
    """Run all connection tests"""
    print("=" * 60)
    print("Hedera Flow - Supabase Connection Test")
    print("=" * 60)
    
    db_success = test_database_connection()
    redis_success = test_redis_connection()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"PostgreSQL: {'[PASS]' if db_success else '[FAIL]'}")
    print(f"Redis:      {'[PASS]' if redis_success else '[FAIL]'}")
    print("=" * 60)
    
    if db_success and redis_success:
        print("\nAll tests passed! Supabase setup is complete.")
        sys.exit(0)
    else:
        print("\nSome tests failed. Please check the configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
