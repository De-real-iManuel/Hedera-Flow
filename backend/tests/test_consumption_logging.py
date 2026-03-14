"""
Test Smart Meter Consumption Logging

Tests the log_consumption() method which:
- Verifies signatures before accepting consumption data
- Deducts units from prepaid tokens (FIFO)
- Stores consumption logs in database
- Logs to HCS with SMART_METER_CONSUMPTION type

Requirements: FR-9.6, FR-9.7, FR-9.8, FR-9.9, US-16, Task 2.5
Spec: prepaid-smart-meter-mvp
"""
import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, MagicMock
import uuid

from app.services.smart_meter_service import SmartMeterService, SmartMeterError


@pytest.fixture
def smart_meter_service(db_session: Session):
    """Create smart meter service instance"""
    return SmartMeterService(db_session)


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
        'meter_id': 'SMART-ESP-001',
        'utility': 'Iberdrola',
        'status': 'active'
    })
    db_session.commit()
    return meter_id


@pytest.fixture
def test_meter_with_keypair(smart_meter_service, test_meter_id):
    """Create test meter with generated keypair"""
    smart_meter_service.generate_keypair(test_meter_id)
    return test_meter_id


@pytest.fixture
def signed_consumption_data(smart_meter_service, test_meter_with_keypair):
    """Generate signed consumption data for testing"""
    return smart_meter_service.sign_consumption(
        meter_id=test_meter_with_keypair,
        consumption_kwh=15.5,
        timestamp=1234567890
    )


class TestConsumptionLoggingBasic:
    """Test basic consumption logging functionality"""
    
    def test_log_consumption_with_valid_signature(
        self, smart_meter_service, test_meter_with_keypair, signed_consumption_data, db_session
    ):
        """Test logging consumption with valid signature"""
        result = smart_meter_service.log_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=signed_consumption_data['consumption_kwh'],
            timestamp=signed_consumption_data['timestamp'],
            signature=signed_consumption_data['signature'],
            public_key_pem=signed_consumption_data['public_key'],
            reading_before=5000.0,
            reading_after=5015.5
        )
        
        # Verify result structure
        assert 'consumption_log_id' in result
        assert result['meter_id'] == test_meter_with_keypair
        assert result['consumption_kwh'] == 15.5
        assert result['signature_valid'] is True
        
        # Verify consumption log in database
        query = text("""
            SELECT id, meter_id, consumption_kwh, signature_valid, signature
            FROM consumption_logs
            WHERE id = :id
        """)
        row = db_session.execute(query, {'id': result['consumption_log_id']}).fetchone()
        
        assert row is not None
        assert str(row[0]) == result['consumption_log_id']
        assert str(row[1]) == test_meter_with_keypair
        assert float(row[2]) == 15.5
        assert row[3] is True  # signature_valid
        assert row[4] == signed_consumption_data['signature']
    
    def test_log_consumption_rejects_invalid_signature(
        self, smart_meter_service, test_meter_with_keypair, signed_consumption_data
    ):
        """Test that invalid signature is rejected (fraud detection)"""
        with pytest.raises(SmartMeterError, match="Invalid signature"):
            smart_meter_service.log_consumption(
                meter_id=test_meter_with_keypair,
                consumption_kwh=100.0,  # Tampered consumption
                timestamp=signed_consumption_data['timestamp'],
                signature=signed_consumption_data['signature'],
                public_key_pem=signed_consumption_data['public_key']
            )
    
    def test_log_consumption_stores_readings(
        self, smart_meter_service, test_meter_with_keypair, signed_consumption_data, db_session
    ):
        """Test that meter readings are stored correctly"""
        result = smart_meter_service.log_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=signed_consumption_data['consumption_kwh'],
            timestamp=signed_consumption_data['timestamp'],
            signature=signed_consumption_data['signature'],
            public_key_pem=signed_consumption_data['public_key'],
            reading_before=5000.0,
            reading_after=5015.5
        )
        
        # Verify readings in database
        query = text("""
            SELECT reading_before, reading_after
            FROM consumption_logs
            WHERE id = :id
        """)
        row = db_session.execute(query, {'id': result['consumption_log_id']}).fetchone()
        
        assert float(row[0]) == 5000.0
        assert float(row[1]) == 5015.5
    
    def test_log_consumption_without_readings(
        self, smart_meter_service, test_meter_with_keypair, signed_consumption_data, db_session
    ):
        """Test logging consumption without meter readings (optional)"""
        result = smart_meter_service.log_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=signed_consumption_data['consumption_kwh'],
            timestamp=signed_consumption_data['timestamp'],
            signature=signed_consumption_data['signature'],
            public_key_pem=signed_consumption_data['public_key']
            # reading_before and reading_after not provided
        )
        
        # Verify readings are NULL in database
        query = text("""
            SELECT reading_before, reading_after
            FROM consumption_logs
            WHERE id = :id
        """)
        row = db_session.execute(query, {'id': result['consumption_log_id']}).fetchone()
        
        assert row[0] is None
        assert row[1] is None


