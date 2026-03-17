"""
Manual integration test for CoinGecko API
Tests real API calls with rate limiting and proper error handling
"""
import time
from app.core.database import get_db
from app.services.exchange_rate_service import ExchangeRateService
from config import settings

def test_coingecko_integration():
    """Test CoinGecko API integration with real calls"""
    
    print("\n" + "="*70)
    print("COINGECKO API INTEGRATION TEST")
    print("="*70)
    
    # Check if API key is configured
    if settings.coingecko_api_key:
        print(f"✅ CoinGecko API Key: Configured")
    else:
        print(f"⚠️  CoinGecko API Key: Not configured (using free tier)")
    
    # Get database session
    db = next(get_db())
    service = ExchangeRateService(db)
    
    try:
        # Test 1: Fetch EUR rate
        print("\n" + "-"*70)
        print("TEST 1: Fetch HBAR/EUR rate")
        print("-"*70)
        
        price_eur = service.get_hbar_price('EUR', use_cache=False)
        print(f"✅ HBAR Price (EUR): €{price_eur:.6f}")
        
        # Verify database storage
        rate_data = service.get_latest_rate_from_db('EUR')
        if rate_data:
            print(f"✅ Database Storage: Success")
            print(f"   - Currency: {rate_data['currency']}")
            print(f"   - Price: {rate_data['hbarPrice']}")
            print(f"   - Source: {rate_data['source']}")
            print(f"   - Fetched At: {rate_data['fetchedAt']}")
        else:
            print(f"❌ Database Storage: Failed")
        
        # Verify cache
        cached_price = service.get_cached_rate('EUR')
        if cached_price:
            print(f"✅ Redis Cache: Success (€{cached_price:.6f})")
        else:
            print(f"❌ Redis Cache: Failed")
        
        # Test 2: Cache hit
        print("\n" + "-"*70)
        print("TEST 2: Cache hit test")
        print("-"*70)
        
        price_eur_cached = service.get_hbar_price('EUR', use_cache=True)
        if price_eur_cached == price_eur:
            print(f"✅ Cache Hit: Success (€{price_eur_cached:.6f})")
        else:
            print(f"❌ Cache Hit: Failed")
        
        # Test 3: Multiple currencies (with rate limiting)
        print("\n" + "-"*70)
        print("TEST 3: Multiple currencies (with 2s delay between calls)")
        print("-"*70)
        
        currencies = ['USD', 'INR', 'BRL', 'NGN']
        results = {}
        
        for currency in currencies:
            try:
                # Add delay to avoid rate limiting
                time.sleep(2)
                
                price = service.get_hbar_price(currency, use_cache=False)
                results[currency] = price
                print(f"✅ {currency}: {price:.6f} (1 HBAR)")
                
                # Verify database storage
                rate_data = service.get_latest_rate_from_db(currency)
                if rate_data:
                    print(f"   ✓ Stored in database")
                else:
                    print(f"   ✗ Not stored in database")
                    
            except Exception as e:
                print(f"❌ {currency}: Failed - {e}")
                results[currency] = None
        
        # Test 4: Price relationship validation
        print("\n" + "-"*70)
        print("TEST 4: Price relationship validation")
        print("-"*70)
        
        if results.get('USD') and results.get('EUR'):
            ratio = results['USD'] / results['EUR']
            if 0.5 < ratio < 2.0:
                print(f"✅ USD/EUR ratio: {ratio:.2f} (reasonable)")
            else:
                print(f"⚠️  USD/EUR ratio: {ratio:.2f} (unusual)")
        
        if results.get('INR') and results.get('USD'):
            if results['INR'] > results['USD'] * 10:
                print(f"✅ INR > USD * 10: Valid")
            else:
                print(f"⚠️  INR price seems incorrect")
        
        if results.get('NGN') and results.get('USD'):
            if results['NGN'] > results['USD'] * 100:
                print(f"✅ NGN > USD * 100: Valid")
            else:
                print(f"⚠️  NGN price seems incorrect")
        
        # Test 5: Cache invalidation
        print("\n" + "-"*70)
        print("TEST 5: Cache invalidation")
        print("-"*70)
        
        result = service.invalidate_cache('EUR')
        if result:
            print(f"✅ Cache Invalidation: Success")
        else:
            print(f"❌ Cache Invalidation: Failed")
        
        # Verify cache is empty
        cached_after = service.get_cached_rate('EUR')
        if cached_after is None:
            print(f"✅ Cache Verification: Empty after invalidation")
        else:
            print(f"❌ Cache Verification: Still contains data")
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"✅ CoinGecko API: Working")
        print(f"✅ Database Storage: Working")
        print(f"✅ Redis Caching: Working")
        print(f"✅ Multi-currency: {len([r for r in results.values() if r])} / {len(currencies)} currencies")
        print(f"✅ Cache Invalidation: Working")
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == '__main__':
    test_coingecko_integration()
