"""
Manual test for ExchangeRateService with real API calls

This script tests the ExchangeRateService with actual CoinGecko API calls.
Run this manually to verify the integration works.

Usage:
    python test_exchange_rate_manual.py
"""
import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.exchange_rate_service import ExchangeRateService, SUPPORTED_CURRENCIES
from app.utils.redis_client import redis_client


def test_redis_connection():
    """Test Redis connection"""
    print("\n=== Testing Redis Connection ===")
    try:
        if redis_client.ping():
            print("✓ Redis connection successful")
            return True
        else:
            print("✗ Redis connection failed")
            return False
    except Exception as e:
        print(f"✗ Redis error: {e}")
        return False


def test_fetch_all_currencies(db: Session):
    """Test fetching HBAR prices for all supported currencies"""
    print("\n=== Testing HBAR Price Fetching ===")
    service = ExchangeRateService(db)
    
    results = {}
    for currency in SUPPORTED_CURRENCIES:
        try:
            print(f"\nFetching {currency}...")
            price = service.get_hbar_price(currency, use_cache=False)
            results[currency] = price
            print(f"✓ {currency}: {price}")
        except Exception as e:
            print(f"✗ {currency}: {e}")
            results[currency] = None
    
    return results


def test_cache_functionality(db: Session):
    """Test Redis caching"""
    print("\n=== Testing Cache Functionality ===")
    service = ExchangeRateService(db)
    
    currency = 'USD'
    
    # First call (should fetch from API)
    print(f"\n1. First call (cache miss)...")
    price1 = service.get_hbar_price(currency, use_cache=True)
    print(f"   Price: {price1}")
    
    # Second call (should hit cache)
    print(f"\n2. Second call (cache hit)...")
    price2 = service.get_hbar_price(currency, use_cache=True)
    print(f"   Price: {price2}")
    
    if price1 == price2:
        print("✓ Cache working correctly (same price)")
    else:
        print("⚠ Prices differ (might be API rate change)")
    
    # Check cached data
    cached = service.get_cached_rate(currency)
    if cached:
        print(f"✓ Cached data found: {cached}")
    else:
        print("✗ No cached data found")
    
    # Invalidate cache
    print(f"\n3. Invalidating cache...")
    service.invalidate_cache(currency)
    
    # Third call (should fetch from API again)
    print(f"\n4. Third call (cache miss after invalidation)...")
    price3 = service.get_hbar_price(currency, use_cache=True)
    print(f"   Price: {price3}")


def test_database_storage(db: Session):
    """Test database storage"""
    print("\n=== Testing Database Storage ===")
    service = ExchangeRateService(db)
    
    currency = 'EUR'
    
    # Fetch and store
    print(f"\nFetching {currency} and storing in DB...")
    price = service.get_hbar_price(currency, use_cache=False)
    print(f"✓ Fetched and stored: {price}")
    
    # Retrieve from DB
    print(f"\nRetrieving latest rate from DB...")
    latest = service.get_latest_rate_from_db(currency)
    if latest:
        print(f"✓ Latest rate from DB:")
        print(f"   Currency: {latest['currency']}")
        print(f"   Price: {latest['hbarPrice']}")
        print(f"   Source: {latest['source']}")
        print(f"   Fetched at: {latest['fetchedAt']}")
    else:
        print("✗ No rate found in DB")


def test_error_handling(db: Session):
    """Test error handling"""
    print("\n=== Testing Error Handling ===")
    service = ExchangeRateService(db)
    
    # Test unsupported currency
    print("\n1. Testing unsupported currency (GBP)...")
    try:
        service.get_hbar_price('GBP')
        print("✗ Should have raised error")
    except Exception as e:
        print(f"✓ Correctly raised error: {e}")
    
    # Test case insensitivity
    print("\n2. Testing case insensitivity (lowercase 'usd')...")
    try:
        price = service.get_hbar_price('usd', use_cache=False)
        print(f"✓ Lowercase works: {price}")
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("ExchangeRateService Manual Integration Test")
    print("=" * 60)
    
    # Test Redis
    redis_ok = test_redis_connection()
    if not redis_ok:
        print("\n⚠ Warning: Redis not available, caching will not work")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Run tests
        test_fetch_all_currencies(db)
        
        if redis_ok:
            test_cache_functionality(db)
        
        test_database_storage(db)
        test_error_handling(db)
        
        print("\n" + "=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    main()
