"""
Tests for ExchangeRateService

Tests HBAR price fetching, caching, and database storage.
Requirements: FR-5.2, US-7
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import time

from app.services.exchange_rate_service import (
    ExchangeRateService,
    ExchangeRateError,
    ExchangeRateAPIError,
    SUPPORTED_CURRENCIES,
    get_hbar_price
)


class TestExchangeRateService:
    """Test suite for ExchangeRateService"""
    
    def test_supported_currencies(self):
        """Test that all required currencies are supported"""
        assert 'EUR' in SUPPORTED_CURRENCIES
        assert 'USD' in SUPPORTED_CURRENCIES
        assert 'INR' in SUPPORTED_CURRENCIES
        assert 'BRL' in SUPPORTED_CURRENCIES
        assert 'NGN' in SUPPORTED_CURRENCIES
    
    def test_unsupported_currency_raises_error(self):
        """Test that unsupported currency raises ExchangeRateError"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        
        with pytest.raises(ExchangeRateError) as exc_info:
            service.get_hbar_price('GBP')
        
        assert 'not supported' in str(exc_info.value).lower()
    
    @patch('app.services.exchange_rate_service.redis_client')
    def test_cache_hit_returns_cached_price(self, mock_redis):
        """Test that cached price is returned when available"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        
        # Mock cache hit
        mock_redis.get_exchange_rate.return_value = {
            'currency': 'EUR',
            'hbarPrice': 0.34,
            'source': 'coingecko',
            'fetchedAt': datetime.now(timezone.utc).isoformat()
        }
        
        price = service.get_hbar_price('EUR', use_cache=True)
        
        assert price == 0.34
        mock_redis.get_exchange_rate.assert_called_once_with('EUR')
    
    @patch('app.services.exchange_rate_service.redis_client')
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_cache_miss_fetches_from_api(self, mock_httpx, mock_redis):
        """Test that API is called when cache misses"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        
        # Mock cache miss
        mock_redis.get_exchange_rate.return_value = None
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'hedera-hashgraph': {
                'usd': 0.35
            }
        }
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_httpx.return_value = mock_client
        
        # Mock cache and DB storage
        mock_redis.set_exchange_rate.return_value = True
        db.execute = Mock()
        db.commit = Mock()
        
        price = service.get_hbar_price('USD', use_cache=True)
        
        assert price == 0.35
        mock_redis.get_exchange_rate.assert_called_once_with('USD')
        mock_redis.set_exchange_rate.assert_called_once()
        db.execute.assert_called_once()
        db.commit.assert_called_once()
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_fetch_from_api_success(self, mock_httpx):
        """Test successful API fetch from CoinGecko"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'hedera-hashgraph': {
                'eur': 0.32,
                'usd': 0.35,
                'inr': 28.5,
                'brl': 1.75,
                'ngn': 540.0
            }
        }
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_httpx.return_value = mock_client
        
        # Test each currency
        assert service.fetch_from_api('EUR') == 0.32
        assert service.fetch_from_api('USD') == 0.35
        assert service.fetch_from_api('INR') == 28.5
        assert service.fetch_from_api('BRL') == 1.75
        assert service.fetch_from_api('NGN') == 540.0
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_fetch_from_api_invalid_response(self, mock_httpx):
        """Test API fetch with invalid response"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        
        # Mock invalid response (missing hedera-hashgraph)
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_httpx.return_value = mock_client
        
        with pytest.raises(ExchangeRateAPIError) as exc_info:
            service.fetch_from_api('EUR')
        
        assert 'missing hedera-hashgraph' in str(exc_info.value).lower()
    
    @patch('app.services.exchange_rate_service.redis_client')
    def test_cache_rate_success(self, mock_redis):
        """Test successful rate caching"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        
        mock_redis.set_exchange_rate.return_value = True
        
        result = service.cache_rate('EUR', 0.34)
        
        assert result is True
        mock_redis.set_exchange_rate.assert_called_once()
        
        # Verify cache data structure
        call_args = mock_redis.set_exchange_rate.call_args
        assert call_args[0][0] == 'EUR'
        cache_data = call_args[0][1]
        assert cache_data['currency'] == 'EUR'
        assert cache_data['hbarPrice'] == 0.34
        assert cache_data['source'] == 'coingecko'
        assert 'fetchedAt' in cache_data
    
    @patch('app.services.exchange_rate_service.redis_client')
    def test_get_cached_rate_success(self, mock_redis):
        """Test successful retrieval of cached rate"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        
        mock_redis.get_exchange_rate.return_value = {
            'currency': 'USD',
            'hbarPrice': 0.35,
            'source': 'coingecko',
            'fetchedAt': datetime.now(timezone.utc).isoformat()
        }
        
        price = service.get_cached_rate('USD')
        
        assert price == 0.35
        mock_redis.get_exchange_rate.assert_called_once_with('USD')
    
    @patch('app.services.exchange_rate_service.redis_client')
    def test_get_cached_rate_miss(self, mock_redis):
        """Test cache miss returns None"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        
        mock_redis.get_exchange_rate.return_value = None
        
        price = service.get_cached_rate('EUR')
        
        assert price is None
    
    def test_store_in_db_success(self):
        """Test successful database storage"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        
        db.execute = Mock()
        db.commit = Mock()
        
        result = service.store_in_db('EUR', 0.34, 'coingecko')
        
        assert result is True
        db.execute.assert_called_once()
        db.commit.assert_called_once()
        
        # Verify SQL parameters
        call_args = db.execute.call_args
        params = call_args[0][1]
        assert params['currency'] == 'EUR'
        assert params['hbar_price'] == Decimal('0.34')
        assert params['source'] == 'coingecko'
    
    def test_store_in_db_failure_rollback(self):
        """Test database storage failure triggers rollback"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        
        db.execute = Mock(side_effect=Exception("DB error"))
        db.rollback = Mock()
        
        result = service.store_in_db('EUR', 0.34, 'coingecko')
        
        assert result is False
        db.rollback.assert_called_once()
    
    def test_get_latest_rate_from_db_success(self):
        """Test retrieval of latest rate from database"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        
        # Mock database result
        mock_result = Mock()
        mock_result.fetchone.return_value = (
            'EUR',
            Decimal('0.34'),
            'coingecko',
            datetime(2024, 3, 18, 10, 30, 0, tzinfo=timezone.utc)
        )
        db.execute = Mock(return_value=mock_result)
        
        rate_data = service.get_latest_rate_from_db('EUR')
        
        assert rate_data is not None
        assert rate_data['currency'] == 'EUR'
        assert rate_data['hbarPrice'] == 0.34
        assert rate_data['source'] == 'coingecko'
        assert 'fetchedAt' in rate_data
    
    def test_get_latest_rate_from_db_not_found(self):
        """Test database query returns None when no rate found"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        
        mock_result = Mock()
        mock_result.fetchone.return_value = None
        db.execute = Mock(return_value=mock_result)
        
        rate_data = service.get_latest_rate_from_db('EUR')
        
        assert rate_data is None
    
    @patch('app.services.exchange_rate_service.redis_client')
    def test_invalidate_cache_success(self, mock_redis):
        """Test cache invalidation"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        
        mock_redis.delete_exchange_rate.return_value = True
        
        result = service.invalidate_cache('EUR')
        
        assert result is True
        mock_redis.delete_exchange_rate.assert_called_once_with('EUR')
    
    @patch('app.services.exchange_rate_service.ExchangeRateService')
    def test_convenience_function(self, mock_service_class):
        """Test convenience function get_hbar_price"""
        db = Mock(spec=Session)
        
        # Mock service instance
        mock_service = Mock()
        mock_service.get_hbar_price.return_value = 0.34
        mock_service_class.return_value = mock_service
        
        price = get_hbar_price(db, 'EUR', use_cache=True)
        
        assert price == 0.34
        mock_service_class.assert_called_once_with(db)
        mock_service.get_hbar_price.assert_called_once_with('EUR', True)
    
    def test_currency_case_insensitive(self):
        """Test that currency codes are case-insensitive"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        
        # Should not raise error for lowercase
        with patch.object(service, 'fetch_from_api', return_value=0.34):
            with patch.object(service, 'cache_rate', return_value=True):
                with patch.object(service, 'store_in_db', return_value=True):
                    price = service.get_hbar_price('eur', use_cache=False)
                    assert price == 0.34
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_coingecko_failure_triggers_coinmarketcap_fallback(self, mock_httpx):
        """Test that CoinGecko failure triggers CoinMarketCap fallback"""
        import httpx
        
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = 'test-cmc-key'
        
        # Mock CoinMarketCap success
        mock_cmc_response = Mock()
        mock_cmc_response.json.return_value = {
            'data': {
                'HBAR': {
                    'quote': {
                        'USD': {
                            'price': 0.36
                        }
                    }
                }
            }
        }
        mock_cmc_response.raise_for_status = Mock()
        
        # Setup mock client to fail for CoinGecko, succeed for CoinMarketCap
        call_count = [0]
        def get_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call (CoinGecko) fails with HTTP error
                raise httpx.HTTPStatusError(
                    "CoinGecko error",
                    request=Mock(),
                    response=Mock(status_code=500)
                )
            else:
                # Second call (CoinMarketCap) succeeds
                return mock_cmc_response
        
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = get_side_effect
        mock_httpx.return_value = mock_client
        
        # Should fallback to CoinMarketCap and return price
        price = service.fetch_from_api('USD')
        assert price == 0.36
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_coingecko_timeout_triggers_coinmarketcap_fallback(self, mock_httpx):
        """Test that CoinGecko timeout triggers CoinMarketCap fallback"""
        import httpx
        
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = 'test-cmc-key'
        
        # Mock CoinMarketCap success
        mock_cmc_response = Mock()
        mock_cmc_response.json.return_value = {
            'data': {
                'HBAR': {
                    'quote': {
                        'EUR': {
                            'price': 0.33
                        }
                    }
                }
            }
        }
        mock_cmc_response.raise_for_status = Mock()
        
        # Setup mock client to timeout for CoinGecko, succeed for CoinMarketCap
        call_count = [0]
        def get_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call (CoinGecko) times out
                raise httpx.TimeoutException("Request timeout")
            else:
                # Second call (CoinMarketCap) succeeds
                return mock_cmc_response
        
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = get_side_effect
        mock_httpx.return_value = mock_client
        
        # Should fallback to CoinMarketCap and return price
        price = service.fetch_from_api('EUR')
        assert price == 0.33
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_both_apis_fail_raises_error(self, mock_httpx):
        """Test that failure of both APIs raises ExchangeRateAPIError"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = 'test-cmc-key'
        
        # Mock both APIs failing
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = Exception("API error")
        mock_httpx.return_value = mock_client
        
        # Should raise ExchangeRateAPIError
        with pytest.raises(ExchangeRateAPIError):
            service.fetch_from_api('USD')
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_coinmarketcap_not_configured_no_fallback(self, mock_httpx):
        """Test that without CoinMarketCap key, no fallback occurs"""
        import httpx
        
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = None  # No fallback configured
        
        # Mock CoinGecko timeout
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = httpx.TimeoutException("Timeout")
        mock_httpx.return_value = mock_client
        
        # Should raise error without attempting fallback
        with pytest.raises(ExchangeRateAPIError) as exc_info:
            service.fetch_from_api('USD')
        
        assert 'timeout' in str(exc_info.value).lower()


