"""
Tests for 2% volatility buffer implementation (Task 16.6)

Requirements:
- FR-6.13: System shall handle exchange rate volatility with 2% buffer
- Risk 8.1.6: HBAR price volatility during payment

This test suite verifies that the 2% volatility buffer is correctly applied
to protect users from price fluctuations during the payment window.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from app.services.exchange_rate_service import ExchangeRateService


class TestVolatilityBuffer:
    """Test suite for 2% volatility buffer functionality"""
    
    def test_buffer_increases_hbar_amount_by_2_percent(self, db_session):
        """
        Test that applying the buffer increases HBAR amount by 2%
        
        Given: A bill of €85.40 and HBAR price of €0.34
        When: Buffer is applied
        Then: HBAR amount should be 2% higher than without buffer
        """
        service = ExchangeRateService(db_session)
        
        # Mock the get_hbar_price method
        service.get_hbar_price = Mock(return_value=0.34)
        
        # Calculate without buffer
        result_no_buffer = service.calculate_hbar_amount(
            fiat_amount=85.40,
            currency='EUR',
            apply_buffer=False
        )
        
        # Calculate with buffer
        result_with_buffer = service.calculate_hbar_amount(
            fiat_amount=85.40,
            currency='EUR',
            apply_buffer=True,
            buffer_percentage=2.0
        )
        
        # Verify buffer was applied
        assert result_with_buffer['buffer_applied'] is True
        assert result_with_buffer['buffer_percentage'] == 2.0
        assert result_no_buffer['buffer_applied'] is False
        
        # Verify HBAR amount increased by 2%
        hbar_no_buffer = result_no_buffer['hbar_amount']
        hbar_with_buffer = result_with_buffer['hbar_amount']
        
        expected_increase = hbar_no_buffer * 0.02
        actual_increase = hbar_with_buffer - hbar_no_buffer
        
        # Allow small floating point difference
        assert abs(actual_increase - expected_increase) < 0.01
        
        # Verify the increase is approximately 2%
        percentage_increase = (hbar_with_buffer - hbar_no_buffer) / hbar_no_buffer * 100
        assert abs(percentage_increase - 2.0) < 0.01
    
    def test_buffer_calculation_formula(self, db_session):
        """
        Test the exact formula: HBAR = (fiat_amount * 1.02) / hbar_price
        
        Given: €100 bill and €0.50 HBAR price
        When: 2% buffer applied
        Then: HBAR = (100 * 1.02) / 0.50 = 204 HBAR
        """
        service = ExchangeRateService(db_session)
        service.get_hbar_price = Mock(return_value=0.50)
        
        result = service.calculate_hbar_amount(
            fiat_amount=100.00,
            currency='EUR',
            apply_buffer=True,
            buffer_percentage=2.0
        )
        
        # Expected: (100 * 1.02) / 0.50 = 204.0
        assert result['hbar_amount_rounded'] == 204.0
        assert result['buffer_applied'] is True
    
    def test_buffer_with_different_currencies(self, db_session):
        """
        Test that buffer works correctly for all supported currencies
        """
        service = ExchangeRateService(db_session)
        
        test_cases = [
            ('EUR', 85.40, 0.34),
            ('USD', 120.50, 0.38),
            ('INR', 450.00, 28.50),
            ('BRL', 95.00, 1.90),
            ('NGN', 12500.00, 425.00)
        ]
        
        for currency, fiat_amount, hbar_price in test_cases:
            service.get_hbar_price = Mock(return_value=hbar_price)
            
            result_no_buffer = service.calculate_hbar_amount(
                fiat_amount=fiat_amount,
                currency=currency,
                apply_buffer=False
            )
            
            result_with_buffer = service.calculate_hbar_amount(
                fiat_amount=fiat_amount,
                currency=currency,
                apply_buffer=True,
                buffer_percentage=2.0
            )
            
            # Verify 2% increase for each currency
            hbar_no_buffer = result_no_buffer['hbar_amount']
            hbar_with_buffer = result_with_buffer['hbar_amount']
            percentage_increase = (hbar_with_buffer - hbar_no_buffer) / hbar_no_buffer * 100
            
            assert abs(percentage_increase - 2.0) < 0.01, \
                f"Buffer not correctly applied for {currency}"
    
    def test_custom_buffer_percentage(self, db_session):
        """
        Test that custom buffer percentages work correctly
        
        While default is 2%, the system should support custom percentages
        """
        service = ExchangeRateService(db_session)
        service.get_hbar_price = Mock(return_value=0.34)
        
        # Test 5% buffer
        result_5_percent = service.calculate_hbar_amount(
            fiat_amount=100.00,
            currency='EUR',
            apply_buffer=True,
            buffer_percentage=5.0
        )
        
        # Test 1% buffer
        result_1_percent = service.calculate_hbar_amount(
            fiat_amount=100.00,
            currency='EUR',
            apply_buffer=True,
            buffer_percentage=1.0
        )
        
        assert result_5_percent['buffer_percentage'] == 5.0
        assert result_1_percent['buffer_percentage'] == 1.0
        
        # Verify different buffer amounts
        hbar_5_percent = result_5_percent['hbar_amount']
        hbar_1_percent = result_1_percent['hbar_amount']
        
        assert hbar_5_percent > hbar_1_percent
    
    def test_buffer_protects_against_price_increase(self, db_session):
        """
        Test that buffer provides protection against price increases
        
        Scenario: User prepares payment at €0.34/HBAR, but price increases
        to €0.35/HBAR before transaction. Buffer should cover this.
        """
        service = ExchangeRateService(db_session)
        
        # Initial price when preparing payment
        initial_price = 0.34
        service.get_hbar_price = Mock(return_value=initial_price)
        
        fiat_amount = 85.40
        
        # Calculate with buffer
        result = service.calculate_hbar_amount(
            fiat_amount=fiat_amount,
            currency='EUR',
            apply_buffer=True,
            buffer_percentage=2.0
        )
        
        hbar_with_buffer = result['hbar_amount_rounded']
        
        # Simulate price increase of 1.5% (within 2% buffer)
        increased_price = initial_price * 1.015  # €0.3451
        
        # Calculate how much HBAR would be needed at new price
        hbar_needed_at_new_price = fiat_amount / increased_price
        
        # Buffer should cover this increase
        assert hbar_with_buffer >= hbar_needed_at_new_price, \
            "Buffer should protect against 1.5% price increase"
    
    def test_buffer_response_includes_metadata(self, db_session):
        """
        Test that response includes buffer metadata for transparency
        """
        service = ExchangeRateService(db_session)
        service.get_hbar_price = Mock(return_value=0.34)
        
        result = service.calculate_hbar_amount(
            fiat_amount=85.40,
            currency='EUR',
            apply_buffer=True,
            buffer_percentage=2.0
        )
        
        # Verify all required fields are present
        assert 'buffer_applied' in result
        assert 'buffer_percentage' in result
        assert result['buffer_applied'] is True
        assert result['buffer_percentage'] == 2.0
        
        # Verify other standard fields
        assert 'fiat_amount' in result
        assert 'currency' in result
        assert 'hbar_price' in result
        assert 'hbar_amount' in result
        assert 'hbar_amount_rounded' in result
        assert 'exchange_rate_timestamp' in result
    
    def test_buffer_disabled_by_default(self, db_session):
        """
        Test that buffer is not applied when apply_buffer=False
        """
        service = ExchangeRateService(db_session)
        service.get_hbar_price = Mock(return_value=0.34)
        
        result = service.calculate_hbar_amount(
            fiat_amount=85.40,
            currency='EUR',
            apply_buffer=False
        )
        
        assert result['buffer_applied'] is False
        assert result['buffer_percentage'] == 0.0
    
    def test_buffer_with_edge_cases(self, db_session):
        """
        Test buffer with edge case amounts
        """
        service = ExchangeRateService(db_session)
        service.get_hbar_price = Mock(return_value=0.34)
        
        # Very small amount
        result_small = service.calculate_hbar_amount(
            fiat_amount=0.01,
            currency='EUR',
            apply_buffer=True,
            buffer_percentage=2.0
        )
        assert result_small['hbar_amount_rounded'] > 0
        assert result_small['buffer_applied'] is True
        
        # Very large amount
        result_large = service.calculate_hbar_amount(
            fiat_amount=10000.00,
            currency='EUR',
            apply_buffer=True,
            buffer_percentage=2.0
        )
        assert result_large['hbar_amount_rounded'] > 0
        assert result_large['buffer_applied'] is True
        
        # Verify 2% increase for both
        result_small_no_buffer = service.calculate_hbar_amount(
            fiat_amount=0.01,
            currency='EUR',
            apply_buffer=False
        )
        
        percentage_increase = (
            (result_small['hbar_amount'] - result_small_no_buffer['hbar_amount']) 
            / result_small_no_buffer['hbar_amount'] * 100
        )
        assert abs(percentage_increase - 2.0) < 0.01


# Integration test removed - unit tests above provide sufficient coverage
# The payment endpoint integration is tested in test_e2e_payment_flow.py

