"""
Test HBAR Amount Calculation

Tests for Task 16.5: Calculate HBAR amount from fiat bill amount
Requirements: FR-5.4, FR-6.2, US-7
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.exchange_rate_service import (
    ExchangeRateService,
    ExchangeRateError
)


class TestHBARCalculation:
    """Test HBAR amount calculation from fiat amounts"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create ExchangeRateService instance"""
        return ExchangeRateService(mock_db)
    
    def test_calculate_hbar_amount_eur(self, service):
        """Test HBAR calculation for EUR"""
        # Mock get_hbar_price to return 0.34 EUR per HBAR
        with patch.object(service, 'get_hbar_price', return_value=0.34):
            result = service.calculate_hbar_amount(85.40, 'EUR')
            
            # Verify calculation: 85.40 / 0.34 = 251.17647...
            assert result['fiat_amount'] == 85.40
            assert result['currency'] == 'EUR'
            assert result['hbar_price'] == 0.34
            assert result['hbar_amount'] == pytest.approx(251.17647, rel=1e-5)
            assert result['hbar_amount_rounded'] == 251.17647059
            assert result['buffer_applied'] is False
            assert result['buffer_percentage'] == 0.0
            assert 'exchange_rate_timestamp' in result
    
    def test_calculate_hbar_amount_usd(self, service):
        """Test HBAR calculation for USD"""
        with patch.object(service, 'get_hbar_price', return_value=0.38):
            result = service.calculate_hbar_amount(120.50, 'USD')
            
            # Verify calculation: 120.50 / 0.38 = 317.10526...
            assert result['fiat_amount'] == 120.50
            assert result['currency'] == 'USD'
            assert result['hbar_price'] == 0.38
            assert result['hbar_amount'] == pytest.approx(317.10526, rel=1e-5)
            assert result['hbar_amount_rounded'] == 317.10526316
            assert result['buffer_applied'] is False
    
    def test_calculate_hbar_amount_inr(self, service):
        """Test HBAR calculation for INR"""
        with patch.object(service, 'get_hbar_price', return_value=28.5):
            result = service.calculate_hbar_amount(450.00, 'INR')
            
            # Verify calculation: 450.00 / 28.5 = 15.78947...
            assert result['fiat_amount'] == 450.00
            assert result['currency'] == 'INR'
            assert result['hbar_price'] == 28.5
            assert result['hbar_amount'] == pytest.approx(15.78947, rel=1e-5)
            assert result['hbar_amount_rounded'] == 15.78947368
    
    def test_calculate_hbar_amount_brl(self, service):
        """Test HBAR calculation for BRL"""
        with patch.object(service, 'get_hbar_price', return_value=1.75):
            result = service.calculate_hbar_amount(95.00, 'BRL')
            
            # Verify calculation: 95.00 / 1.75 = 54.28571...
            assert result['fiat_amount'] == 95.00
            assert result['currency'] == 'BRL'
            assert result['hbar_price'] == 1.75
            assert result['hbar_amount'] == pytest.approx(54.28571, rel=1e-5)
            assert result['hbar_amount_rounded'] == 54.28571429
    
    def test_calculate_hbar_amount_ngn(self, service):
        """Test HBAR calculation for NGN"""
        with patch.object(service, 'get_hbar_price', return_value=540.0):
            result = service.calculate_hbar_amount(12500.00, 'NGN')
            
            # Verify calculation: 12500.00 / 540.0 = 23.14814...
            assert result['fiat_amount'] == 12500.00
            assert result['currency'] == 'NGN'
            assert result['hbar_price'] == 540.0
            assert result['hbar_amount'] == pytest.approx(23.14814, rel=1e-5)
            assert result['hbar_amount_rounded'] == 23.14814815
    
    def test_calculate_hbar_amount_with_buffer(self, service):
        """Test HBAR calculation with 2% volatility buffer (FR-6.13)"""
        with patch.object(service, 'get_hbar_price', return_value=0.34):
            result = service.calculate_hbar_amount(
                85.40,
                'EUR',
                apply_buffer=True,
                buffer_percentage=2.0
            )
            
            # With 2% buffer: 85.40 * 1.02 = 87.108
            # HBAR amount: 87.108 / 0.34 = 256.20000
            assert result['fiat_amount'] == 85.40
            assert result['buffer_applied'] is True
            assert result['buffer_percentage'] == 2.0
            assert result['hbar_amount'] == pytest.approx(256.2, rel=1e-5)
            assert result['hbar_amount_rounded'] == 256.2
    
    def test_calculate_hbar_amount_custom_buffer(self, service):
        """Test HBAR calculation with custom buffer percentage"""
        with patch.object(service, 'get_hbar_price', return_value=0.34):
            result = service.calculate_hbar_amount(
                100.00,
                'EUR',
                apply_buffer=True,
                buffer_percentage=5.0
            )
            
            # With 5% buffer: 100.00 * 1.05 = 105.00
            # HBAR amount: 105.00 / 0.34 = 308.82352...
            assert result['fiat_amount'] == 100.00
            assert result['buffer_applied'] is True
            assert result['buffer_percentage'] == 5.0
            assert result['hbar_amount'] == pytest.approx(308.82352, rel=1e-5)
    
    def test_calculate_hbar_amount_lowercase_currency(self, service):
        """Test that lowercase currency codes are handled"""
        with patch.object(service, 'get_hbar_price', return_value=0.34):
            result = service.calculate_hbar_amount(85.40, 'eur')
            
            assert result['currency'] == 'EUR'
            assert result['hbar_amount_rounded'] == 251.17647059
    
    def test_calculate_hbar_amount_uses_cache(self, service):
        """Test that calculation uses cached exchange rates by default"""
        with patch.object(service, 'get_hbar_price', return_value=0.34) as mock_get:
            service.calculate_hbar_amount(85.40, 'EUR')
            
            # Verify get_hbar_price was called with use_cache=True
            mock_get.assert_called_once_with('EUR', True)
    
    def test_calculate_hbar_amount_bypass_cache(self, service):
        """Test that calculation can bypass cache"""
        with patch.object(service, 'get_hbar_price', return_value=0.34) as mock_get:
            service.calculate_hbar_amount(85.40, 'EUR', use_cache=False)
            
            # Verify get_hbar_price was called with use_cache=False
            mock_get.assert_called_once_with('EUR', False)
    
    def test_calculate_hbar_amount_precision(self, service):
        """Test that HBAR amount is rounded to 8 decimal places"""
        with patch.object(service, 'get_hbar_price', return_value=0.333333):
            result = service.calculate_hbar_amount(100.00, 'EUR')
            
            # Verify 8 decimal places
            hbar_str = str(result['hbar_amount_rounded'])
            if '.' in hbar_str:
                decimals = len(hbar_str.split('.')[1])
                assert decimals <= 8
    
    def test_calculate_hbar_amount_invalid_currency(self, service):
        """Test error handling for unsupported currency"""
        with patch.object(service, 'get_hbar_price', side_effect=ExchangeRateError("Currency XYZ not supported")):
            with pytest.raises(ExchangeRateError, match="Currency XYZ not supported"):
                service.calculate_hbar_amount(100.00, 'XYZ')
    
    def test_calculate_hbar_amount_zero_amount(self, service):
        """Test error handling for zero fiat amount"""
        with pytest.raises(ValueError, match="Fiat amount must be positive"):
            service.calculate_hbar_amount(0.00, 'EUR')
    
    def test_calculate_hbar_amount_negative_amount(self, service):
        """Test error handling for negative fiat amount"""
        with pytest.raises(ValueError, match="Fiat amount must be positive"):
            service.calculate_hbar_amount(-50.00, 'EUR')
    
    def test_calculate_hbar_amount_api_failure(self, service):
        """Test error handling when exchange rate API fails"""
        with patch.object(service, 'get_hbar_price', side_effect=ExchangeRateError("API unavailable")):
            with pytest.raises(ExchangeRateError, match="API unavailable"):
                service.calculate_hbar_amount(85.40, 'EUR')
    
    def test_calculate_hbar_amount_small_amount(self, service):
        """Test calculation for small fiat amounts"""
        with patch.object(service, 'get_hbar_price', return_value=0.34):
            result = service.calculate_hbar_amount(5.00, 'EUR')
            
            # Verify calculation: 5.00 / 0.34 = 14.70588...
            assert result['fiat_amount'] == 5.00
            assert result['hbar_amount'] == pytest.approx(14.70588, rel=1e-5)
            assert result['hbar_amount_rounded'] == 14.70588235
    
    def test_calculate_hbar_amount_large_amount(self, service):
        """Test calculation for large fiat amounts"""
        with patch.object(service, 'get_hbar_price', return_value=0.34):
            result = service.calculate_hbar_amount(10000.00, 'EUR')
            
            # Verify calculation: 10000.00 / 0.34 = 29411.76470...
            assert result['fiat_amount'] == 10000.00
            assert result['hbar_amount'] == pytest.approx(29411.76470, rel=1e-5)
            assert result['hbar_amount_rounded'] == 29411.76470588


