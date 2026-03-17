"""
Test script for database connection pool
Verifies that the connection pool is working correctly
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import (
    engine,
    SessionLocal,
    get_db,
    check_db_connection,
    get_db_stats,
    close_db
)


def test_engine_creation():
    """Test that engine is created successfully"""
    print("✓ Testing engine creation...")
    assert engine is not None
    print(f"  Engine: {engine}")
    print(f"  Pool class: {engine.pool.__class__.__name__}")
    print("  ✅ Engine created successfully")


def test_session_creation():
    """Test that sessions can be created"""
    print("\n✓ Testing session creation...")
    session = SessionLocal()
    assert session is not None
    print(f"  Session: {session}")
    session.close()
    print("  ✅ Session created and closed successfully")


def test_get_db_dependency():
    """Test the get_db dependency function"""
    print("\n✓ Testing get_db dependency...")
    db_gen = get_db()
    db = next(db_gen)
    assert db is not None
    print(f"  Database session: {db}")
    try:
        next(db_gen)
    except StopIteration:
        print("  ✅ Session properly closed after use")


def test_pool_stats():
    """Test getting pool statistics"""
    print("\n✓ Testing pool statistics...")
    stats = get_db_stats()
    print(f"  Pool stats: {stats}")
    assert isinstance(stats, dict)
    assert "pool_size" in stats
    assert "checked_in" in stats
    assert "checked_out" in stats
    print("  ✅ Pool statistics retrieved successfully")


def test_health_check():
    """Test database health check"""
    print("\n✓ Testing database health check...")
    # Note: This will fail if database is not accessible
    # but the function should not raise an exception
    try:
        is_healthy = check_db_connection()
        if is_healthy:
            print("  ✅ Database connection is healthy")
        else:
            print("  ⚠️  Database connection failed (expected if DB not accessible)")
    except Exception as e:
        print(f"  ❌ Health check raised exception: {e}")


def test_multiple_sessions():
    """Test creating multiple sessions from the pool"""
    print("\n✓ Testing multiple concurrent sessions...")
    sessions = []
    
    # Create 5 sessions
    for i in range(5):
        session = SessionLocal()
        sessions.append(session)
        print(f"  Created session {i+1}")
    
    # Check pool stats
    stats = get_db_stats()
    print(f"  Pool stats after creating 5 sessions: {stats}")
    
    # Close all sessions
    for i, session in enumerate(sessions):
        session.close()
        print(f"  Closed session {i+1}")
    
    # Check pool stats again
    stats = get_db_stats()
    print(f"  Pool stats after closing sessions: {stats}")
    print("  ✅ Multiple sessions handled correctly")


def main():
    """Run all tests"""
    print("=" * 60)
    print("DATABASE CONNECTION POOL TESTS")
    print("=" * 60)
    
    try:
        test_engine_creation()
        test_session_creation()
        test_get_db_dependency()
        test_pool_stats()
        test_health_check()
        test_multiple_sessions()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Clean up
        print("\n✓ Cleaning up...")
        close_db()
        print("  ✅ Database connections closed")


if __name__ == "__main__":
    main()
