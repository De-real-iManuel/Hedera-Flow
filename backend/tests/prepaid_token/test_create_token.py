"""
Unit tests for PrepaidTokenService.create_token method

Tests the token creation functionality.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.prepaid_token_service import PrepaidTokenService, PrepaidTokenError


class TestCreateToken:
    """Test create_token method"""
    
    def test_create_token_success_hbar(self):
        """Test successful token creation with HBAR payment"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock calculate_units_from_fiat
        with patch.object(service, 'calculate_units_from_fiat', return_value={
            'units_kwh': 125.0,
            'tariff_rate': 0.40,
            'currency': 'EUR'
        }):
            # Mock generate_token_id
            with patch.object(service, 'generate_token_id', return_value='TOKEN-ES-2026-001'):
                # Mock database insert
                result_mock = Mock()
                result_mock.fetchone.return_value = (
                    'test-uuid',
                    'TOKEN-ES-2026-001',
                    datetime(2026, 3, 3, 10, 0, 0),
                    datetime(2027, 3, 3, 10, 0, 0)
                )
                db_mock.execute.return_value = result_mock
                
                # Execute
                result = service.create_token(
                    user_id='user-uuid',
                    meter_id='meter-uuid',
                    amount_fiat=50.0,
                    currency='EUR',
                    country_code='ES',
                    utility_provider='Iberdrola',
                    payment_method='HBAR',
                    amount_crypto=147.0,
                    exchange_rate=0.34,
                    hedera_tx_id='0.0.123456@1234567890.123'
                )
                
                # Verify
                assert result['token_id'] == 'TOKEN-ES-2026-001'
                assert result['units_purchased'] == 125.0
                assert result['units_remaining'] == 125.0
                assert result['amount_paid_fiat'] == 50.0
                assert result['amount_paid_hbar'] == 147.0
                assert result['amount_paid_usdc'] is None
                assert result['currency'] == 'EUR'
                assert result['exchange_rate'] == 0.34
                assert result['tariff_rate'] == 0.40
                assert result['status'] == 'active'
                
                # Verify database commit was called
                db_mock.commit.assert_called_once()
    
    def test_create_token_success_usdc(self):
        """Test successful token creation with USDC payment"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock calculate_units_from_fiat
        with patch.object(service, 'calculate_units_from_fiat', return_value={
            'units_kwh': 333.33,
            'tariff_rate': 0.15,
            'currency': 'USD'
        }):
            # Mock generate_token_id
            with patch.object(service, 'generate_token_id', return_value='TOKEN-US-2026-001'):
                # Mock database insert
                result_mock = Mock()
                result_mock.fetchone.return_value = (
                    'test-uuid',
                    'TOKEN-US-2026-001',
                    datetime(2026, 3, 3, 10, 0, 0),
                    datetime(2027, 3, 3, 10, 0, 0)
                )
                db_mock.execute.return_value = result_mock
                
                # Execute
                result = service.create_token(
                    user_id='user-uuid',
                    meter_id='meter-uuid',
                    amount_fiat=50.0,
                    currency='USD',
                    country_code='US',
                    utility_provider='PG&E',
                    payment_method='USDC',
                    amount_crypto=50.0,
                    exchange_rate=1.0,
                    hedera_tx_id='0.0.123456@1234567890.123'
                )
                
                # Verify
                assert result['token_id'] == 'TOKEN-US-2026-001'
                assert result['units_purchased'] == 333.33
                assert result['amount_paid_usdc'] == 50.0
                assert result['amount_paid_hbar'] is None
                assert result['currency'] == 'USD'
    
    def test_create_token_expiry_one_year(self):
        """Test that token expiry is set to 1 year from issuance"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock dependencies
        with patch.object(service, 'calculate_units_from_fiat', return_value={
            'units_kwh': 125.0,
            'tariff_rate': 0.40,
            'currency': 'EUR'
        }):
            with patch.object(service, 'generate_token_id', return_value='TOKEN-ES-2026-001'):
                # Mock database insert with specific dates
                issued_at = datetime(2026, 3, 3, 10, 0, 0)
                expires_at = datetime(2027, 3, 3, 10, 0, 0)
                
                result_mock = Mock()
                result_mock.fetchone.return_value = (
                    'test-uuid',
                    'TOKEN-ES-2026-001',
                    issued_at,
                    expires_at
                )
                db_mock.execute.return_value = result_mock
                
                # Execute
                result = service.create_token(
                    user_id='user-uuid',
                    meter_id='meter-uuid',
                    amount_fiat=50.0,
                    currency='EUR',
                    country_code='ES',
                    utility_provider='Iberdrola',
                    payment_method='HBAR',
                    amount_crypto=147.0,
                    exchange_rate=0.34
                )
                
                # Verify expiry is 1 year from issuance
                issued = datetime.fromisoformat(result['issued_at'])
                expires = datetime.fromisoformat(result['expires_at'])
                delta = expires - issued
                assert delta.days == 365
    
    def test_create_token_without_hedera_tx(self):
        """Test token creation without Hedera transaction ID (optional)"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock dependencies
        with patch.object(service, 'calculate_units_from_fiat', return_value={
            'units_kwh': 125.0,
            'tariff_rate': 0.40,
            'currency': 'EUR'
        }):
            with patch.object(service, 'generate_token_id', return_value='TOKEN-ES-2026-001'):
                # Mock database insert
                result_mock = Mock()
                result_mock.fetchone.return_value = (
                    'test-uuid',
                    'TOKEN-ES-2026-001',
                    datetime(2026, 3, 3, 10, 0, 0),
                    datetime(2027, 3, 3, 10, 0, 0)
                )
                db_mock.execute.return_value = result_mock
                
                # Execute without hedera_tx_id
                result = service.create_token(
                    user_id='user-uuid',
                    meter_id='meter-uuid',
                    amount_fiat=50.0,
                    currency='EUR',
                    country_code='ES',
                    utility_provider='Iberdrola',
                    payment_method='HBAR',
                    amount_crypto=147.0,
                    exchange_rate=0.34
                )
                
                # Verify - should still succeed
                assert result['token_id'] == 'TOKEN-ES-2026-001'
                assert result['status'] == 'active'
    
    def test_create_token_database_error(self):
        """Test that PrepaidTokenError is raised on database error"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock dependencies
        with patch.object(service, 'calculate_units_from_fiat', return_value={
            'units_kwh': 125.0,
            'tariff_rate': 0.40,
            'currency': 'EUR'
        }):
            with patch.object(service, 'generate_token_id', return_value='TOKEN-ES-2026-001'):
                # Mock database error
                db_mock.execute.side_effect = Exception("Database connection failed")
                
                # Execute & Verify
                with pytest.raises(PrepaidTokenError, match="Failed to create token"):
                    service.create_token(
                        user_id='user-uuid',
                        meter_id='meter-uuid',
                        amount_fiat=50.0,
                        currency='EUR',
                        country_code='ES',
                        utility_provider='Iberdrola',
                        payment_method='HBAR',
                        amount_crypto=147.0,
                        exchange_rate=0.34
                    )
                
                # Verify rollback was called
                db_mock.rollback.assert_called_once()
    
    def test_create_token_calculation_error(self):
        """Test that PrepaidTokenError is propagated from calculate_units_from_fiat"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock calculate_units_from_fiat to raise error
        with patch.object(service, 'calculate_units_from_fiat', side_effect=PrepaidTokenError("Invalid tariff")):
            # Execute & Verify
            with pytest.raises(PrepaidTokenError, match="Invalid tariff"):
                service.create_token(
                    user_id='user-uuid',
                    meter_id='meter-uuid',
                    amount_fiat=50.0,
                    currency='EUR',
                    country_code='ES',
                    utility_provider='Iberdrola',
                    payment_method='HBAR',
                    amount_crypto=147.0,
                    exchange_rate=0.34
                )
            
            # Verify rollback was called
            db_mock.rollback.assert_called_once()
    
    def test_create_token_token_id_generation_error(self):
        """Test that PrepaidTokenError is propagated from generate_token_id"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock dependencies
        with patch.object(service, 'calculate_units_from_fiat', return_value={
            'units_kwh': 125.0,
            'tariff_rate': 0.40,
            'currency': 'EUR'
        }):
            # Mock generate_token_id to raise error
            with patch.object(service, 'generate_token_id', side_effect=PrepaidTokenError("Failed to generate token ID")):
                # Execute & Verify
                with pytest.raises(PrepaidTokenError, match="Failed to generate token ID"):
                    service.create_token(
                        user_id='user-uuid',
                        meter_id='meter-uuid',
                        amount_fiat=50.0,
                        currency='EUR',
                        country_code='ES',
                        utility_provider='Iberdrola',
                        payment_method='HBAR',
                        amount_crypto=147.0,
                        exchange_rate=0.34
                    )
                
                # Verify rollback was called
                db_mock.rollback.assert_called_once()
    
    def test_create_token_initial_units_remaining_equals_purchased(self):
        """Test that units_remaining is initially equal to units_purchased"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock dependencies
        with patch.object(service, 'calculate_units_from_fiat', return_value={
            'units_kwh': 250.5,
            'tariff_rate': 0.20,
            'currency': 'USD'
        }):
            with patch.object(service, 'generate_token_id', return_value='TOKEN-US-2026-001'):
                # Mock database insert
                result_mock = Mock()
                result_mock.fetchone.return_value = (
                    'test-uuid',
                    'TOKEN-US-2026-001',
                    datetime(2026, 3, 3, 10, 0, 0),
                    datetime(2027, 3, 3, 10, 0, 0)
                )
                db_mock.execute.return_value = result_mock
                
                # Execute
                result = service.create_token(
                    user_id='user-uuid',
                    meter_id='meter-uuid',
                    amount_fiat=50.0,
                    currency='USD',
                    country_code='US',
                    utility_provider='PG&E',
                    payment_method='HBAR',
                    amount_crypto=147.0,
                    exchange_rate=0.34
                )
                
                # Verify
                assert result['units_purchased'] == result['units_remaining']
                assert result['units_purchased'] == 250.5
    
    def test_create_token_status_active(self):
        """Test that newly created token has status 'active'"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock dependencies
        with patch.object(service, 'calculate_units_from_fiat', return_value={
            'units_kwh': 125.0,
            'tariff_rate': 0.40,
            'currency': 'EUR'
        }):
            with patch.object(service, 'generate_token_id', return_value='TOKEN-ES-2026-001'):
                # Mock database insert
                result_mock = Mock()
                result_mock.fetchone.return_value = (
                    'test-uuid',
                    'TOKEN-ES-2026-001',
                    datetime(2026, 3, 3, 10, 0, 0),
                    datetime(2027, 3, 3, 10, 0, 0)
                )
                db_mock.execute.return_value = result_mock
                
                # Execute
                result = service.create_token(
                    user_id='user-uuid',
                    meter_id='meter-uuid',
                    amount_fiat=50.0,
                    currency='EUR',
                    country_code='ES',
                    utility_provider='Iberdrola',
                    payment_method='HBAR',
                    amount_crypto=147.0,
                    exchange_rate=0.34
                )
                
                # Verify
                assert result['status'] == 'active'
    
    def test_create_token_multiple_currencies(self):
        """Test token creation with different currencies"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        test_cases = [
            ('EUR', 'ES', 'Iberdrola'),
            ('USD', 'US', 'PG&E'),
            ('INR', 'IN', 'TATA Power'),
            ('BRL', 'BR', 'Eletrobras'),
            ('NGN', 'NG', 'EKEDC')
        ]
        
        for currency, country, provider in test_cases:
            # Mock dependencies
            with patch.object(service, 'calculate_units_from_fiat', return_value={
                'units_kwh': 100.0,
                'tariff_rate': 0.50,
                'currency': currency
            }):
                with patch.object(service, 'generate_token_id', return_value=f'TOKEN-{country}-2026-001'):
                    # Mock database insert
                    result_mock = Mock()
                    result_mock.fetchone.return_value = (
                        'test-uuid',
                        f'TOKEN-{country}-2026-001',
                        datetime(2026, 3, 3, 10, 0, 0),
                        datetime(2027, 3, 3, 10, 0, 0)
                    )
                    db_mock.execute.return_value = result_mock
                    
                    # Execute
                    result = service.create_token(
                        user_id='user-uuid',
                        meter_id='meter-uuid',
                        amount_fiat=50.0,
                        currency=currency,
                        country_code=country,
                        utility_provider=provider,
                        payment_method='HBAR',
                        amount_crypto=147.0,
                        exchange_rate=0.34
                    )
                    
                    # Verify
                    assert result['currency'] == currency
                    assert result['token_id'] == f'TOKEN-{country}-2026-001'