class TestConsumptionLoggingWithTokenDeduction:
    """Test consumption logging with prepaid token deduction"""
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_log_consumption_deducts_from_token(
        self, mock_get_tariff, smart_meter_service, test_meter_with_keypair,
        test_user_id, signed_consumption_data, db_session
    ):
        """Test that consumption deducts units from prepaid token"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {'type': 'flat', 'rate': 0.40}
        }
        
        # Create prepaid token
        from app.services.prepaid_token_service import PrepaidTokenService
        prepaid_service = PrepaidTokenService(db_session)
        
        token = prepaid_service.create_token(
            user_id=test_user_id,
            meter_id=test_meter_with_keypair,
            amount_fiat=50.0,
            currency='EUR',
            country_code='ES',
            utility_provider='Iberdrola',
            payment_method='HBAR',
            amount_crypto=147.06,
            exchange_rate=0.34
        )
        
        # Log consumption
        result = smart_meter_service.log_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=signed_consumption_data['consumption_kwh'],
            timestamp=signed_consumption_data['timestamp'],
            signature=signed_consumption_data['signature'],
            public_key_pem=signed_consumption_data['public_key']
        )
        
        # Verify token deduction
        assert 'token_deduction' in result
        assert result['token_deduction'] is not None
        assert result['token_deduction']['total_deducted'] == 15.5
        
        # Verify units_deducted and units_remaining in consumption log
        query = text("""
            SELECT units_deducted, units_remaining, token_id
            FROM consumption_logs
            WHERE id = :id
        """)
        row = db_session.execute(query, {'id': result['consumption_log_id']}).fetchone()
        
        assert float(row[0]) == 15.5  # units_deducted
        assert float(row[1]) == 109.5  # units_remaining (125 - 15.5)
        assert row[2] is not None  # token_id
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_log_consumption_without_token(
        self, mock_get_tariff, smart_meter_service, test_meter_with_keypair,
        signed_consumption_data, db_session
    ):
        """Test logging consumption when no prepaid token exists"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {'type': 'flat', 'rate': 0.40}
        }
        
        # Log consumption without creating token
        result = smart_meter_service.log_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=signed_consumption_data['consumption_kwh'],
            timestamp=signed_consumption_data['timestamp'],
            signature=signed_consumption_data['signature'],
            public_key_pem=signed_consumption_data['public_key']
        )
        
        # Verify no token deduction
        assert result.get('token_deduction') is None or result['token_deduction']['total_deducted'] == 0
        
        # Verify units_deducted and units_remaining are NULL
        query = text("""
            SELECT units_deducted, units_remaining, token_id
            FROM consumption_logs
            WHERE id = :id
        """)
        row = db_session.execute(query, {'id': result['consumption_log_id']}).fetchone()
        
        assert row[0] is None  # units_deducted
        assert row[1] is None  # units_remaining
        assert row[2] is None  # token_id
    
    @patch('app.services.prepaid_token_service.get_tariff')
    def test_log_consumption_fifo_token_deduction(
        self, mock_get_tariff, smart_meter_service, test_meter_with_keypair,
        test_user_id, db_session
    ):
        """Test that consumption deducts from oldest token first (FIFO)"""
        mock_get_tariff.return_value = {
            'currency': 'EUR',
            'rate_structure': {'type': 'flat', 'rate': 0.40}
        }
        
        # Create two tokens
        from app.services.prepaid_token_service import PrepaidTokenService
        prepaid_service = PrepaidTokenService(db_session)
        
        token1 = prepaid_service.create_token(
            user_id=test_user_id,
            meter_id=test_meter_with_keypair,
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
            meter_id=test_meter_with_keypair,
            amount_fiat=30.0,
            currency='EUR',
            country_code='ES',
            utility_provider='Iberdrola',
            payment_method='HBAR',
            amount_crypto=88.24,
            exchange_rate=0.34
        )
        
        # Sign and log consumption
        signed = smart_meter_service.sign_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=20.0,
            timestamp=1234567890
        )
        
        result = smart_meter_service.log_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=signed['consumption_kwh'],
            timestamp=signed['timestamp'],
            signature=signed['signature'],
            public_key_pem=signed['public_key']
        )
        
        # Verify deduction from first (oldest) token
        assert result['token_deduction']['tokens_deducted'][0]['token_id'] == token1['token_id']
        assert result['token_deduction']['tokens_deducted'][0]['deducted'] == 20.0


