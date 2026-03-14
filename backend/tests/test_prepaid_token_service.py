"""
Test Prepaid Token Service - Core Logic

Tests the prepaid token service functionality including:
- Token ID generation
- Units calculation from fiat
- HBAR exchange rate fetching
- Token creation
- User token retrieval
- FIFO token deduction

Requirements: FR-8.1 to FR-8.12, US-13 to US-15, Task 1.2
Spec: prepaid-smart-meter-mvp
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, MagicMock
import uuid

from app.services.prepaid_token_service import PrepaidTokenService, PrepaidTokenError


@pytest.fixture
def prepaid_service(db_session: Session):
    """Create prepaid token service instance"""
    return PrepaidTokenService(db_session)


@pytest.fixture
def test_user_id(db_session):
    """Create test user and return ID"""
    user_id = str(uuid.uuid4())
    query = text("""
        INSERT INTO users (id, email, password_hash, full_name, country_code, currency)
        VALUES (:id, :email, :password, :name, :country, :currency)
    """)
    db_session.execute(query, {
        'id': user_id,
        'email': 'test@example.com',
        'password': 'hashed_password',
        'name': 'Test User',
        'country': 'ES',
        'currency': 'EUR'
    })
    db_session.commit()
    return user_id


@pytest.fixture
def test_meter_id(db_session, test_user_id):
    """Create test meter and return ID"""
    meter_id = str(uuid.uuid4())
    query = text("""
        INSERT INTO meters (id, user_id, meter_id, utility_provider, status)
        VALUES (:id, :user_id, :meter_id, :utility, :status)
    """)
    db_session.execute(query, {
        'id': meter_id,
        'user_id': test_user_id,
        'meter_id': 'ESP-12345678',
        'utility': 'Iberdrola',
        'status': 'active'
    })
    db_session.commit()
    return meter_id


@pytest.fixture
def mock_tariff():
    """Mock tariff data"""
    return {
        'currency': 'EUR',
        'rate_structure': {
            'type': 'flat',
            'rate': 0.40
        }
    }


@pytest.fixture
def mock_exchange_rate():
    """Mock HBAR exchange rate"""
    return 0.34  # 1 HBAR = 0.34 EUR


class TestTokenIDGeneration:
    """Test generate_token_id() method"""
    
    def test_token_id_format(self, prepaid_service):
        """Test that token ID follows format TOKEN-{COUNTRY}-{YEAR}-{SEQ}"""
        token_id = prepaid_service.generate_token_id('ES', 2026)
        
        # Verify format
        assert token_id.startswith('TOKEN-ES-2026-')
        assert len(token_id.split('-')) == 4
        
        # Verify sequence is 3 digits
        sequence = token_id.split('-')[3]
        assert len(sequence) == 3
        assert sequence.isdigit()
    
    def test_token_id_sequence_increments(self, prepaid_service, test_user_id, test_meter_id):
        """Test that sequence number increments for same country/year"""
        # Create first token
        token_id1 = prepaid_service.generate_token_id('ES', 2026)
        assert token_id1 == 'TOKEN-ES-2026-001'
        
        # Insert token to database
        query = text("""
            INSERT INTO prepaid_tokens (
                id, token_id, user_id, meter_id,
                units_purchased, units_remaining,
                amount_paid_fiat, currency,
                exchange_rate, tariff_rate,
                issued_at, expires_at
            ) VALUES (
                :id, :token_id, :user_id, :meter_id,
                :units, :units, :amount, :currency,
                :rate, :tariff, NOW(), NOW() + INTERVAL '1 year'
            )
        """)
        prepaid_service.db.execute(query, {
            'id': str(uuid.uuid4()),
            'token_id': token_id1,
            'user_id': test_user_id,
            'meter_id': test_meter_id,
            'units': 100.0,
            'amount': 50.0,
            'currency': 'EUR',
            'rate': 0.34,
            'tariff': 0.40
        })
        prepaid_service.db.commit()
        
        # Generate second token
        token_id2 = prepaid_service.generate_token_id('ES', 2026)
        assert token_id2 == 'TOKEN-ES-2026-002'
    
    def test_token_id_different_countries(self, prepaid_service):
        """Test that different countries have independent sequences"""
        token_es = prepaid_service.generate_token_id('ES', 2026)
        token_us = prepaid_service.generate_token_id('US', 2026)
        
        assert token_es.startswith('TOKEN-ES-2026-')
        assert token_us.startswith('TOKEN-US-2026-')
    
    def test_token_id_uses_current_year_by_default(self, prepaid_service):
        """Test that current year is used if not specified"""
        token_id = prepaid_service.generate_token_id('ES')
        current_year = datetime.now().year
        assert f'TOKEN-ES-{current_year}-' in token_id


class TestUnitsCalculation:
    """Test calculate_units_from_fiat() method"""
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_calculate_units_flat_rate(self, mock_get_tariff, prepaid_service):
        """Test units calculation with flat rate tariff"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {
                'type': 'flat',
                'rate': 0.40
            }
        }
        
        result = prepaid_service.calculate_units_from_fiat(
            amount_fiat=50.0,
            country_code='ES',
            utility_provider='Iberdrola'
        )
        
        # 50 EUR / 0.40 EUR/kWh = 125 kWh
        assert result['units_kwh'] == 125.0
        assert result['tariff_rate'] == 0.40
        assert result['currency'] == 'EUR'
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_calculate_units_tiered_rate(self, mock_get_tariff, prepaid_service):
        """Test units calculation with tiered rate (uses first tier)"""
        mock_get_tariff.return_value = {
            'currency': 'USD',
            'rate_structure': {
                'type': 'tiered',
                'tiers': [
                    {'max_kwh': 500, 'price': 0.12},
                    {'max_kwh': 1000, 'price': 0.15}
                ]
            }
        }
        
        result = prepaid_service.calculate_units_from_fiat(
            amount_fiat=60.0,
            country_code='US',
            utility_provider='PG&E'
        )
        
        # Uses first tier: 60 USD / 0.12 USD/kWh = 500 kWh
        assert result['units_kwh'] == 500.0
        assert result['tariff_rate'] == 0.12
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_calculate_units_time_of_use(self, mock_get_tariff, prepaid_service):
        """Test units calculation with time-of-use rate (uses average)"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {
                'type': 'time_of_use',
                'periods': [
                    {'name': 'peak', 'price': 0.50},
                    {'name': 'off-peak', 'price': 0.30}
                ]
            }
        }
        
        result = prepaid_service.calculate_units_from_fiat(
            amount_fiat=40.0,
            country_code='ES',
            utility_provider='Iberdrola'
        )
        
        # Average rate: (0.50 + 0.30) / 2 = 0.40
        # 40 EUR / 0.40 EUR/kWh = 100 kWh
        assert result['units_kwh'] == 100.0
        assert result['tariff_rate'] == 0.40
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_calculate_units_invalid_tariff_rate(self, mock_get_tariff, prepaid_service):
        """Test that zero or negative tariff rate raises error"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {
                'type': 'flat',
                'rate': 0
            }
        }
        
        with pytest.raises(PrepaidTokenError, match="Invalid tariff rate"):
            prepaid_service.calculate_units_from_fiat(
                amount_fiat=50.0,
                country_code='ES',
                utility_provider='Iberdrola'
            )


