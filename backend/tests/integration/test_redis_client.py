"""
Test script for Redis client setup
Tests all Redis client functionality including sessions, exchange rates, tariffs, and rate limiting
"""
import sys
from datetime import datetime, timezone
from app.utils.redis_client import redis_client


def test_connection():
    """Test Redis connection"""
    print("\n=== Testing Redis Connection ===")
    try:
        result = redis_client.ping()
        if result:
            print("✓ Redis connection successful")
            return True
        else:
            print("✗ Redis connection failed")
            return False
    except Exception as e:
        print(f"✗ Redis connection error: {e}")
        return False


def test_session_cache():
    """Test session cache operations"""
    print("\n=== Testing Session Cache ===")
    
    # Test data
    user_id = "test-user-123"
    session_data = {
        "userId": user_id,
        "email": "test@example.com",
        "countryCode": "ES",
        "hederaAccountId": "0.0.123456",
        "lastActivity": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        # Set session
        result = redis_client.set_session(user_id, session_data)
        if result:
            print("✓ Session set successfully")
        else:
            print("✗ Failed to set session")
            return False
        
        # Get session
        retrieved = redis_client.get_session(user_id)
        if retrieved and retrieved["email"] == session_data["email"]:
            print("✓ Session retrieved successfully")
        else:
            print("✗ Failed to retrieve session")
            return False
        
        # Update activity
        result = redis_client.update_session_activity(user_id)
        if result:
            print("✓ Session activity updated")
        else:
            print("✗ Failed to update session activity")
            return False
        
        # Check TTL
        ttl = redis_client.get_ttl(f"session:{user_id}")
        if ttl > 0:
            print(f"✓ Session TTL: {ttl} seconds (~{ttl/86400:.1f} days)")
        else:
            print("✗ Session TTL not set correctly")
            return False
        
        # Delete session
        result = redis_client.delete_session(user_id)
        if result:
            print("✓ Session deleted successfully")
        else:
            print("✗ Failed to delete session")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Session cache error: {e}")
        return False


def test_exchange_rate_cache():
    """Test exchange rate cache operations"""
    print("\n=== Testing Exchange Rate Cache ===")
    
    # Test data
    currency = "EUR"
    rate_data = {
        "currency": currency,
        "hbarPrice": 0.34,
        "source": "coingecko",
        "fetchedAt": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        # Set exchange rate
        result = redis_client.set_exchange_rate(currency, rate_data)
        if result:
            print("✓ Exchange rate set successfully")
        else:
            print("✗ Failed to set exchange rate")
            return False
        
        # Get exchange rate
        retrieved = redis_client.get_exchange_rate(currency)
        if retrieved and retrieved["hbarPrice"] == rate_data["hbarPrice"]:
            print("✓ Exchange rate retrieved successfully")
        else:
            print("✗ Failed to retrieve exchange rate")
            return False
        
        # Check TTL
        ttl = redis_client.get_ttl(f"exchange_rate:{currency}")
        if ttl > 0:
            print(f"✓ Exchange rate TTL: {ttl} seconds (~{ttl/60:.1f} minutes)")
        else:
            print("✗ Exchange rate TTL not set correctly")
            return False
        
        # Delete exchange rate
        result = redis_client.delete_exchange_rate(currency)
        if result:
            print("✓ Exchange rate deleted successfully")
        else:
            print("✗ Failed to delete exchange rate")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Exchange rate cache error: {e}")
        return False


def test_tariff_cache():
    """Test tariff cache operations"""
    print("\n=== Testing Tariff Cache ===")
    
    # Test data
    country_code = "ES"
    utility_provider = "Iberdrola"
    tariff_data = {
        "tariffId": "tariff-123",
        "rateStructure": {
            "type": "time_of_use",
            "periods": [
                {"name": "peak", "price": 0.40},
                {"name": "standard", "price": 0.25},
                {"name": "off_peak", "price": 0.15}
            ]
        },
        "taxesAndFees": {
            "vat": 0.21,
            "distribution_charge": 0.045
        },
        "validFrom": "2024-01-01"
    }
    
    try:
        # Set tariff
        result = redis_client.set_tariff(country_code, utility_provider, tariff_data)
        if result:
            print("✓ Tariff set successfully")
        else:
            print("✗ Failed to set tariff")
            return False
        
        # Get tariff
        retrieved = redis_client.get_tariff(country_code, utility_provider)
        if retrieved and retrieved["tariffId"] == tariff_data["tariffId"]:
            print("✓ Tariff retrieved successfully")
        else:
            print("✗ Failed to retrieve tariff")
            return False
        
        # Check TTL
        ttl = redis_client.get_ttl(f"tariff:{country_code}:{utility_provider}")
        if ttl > 0:
            print(f"✓ Tariff TTL: {ttl} seconds (~{ttl/3600:.1f} hours)")
        else:
            print("✗ Tariff TTL not set correctly")
            return False
        
        # Delete tariff
        result = redis_client.delete_tariff(country_code, utility_provider)
        if result:
            print("✓ Tariff deleted successfully")
        else:
            print("✗ Failed to delete tariff")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Tariff cache error: {e}")
        return False


def test_rate_limiting():
    """Test rate limiting operations"""
    print("\n=== Testing Rate Limiting ===")
    
    # Test data
    ip_address = "192.168.1.100"
    
    try:
        # Reset first
        redis_client.reset_rate_limit(ip_address)
        
        # Increment rate limit
        count1 = redis_client.increment_rate_limit(ip_address)
        if count1 == 1:
            print("✓ Rate limit incremented (count: 1)")
        else:
            print(f"✗ Rate limit increment failed (expected 1, got {count1})")
            return False
        
        # Increment again
        count2 = redis_client.increment_rate_limit(ip_address)
        if count2 == 2:
            print("✓ Rate limit incremented (count: 2)")
        else:
            print(f"✗ Rate limit increment failed (expected 2, got {count2})")
            return False
        
        # Get rate limit
        count = redis_client.get_rate_limit(ip_address)
        if count == 2:
            print("✓ Rate limit retrieved successfully")
        else:
            print(f"✗ Failed to retrieve rate limit (expected 2, got {count})")
            return False
        
        # Check TTL
        ttl = redis_client.get_ttl(f"rate_limit:{ip_address}")
        if ttl > 0:
            print(f"✓ Rate limit TTL: {ttl} seconds")
        else:
            print("✗ Rate limit TTL not set correctly")
            return False
        
        # Reset rate limit
        result = redis_client.reset_rate_limit(ip_address)
        if result:
            print("✓ Rate limit reset successfully")
        else:
            print("✗ Failed to reset rate limit")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Rate limiting error: {e}")
        return False


def test_utility_methods():
    """Test utility methods"""
    print("\n=== Testing Utility Methods ===")
    
    try:
        # Set some test keys
        redis_client.set_session("test-user-1", {"test": "data1"})
        redis_client.set_session("test-user-2", {"test": "data2"})
        
        # Get keys by pattern
        keys = redis_client.get_keys_by_pattern("session:test-*")
        if len(keys) >= 2:
            print(f"✓ Found {len(keys)} keys matching pattern")
        else:
            print(f"✗ Expected at least 2 keys, found {len(keys)}")
            return False
        
        # Clean up test keys
        redis_client.delete_session("test-user-1")
        redis_client.delete_session("test-user-2")
        print("✓ Utility methods working correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Utility methods error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("REDIS CLIENT TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Connection", test_connection),
        ("Session Cache", test_session_cache),
        ("Exchange Rate Cache", test_exchange_rate_cache),
        ("Tariff Cache", test_tariff_cache),
        ("Rate Limiting", test_rate_limiting),
        ("Utility Methods", test_utility_methods),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Redis client is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