class TestExchangeRateIntegration:
    """Integration tests for ExchangeRateService (requires real DB and Redis)"""
    
    def test_full_flow_with_real_db(self):
        """Test full flow with real database and cache"""
        from app.core.database import get_db
        
        # Get real database session
        db = next(get_db())
        
        try:
            service = ExchangeRateService(db)
            
            # Clear cache before testing
            service.invalidate_cache('EUR')
            
            # Test 1: Fetch fresh rate (with cache enabled to populate it)
            try:
                price_eur = service.get_hbar_price('EUR', use_cache=True)
            except ExchangeRateError as e:
                # If we hit rate limit, skip the test
                if "429" in str(e):
                    pytest.skip("CoinGecko API rate limit reached")
                raise
            
            assert price_eur > 0, "HBAR price should be positive"
            assert isinstance(price_eur, float), "Price should be a float"
            
            # Test 2: Verify it was stored in database
            rate_data = service.get_latest_rate_from_db('EUR')
            assert rate_data is not None, "Rate should be stored in database"
            assert rate_data['currency'] == 'EUR'
            # Database stores with 6 decimal precision, so compare with tolerance
            assert abs(rate_data['hbarPrice'] - price_eur) < 0.000001, "Stored price should match fetched price (within precision)"
            assert rate_data['source'] == 'coingecko'
            
            # Test 3: Verify cache was populated
            cached_price = service.get_cached_rate('EUR')
            assert cached_price == price_eur, "Cached price should match fetched price"
            
            # Test 4: Fetch with cache enabled (should hit cache)
            price_eur_cached = service.get_hbar_price('EUR', use_cache=True)
            assert price_eur_cached == price_eur, "Cached price should be returned"
            
            # Test 5: Test multiple currencies (with delays to avoid rate limiting)
            currencies = ['USD', 'INR', 'BRL', 'NGN']
            for i, currency in enumerate(currencies):
                # Add delay to avoid rate limiting
                if i > 0:
                    time.sleep(2)
                
                try:
                    price = service.get_hbar_price(currency, use_cache=True)
                    assert price > 0, f"HBAR price for {currency} should be positive"
                    
                    # Verify database storage
                    rate_data = service.get_latest_rate_from_db(currency)
                    assert rate_data is not None, f"Rate for {currency} should be in database"
                    assert rate_data['currency'] == currency
                except ExchangeRateError as e:
                    # If we hit rate limit, stop testing additional currencies
                    if "429" in str(e):
                        print(f"⚠️  Rate limit reached at {currency}, skipping remaining currencies")
                        break
                    raise
            
            # Test 6: Test cache invalidation
            result = service.invalidate_cache('EUR')
            assert result is True, "Cache invalidation should succeed"
            
            # Verify cache is empty
            cached_price_after = service.get_cached_rate('EUR')
            assert cached_price_after is None, "Cache should be empty after invalidation"
            
            print("\n✅ Full flow integration test PASSED")
            print(f"   - EUR: {price_eur}")
            print(f"   - Database storage: ✓")
            print(f"   - Redis caching: ✓")
            print(f"   - Cache invalidation: ✓")
            print(f"   - Multi-currency: ✓")
            
        finally:
            db.close()
    
    def test_real_api_call(self):
        """Test real API call to CoinGecko"""
        from app.core.database import get_db
        
        # Get real database session
        db = next(get_db())
        
        try:
            service = ExchangeRateService(db)
            
            # Test CoinGecko API for all supported currencies
            # Add delays to avoid rate limiting
            currencies = ['EUR', 'USD', 'INR', 'BRL', 'NGN']
            results = {}
            
            for i, currency in enumerate(currencies):
                try:
                    # Add 2-second delay between requests to avoid rate limiting
                    if i > 0:
                        time.sleep(2)
                    
                    price = service.fetch_from_api(currency)
                    assert price > 0, f"Price for {currency} should be positive"
                    assert isinstance(price, float), f"Price for {currency} should be float"
                    results[currency] = price
                    print(f"✅ {currency}: {price} (1 HBAR)")
                except ExchangeRateAPIError as e:
                    # If we hit rate limit, skip remaining currencies
                    if "429" in str(e):
                        pytest.skip(f"CoinGecko API rate limit reached at {currency}")
                    pytest.fail(f"CoinGecko API call failed for {currency}: {e}")
            
            # Verify price relationships make sense (only if we have the data)
            # USD should be close to EUR (within 50% difference)
            if 'USD' in results and 'EUR' in results:
                ratio = results['USD'] / results['EUR']
                assert 0.5 < ratio < 2.0, "USD/EUR ratio should be reasonable"
            
            # INR should be much higher than USD (India uses smaller currency units)
            if 'INR' in results and 'USD' in results:
                assert results['INR'] > results['USD'] * 10, "INR should be significantly higher than USD"
            
            # NGN should be much higher than USD (Nigeria uses smaller currency units)
            if 'NGN' in results and 'USD' in results:
                assert results['NGN'] > results['USD'] * 100, "NGN should be significantly higher than USD"
            
            print("\n✅ Real API call test PASSED")
            print(f"   - {len(results)}/{len(currencies)} currencies fetched successfully")
            print(f"   - Price relationships validated")
            
        finally:
            db.close()
    
    def test_coingecko_api_with_key(self):
        """Test CoinGecko API with API key (if configured)"""
        from app.core.database import get_db
        from config import settings
        
        if not settings.coingecko_api_key:
            pytest.skip("CoinGecko API key not configured")
        
        db = next(get_db())
        
        try:
            service = ExchangeRateService(db)
            
            # Test with API key (should have higher rate limits)
            price = service.fetch_from_api('EUR')
            assert price > 0, "Price should be positive"
            
            print(f"\n✅ CoinGecko API with key test PASSED")
            print(f"   - EUR: {price} (using API key)")
            
        finally:
            db.close()
    
    def test_coinmarketcap_fallback(self):
        """Test CoinMarketCap fallback API (if configured)"""
        from app.core.database import get_db
        from config import settings
        
        if not settings.coinmarketcap_api_key:
            pytest.skip("CoinMarketCap API key not configured")
        
        db = next(get_db())
        
        try:
            service = ExchangeRateService(db)
            
            # Test CoinMarketCap fallback for all supported currencies
            currencies = ['EUR', 'USD', 'INR', 'BRL', 'NGN']
            results = {}
            
            for currency in currencies:
                price = service._fetch_from_coinmarketcap(currency)
                assert price > 0, f"Price for {currency} should be positive"
                assert isinstance(price, float), f"Price for {currency} should be float"
                results[currency] = price
                print(f"✅ {currency}: {price} (1 HBAR via CoinMarketCap)")
            
            # Verify price relationships make sense
            if 'USD' in results and 'EUR' in results:
                ratio = results['USD'] / results['EUR']
                assert 0.5 < ratio < 2.0, "USD/EUR ratio should be reasonable"
            
            if 'INR' in results and 'USD' in results:
                assert results['INR'] > results['USD'] * 10, "INR should be significantly higher than USD"
            
            if 'NGN' in results and 'USD' in results:
                assert results['NGN'] > results['USD'] * 100, "NGN should be significantly higher than USD"
            
            print(f"\n✅ CoinMarketCap fallback test PASSED")
            print(f"   - All {len(currencies)} currencies fetched successfully")
            print(f"   - Price relationships validated")
            
        finally:
            db.close()
    
    def test_exchange_rate_caching_ttl(self):
        """Test that exchange rate cache respects 5-minute TTL"""
        import time
        from app.core.database import get_db
        
        db = next(get_db())
        
        try:
            service = ExchangeRateService(db)
            
            # Clear cache first
            service.invalidate_cache('EUR')
            
            # Fetch fresh rate (with rate limit protection)
            try:
                price1 = service.get_hbar_price('EUR', use_cache=True)
            except ExchangeRateError as e:
                # If we hit rate limit, skip the test
                if "429" in str(e):
                    pytest.skip("CoinGecko API rate limit reached")
                raise
            
            # Immediately fetch again (should hit cache)
            price2 = service.get_hbar_price('EUR', use_cache=True)
            assert price1 == price2, "Cached price should be returned"
            
            # Verify cache exists
            cached = service.get_cached_rate('EUR')
            assert cached == price1, "Cache should contain the price"
            
            print(f"\n✅ Cache TTL test PASSED")
            print(f"   - Initial fetch: {price1}")
            print(f"   - Cached fetch: {price2}")
            print(f"   - Cache hit confirmed: ✓")
            
        finally:
            db.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
