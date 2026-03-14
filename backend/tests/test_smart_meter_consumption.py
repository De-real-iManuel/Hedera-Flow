"""
Test Smart Meter Consumption Logging

Tests the log_consumption() method which handles:
- Signature verification before accepting consumption
- Token deduction using FIFO logic
- Database storage of consumption logs
- HCS logging with SMART_METER_CONSUMPTION type

Requirements: FR-9.6, FR-9.7, FR-9.8, FR-9.9, US-16, Task 2.5
Spec: prepaid-smart-meter-mvp
"""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, MagicMock

from app.services.smart_meter_service import SmartMeterService, SmartMeterError


# Mock Hedera SDK at module level to avoid import errors
@pytest.fixture(autouse=True)
def mock_hedera_sdk():
    """Mock Hedera SDK to avoid actual blockchain calls"""
    with patch('hedera.TopicMessageSubmitTransaction') as mock_tx, \
         patch('hedera.TopicId') as mock_topic_id:
        
        # Setup mock transaction
        mock_transaction = MagicMock()
        mock_receipt = MagicMock()
        mock_receipt.topicSequenceNumber = 12345
        mock_response = MagicMock()
        mock_response.getReceipt.return_value = mock_receipt
        mock_transaction.execute.return_value = mock_response
        
        mock_tx.return_value.setTopicId.return_value.setMessage.return_value = mock_transaction
        mock_topic_id.fromString.return_value = MagicMock()
        
        yield {
            'transaction': mock_tx,
            'topic_id': mock_topic_id,
            'receipt': mock_receipt
        }


@pytest.fixture
def smart_meter_service(db_session: Session):
    """Create smart meter service instance"""
    return SmartMeterService(db_session)


@pytest.fixture
def test_user_id(db_session: Session):
    """Create test user"""
    user_id = str(uuid.uuid4())
    query = text("""
        INSERT INTO users (id, email, first_name, last_name, country_code, is_active, is_email_verified, subsidy_eligible, created_at)
        VALUES (:id, :email, :first_name, :last_name, :country_code, :is_active, :is_email_verified, :subsidy_eligible, NOW())
    """)
    db_session.execute(query, {
        'id': user_id,
        'email': f'test_{user_id[:8]}@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'country_code': 'ES',
        'is_active': True,
        'is_email_verified': True,
        'subsidy_eligible': False
    })
    db_session.commit()
    return user_id


@pytest.fixture
def test_meter_id(db_session: Session, test_user_id: str):
    """Create test meter"""
    meter_id = str(uuid.uuid4())
    query = text("""
        INSERT INTO meters (id, user_id, meter_id, utility_provider, meter_type, is_primary, created_at)
        VALUES (:id, :user_id, :meter_id, :utility_provider, :meter_type, :is_primary, NOW())
    """)
    db_session.execute(query, {
        'id': meter_id,
        'user_id': test_user_id,
        'meter_id': f'SMART-ESP-{meter_id[:8]}',
        'utility_provider': 'Test Utility Provider',
        'meter_type': 'prepaid',
        'is_primary': True
    })
    db_session.commit()
    return meter_id


@pytest.fixture
def test_meter_with_keypair(smart_meter_service, test_meter_id):
    """Create test meter with generated keypair"""
    smart_meter_service.generate_keypair(test_meter_id)
    return test_meter_id


@pytest.fixture
def test_prepaid_token(db_session: Session, test_user_id: str, test_meter_id: str):
    """Create test prepaid token"""
    token_id_str = f"TOKEN-ES-2026-{uuid.uuid4().hex[:6].upper()}"
    token_uuid = str(uuid.uuid4())
    
    query = text("""
        INSERT INTO prepaid_tokens (
            id, token_id, user_id, meter_id,
            units_purchased, units_remaining,
            amount_paid_fiat, currency, exchange_rate, tariff_rate,
            status, issued_at, expires_at
        ) VALUES (
            :id, :token_id, :user_id, :meter_id,
            :units_purchased, :units_remaining,
            :amount_paid_fiat, :currency, :exchange_rate, :tariff_rate,
            :status, NOW(), :expires_at
        )
    """)
    
    db_session.execute(query, {
        'id': token_uuid,
        'token_id': token_id_str,
        'user_id': test_user_id,
        'meter_id': test_meter_id,
        'units_purchased': 100.0,
        'units_remaining': 100.0,
        'amount_paid_fiat': 50.0,
        'currency': 'EUR',
        'exchange_rate': 0.34,
        'tariff_rate': 0.50,
        'status': 'active',
        'expires_at': datetime.now() + timedelta(days=365)
    })
    db_session.commit()
    
    return {'token_id': token_id_str, 'token_uuid': token_uuid}


