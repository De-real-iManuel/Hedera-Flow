"""
Manual test script for Redis cache structure
Run this to verify Redis client implementation
"""
import sys
from datetime import datetime
from app.utils.redis_client import RedisClient


def test_redis_connection():
    """Test Redis connection"""
    print("Testing Redis connection...")
    client = RedisClient()
    
    if client.ping():
        print("✓ Redis connection successful")
        return True
    else:
        print("✗ Redis connection failed")
        return False


def test_session_cache():
    """Test session cache operations"""
    print("\nTesting Session Cache...")
    client = RedisClient()
    
    user_id = "test-user-123"
    session_data = {
        "userId": user_id,
        "email": "test@example.com",
        "countryCode": "ES",
        "hederaAccountId": "0.0.12345",
        "lastActivity": datetime.utcnow().isoformat()
    }
    
    # Set session
    if client.set_session(user_id, session_data):
        print("✓ Session set successfully")
    else:
        print("✗ Failed to set session")
        return False
    
    # Get session
    retrieved = client.get_session(user_id)
    if retrieved and retrieved["userId"] == user_id:
        print(f"✓ Session retrieved: {retrieved['email']}")
    else:
        print("✗ Failed to retrieve session")
        return False
    
    # Update activity
    if client.update_session_activity(user_id):
        print("✓ Session activity updated")
    else:
        print("✗ Failed to update session activity")
    
    # Delete session
    if client.delete_session(user_id):
        print("✓ Session deleted successfully")
    else:
        print("✗ Failed to delete session")
    
    return True


def test_exchange_rate_cache():
    """Test exchange rate cache operations"""
    print("\nTesting Exchange Rate Cache...")
    client = RedisClient()
    
    currency = "EUR"
    rate_data = {
        "currency": currency,
        "hbarPrice": 0.34,
        "source": "coingecko",
        "fetchedAt": datetime.utcnow().isoformat()
    }
    
    # Set rate
    if client.set_exchange_rate(currency, rate_data):
        print("✓ Exchange rate set successfully")
    else:
        print("✗ Failed to set exchange rate")
        return False
    
    # Get rate
    retrieved = client.get_exchange_rate(currency)
    if retrieved and retrieved["hbarPrice"] == 0.34:
        print(f"✓ Exchange rate retrieved: {retrieved['hbarPrice']} {currency}/HBAR")
    else:
        print("✗ Failed to retrieve exchange rate")
        return False
    
    # Test case insensitivity
    retrieved_lower = client.get_exchange_rate("eur")
    if retrieved_lower and retrieved_lower["hbarPrice"] == 0.34:
        print("✓ Case-insensitive retrieval works")
    else:
        print("✗ Case-insensitive retrieval failed")
    
    # Delete rate
    if client.delete_exchange_rate(currency):
        print("✓ Exchange rate deleted successfully")
    else:
        print("✗ Failed to delete exchange rate")
    
    return True


def test_tariff_cache():
    """Test tariff cache operations"""
    print("\nTesting Tariff Cache...")
    client = RedisClient()
    
    country_code = "ES"
    utility_provider = "Iberdrola"
    tariff_data = {
        "tariffId": "tariff-123",
        "rateStructure": {
            "type": "time_of_use",
            "periods": [
                {"name": "peak", "price": 0.40},
                {"name": "off_peak", "price": 0.15}
            ]
        },
        "taxesAndFees": {
            "vat": 0.21,
            "distribution_charge": 0.045
        },
        "validFrom": "2024-01-01"
    }
    
    # Set tariff
    if client.set_tariff(country_code, utility_provider, tariff_data):
        print("✓ Tariff set successfully")
    else:
        print("✗ Failed to set tariff")
        return False
    
    # Get tariff
    retrieved = client.get_tariff(country_code, utility_provider)
    if retrieved and retrieved["tariffId"] == "tariff-123":
        print(f"✓ Tariff retrieved: {retrieved['rateStructure']['type']}")
    else:
        print("✗ Failed to retrieve tariff")
        return False
    
    # Test case insensitivity
    retrieved_lower = client.get_tariff("es", utility_provider)
    if retrieved_lower and retrieved_lower["tariffId"] == "tariff-123":
        print("✓ Case-insensitive retrieval works")
    else:
        print("✗ Case-insensitive retrieval failed")
    
    # Delete tariff
    if client.delete_tariff(country_code, utility_provider):
        print("✓ Tariff deleted successfully")
    else:
        print("✗ Failed to delete tariff")
    
    return True


def test_rate_limiting():
    """Test rate limiting operations"""
    print("\nTesting Rate Limiting...")
    client = RedisClient()
    
    ip_address = "192.168.1.100"
    
    # Increment counter
    count1 = client.increment_rate_limit(ip_address)
    if count1 == 1:
        print(f"✓ First request counted: {count1}")
    else:
        print(f"✗ Unexpected count: {count1}")
        return False
    
    count2 = client.increment_rate_limit(ip_address)
    if count2 == 2:
        print(f"✓ Second request counted: {count2}")
    else:
        print(f"✗ Unexpected count: {count2}")
        return False
    
    # Get count
    current_count = client.get_rate_limit(ip_address)
    if current_count == 2:
        print(f"✓ Current count retrieved: {current_count}")
    else:
        print(f"✗ Unexpected count: {current_count}")
    
    # Reset
    if client.reset_rate_limit(ip_address):
        print("✓ Rate limit reset successfully")
    else:
        print("✗ Failed to reset rate limit")
    
    # Verify reset
    reset_count = client.get_rate_limit(ip_address)
    if reset_count == 0:
        print(f"✓ Count after reset: {reset_count}")
    else:
        print(f"✗ Count not reset: {reset_count}")
    
    return True


def test_utility_methods():
    """Test utility methods"""
    print("\nTesting Utility Methods...")
    client = RedisClient()
    
    # Set some test data
    client.set_session("user-1", {"userId": "user-1"})
    client.set_session("user-2", {"userId": "user-2"})
    
    # Get keys by pattern
    keys = client.get_keys_by_pattern("session:*")
    if len(keys) >= 2:
        print(f"✓ Found {len(keys)} session keys")
    else:
        print(f"✗ Expected at least 2 keys, found {len(keys)}")
    
    # Get TTL
    ttl = client.get_ttl("session:user-1")
    if ttl > 0:
        print(f"✓ TTL retrieved: {ttl} seconds (~{ttl/86400:.1f} days)")
    else:
        print(f"✗ Invalid TTL: {ttl}")
    
    # Cleanup
    client.delete_session("user-1")
    client.delete_session("user-2")
    
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Redis Cache Structure Test Suite")
    print("=" * 60)
    
    tests = [
        ("Connection", test_redis_connection),
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
            print(f"\n✗ {name} failed with error: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