class TestConsumptionLoggingHCS:
    """Test HCS logging for consumption events"""
    
    @patch('app.services.smart_meter_service.submit_hcs_message')
    def test_log_consumption_submits_to_hcs(
        self, mock_submit_hcs, smart_meter_service, test_meter_with_keypair,
        signed_consumption_data
    ):
        """Test that consumption is logged to HCS"""
        mock_submit_hcs.return_value = {
            'sequence_number': 12345,
            'topic_id': '0.0.8052384'
        }
        
        result = smart_meter_service.log_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=signed_consumption_data['consumption_kwh'],
            timestamp=signed_consumption_data['timestamp'],
            signature=signed_consumption_data['signature'],
            public_key_pem=signed_consumption_data['public_key']
        )
        
        # Verify HCS submission
        assert 'hcs_sequence_number' in result
        assert result['hcs_sequence_number'] == 12345
    
    @patch('app.services.smart_meter_service.submit_hcs_message')
    def test_log_consumption_hcs_message_format(
        self, mock_submit_hcs, smart_meter_service, test_meter_with_keypair,
        signed_consumption_data
    ):
        """Test that HCS message follows correct format"""
        mock_submit_hcs.return_value = {
            'sequence_number': 12345,
            'topic_id': '0.0.8052384'
        }
        
        smart_meter_service.log_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=signed_consumption_data['consumption_kwh'],
            timestamp=signed_consumption_data['timestamp'],
            signature=signed_consumption_data['signature'],
            public_key_pem=signed_consumption_data['public_key']
        )
        
        # Verify HCS message was submitted with correct format
        assert mock_submit_hcs.called
        call_args = mock_submit_hcs.call_args
        
        # Check message structure
        message = call_args[1]['message']
        assert message['type'] == 'SMART_METER_CONSUMPTION'
        assert 'meter_id' in message
        assert message['consumption_kwh'] == 15.5
        assert message['timestamp'] == 1234567890
        assert 'signature' in message
        assert message['signature_valid'] is True
    
    @patch('app.services.smart_meter_service.submit_hcs_message')
    def test_log_consumption_hcs_regional_topic_selection(
        self, mock_submit_hcs, smart_meter_service, test_meter_with_keypair,
        signed_consumption_data, db_session
    ):
        """Test that correct regional HCS topic is selected"""
        mock_submit_hcs.return_value = {
            'sequence_number': 12345,
            'topic_id': '0.0.8052384'
        }
        
        smart_meter_service.log_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=signed_consumption_data['consumption_kwh'],
            timestamp=signed_consumption_data['timestamp'],
            signature=signed_consumption_data['signature'],
            public_key_pem=signed_consumption_data['public_key']
        )
        
        # Verify correct topic was used (ES -> EU topic)
        call_args = mock_submit_hcs.call_args
        topic_id = call_args[1]['topic_id']
        
        # Should use EU topic for Spain
        assert topic_id in ['0.0.8052384', '0.0.5078302']  # EU topic IDs
    
    @patch('app.services.smart_meter_service.submit_hcs_message')
    def test_log_consumption_continues_on_hcs_failure(
        self, mock_submit_hcs, smart_meter_service, test_meter_with_keypair,
        signed_consumption_data, db_session
    ):
        """Test that consumption logging continues even if HCS submission fails"""
        mock_submit_hcs.side_effect = Exception("HCS unavailable")
        
        # Should not raise exception
        result = smart_meter_service.log_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=signed_consumption_data['consumption_kwh'],
            timestamp=signed_consumption_data['timestamp'],
            signature=signed_consumption_data['signature'],
            public_key_pem=signed_consumption_data['public_key']
        )
        
        # Verify consumption was still logged to database
        assert 'consumption_log_id' in result
        
        # Verify HCS sequence number is None
        assert result.get('hcs_sequence_number') is None