class TestLogConsumptionSignatureVerification:
    """Test signature verification in log_consumption"""
    
    def test_valid_signature_accepted(
        self, smart_meter_service, test_meter_with_keypair, db_session
    ):
        """Test that valid signature is accepted"""
        meter_id = test_meter_with_keypair
        consumption_kwh = 15.5
        timestamp = 1234567890
        
        # Sign consumption data
        sign_result = smart_meter_service.sign_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp
        )
        
        # Log consumption with valid signature
        result = smart_meter_service.log_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp,
            signature=sign_result['signature'],
            public_key_pem=sign_result['public_key']
        )
        
        # Verify result
        assert result['signature_valid'] is True
        assert result['consumption_kwh'] == consumption_kwh
        assert result['meter_id'] == meter_id
        assert 'consumption_log_id' in result
    
    def test_invalid_signature_rejected(
        self, smart_meter_service, test_meter_with_keypair
    ):
        """Test that invalid signature is rejected (FR-9.7)"""
        meter_id = test_meter_with_keypair
        consumption_kwh = 15.5
        timestamp = 1234567890
        
        # Get public key
        public_key = smart_meter_service.get_public_key(meter_id)
        
        # Use invalid signature
        invalid_signature = "0" * 128  # Invalid hex signature
        
        # Should raise SmartMeterError
        with pytest.raises(SmartMeterError) as exc_info:
            smart_meter_service.log_consumption(
                meter_id=meter_id,
                consumption_kwh=consumption_kwh,
                timestamp=timestamp,
                signature=invalid_signature,
                public_key_pem=public_key
            )
        
        assert "Invalid signature" in str(exc_info.value)
        assert "fraud prevention" in str(exc_info.value).lower()
    
    def test_tampered_consumption_data_rejected(
        self, smart_meter_service, test_meter_with_keypair
    ):
        """Test that tampered consumption data is rejected"""
        meter_id = test_meter_with_keypair
        original_consumption = 15.5
        tampered_consumption = 5.0  # Attacker tries to reduce consumption
        timestamp = 1234567890
        
        # Sign original consumption
        sign_result = smart_meter_service.sign_consumption(
            meter_id=meter_id,
            consumption_kwh=original_consumption,
            timestamp=timestamp
        )
        
        # Try to log with tampered consumption but original signature
        with pytest.raises(SmartMeterError) as exc_info:
            smart_meter_service.log_consumption(
                meter_id=meter_id,
                consumption_kwh=tampered_consumption,  # Tampered!
                timestamp=timestamp,
                signature=sign_result['signature'],
                public_key_pem=sign_result['public_key']
            )
        
        assert "Invalid signature" in str(exc_info.value)


class TestLogConsumptionTokenDeduction:
    """Test token deduction in log_consumption"""
    
    def test_units_deducted_from_prepaid_token(
        self, smart_meter_service, test_meter_with_keypair, 
        test_prepaid_token, db_session
    ):
        """Test that units are deducted from prepaid token"""
        meter_id = test_meter_with_keypair
        consumption_kwh = 15.5
        timestamp = 1234567890
        
        # Sign consumption
        sign_result = smart_meter_service.sign_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp
        )
        
        # Log consumption
        result = smart_meter_service.log_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp,
            signature=sign_result['signature'],
            public_key_pem=sign_result['public_key']
        )
        
        # Verify token deduction
        assert result['units_deducted'] == consumption_kwh
        assert result['units_remaining'] == 100.0 - consumption_kwh
        assert result['token_deduction'] is not None
        
        # Verify database updated
        query = text("""
            SELECT units_remaining FROM prepaid_tokens
            WHERE token_id = :token_id
        """)
        row = db_session.execute(
            query, 
            {'token_id': test_prepaid_token['token_id']}
        ).fetchone()
        
        assert row[0] == 100.0 - consumption_kwh
    
    def test_consumption_without_prepaid_token(
        self, smart_meter_service, test_meter_with_keypair
    ):
        """Test that consumption is logged even without prepaid token"""
        meter_id = test_meter_with_keypair
        consumption_kwh = 15.5
        timestamp = 1234567890
        
        # Sign consumption
        sign_result = smart_meter_service.sign_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp
        )
        
        # Log consumption (no prepaid token exists)
        result = smart_meter_service.log_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp,
            signature=sign_result['signature'],
            public_key_pem=sign_result['public_key']
        )
        
        # Verify consumption logged but no token deduction
        assert result['signature_valid'] is True
        assert result['units_deducted'] is None
        assert result['units_remaining'] is None
        assert result['token_deduction'] is None
    
    def test_token_status_updated_when_depleted(
        self, smart_meter_service, test_meter_with_keypair,
        test_prepaid_token, db_session
    ):
        """Test that token status changes to 'depleted' when units reach 0"""
        meter_id = test_meter_with_keypair
        # Consume all 100 units
        consumption_kwh = 100.0
        timestamp = 1234567890
        
        # Sign consumption
        sign_result = smart_meter_service.sign_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp
        )
        
        # Log consumption
        result = smart_meter_service.log_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp,
            signature=sign_result['signature'],
            public_key_pem=sign_result['public_key']
        )
        
        # Verify token depleted
        assert result['units_remaining'] == 0.0
        
        # Verify status in database
        query = text("""
            SELECT status, units_remaining FROM prepaid_tokens
            WHERE token_id = :token_id
        """)
        row = db_session.execute(
            query,
            {'token_id': test_prepaid_token['token_id']}
        ).fetchone()
        
        assert row[0] == 'depleted'
        assert row[1] == 0.0