class TestHBARExchangeRate:
    """Test HBAR exchange rate methods"""
    
    @patch('app.services.prepaid_token_service.get_hbar_price')
    def test_get_hbar_exchange_rate(self, mock_get_price, prepaid_service):
        """Test fetching HBAR exchange rate"""
        mock_get_price.return_value = 0.34
        
        rate = prepaid_service.get_hbar_exchange_rate('EUR')
        
        assert rate == 0.34
        mock_get_price.assert_called_once_with(
            db=prepaid_service.db,
            currency='EUR',
            use_cache=True
        )
    
    @patch('app.services.prepaid_token_service.get_hbar_price')
    def test_calculate_hbar_amount(self, mock_get_price, prepaid_service):
        """Test calculating HBAR amount from fiat"""
        mock_get_price.return_value = 0.34
        
        result = prepaid_service.calculate_hbar_amount(
            amount_fiat=50.0,
            currency='EUR'
        )
        
        # 50 EUR / 0.34 EUR/HBAR = 147.06 HBAR
        assert result['amount_hbar'] == pytest.approx(147.06, rel=0.01)
        assert result['exchange_rate'] == 0.34
        assert result['currency'] == 'EUR'
    
    @patch('app.services.prepaid_token_service.get_hbar_price')
    def test_exchange_rate_fetch_failure(self, mock_get_price, prepaid_service):
        """Test that exchange rate fetch failure raises error"""
        mock_get_price.side_effect = Exception("API unavailable")
        
        with pytest.raises(PrepaidTokenError, match="Failed to fetch exchange rate"):
            prepaid_service.get_hbar_exchange_rate('EUR')


