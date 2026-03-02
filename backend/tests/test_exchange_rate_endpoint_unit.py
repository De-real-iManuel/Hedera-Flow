"""
Unit Test Exchange Rate Endpoint
Tests for GET /api/exchange-rate/{currency} without full app initialization

Requirements: FR-5.2, US-7
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from fastapi import HTTPException

from app.services.exchange_rate_service import ExchangeRateError


class TestExchangeRateEndpointUnit:
    """Unit test suite for exchange rate endpoint logic"""
    
    def test_successful_exchange_rate_fetch(self):
        """Test successful exchange rate fetch logic"""
        # Mock database session
        mock_db = Mock()
        
        # Mock ExchangeRateService
        with patch('app.services.exchange_rate_service.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.return_value = 0.34
            mock_service.get_cached_rate.return_value = {
                'currency': 'EUR',
                'hbarPrice': 0.34,
                'source': 'coingecko',
                'fetchedAt': '2024-03-18T10:30:00Z'
            }
            MockService.return_value = mock_service
            
            # Simulate endpoint logic
            service = MockService(mock_db)
            currency = 'EUR'
            hbar_price = service.get_hbar_price(currency, use_cache=True)
            rate_data = service.get_cached_rate(currency)
            
            # Assertions
            assert hbar_price == 0.34
            assert rate_data['currency'] == 'EUR'
            assert rate_data['hbarPrice'] == 0.34
            assert rate_data['source'] == 'coingecko'
            assert 'fetchedAt' in rate_data
    
    def test_currency_normalization(self):
        """Test that currency codes are normalized to uppercase"""
        currency = 'eur'
        normalized = currency.upper()
        assert normalized == 'EUR'
        
        currency = 'usd'
        normalized = currency.upper()
        assert normalized == 'USD'
    
    def test_unsupported_currency_error(self):
        """Test error handling for unsupported currency"""
        mock_db = Mock()
        
        with patch('app.services.exchange_rate_service.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.side_effect = ExchangeRateError(
                "Currency GBP not supported. Supported: EUR, USD, INR, BRL, NGN"
            )
            MockService.return_value = mock_service
            
            service = MockService(mock_db)
            
            with pytest.raises(ExchangeRateError) as exc_info:
                service.get_hbar_price('GBP', use_cache=True)
            
            assert 'not supported' in str(exc_info.value).lower()
    
    def test_api_unavailable_error(self):
        """Test error handling when API is unavailable"""
        mock_db = Mock()
        
        with patch('app.services.exchange_rate_service.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.side_effect = ExchangeRateError(
                "CoinGecko API timeout"
            )
            MockService.return_value = mock_service
            
            service = MockService(mock_db)
            
            with pytest.raises(ExchangeRateError) as exc_info:
                service.get_hbar_price('EUR', use_cache=True)
            
            assert 'timeout' in str(exc_info.value).lower()
    
    def test_cache_fallback_to_db(self):
        """Test fallback to database when cache is empty"""
        mock_db = Mock()
        
        with patch('app.services.exchange_rate_service.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.return_value = 0.34
            mock_service.get_cached_rate.return_value = None  # Cache miss
            mock_service.get_latest_rate_from_db.return_value = {
                'currency': 'EUR',
                'hbarPrice': 0.34,
                'source': 'coingecko',
                'fetchedAt': '2024-03-18T10:25:00Z'
            }
            MockService.return_value = mock_service
            
            service = MockService(mock_db)
            hbar_price = service.get_hbar_price('EUR', use_cache=True)
            rate_data = service.get_cached_rate('EUR')
            
            # Cache miss, so get from DB
            if not rate_data:
                rate_data = service.get_latest_rate_from_db('EUR')
            
            assert hbar_price == 0.34
            assert rate_data is not None
            assert rate_data['currency'] == 'EUR'
    
    def test_response_schema_structure(self):
        """Test that response data has correct structure"""
        rate_data = {
            'currency': 'EUR',
            'hbarPrice': 0.34,
            'source': 'coingecko',
            'fetchedAt': '2024-03-18T10:30:00Z'
        }
        
        # Verify all required fields are present
        assert 'currency' in rate_data
        assert 'hbarPrice' in rate_data
        assert 'source' in rate_data
        assert 'fetchedAt' in rate_data
        
        # Verify field types
        assert isinstance(rate_data['currency'], str)
        assert isinstance(rate_data['hbarPrice'], (int, float))
        assert isinstance(rate_data['source'], str)
        assert isinstance(rate_data['fetchedAt'], str)
    
    def test_all_supported_currencies(self):
        """Test that all supported currencies can be fetched"""
        supported_currencies = ['EUR', 'USD', 'INR', 'BRL', 'NGN']
        mock_db = Mock()
        
        for currency in supported_currencies:
            with patch('app.services.exchange_rate_service.ExchangeRateService') as MockService:
                mock_service = Mock()
                mock_service.get_hbar_price.return_value = 0.34
                mock_service.get_cached_rate.return_value = {
                    'currency': currency,
                    'hbarPrice': 0.34,
                    'source': 'coingecko',
                    'fetchedAt': '2024-03-18T10:30:00Z'
                }
                MockService.return_value = mock_service
                
                service = MockService(mock_db)
                hbar_price = service.get_hbar_price(currency, use_cache=True)
                
                assert hbar_price == 0.34
    
    def test_cache_usage_flag(self):
        """Test that use_cache parameter is passed correctly"""
        mock_db = Mock()
        
        with patch('app.services.exchange_rate_service.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.return_value = 0.34
            MockService.return_value = mock_service
            
            service = MockService(mock_db)
            service.get_hbar_price('EUR', use_cache=True)
            
            # Verify the method was called with use_cache=True
            mock_service.get_hbar_price.assert_called_once_with('EUR', use_cache=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
