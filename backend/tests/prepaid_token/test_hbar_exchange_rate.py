"""
Unit tests for HBAR exchange rate fetching in PrepaidTokenService

Tests the integration with ExchangeRateService for:
- Fetching HBAR exchange rates
- Calculating HBAR amounts from fiat
- Cache usage
- Error handling

Requirements: FR-8.1, US-13
Spec: prepaid-smart-meter-mvp
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.prepaid_token_service import PrepaidTokenService, PrepaidTokenError


class TestHBARExchangeRate:
    """Test HBAR exchange rate fetching functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create PrepaidTokenService instance"""
        return PrepaidTokenService(db=mock_db)
    
    def test_get_hbar_exchange_rate_success(self, service, mock_db):
        """Test successful HBAR exchange rate fetch"""
        # Mock get_hbar_price function
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            mock_get_price.return_value = 0.34
            
            # Call method
            rate = service.get_hbar_exchange_rate(currency='EUR', use_cache=True)
            
            # Verify
            assert rate == 0.34
            mock_get_price.assert_called_once_with(
                db=mock_db,
                currency='EUR',
                use_cache=True
            )
    
    def test_get_hbar_exchange_rate_different_currencies(self, service, mock_db):
        """Test exchange rate fetch for different currencies"""
        test_cases = [
            ('EUR', 0.34),
            ('USD', 0.40),
            ('INR', 33.50),
            ('BRL', 2.10),
            ('NGN', 165.00)
        ]
        
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            for currency, expected_rate in test_cases:
                mock_get_price.return_value = expected_rate
                
                rate = service.get_hbar_exchange_rate(currency=currency)
                
                assert rate == expected_rate
                assert mock_get_price.call_args[1]['currency'] == currency
    
    def test_get_hbar_exchange_rate_cache_disabled(self, service, mock_db):
        """Test exchange rate fetch with cache disabled"""
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            mock_get_price.return_value = 0.34
            
            rate = service.get_hbar_exchange_rate(currency='EUR', use_cache=False)
            
            assert rate == 0.34
            mock_get_price.assert_called_once_with(
                db=mock_db,
                currency='EUR',
                use_cache=False
            )
    
    def test_get_hbar_exchange_rate_error(self, service, mock_db):
        """Test exchange rate fetch error handling"""
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            mock_get_price.side_effect = Exception("API unavailable")
            
            with pytest.raises(PrepaidTokenError) as exc_info:
                service.get_hbar_exchange_rate(currency='EUR')
            
            assert "Failed to fetch exchange rate" in str(exc_info.value)
    
    def test_calculate_hbar_amount_success(self, service, mock_db):
        """Test successful HBAR amount calculation"""
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            mock_get_price.return_value = 0.34  # 1 HBAR = 0.34 EUR
            
            result = service.calculate_hbar_amount(
                amount_fiat=50.0,
                currency='EUR',
                use_cache=True
            )
            
            # Verify calculation: 50 / 0.34 = 147.05882353 HBAR
            assert result['amount_hbar'] == pytest.approx(147.05882353, rel=1e-6)
            assert result['exchange_rate'] == 0.34
            assert result['currency'] == 'EUR'
    
    def test_calculate_hbar_amount_different_amounts(self, service, mock_db):
        """Test HBAR calculation for different fiat amounts"""
        test_cases = [
            (10.0, 0.34, 29.41176471),   # 10 EUR
            (50.0, 0.34, 147.05882353),  # 50 EUR
            (100.0, 0.40, 250.0),        # 100 USD
            (500.0, 33.50, 14.92537313), # 500 INR
            (1000.0, 2.10, 476.19047619) # 1000 BRL
        ]
        
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            for amount_fiat, hbar_price, expected_hbar in test_cases:
                mock_get_price.return_value = hbar_price
                
                result = service.calculate_hbar_amount(
                    amount_fiat=amount_fiat,
                    currency='EUR'
                )
                
                assert result['amount_hbar'] == pytest.approx(expected_hbar, rel=1e-6)
                assert result['exchange_rate'] == hbar_price
    
    def test_calculate_hbar_amount_precision(self, service, mock_db):
        """Test HBAR amount calculation precision (8 decimal places)"""
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            mock_get_price.return_value = 0.34567890
            
            result = service.calculate_hbar_amount(
                amount_fiat=12.34,
                currency='EUR'
            )
            
            # Result should be rounded to 8 decimal places
            assert isinstance(result['amount_hbar'], float)
            # Check that we have at most 8 decimal places
            decimal_str = str(result['amount_hbar']).split('.')
            if len(decimal_str) > 1:
                assert len(decimal_str[1]) <= 8
    
    def test_calculate_hbar_amount_cache_usage(self, service, mock_db):
        """Test that cache parameter is passed correctly"""
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            mock_get_price.return_value = 0.34
            
            # Test with cache enabled
            service.calculate_hbar_amount(
                amount_fiat=50.0,
                currency='EUR',
                use_cache=True
            )
            assert mock_get_price.call_args[1]['use_cache'] is True
            
            # Test with cache disabled
            service.calculate_hbar_amount(
                amount_fiat=50.0,
                currency='EUR',
                use_cache=False
            )
            assert mock_get_price.call_args[1]['use_cache'] is False
    
    def test_calculate_hbar_amount_error_handling(self, service, mock_db):
        """Test error handling in HBAR calculation"""
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            mock_get_price.side_effect = Exception("Exchange rate service down")
            
            with pytest.raises(PrepaidTokenError) as exc_info:
                service.calculate_hbar_amount(
                    amount_fiat=50.0,
                    currency='EUR'
                )
            
            # Error can be from either get_hbar_exchange_rate or calculate_hbar_amount
            assert "Failed to fetch exchange rate" in str(exc_info.value) or \
                   "Failed to calculate HBAR amount" in str(exc_info.value)
    
    def test_calculate_hbar_amount_zero_amount(self, service, mock_db):
        """Test HBAR calculation with zero fiat amount"""
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            mock_get_price.return_value = 0.34
            
            result = service.calculate_hbar_amount(
                amount_fiat=0.0,
                currency='EUR'
            )
            
            assert result['amount_hbar'] == 0.0
    
    def test_calculate_hbar_amount_small_amount(self, service, mock_db):
        """Test HBAR calculation with very small fiat amount"""
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            mock_get_price.return_value = 0.34
            
            result = service.calculate_hbar_amount(
                amount_fiat=0.01,  # 1 cent
                currency='EUR'
            )
            
            # 0.01 / 0.34 = 0.02941176 HBAR
            assert result['amount_hbar'] == pytest.approx(0.02941176, rel=1e-6)
    
    def test_calculate_hbar_amount_large_amount(self, service, mock_db):
        """Test HBAR calculation with large fiat amount"""
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            mock_get_price.return_value = 0.34
            
            result = service.calculate_hbar_amount(
                amount_fiat=10000.0,  # 10,000 EUR
                currency='EUR'
            )
            
            # 10000 / 0.34 = 29411.76470588 HBAR
            assert result['amount_hbar'] == pytest.approx(29411.76470588, rel=1e-6)
    
    def test_integration_with_create_token(self, service, mock_db):
        """Test that exchange rate methods integrate with create_token flow"""
        # This is a conceptual test showing how the methods would be used
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            mock_get_price.return_value = 0.34
            
            # Step 1: Calculate HBAR amount needed
            hbar_calc = service.calculate_hbar_amount(
                amount_fiat=50.0,
                currency='EUR'
            )
            
            assert hbar_calc['amount_hbar'] > 0
            assert hbar_calc['exchange_rate'] == 0.34
            
            # Step 2: These values would be passed to create_token
            # (actual create_token test would mock database operations)
            assert 'amount_hbar' in hbar_calc
            assert 'exchange_rate' in hbar_calc
            assert 'currency' in hbar_calc


class TestHBARExchangeRateEdgeCases:
    """Test edge cases and error scenarios"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        return PrepaidTokenService(db=mock_db)
    
    def test_exchange_rate_with_high_volatility(self, service, mock_db):
        """Test handling of rapidly changing exchange rates"""
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            # Simulate volatile rates
            rates = [0.30, 0.35, 0.32, 0.38]
            
            for rate in rates:
                mock_get_price.return_value = rate
                result = service.calculate_hbar_amount(
                    amount_fiat=50.0,
                    currency='EUR'
                )
                
                expected_hbar = 50.0 / rate
                assert result['amount_hbar'] == pytest.approx(expected_hbar, rel=1e-6)
    
    def test_exchange_rate_decimal_precision(self, service, mock_db):
        """Test that Decimal precision is maintained throughout calculation"""
        with patch('app.services.prepaid_token_service.get_hbar_price') as mock_get_price:
            # Use a rate with many decimal places
            mock_get_price.return_value = 0.123456789
            
            result = service.calculate_hbar_amount(
                amount_fiat=99.99,
                currency='EUR'
            )
            
            # Verify calculation is accurate
            expected = 99.99 / 0.123456789
            assert result['amount_hbar'] == pytest.approx(expected, rel=1e-6)