class TestLogConsumptionDatabaseStorage:
    """Test database storage in log_consumption"""
    
    def test_consumption_log_stored_in_database(
        self, smart_meter_service, test_meter_with_keypair, db_session
    ):
        """Test that consumption log is stored in database"""
        meter_id = test_meter_with_keypair
        consumption_kwh = 15.5
        timestamp = 1234567890
        reading_before = 5000.0
        reading_after = 5015.5
        
        # Sign consumption
        sign_result = smart_meter_service.sign_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp
        )
        
        # Log consumption
        result = smart_meter_service.log_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp,
            signature=sign_result['signature'],
            public_key_pem=sign_result['public_key'],
            reading_before=reading_before,
            reading_after=reading_after
        )
        
        # Verify log stored in database
        query = text("""
            SELECT meter_id, consumption_kwh, timestamp, signature,
                   signature_valid, reading_before, reading_after
            FROM consumption_logs
            WHERE id = :id
        """)
        row = db_session.execute(
            query,
            {'id': result['consumption_log_id']}
        ).fetchone()
        
        assert row is not None
        assert str(row[0]) == meter_id
        assert float(row[1]) == consumption_kwh
        assert row[2] == timestamp
        assert row[3] == sign_result['signature']
        assert row[4] is True  # signature_valid
        assert float(row[5]) == reading_before
        assert float(row[6]) == reading_after
    
    def test_consumption_log_includes_token_reference(
        self, smart_meter_service, test_meter_with_keypair,
        test_prepaid_token, db_session
    ):
        """Test that consumption log includes token reference"""
        meter_id = test_meter_with_keypair
        consumption_kwh = 15.5
        timestamp = 1234567890
        
        # Sign consumption
        sign_result = smart_meter_service.sign_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp
        )
        
        # Log consumption
        result = smart_meter_service.log_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp,
            signature=sign_result['signature'],
            public_key_pem=sign_result['public_key']
        )
        
        # Verify token reference in database
        query = text("""
            SELECT token_id, units_deducted, units_remaining
            FROM consumption_logs
            WHERE id = :id
        """)
        row = db_session.execute(
            query,
            {'id': result['consumption_log_id']}
        ).fetchone()
        
        assert str(row[0]) == test_prepaid_token['token_uuid']
        assert float(row[1]) == consumption_kwh
        assert float(row[2]) == 100.0 - consumption_kwh


