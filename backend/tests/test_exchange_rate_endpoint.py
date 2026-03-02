"""
Test Exchange Rate Endpoint
Tests for GET /api/exchange-rate/{currency}

Requirements: FR-5.2, US-7
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from main import app
from app.services.exchange_rate_service import ExchangeRateError


client = TestClient(app)


class TestExchangeRateEndpoint:
    """Test suite for exchange rate endpoint"""
    
    def test_get_exchange_rate_success_eur(self):
        """Test successful EUR exchange rate fetch"""
        with patch('app.api.endpoints.exchange_rates.ExchangeRateService') as MockService:
            # Mock service
            mock_service = Mock()
            mock_service.get_hbar_price.return_value = 0.34
            mock_service.get_cached_rate.return_value = {
                'currency': 'EUR',
                'hbarPrice': 0.34,
                'source': 'coingecko',
                'fetchedAt': '2024-03-18T10:30:00Z'
            }
            MockService.return_value = mock_service
            
            # Make request
            response = client.get("/api/exchange-rate/EUR")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data['currency'] == 'EUR'
            assert data['hbarPrice'] == 0.34
            assert data['source'] == 'coingecko'
            assert 'fetchedAt' in data
    
    def test_get_exchange_rate_success_usd(self):
        """Test successful USD exchange rate fetch"""
        with patch('app.api.endpoints.exchange_rates.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.return_value = 0.36
            mock_service.get_cached_rate.return_value = {
                'currency': 'USD',
                'hbarPrice': 0.36,
                'source': 'coingecko',
                'fetchedAt': '2024-03-18T10:30:00Z'
            }
            MockService.return_value = mock_service
            
            response = client.get("/api/exchange-rate/USD")
            
            assert response.status_code == 200
            data = response.json()
            assert data['currency'] == 'USD'
            assert data['hbarPrice'] == 0.36
    
    def test_get_exchange_rate_success_inr(self):
        """Test successful INR exchange rate fetch"""
        with patch('app.api.endpoints.exchange_rates.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.return_value = 28.5
            mock_service.get_cached_rate.return_value = {
                'currency': 'INR',
                'hbarPrice': 28.5,
                'source': 'coingecko',
                'fetchedAt': '2024-03-18T10:30:00Z'
            }
            MockService.return_value = mock_service
            
            response = client.get("/api/exchange-rate/INR")
            
            assert response.status_code == 200
            data = response.json()
            assert data['currency'] == 'INR'
            assert data['hbarPrice'] == 28.5
    
    def test_get_exchange_rate_success_brl(self):
        """Test successful BRL exchange rate fetch"""
        with patch('app.api.endpoints.exchange_rates.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.return_value = 1.75
            mock_service.get_cached_rate.return_value = {
                'currency': 'BRL',
                'hbarPrice': 1.75,
                'source': 'coingecko',
                'fetchedAt': '2024-03-18T10:30:00Z'
            }
            MockService.return_value = mock_service
            
            response = client.get("/api/exchange-rate/BRL")
            
            assert response.status_code == 200
            data = response.json()
            assert data['currency'] == 'BRL'
            assert data['hbarPrice'] == 1.75
    
    def test_get_exchange_rate_success_ngn(self):
        """Test successful NGN exchange rate fetch"""
        with patch('app.api.endpoints.exchange_rates.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.return_value = 540.0
            mock_service.get_cached_rate.return_value = {
                'currency': 'NGN',
                'hbarPrice': 540.0,
                'source': 'coingecko',
                'fetchedAt': '2024-03-18T10:30:00Z'
            }
            MockService.return_value = mock_service
            
            response = client.get("/api/exchange-rate/NGN")
            
            assert response.status_code == 200
            data = response.json()
            assert data['currency'] == 'NGN'
            assert data['hbarPrice'] == 540.0
    
    def test_get_exchange_rate_lowercase_currency(self):
        """Test that lowercase currency codes are normalized"""
        with patch('app.api.endpoints.exchange_rates.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.return_value = 0.34
            mock_service.get_cached_rate.return_value = {
                'currency': 'EUR',
                'hbarPrice': 0.34,
                'source': 'coingecko',
                'fetchedAt': '2024-03-18T10:30:00Z'
            }
            MockService.return_value = mock_service
            
            response = client.get("/api/exchange-rate/eur")
            
            assert response.status_code == 200
            data = response.json()
            assert data['currency'] == 'EUR'
    
    def test_get_exchange_rate_unsupported_currency(self):
        """Test error for unsupported currency"""
        with patch('app.api.endpoints.exchange_rates.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.side_effect = ExchangeRateError(
                "Currency GBP not supported. Supported: EUR, USD, INR, BRL, NGN"
            )
            MockService.return_value = mock_service
            
            response = client.get("/api/exchange-rate/GBP")
            
            assert response.status_code == 404
            data = response.json()
            assert 'not supported' in data['detail'].lower()
    
    def test_get_exchange_rate_api_unavailable(self):
        """Test error when exchange rate API is unavailable"""
        with patch('app.api.endpoints.exchange_rates.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.side_effect = ExchangeRateError(
                "CoinGecko API timeout"
            )
            MockService.return_value = mock_service
            
            response = client.get("/api/exchange-rate/EUR")
            
            assert response.status_code == 503
            data = response.json()
            assert 'unavailable' in data['detail'].lower()
    
    def test_get_exchange_rate_cache_hit(self):
        """Test that cached rates are returned"""
        with patch('app.api.endpoints.exchange_rates.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.return_value = 0.34
            mock_service.get_cached_rate.return_value = {
                'currency': 'EUR',
                'hbarPrice': 0.34,
                'source': 'coingecko',
                'fetchedAt': '2024-03-18T10:30:00Z'
            }
            MockService.return_value = mock_service
            
            response = client.get("/api/exchange-rate/EUR")
            
            assert response.status_code == 200
            # Verify get_hbar_price was called with use_cache=True
            mock_service.get_hbar_price.assert_called_once_with('EUR', use_cache=True)
    
    def test_get_exchange_rate_fallback_to_db(self):
        """Test fallback to database when cache is empty"""
        with patch('app.api.endpoints.exchange_rates.ExchangeRateService') as MockService:
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
            
            response = client.get("/api/exchange-rate/EUR")
            
            assert response.status_code == 200
            data = response.json()
            assert data['currency'] == 'EUR'
            assert data['hbarPrice'] == 0.34
            # Verify fallback to DB was called
            mock_service.get_latest_rate_from_db.assert_called_once_with('EUR')
    
    def test_get_exchange_rate_response_schema(self):
        """Test that response matches expected schema"""
        with patch('app.api.endpoints.exchange_rates.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.return_value = 0.34
            mock_service.get_cached_rate.return_value = {
                'currency': 'EUR',
                'hbarPrice': 0.34,
                'source': 'coingecko',
                'fetchedAt': '2024-03-18T10:30:00Z'
            }
            MockService.return_value = mock_service
            
            response = client.get("/api/exchange-rate/EUR")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify all required fields are present
            assert 'currency' in data
            assert 'hbarPrice' in data
            assert 'source' in data
            assert 'fetchedAt' in data
            
            # Verify field types
            assert isinstance(data['currency'], str)
            assert isinstance(data['hbarPrice'], (int, float))
            assert isinstance(data['source'], str)
            assert isinstance(data['fetchedAt'], str)
    
    def test_get_exchange_rate_internal_error(self):
        """Test handling of unexpected internal errors"""
        with patch('app.api.endpoints.exchange_rates.ExchangeRateService') as MockService:
            mock_service = Mock()
            mock_service.get_hbar_price.side_effect = Exception("Unexpected error")
            MockService.return_value = mock_service
            
            response = client.get("/api/exchange-rate/EUR")
            
            assert response.status_code == 500
            data = response.json()
            assert 'internal server error' in data['detail'].lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