class TestConsumptionLoggingEdgeCases:
    """Test edge cases for consumption logging"""
    
    def test_log_zero_consumption(
        self, smart_meter_service, test_meter_with_keypair, db_session
    ):
        """Test logging zero consumption"""
        signed = smart_meter_service.sign_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=0.0,
            timestamp=1234567890
        )
        
        result = smart_meter_service.log_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=0.0,
            timestamp=1234567890,
            signature=signed['signature'],
            public_key_pem=signed['public_key']
        )
        
        assert result['consumption_kwh'] == 0.0
        assert result['signature_valid'] is True
    
    def test_log_large_consumption(
        self, smart_meter_service, test_meter_with_keypair, db_session
    ):
        """Test logging large consumption value"""
        signed = smart_meter_service.sign_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=9999.99,
            timestamp=1234567890
        )
        
        result = smart_meter_service.log_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=9999.99,
            timestamp=1234567890,
            signature=signed['signature'],
            public_key_pem=signed['public_key']
        )
        
        assert result['consumption_kwh'] == 9999.99
        assert result['signature_valid'] is True
    
    def test_log_fractional_consumption(
        self, smart_meter_service, test_meter_with_keypair, db_session
    ):
        """Test logging fractional consumption"""
        signed = smart_meter_service.sign_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=0.123456,
            timestamp=1234567890
        )
        
        result = smart_meter_service.log_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=0.123456,
            timestamp=1234567890,
            signature=signed['signature'],
            public_key_pem=signed['public_key']
        )
        
        assert result['consumption_kwh'] == pytest.approx(0.123456, rel=1e-6)
        assert result['signature_valid'] is True
    
    def test_log_consumption_multiple_times(
        self, smart_meter_service, test_meter_with_keypair, db_session
    ):
        """Test logging multiple consumption events"""
        consumption_logs = []
        
        for i in range(5):
            signed = smart_meter_service.sign_consumption(
                meter_id=test_meter_with_keypair,
                consumption_kwh=10.0 + i,
                timestamp=1234567890 + i
            )
            
            result = smart_meter_service.log_consumption(
                meter_id=test_meter_with_keypair,
                consumption_kwh=signed['consumption_kwh'],
                timestamp=signed['timestamp'],
                signature=signed['signature'],
                public_key_pem=signed['public_key']
            )
            
            consumption_logs.append(result)
        
        # Verify all logs were created
        assert len(consumption_logs) == 5
        
        # Verify all have unique IDs
        log_ids = [log['consumption_log_id'] for log in consumption_logs]
        assert len(set(log_ids)) == 5
        
        # Verify all in database
        query = text("""
            SELECT COUNT(*) FROM consumption_logs
            WHERE meter_id = :meter_id
        """)
        count = db_session.execute(query, {'meter_id': test_meter_with_keypair}).scalar()
        assert count == 5


class TestConsumptionLoggingPerformance:
    """Test performance requirements for consumption logging"""
    
    def test_log_consumption_completes_quickly(
        self, smart_meter_service, test_meter_with_keypair, signed_consumption_data
    ):
        """Test that consumption logging completes quickly"""
        import time
        
        start = time.time()
        smart_meter_service.log_consumption(
            meter_id=test_meter_with_keypair,
            consumption_kwh=signed_consumption_data['consumption_kwh'],
            timestamp=signed_consumption_data['timestamp'],
            signature=signed_consumption_data['signature'],
            public_key_pem=signed_consumption_data['public_key']
        )
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        # Should complete reasonably fast (< 1 second for unit test)
        assert elapsed < 1000, f"Consumption logging took {elapsed}ms (should be < 1000ms)"


class TestFraudDetection:
    """Test fraud detection for consumption logging"""
    
    def test_fraud_detection_rejects_tampered_consumption(
        self, smart_meter_service, test_meter_with_keypair, signed_consumption_data
    ):
        """Test that tampered consumption is rejected"""
        with pytest.raises(SmartMeterError, match="Invalid signature"):
            smart_meter_service.log_consumption(
                meter_id=test_meter_with_keypair,
                consumption_kwh=1000.0,  # Inflated consumption
                timestamp=signed_consumption_data['timestamp'],
                signature=signed_consumption_data['signature'],
                public_key_pem=signed_consumption_data['public_key']
            )
    
    def test_fraud_detection_rejects_tampered_timestamp(
        self, smart_meter_service, test_meter_with_keypair, signed_consumption_data
    ):
        """Test that tampered timestamp is rejected"""
        with pytest.raises(SmartMeterError, match="Invalid signature"):
            smart_meter_service.log_consumption(
                meter_id=test_meter_with_keypair,
                consumption_kwh=signed_consumption_data['consumption_kwh'],
                timestamp=9999999999,  # Tampered timestamp
                signature=signed_consumption_data['signature'],
                public_key_pem=signed_consumption_data['public_key']
            )
    
    def test_fraud_detection_rejects_wrong_signature(
        self, smart_meter_service, test_meter_with_keypair, signed_consumption_data
    ):
        """Test that wrong signature is rejected"""
        with pytest.raises(SmartMeterError, match="Invalid signature"):
            smart_meter_service.log_consumption(
                meter_id=test_meter_with_keypair,
                consumption_kwh=signed_consumption_data['consumption_kwh'],
                timestamp=signed_consumption_data['timestamp'],
                signature="0x" + "a" * 128,  # Wrong signature
                public_key_pem=signed_consumption_data['public_key']
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