class TestLogConsumptionHCSLogging:
    """Test HCS logging in log_consumption"""
    
    @patch('app.services.smart_meter_service.TopicMessageSubmitTransaction')
    def test_consumption_logged_to_hcs(
        self, mock_transaction_class, smart_meter_service, 
        test_meter_with_keypair, db_session
    ):
        """Test that consumption is logged to HCS (FR-9.8)"""
        meter_id = test_meter_with_keypair
        consumption_kwh = 15.5
        timestamp = 1234567890
        
        # Mock HCS transaction
        mock_transaction = MagicMock()
        mock_receipt = MagicMock()
        mock_receipt.topicSequenceNumber = 12345
        mock_response = MagicMock()
        mock_response.getReceipt.return_value = mock_receipt
        mock_transaction.execute.return_value = mock_response
        mock_transaction_class.return_value = mock_transaction
        
        # Configure mock methods to return self for chaining
        mock_transaction.setTopicId.return_value = mock_transaction
        mock_transaction.setMessage.return_value = mock_transaction
        
        # Sign consumption
        sign_result = smart_meter_service.sign_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp
        )
        
        # Log consumption
        result = smart_meter_service.log_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp,
            signature=sign_result['signature'],
            public_key_pem=sign_result['public_key']
        )
        
        # Verify HCS transaction was called
        assert mock_transaction_class.called
        assert mock_transaction.setTopicId.called
        assert mock_transaction.setMessage.called
        assert mock_transaction.execute.called
        
        # Verify HCS sequence number returned
        assert result['hcs_sequence_number'] == 12345
        assert result['hcs_topic_id'] is not None
    
    @patch('app.services.smart_meter_service.TopicMessageSubmitTransaction')
    def test_hcs_message_includes_signature_status(
        self, mock_transaction_class, smart_meter_service,
        test_meter_with_keypair
    ):
        """Test that HCS message includes signature verification status (FR-9.9)"""
        meter_id = test_meter_with_keypair
        consumption_kwh = 15.5
        timestamp = 1234567890
        
        # Mock HCS transaction
        mock_transaction = MagicMock()
        mock_receipt = MagicMock()
        mock_receipt.topicSequenceNumber = 12345
        mock_response = MagicMock()
        mock_response.getReceipt.return_value = mock_receipt
        mock_transaction.execute.return_value = mock_response
        mock_transaction_class.return_value = mock_transaction
        
        # Configure mock methods
        mock_transaction.setTopicId.return_value = mock_transaction
        mock_transaction.setMessage.return_value = mock_transaction
        
        # Sign consumption
        sign_result = smart_meter_service.sign_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp
        )
        
        # Log consumption
        smart_meter_service.log_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp,
            signature=sign_result['signature'],
            public_key_pem=sign_result['public_key']
        )
        
        # Get the message that was sent to HCS
        call_args = mock_transaction.setMessage.call_args
        message_json = call_args[0][0]
        
        # Parse message
        import json
        message = json.loads(message_json)
        
        # Verify message format
        assert message['type'] == 'SMART_METER_CONSUMPTION'
        assert 'signature' in message
        assert message['signature_valid'] is True
        assert message['consumption_kwh'] == consumption_kwh
        assert message['timestamp'] == timestamp
    
    def test_hcs_logging_failure_does_not_block_consumption(
        self, smart_meter_service, test_meter_with_keypair, db_session
    ):
        """Test that HCS logging failure doesn't prevent consumption logging"""
        meter_id = test_meter_with_keypair
        consumption_kwh = 15.5
        timestamp = 1234567890
        
        # Sign consumption
        sign_result = smart_meter_service.sign_consumption(
            meter_id=meter_id,
            consumption_kwh=consumption_kwh,
            timestamp=timestamp
        )
        
        # Mock HCS to raise exception
        with patch('hedera.TopicMessageSubmitTransaction') as mock_tx:
            mock_tx.side_effect = Exception("HCS unavailable")
            
            # Should not raise exception
            result = smart_meter_service.log_consumption(
                meter_id=meter_id,
                consumption_kwh=consumption_kwh,
                timestamp=timestamp,
                signature=sign_result['signature'],
                public_key_pem=sign_result['public_key']
            )
        
        # Verify consumption still logged
        assert result['signature_valid'] is True
        assert result['hcs_sequence_number'] is None
        
        # Verify database record exists
        query = text("""
            SELECT id FROM consumption_logs
            WHERE id = :id
        """)
        row = db_session.execute(
            query,
            {'id': result['consumption_log_id']}
        ).fetchone()
        
        assert row is not None


class TestLogConsumptionErrorHandling:
    """Test error handling in log_consumption"""
    
    def test_rollback_on_signature_verification_failure(
        self, smart_meter_service, test_meter_with_keypair, db_session
    ):
        """Test that database is rolled back on signature verification failure"""
        meter_id = test_meter_with_keypair
        consumption_kwh = 15.5
        timestamp = 1234567890
        
        # Get public key
        public_key = smart_meter_service.get_public_key(meter_id)
        
        # Get initial consumption log count
        count_query = text("SELECT COUNT(*) FROM consumption_logs WHERE meter_id = :meter_id")
        initial_count = db_session.execute(count_query, {'meter_id': meter_id}).scalar()
        
        # Try to log with invalid signature
        try:
            smart_meter_service.log_consumption(
                meter_id=meter_id,
                consumption_kwh=consumption_kwh,
                timestamp=timestamp,
                signature="0" * 128,  # Invalid
                public_key_pem=public_key
            )
        except SmartMeterError:
            pass
        
        # Verify no consumption log was created
        final_count = db_session.execute(count_query, {'meter_id': meter_id}).scalar()
        assert final_count == initial_count
    
    def test_missing_meter_handled_gracefully(
        self, smart_meter_service
    ):
        """Test that missing meter is handled gracefully"""
        fake_meter_id = str(uuid.uuid4())
        
        # Should raise error
        with pytest.raises(SmartMeterError):
            smart_meter_service.log_consumption(
                meter_id=fake_meter_id,
                consumption_kwh=15.5,
                timestamp=1234567890,
                signature="0" * 128,
                public_key_pem="fake_key"
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
