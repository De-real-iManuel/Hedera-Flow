"""
Tests for CoinMarketCap Fallback API Integration

Tests the fallback mechanism when CoinGecko API fails.
Requirements: FR-5.2, Risk 8.1.7
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
import httpx

from app.services.exchange_rate_service import (
    ExchangeRateService,
    ExchangeRateAPIError,
    SUPPORTED_CURRENCIES
)


class TestCoinMarketCapFallback:
    """Test suite for CoinMarketCap fallback functionality"""
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_fetch_from_coinmarketcap_success(self, mock_httpx):
        """Test successful fetch from CoinMarketCap API"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = 'test-api-key'
        
        # Mock successful CoinMarketCap response
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'HBAR': {
                    'quote': {
                        'USD': {
                            'price': 0.35,
                            'volume_24h': 1000000,
                            'percent_change_24h': 2.5
                        }
                    }
                }
            }
        }
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_httpx.return_value = mock_client
        
        # Test fetch
        price = service._fetch_from_coinmarketcap('USD')
        
        assert price == 0.35
        assert isinstance(price, float)
        
        # Verify API call was made correctly
        call_args = mock_client.__enter__.return_value.get.call_args
        assert 'symbol=HBAR' in str(call_args) or call_args[1]['params']['symbol'] == 'HBAR'
        assert call_args[1]['params']['convert'] == 'USD'
        assert call_args[1]['headers']['X-CMC_PRO_API_KEY'] == 'test-api-key'
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_fetch_from_coinmarketcap_all_currencies(self, mock_httpx):
        """Test CoinMarketCap fetch for all supported currencies"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = 'test-api-key'
        
        test_prices = {
            'EUR': 0.32,
            'USD': 0.35,
            'INR': 28.5,
            'BRL': 1.75,
            'NGN': 540.0
        }
        
        for currency, expected_price in test_prices.items():
            # Mock response for each currency
            mock_response = Mock()
            mock_response.json.return_value = {
                'data': {
                    'HBAR': {
                        'quote': {
                            currency: {
                                'price': expected_price
                            }
                        }
                    }
                }
            }
            mock_response.raise_for_status = Mock()
            
            mock_client = MagicMock()
            mock_client.__enter__.return_value.get.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            # Test fetch
            price = service._fetch_from_coinmarketcap(currency)
            assert price == expected_price, f"Price mismatch for {currency}"
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_coinmarketcap_invalid_response_raises_error(self, mock_httpx):
        """Test that invalid CoinMarketCap response raises error"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = 'test-api-key'
        
        # Mock invalid response (missing data)
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_httpx.return_value = mock_client
        
        with pytest.raises(ExchangeRateAPIError) as exc_info:
            service._fetch_from_coinmarketcap('USD')
        
        assert 'invalid' in str(exc_info.value).lower()
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_coinmarketcap_missing_price_raises_error(self, mock_httpx):
        """Test that missing price in response raises error"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = 'test-api-key'
        
        # Mock response with missing price
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'HBAR': {
                    'quote': {
                        'USD': {}  # Missing 'price' field
                    }
                }
            }
        }
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_httpx.return_value = mock_client
        
        with pytest.raises(ExchangeRateAPIError) as exc_info:
            service._fetch_from_coinmarketcap('USD')
        
        assert 'missing price' in str(exc_info.value).lower()
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_coinmarketcap_http_error_raises_error(self, mock_httpx):
        """Test that HTTP error from CoinMarketCap raises error"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = 'test-api-key'
        
        # Mock HTTP error
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = httpx.HTTPStatusError(
            "API error", request=Mock(), response=Mock(status_code=401)
        )
        mock_httpx.return_value = mock_client
        
        with pytest.raises(ExchangeRateAPIError):
            service._fetch_from_coinmarketcap('USD')
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_coinmarketcap_timeout_raises_error(self, mock_httpx):
        """Test that timeout from CoinMarketCap raises error"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = 'test-api-key'
        
        # Mock timeout
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = httpx.TimeoutException("Timeout")
        mock_httpx.return_value = mock_client
        
        with pytest.raises(ExchangeRateAPIError):
            service._fetch_from_coinmarketcap('USD')
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_coingecko_failure_triggers_coinmarketcap(self, mock_httpx):
        """Test that CoinGecko failure automatically triggers CoinMarketCap fallback"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = 'test-cmc-key'
        
        # Track API calls
        call_count = [0]
        
        def get_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call (CoinGecko) fails
                raise httpx.HTTPStatusError(
                    "CoinGecko error", 
                    request=Mock(), 
                    response=Mock(status_code=500)
                )
            else:
                # Second call (CoinMarketCap) succeeds
                mock_response = Mock()
                mock_response.json.return_value = {
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
                mock_response.raise_for_status = Mock()
                return mock_response
        
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = get_side_effect
        mock_httpx.return_value = mock_client
        
        # Should fallback to CoinMarketCap and return price
        price = service.fetch_from_api('EUR')
        
        assert price == 0.33
        assert call_count[0] == 2, "Should have made 2 API calls (CoinGecko + CoinMarketCap)"
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_coingecko_timeout_triggers_coinmarketcap(self, mock_httpx):
        """Test that CoinGecko timeout triggers CoinMarketCap fallback"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = 'test-cmc-key'
        
        call_count = [0]
        
        def get_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call (CoinGecko) times out
                raise httpx.TimeoutException("Request timeout")
            else:
                # Second call (CoinMarketCap) succeeds
                mock_response = Mock()
                mock_response.json.return_value = {
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
                mock_response.raise_for_status = Mock()
                return mock_response
        
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = get_side_effect
        mock_httpx.return_value = mock_client
        
        # Should fallback to CoinMarketCap
        price = service.fetch_from_api('USD')
        
        assert price == 0.36
        assert call_count[0] == 2, "Should have made 2 API calls"
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_no_fallback_when_coinmarketcap_not_configured(self, mock_httpx):
        """Test that fallback doesn't occur when CoinMarketCap key is not configured"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = None  # Not configured
        
        # Mock CoinGecko failure
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = httpx.TimeoutException("Timeout")
        mock_httpx.return_value = mock_client
        
        # Should raise error without attempting fallback
        with pytest.raises(ExchangeRateAPIError) as exc_info:
            service.fetch_from_api('USD')
        
        assert 'timeout' in str(exc_info.value).lower()
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_both_apis_fail_raises_error(self, mock_httpx):
        """Test that failure of both APIs raises ExchangeRateAPIError"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = 'test-cmc-key'
        
        # Mock both APIs failing
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = Exception("Network error")
        mock_httpx.return_value = mock_client
        
        # Should raise error after both attempts fail
        with pytest.raises(ExchangeRateAPIError):
            service.fetch_from_api('USD')
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    @patch('app.services.exchange_rate_service.redis_client')
    def test_fallback_result_cached_correctly(self, mock_redis, mock_httpx):
        """Test that CoinMarketCap fallback result is cached properly"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = 'test-cmc-key'
        
        # Mock cache miss
        mock_redis.get_exchange_rate.return_value = None
        mock_redis.set_exchange_rate.return_value = True
        
        # Mock CoinGecko failure and CoinMarketCap success
        call_count = [0]
        
        def get_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise httpx.TimeoutException("Timeout")
            else:
                mock_response = Mock()
                mock_response.json.return_value = {
                    'data': {
                        'HBAR': {
                            'quote': {
                                'INR': {
                                    'price': 29.0
                                }
                            }
                        }
                    }
                }
                mock_response.raise_for_status = Mock()
                return mock_response
        
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = get_side_effect
        mock_httpx.return_value = mock_client
        
        # Mock DB storage
        db.execute = Mock()
        db.commit = Mock()
        
        # Fetch price (should use fallback)
        price = service.get_hbar_price('INR', use_cache=True)
        
        assert price == 29.0
        
        # Verify caching was called
        mock_redis.set_exchange_rate.assert_called_once()
        cache_data = mock_redis.set_exchange_rate.call_args[0][1]
        assert cache_data['hbarPrice'] == 29.0
        assert cache_data['currency'] == 'INR'
    
    @patch('app.services.exchange_rate_service.httpx.Client')
    def test_fallback_result_stored_in_db(self, mock_httpx):
        """Test that CoinMarketCap fallback result is stored in database"""
        db = Mock(spec=Session)
        service = ExchangeRateService(db)
        service.coinmarketcap_api_key = 'test-cmc-key'
        
        # Mock CoinGecko failure and CoinMarketCap success
        call_count = [0]
        
        def get_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise httpx.TimeoutException("Timeout")
            else:
                mock_response = Mock()
                mock_response.json.return_value = {
                    'data': {
                        'HBAR': {
                            'quote': {
                                'BRL': {
                                    'price': 1.80
                                }
                            }
                        }
                    }
                }
                mock_response.raise_for_status = Mock()
                return mock_response
        
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = get_side_effect
        mock_httpx.return_value = mock_client
        
        # Mock DB storage
        db.execute = Mock()
        db.commit = Mock()
        
        # Fetch price
        price = service.fetch_from_api('BRL')
        
        assert price == 1.80
        
        # Store in DB
        result = service.store_in_db('BRL', price, 'coinmarketcap')
        
        assert result is True
        db.execute.assert_called_once()
        db.commit.assert_called_once()


class TestCoinMarketCapIntegration:
    """Integration tests for CoinMarketCap fallback (requires API key)"""
    
    def test_real_coinmarketcap_api_call(self):
        """Test real API call to CoinMarketCap (requires API key)"""
        from app.core.database import get_db
        from config import settings
        
        if not settings.coinmarketcap_api_key:
            pytest.skip("CoinMarketCap API key not configured")
        
        db = next(get_db())
        
        try:
            service = ExchangeRateService(db)
            
            # Test all supported currencies
            for currency in SUPPORTED_CURRENCIES:
                price = service._fetch_from_coinmarketcap(currency)
                
                assert price > 0, f"Price for {currency} should be positive"
                assert isinstance(price, float), f"Price for {currency} should be float"
                
                print(f"✅ {currency}: {price} HBAR (CoinMarketCap)")
            
            print("\n✅ Real CoinMarketCap API test PASSED")
            
        finally:
            db.close()
    
    def test_fallback_mechanism_end_to_end(self):
        """Test complete fallback mechanism with real APIs"""
        from app.core.database import get_db
        from config import settings
        
        if not settings.coinmarketcap_api_key:
            pytest.skip("CoinMarketCap API key not configured")
        
        db = next(get_db())
        
        try:
            service = ExchangeRateService(db)
            
            # Force CoinGecko to fail by using invalid API key
            original_key = service.coingecko_api_key
            service.coingecko_api_key = 'invalid-key-to-force-failure'
            
            # This should trigger fallback to CoinMarketCap
            price = service.fetch_from_api('USD')
            
            assert price > 0, "Fallback should return valid price"
            print(f"\n✅ Fallback mechanism test PASSED")
            print(f"   - USD: {price} HBAR (via CoinMarketCap fallback)")
            
            # Restore original key
            service.coingecko_api_key = original_key
            
        finally:
            db.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