class TestTokenCreation:
    """Test create_token() method"""
    
    @patch('app.services.prepaid_token_service.get_tariff')
    @patch('app.services.prepaid_token_service.get_hbar_price')
    def test_create_token_basic(
        self, mock_get_price, mock_get_tariff,
        prepaid_service, test_user_id, test_meter_id
    ):
        """Test basic token creation"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {'type': 'flat', 'rate': 0.40}
        }
        mock_get_price.return_value = 0.34
        
        result = prepaid_service.create_token(
            user_id=test_user_id,
            meter_id=test_meter_id,
            amount_fiat=50.0,
            currency='EUR',
            country_code='ES',
            utility_provider='Iberdrola',
            payment_method='HBAR',
            amount_crypto=147.06,
            exchange_rate=0.34
        )
        
        # Verify result structure
        assert 'token_id' in result
        assert result['token_id'].startswith('TOKEN-ES-')
        assert result['units_purchased'] == 125.0
        assert result['units_remaining'] == 125.0
        assert result['amount_paid_fiat'] == 50.0
        assert result['amount_paid_hbar'] == 147.06
        assert result['currency'] == 'EUR'
        assert result['status'] == 'active'
        
        # Verify token in database
        query = text("""
            SELECT token_id, units_purchased, status
            FROM prepaid_tokens
            WHERE id = :id
        """)
        row = prepaid_service.db.execute(query, {'id': result['id']}).fetchone()
        assert row is not None
        assert row[0] == result['token_id']
        assert float(row[1]) == 125.0
        assert row[2] == 'active'
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_create_token_with_hcs_info(
        self, mock_get_tariff,
        prepaid_service, test_user_id, test_meter_id
    ):
        """Test token creation with HCS logging information"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {'type': 'flat', 'rate': 0.40}
        }
        
        result = prepaid_service.create_token(
            user_id=test_user_id,
            meter_id=test_meter_id,
            amount_fiat=50.0,
            currency='EUR',
            country_code='ES',
            utility_provider='Iberdrola',
            payment_method='HBAR',
            amount_crypto=147.06,
            exchange_rate=0.34,
            hcs_topic_id='0.0.5078302',
            hcs_sequence_number=12345
        )
        
        # Verify HCS info stored
        assert result['hcs_topic_id'] == '0.0.5078302'
        assert result['hcs_sequence_number'] == 12345
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_create_token_expiry_one_year(
        self, mock_get_tariff,
        prepaid_service, test_user_id, test_meter_id
    ):
        """Test that token expires in 1 year"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {'type': 'flat', 'rate': 0.40}
        }
        
        result = prepaid_service.create_token(
            user_id=test_user_id,
            meter_id=test_meter_id,
            amount_fiat=50.0,
            currency='EUR',
            country_code='ES',
            utility_provider='Iberdrola',
            payment_method='HBAR',
            amount_crypto=147.06,
            exchange_rate=0.34
        )
        
        # Verify expiry is ~1 year from now
        issued_at = datetime.fromisoformat(result['issued_at'])
        expires_at = datetime.fromisoformat(result['expires_at'])
        delta = expires_at - issued_at
        
        assert 364 <= delta.days <= 366  # Account for leap years


class TestUserTokens:
    """Test get_user_tokens() method"""
    
    def test_get_user_tokens_empty(self, prepaid_service, test_user_id):
        """Test getting tokens when user has none"""
        tokens = prepaid_service.get_user_tokens(test_user_id)
        assert tokens == []
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_get_user_tokens_multiple(
        self, mock_get_tariff,
        prepaid_service, test_user_id, test_meter_id
    ):
        """Test getting multiple tokens for user"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {'type': 'flat', 'rate': 0.40}
        }
        
        # Create two tokens
        prepaid_service.create_token(
            user_id=test_user_id,
            meter_id=test_meter_id,
            amount_fiat=50.0,
            currency='EUR',
            country_code='ES',
            utility_provider='Iberdrola',
            payment_method='HBAR',
            amount_crypto=147.06,
            exchange_rate=0.34
        )
        
        prepaid_service.create_token(
            user_id=test_user_id,
            meter_id=test_meter_id,
            amount_fiat=30.0,
            currency='EUR',
            country_code='ES',
            utility_provider='Iberdrola',
            payment_method='HBAR',
            amount_crypto=88.24,
            exchange_rate=0.34
        )
        
        # Get tokens
        tokens = prepaid_service.get_user_tokens(test_user_id)
        
        assert len(tokens) == 2
        assert all('token_id' in t for t in tokens)
        assert all('units_purchased' in t for t in tokens)
        assert all('units_remaining' in t for t in tokens)
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_get_user_tokens_filter_by_status(
        self, mock_get_tariff,
        prepaid_service, test_user_id, test_meter_id
    ):
        """Test filtering tokens by status"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {'type': 'flat', 'rate': 0.40}
        }
        
        # Create active token
        prepaid_service.create_token(
            user_id=test_user_id,
            meter_id=test_meter_id,
            amount_fiat=50.0,
            currency='EUR',
            country_code='ES',
            utility_provider='Iberdrola',
            payment_method='HBAR',
            amount_crypto=147.06,
            exchange_rate=0.34
        )
        
        # Get only active tokens
        tokens = prepaid_service.get_user_tokens(test_user_id, status='active')
        
        assert len(tokens) == 1
        assert tokens[0]['status'] == 'active'


class TestTokenDeduction:
    """Test deduct_units() method - FIFO logic"""
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_deduct_units_single_token(
        self, mock_get_tariff,
        prepaid_service, test_user_id, test_meter_id
    ):
        """Test deducting units from single token"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {'type': 'flat', 'rate': 0.40}
        }
        
        # Create token with 125 kWh
        prepaid_service.create_token(
            user_id=test_user_id,
            meter_id=test_meter_id,
            amount_fiat=50.0,
            currency='EUR',
            country_code='ES',
            utility_provider='Iberdrola',
            payment_method='HBAR',
            amount_crypto=147.06,
            exchange_rate=0.34
        )
        
        # Deduct 15.5 kWh
        result = prepaid_service.deduct_units(test_meter_id, 15.5)
        
        assert result['total_deducted'] == 15.5
        assert result['remaining_consumption'] == 0
        assert len(result['tokens_deducted']) == 1
        assert result['tokens_deducted'][0]['deducted'] == 15.5
        assert result['tokens_deducted'][0]['remaining'] == 109.5
        assert result['tokens_deducted'][0]['depleted'] is False
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_deduct_units_fifo_order(
        self, mock_get_tariff,
        prepaid_service, test_user_id, test_meter_id
    ):
        """Test that oldest token is deducted first (FIFO)"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {'type': 'flat', 'rate': 0.40}
        }
        
        # Create two tokens
        token1 = prepaid_service.create_token(
            user_id=test_user_id,
            meter_id=test_meter_id,
            amount_fiat=50.0,
            currency='EUR',
            country_code='ES',
            utility_provider='Iberdrola',
            payment_method='HBAR',
            amount_crypto=147.06,
            exchange_rate=0.34
        )
        
        import time
        time.sleep(0.1)  # Ensure different timestamps
        
        token2 = prepaid_service.create_token(
            user_id=test_user_id,
            meter_id=test_meter_id,
            amount_fiat=30.0,
            currency='EUR',
            country_code='ES',
            utility_provider='Iberdrola',
            payment_method='HBAR',
            amount_crypto=88.24,
            exchange_rate=0.34
        )
        
        # Deduct 20 kWh
        result = prepaid_service.deduct_units(test_meter_id, 20.0)
        
        # Should deduct from first (oldest) token only
        assert len(result['tokens_deducted']) == 1
        assert result['tokens_deducted'][0]['token_id'] == token1['token_id']
        assert result['tokens_deducted'][0]['deducted'] == 20.0
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_deduct_units_depletes_token(
        self, mock_get_tariff,
        prepaid_service, test_user_id, test_meter_id
    ):
        """Test that token status changes to depleted when units reach 0"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {'type': 'flat', 'rate': 0.40}
        }
        
        # Create token with 125 kWh
        token = prepaid_service.create_token(
            user_id=test_user_id,
            meter_id=test_meter_id,
            amount_fiat=50.0,
            currency='EUR',
            country_code='ES',
            utility_provider='Iberdrola',
            payment_method='HBAR',
            amount_crypto=147.06,
            exchange_rate=0.34
        )
        
        # Deduct all 125 kWh
        result = prepaid_service.deduct_units(test_meter_id, 125.0)
        
        assert result['tokens_deducted'][0]['depleted'] is True
        assert result['tokens_deducted'][0]['remaining'] == 0
        
        # Verify status in database
        query = text("""
            SELECT status, depleted_at FROM prepaid_tokens WHERE id = :id
        """)
        row = prepaid_service.db.execute(query, {'id': token['id']}).fetchone()
        assert row[0] == 'depleted'
        assert row[1] is not None
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_deduct_units_spans_multiple_tokens(
        self, mock_get_tariff,
        prepaid_service, test_user_id, test_meter_id
    ):
        """Test deduction spanning multiple tokens"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {'type': 'flat', 'rate': 0.40}
        }
        
        # Create two tokens: 125 kWh and 75 kWh
        token1 = prepaid_service.create_token(
            user_id=test_user_id,
            meter_id=test_meter_id,
            amount_fiat=50.0,
            currency='EUR',
            country_code='ES',
            utility_provider='Iberdrola',
            payment_method='HBAR',
            amount_crypto=147.06,
            exchange_rate=0.34
        )
        
        import time
        time.sleep(0.1)
        
        token2 = prepaid_service.create_token(
            user_id=test_user_id,
            meter_id=test_meter_id,
            amount_fiat=30.0,
            currency='EUR',
            country_code='ES',
            utility_provider='Iberdrola',
            payment_method='HBAR',
            amount_crypto=88.24,
            exchange_rate=0.34
        )
        
        # Deduct 150 kWh (more than first token)
        result = prepaid_service.deduct_units(test_meter_id, 150.0)
        
        # Should deduct from both tokens
        assert len(result['tokens_deducted']) == 2
        assert result['total_deducted'] == 150.0
        assert result['remaining_consumption'] == 0
        
        # First token fully depleted
        assert result['tokens_deducted'][0]['token_id'] == token1['token_id']
        assert result['tokens_deducted'][0]['deducted'] == 125.0
        assert result['tokens_deducted'][0]['depleted'] is True
        
        # Second token partially used
        assert result['tokens_deducted'][1]['token_id'] == token2['token_id']
        assert result['tokens_deducted'][1]['deducted'] == 25.0
        assert result['tokens_deducted'][1]['remaining'] == 50.0
        assert result['tokens_deducted'][1]['depleted'] is False
    
    def test_deduct_units_no_tokens(self, prepaid_service, test_meter_id):
        """Test deduction when no tokens available"""
        result = prepaid_service.deduct_units(test_meter_id, 15.5)
        
        assert result['total_deducted'] == 0
        assert result['remaining_consumption'] == 15.5
        assert len(result['tokens_deducted']) == 0


class TestHCSTopicSelection:
    """Test get_topic_for_country() method"""
    
    def test_topic_selection_spain(self, prepaid_service):
        """Test HCS topic selection for Spain (EU)"""
        with patch('config.settings') as mock_settings:
            mock_settings.hcs_topic_eu = '0.0.5078302'
            topic = prepaid_service.get_topic_for_country('ES')
            assert topic == '0.0.5078302'
    
    def test_topic_selection_usa(self, prepaid_service):
        """Test HCS topic selection for USA"""
        with patch('config.settings') as mock_settings:
            mock_settings.hcs_topic_us = '0.0.5078303'
            topic = prepaid_service.get_topic_for_country('US')
            assert topic == '0.0.5078303'
    
    def test_topic_selection_unsupported_country(self, prepaid_service):
        """Test that unsupported country raises error"""
        with pytest.raises(PrepaidTokenError, match="Unsupported country code"):
            prepaid_service.get_topic_for_country('XX')
    
    def test_topic_selection_not_configured(self, prepaid_service):
        """Test handling of unconfigured topic"""
        with patch('config.settings') as mock_settings:
            mock_settings.hcs_topic_eu = '0.0.xxxxx'
            topic = prepaid_service.get_topic_for_country('ES')
            assert topic is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