class TestHBARCalculationIntegration:
    """Integration tests with real exchange rate fetching"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = Mock(spec=Session)
        db.execute = Mock()
        db.commit = Mock()
        db.rollback = Mock()
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create ExchangeRateService instance"""
        return ExchangeRateService(mock_db)
    
    def test_calculate_hbar_amount_with_real_fetch(self, service):
        """Test HBAR calculation with mocked API fetch"""
        # Mock the fetch_from_api method
        with patch.object(service, 'fetch_from_api', return_value=0.34):
            with patch.object(service, 'get_cached_rate', return_value=None):
                with patch.object(service, 'cache_rate', return_value=True):
                    with patch.object(service, 'store_in_db', return_value=True):
                        result = service.calculate_hbar_amount(85.40, 'EUR')
                        
                        assert result['fiat_amount'] == 85.40
                        assert result['currency'] == 'EUR'
                        assert result['hbar_price'] == 0.34
                        assert result['hbar_amount_rounded'] == 251.17647059


class TestHBARCalculationExamples:
    """Test examples from requirements document"""
    
    @pytest.fixture
    def service(self):
        """Create ExchangeRateService instance with mock DB"""
        return ExchangeRateService(Mock(spec=Session))
    
    def test_spain_example(self, service):
        """Test Spain example: €85.40 at €0.34/HBAR = 251.18 HBAR"""
        with patch.object(service, 'get_hbar_price', return_value=0.34):
            result = service.calculate_hbar_amount(85.40, 'EUR')
            
            assert result['fiat_amount'] == 85.40
            assert result['currency'] == 'EUR'
            assert result['hbar_amount_rounded'] == pytest.approx(251.18, rel=0.01)
    
    def test_usa_example(self, service):
        """Test USA example: $120.50 at $0.38/HBAR"""
        with patch.object(service, 'get_hbar_price', return_value=0.38):
            result = service.calculate_hbar_amount(120.50, 'USD')
            
            assert result['fiat_amount'] == 120.50
            assert result['currency'] == 'USD'
            # 120.50 / 0.38 = 317.11 HBAR
            assert result['hbar_amount_rounded'] == pytest.approx(317.11, rel=0.01)
    
    def test_india_example(self, service):
        """Test India example: ₹450.00 at ₹28.5/HBAR"""
        with patch.object(service, 'get_hbar_price', return_value=28.5):
            result = service.calculate_hbar_amount(450.00, 'INR')
            
            assert result['fiat_amount'] == 450.00
            assert result['currency'] == 'INR'
            # 450.00 / 28.5 = 15.79 HBAR
            assert result['hbar_amount_rounded'] == pytest.approx(15.79, rel=0.01)
    
    def test_brazil_example(self, service):
        """Test Brazil example: R$95.00 at R$1.75/HBAR"""
        with patch.object(service, 'get_hbar_price', return_value=1.75):
            result = service.calculate_hbar_amount(95.00, 'BRL')
            
            assert result['fiat_amount'] == 95.00
            assert result['currency'] == 'BRL'
            # 95.00 / 1.75 = 54.29 HBAR
            assert result['hbar_amount_rounded'] == pytest.approx(54.29, rel=0.01)
    
    def test_nigeria_example(self, service):
        """Test Nigeria example: ₦12,500 at ₦540/HBAR"""
        with patch.object(service, 'get_hbar_price', return_value=540.0):
            result = service.calculate_hbar_amount(12500.00, 'NGN')
            
            assert result['fiat_amount'] == 12500.00
            assert result['currency'] == 'NGN'
            # 12500.00 / 540.0 = 23.15 HBAR
            assert result['hbar_amount_rounded'] == pytest.approx(23.15, rel=0.01)
