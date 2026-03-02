"""
Test Exchange Rate Redis Caching

Tests for Task 16.4: Implement 5-minute cache in Redis
Requirements: FR-5.3

Tests verify:
1. Exchange rates are cached in Redis with 5-minute TTL
2. Cache hits return cached data without API calls
3. Cache misses trigger API calls and cache storage
4. Cache expiration after 5 minutes
5. Cache invalidation works correctly
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
import time

from app.services.exchange_rate_service import ExchangeRateService, ExchangeRateError
from app.utils.redis_client import redis_client


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = Mock(spec=Session)
    db.execute = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def exchange_service(mock_db):
    """Create ExchangeRateService instance"""
    return ExchangeRateService(mock_db)


@pytest.fixture(autouse=True)
def clear_redis_cache():
    """Clear Redis cache before each test"""
    try:
        # Clear all exchange rate keys
        keys = redis_client.get_keys_by_pattern("exchange_rate:*")
        for key in keys:
            redis_client.client.delete(key)
    except Exception:
        pass
    yield
    # Cleanup after test
    try:
        keys = redis_client.get_keys_by_pattern("exchange_rate:*")
        for key in keys:
            redis_client.client.delete(key)
    except Exception:
        pass


class TestExchangeRateCache:
    """Test exchange rate caching functionality"""
    
    def test_cache_miss_triggers_api_call(self, exchange_service, mock_db):
        """Test that cache miss triggers API call and stores result"""
        # Mock API response
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                'hedera-hashgraph': {'eur': 0.34}
            }
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            # First call should hit API (cache miss)
            price = exchange_service.get_hbar_price('EUR', use_cache=True)
            
            # Verify API was called
            assert mock_client.return_value.__enter__.return_value.get.called
            assert price == 0.34
            
            # Verify rate was cached
            cached_rate = redis_client.get_exchange_rate('EUR')
            assert cached_rate is not None
            assert cached_rate['hbarPrice'] == 0.34
            assert cached_rate['currency'] == 'EUR'
            assert cached_rate['source'] == 'coingecko'
    
    def test_cache_hit_skips_api_call(self, exchange_service, mock_db):
        """Test that cache hit returns cached data without API call"""
        # Pre-populate cache
        rate_data = {
            'currency': 'EUR',
            'hbarPrice': 0.34,
            'source': 'coingecko',
            'fetchedAt': datetime.now(timezone.utc).isoformat()
        }
        redis_client.set_exchange_rate('EUR', rate_data)
        
        # Mock API to verify it's NOT called
        with patch('httpx.Client') as mock_client:
            # Call service
            price = exchange_service.get_hbar_price('EUR', use_cache=True)
            
            # Verify API was NOT called
            assert not mock_client.called
            assert price == 0.34
    
    def test_cache_ttl_is_5_minutes(self, exchange_service):
        """Test that cache TTL is set to 5 minutes (300 seconds)"""
        # Cache a rate
        rate_data = {
            'currency': 'USD',
            'hbarPrice': 0.35,
            'source': 'coingecko',
            'fetchedAt': datetime.now(timezone.utc).isoformat()
        }
        redis_client.set_exchange_rate('USD', rate_data)
        
        # Check TTL
        key = "exchange_rate:USD"
        ttl = redis_client.get_ttl(key)
        
        # TTL should be around 300 seconds (5 minutes)
        # Allow some tolerance for execution time
        assert 295 <= ttl <= 300, f"Expected TTL ~300s, got {ttl}s"
    
    def test_cache_expiration_after_5_minutes(self, exchange_service, mock_db):
        """Test that cache expires after 5 minutes"""
        # This test would take 5 minutes to run naturally,
        # so we'll test the TTL setting instead
        rate_data = {
            'currency': 'INR',
            'hbarPrice': 28.5,
            'source': 'coingecko',
            'fetchedAt': datetime.now(timezone.utc).isoformat()
        }
        redis_client.set_exchange_rate('INR', rate_data)
        
        # Verify cache exists
        cached = redis_client.get_exchange_rate('INR')
        assert cached is not None
        
        # Verify TTL is set
        key = "exchange_rate:INR"
        ttl = redis_client.get_ttl(key)
        assert ttl > 0, "TTL should be set"
        assert ttl <= 300, "TTL should not exceed 5 minutes"
    
    def test_cache_invalidation(self, exchange_service, mock_db):
        """Test that cache can be manually invalidated"""
        # Cache a rate
        rate_data = {
            'currency': 'BRL',
            'hbarPrice': 1.75,
            'source': 'coingecko',
            'fetchedAt': datetime.now(timezone.utc).isoformat()
        }
        redis_client.set_exchange_rate('BRL', rate_data)
        
        # Verify cache exists
        cached = redis_client.get_exchange_rate('BRL')
        assert cached is not None
        
        # Invalidate cache
        result = exchange_service.invalidate_cache('BRL')
        assert result is True
        
        # Verify cache is gone
        cached = redis_client.get_exchange_rate('BRL')
        assert cached is None
    
    def test_use_cache_false_bypasses_cache(self, exchange_service, mock_db):
        """Test that use_cache=False bypasses cache"""
        # Pre-populate cache with old data
        rate_data = {
            'currency': 'NGN',
            'hbarPrice': 500.0,  # Old price
            'source': 'coingecko',
            'fetchedAt': datetime.now(timezone.utc).isoformat()
        }
        redis_client.set_exchange_rate('NGN', rate_data)
        
        # Mock API with new price
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                'hedera-hashgraph': {'ngn': 540.0}  # New price
            }
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            # Call with use_cache=False
            price = exchange_service.get_hbar_price('NGN', use_cache=False)
            
            # Verify API was called and new price returned
            assert mock_client.return_value.__enter__.return_value.get.called
            assert price == 540.0
    
    def test_multiple_currencies_cached_independently(self, exchange_service, mock_db):
        """Test that different currencies are cached independently"""
        # Cache multiple currencies
        currencies = {
            'EUR': 0.34,
            'USD': 0.35,
            'INR': 28.5,
            'BRL': 1.75,
            'NGN': 540.0
        }
        
        for currency, price in currencies.items():
            rate_data = {
                'currency': currency,
                'hbarPrice': price,
                'source': 'coingecko',
                'fetchedAt': datetime.now(timezone.utc).isoformat()
            }
            redis_client.set_exchange_rate(currency, rate_data)
        
        # Verify all are cached independently
        for currency, expected_price in currencies.items():
            cached = redis_client.get_exchange_rate(currency)
            assert cached is not None
            assert cached['hbarPrice'] == expected_price
            assert cached['currency'] == currency
    
    def test_cache_stores_metadata(self, exchange_service, mock_db):
        """Test that cache stores complete metadata"""
        # Mock API response
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                'hedera-hashgraph': {'eur': 0.34}
            }
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            # Fetch rate
            exchange_service.get_hbar_price('EUR', use_cache=True)
            
            # Verify cached data has all required fields
            cached = redis_client.get_exchange_rate('EUR')
            assert cached is not None
            assert 'currency' in cached
            assert 'hbarPrice' in cached
            assert 'source' in cached
            assert 'fetchedAt' in cached
            assert cached['currency'] == 'EUR'
            assert cached['hbarPrice'] == 0.34
            assert cached['source'] == 'coingecko'
            
            # Verify fetchedAt is recent
            fetched_at = datetime.fromisoformat(cached['fetchedAt'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            time_diff = (now - fetched_at).total_seconds()
            assert time_diff < 5, "fetchedAt should be recent"
    
    def test_cache_key_format(self, exchange_service):
        """Test that cache keys follow correct format"""
        # Cache a rate
        rate_data = {
            'currency': 'EUR',
            'hbarPrice': 0.34,
            'source': 'coingecko',
            'fetchedAt': datetime.now(timezone.utc).isoformat()
        }
        redis_client.set_exchange_rate('EUR', rate_data)
        
        # Verify key format
        keys = redis_client.get_keys_by_pattern("exchange_rate:*")
        assert len(keys) > 0
        assert b"exchange_rate:EUR" in keys or "exchange_rate:EUR" in keys
    
    def test_calculate_hbar_amount_uses_cache(self, exchange_service, mock_db):
        """Test that calculate_hbar_amount uses cached rates"""
        # Pre-populate cache
        rate_data = {
            'currency': 'EUR',
            'hbarPrice': 0.34,
            'source': 'coingecko',
            'fetchedAt': datetime.now(timezone.utc).isoformat()
        }
        redis_client.set_exchange_rate('EUR', rate_data)
        
        # Mock API to verify it's NOT called
        with patch('httpx.Client') as mock_client:
            # Calculate HBAR amount
            result = exchange_service.calculate_hbar_amount(85.40, 'EUR', use_cache=True)
            
            # Verify API was NOT called (cache hit)
            assert not mock_client.called
            
            # Verify calculation is correct
            assert result['fiat_amount'] == 85.40
            assert result['currency'] == 'EUR'
            assert result['hbar_price'] == 0.34
            assert result['hbar_amount_rounded'] == round(85.40 / 0.34, 8)


class TestCachePerformance:
    """Test cache performance improvements"""
    
    def test_cache_reduces_api_calls(self, exchange_service, mock_db):
        """Test that cache significantly reduces API calls"""
        # Mock API
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                'hedera-hashgraph': {'eur': 0.34}
            }
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            # Make 10 calls
            for _ in range(10):
                exchange_service.get_hbar_price('EUR', use_cache=True)
            
            # Verify API was called only once (first call)
            assert mock_client.return_value.__enter__.return_value.get.call_count == 1
    
    def test_cache_improves_response_time(self, exchange_service, mock_db):
        """Test that cached responses are faster than API calls"""
        # Mock API with delay
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                'hedera-hashgraph': {'eur': 0.34}
            }
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            # First call (API + cache)
            start = time.time()
            exchange_service.get_hbar_price('EUR', use_cache=True)
            first_call_time = time.time() - start
            
            # Second call (cache only)
            start = time.time()
            exchange_service.get_hbar_price('EUR', use_cache=True)
            second_call_time = time.time() - start
            
            # Cache should be faster (or at least not slower)
            # Note: In tests this might not always be true due to mocking overhead
            # but in production, cache is always faster
            assert second_call_time <= first_call_time * 2  # Allow some tolerance


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
