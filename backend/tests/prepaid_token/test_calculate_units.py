"""
Unit tests for PrepaidTokenService.calculate_units_from_fiat method

Tests the units calculation from fiat amount functionality.
"""
import pytest
from unittest.mock import Mock, patch

from app.services.prepaid_token_service import PrepaidTokenService, PrepaidTokenError
from app.services.tariff_service import TariffNotFoundError


class TestCalculateUnitsFromFiat:
    """Test calculate_units_from_fiat method"""
    
    def test_flat_rate_calculation(self):
        """Test units calculation with flat rate tariff"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock tariff data
        mock_tariff = {
            'tariff_id': 'test-tariff-id',
            'country_code': 'ES',
            'utility_provider': 'Iberdrola',
            'currency': 'EUR',
            'rate_structure': {
                'type': 'flat',
                'rate': 0.40
            }
        }
        
        with patch('app.services.prepaid_token_service.get_tariff', return_value=mock_tariff):
            # Execute
            result = service.calculate_units_from_fiat(
                amount_fiat=50.0,
                country_code='ES',
                utility_provider='Iberdrola'
            )
            
            # Verify
            assert result['units_kwh'] == 125.0  # 50 / 0.40 = 125
            assert result['tariff_rate'] == 0.40
            assert result['currency'] == 'EUR'
    
    def test_tiered_rate_calculation(self):
        """Test units calculation with tiered rate tariff (uses first tier)"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock tariff data with tiers
        mock_tariff = {
            'tariff_id': 'test-tariff-id',
            'country_code': 'US',
            'utility_provider': 'PG&E',
            'currency': 'USD',
            'rate_structure': {
                'type': 'tiered',
                'tiers': [
                    {'threshold': 0, 'price': 0.15},
                    {'threshold': 100, 'price': 0.20},
                    {'threshold': 300, 'price': 0.25}
                ]
            }
        }
        
        with patch('app.services.prepaid_token_service.get_tariff', return_value=mock_tariff):
            # Execute
            result = service.calculate_units_from_fiat(
                amount_fiat=30.0,
                country_code='US',
                utility_provider='PG&E'
            )
            
            # Verify - uses first tier rate
            assert result['units_kwh'] == 200.0  # 30 / 0.15 = 200
            assert result['tariff_rate'] == 0.15
            assert result['currency'] == 'USD'
    
    def test_time_of_use_calculation(self):
        """Test units calculation with time-of-use tariff (uses average rate)"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock tariff data with time-of-use periods
        mock_tariff = {
            'tariff_id': 'test-tariff-id',
            'country_code': 'IN',
            'utility_provider': 'TATA Power',
            'currency': 'INR',
            'rate_structure': {
                'type': 'time_of_use',
                'periods': [
                    {'name': 'peak', 'price': 8.0},
                    {'name': 'off_peak', 'price': 4.0}
                ]
            }
        }
        
        with patch('app.services.prepaid_token_service.get_tariff', return_value=mock_tariff):
            # Execute
            result = service.calculate_units_from_fiat(
                amount_fiat=600.0,
                country_code='IN',
                utility_provider='TATA Power'
            )
            
            # Verify - uses average rate (8.0 + 4.0) / 2 = 6.0
            assert result['units_kwh'] == 100.0  # 600 / 6.0 = 100
            assert result['tariff_rate'] == 6.0
            assert result['currency'] == 'INR'
    
    def test_zero_amount_calculation(self):
        """Test that zero amount returns zero units"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        mock_tariff = {
            'tariff_id': 'test-tariff-id',
            'country_code': 'ES',
            'utility_provider': 'Iberdrola',
            'currency': 'EUR',
            'rate_structure': {
                'type': 'flat',
                'rate': 0.40
            }
        }
        
        with patch('app.services.prepaid_token_service.get_tariff', return_value=mock_tariff):
            # Execute
            result = service.calculate_units_from_fiat(
                amount_fiat=0.0,
                country_code='ES',
                utility_provider='Iberdrola'
            )
            
            # Verify
            assert result['units_kwh'] == 0.0
    
    def test_tariff_not_found_error(self):
        """Test that TariffNotFoundError is raised when tariff doesn't exist"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        with patch('app.services.prepaid_token_service.get_tariff', side_effect=TariffNotFoundError("Tariff not found")):
            # Execute & Verify
            with pytest.raises(TariffNotFoundError):
                service.calculate_units_from_fiat(
                    amount_fiat=50.0,
                    country_code='XX',
                    utility_provider='Unknown'
                )
    
    def test_invalid_tariff_rate_error(self):
        """Test that PrepaidTokenError is raised for invalid tariff rate"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock tariff with zero rate
        mock_tariff = {
            'tariff_id': 'test-tariff-id',
            'country_code': 'ES',
            'utility_provider': 'Iberdrola',
            'currency': 'EUR',
            'rate_structure': {
                'type': 'flat',
                'rate': 0.0  # Invalid rate
            }
        }
        
        with patch('app.services.prepaid_token_service.get_tariff', return_value=mock_tariff):
            # Execute & Verify
            with pytest.raises(PrepaidTokenError, match="Invalid tariff rate"):
                service.calculate_units_from_fiat(
                    amount_fiat=50.0,
                    country_code='ES',
                    utility_provider='Iberdrola'
                )
    
    def test_missing_tiers_error(self):
        """Test that PrepaidTokenError is raised when tiered tariff has no tiers"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock tariff with no tiers
        mock_tariff = {
            'tariff_id': 'test-tariff-id',
            'country_code': 'US',
            'utility_provider': 'PG&E',
            'currency': 'USD',
            'rate_structure': {
                'type': 'tiered',
                'tiers': []  # Empty tiers
            }
        }
        
        with patch('app.services.prepaid_token_service.get_tariff', return_value=mock_tariff):
            # Execute & Verify
            with pytest.raises(PrepaidTokenError, match="No tiers defined"):
                service.calculate_units_from_fiat(
                    amount_fiat=50.0,
                    country_code='US',
                    utility_provider='PG&E'
                )
    
    def test_unknown_tariff_type_error(self):
        """Test that PrepaidTokenError is raised for unknown tariff type"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock tariff with unknown type
        mock_tariff = {
            'tariff_id': 'test-tariff-id',
            'country_code': 'ES',
            'utility_provider': 'Iberdrola',
            'currency': 'EUR',
            'rate_structure': {
                'type': 'unknown_type',
                'rate': 0.40
            }
        }
        
        with patch('app.services.prepaid_token_service.get_tariff', return_value=mock_tariff):
            # Execute & Verify
            with pytest.raises(PrepaidTokenError, match="Unknown tariff type"):
                service.calculate_units_from_fiat(
                    amount_fiat=50.0,
                    country_code='ES',
                    utility_provider='Iberdrola'
                )
    
    def test_precision_handling(self):
        """Test that decimal precision is handled correctly"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock tariff with rate that causes repeating decimal
        mock_tariff = {
            'tariff_id': 'test-tariff-id',
            'country_code': 'ES',
            'utility_provider': 'Iberdrola',
            'currency': 'EUR',
            'rate_structure': {
                'type': 'flat',
                'rate': 0.333333  # Repeating decimal
            }
        }
        
        with patch('app.services.prepaid_token_service.get_tariff', return_value=mock_tariff):
            # Execute
            result = service.calculate_units_from_fiat(
                amount_fiat=100.0,
                country_code='ES',
                utility_provider='Iberdrola'
            )
            
            # Verify - should be rounded to 2 decimal places
            assert isinstance(result['units_kwh'], float)
            assert result['units_kwh'] == 300.0  # 100 / 0.333333 ≈ 300.00 (rounded to 2 decimals)
            assert isinstance(result['tariff_rate'], float)
            # Tariff rate should be rounded to 6 decimal places
            assert result['tariff_rate'] == 0.333333
