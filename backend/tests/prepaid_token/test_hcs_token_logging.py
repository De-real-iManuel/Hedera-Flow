"""
Tests for HCS (Hedera Consensus Service) token issuance logging.

This module tests the log_token_issuance_to_hcs() method which creates
immutable blockchain records of prepaid token issuance for audit and
transparency purposes.

Requirements:
    - FR-8.7: System shall log token issuance to HCS with tag PREPAID_TOKEN_ISSUED
    - US-13: Token issuance logged to HCS with all relevant details
    - Task 1.4: HCS Logging - Token Issuance
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import json
import hashlib

from app.services.prepaid_token_service import PrepaidTokenService, PrepaidTokenError


class TestHCSTokenLogging:
    """Test suite for HCS token issuance logging"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def mock_hedera_service(self):
        """Mock Hedera service with HCS capabilities"""
        service = Mock()
        service.client = Mock()
        return service
    
    @pytest.fixture
    def prepaid_service(self, mock_db, mock_hedera_service):
        """Create PrepaidTokenService with mocked dependencies"""
        with patch('app.services.prepaid_token_service.get_hedera_service', return_value=mock_hedera_service):
            service = PrepaidTokenService(mock_db)
            return service
    
    def test_log_token_issuance_success_hbar(self, prepaid_service):
        """
        Test successful HCS logging for HBAR token issuance.
        
        Verifies:
        - Message format matches specification
        - User ID is anonymized
        - HCS transaction is submitted correctly
        - Sequence number is returned
        """
        # Arrange
        topic_id = "0.0.5078302"
        token_id = "TOKEN-ES-2026-001"
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        meter_id = "ESP-12345678"
        units_purchased = 125.0
        amount_hbar = 147.0
        amount_fiat = 50.0
        currency = "EUR"
        exchange_rate = 0.34
        tariff_rate = 0.40
        tx_id = "0.0.123456@1234567890.123"
        
        # Mock HCS response
        mock_receipt = Mock()
        mock_receipt.topicSequenceNumber = 12345
        mock_response = Mock()
        mock_response.getReceipt = Mock(return_value=mock_receipt)
        
        with patch('hedera.TopicMessageSubmitTransaction') as mock_tx_class, \
             patch('hedera.TopicId') as mock_topic_id:
            mock_tx = Mock()
            mock_tx.setTopicId = Mock(return_value=mock_tx)
            mock_tx.setMessage = Mock(return_value=mock_tx)
            mock_tx.execute = Mock(return_value=mock_response)
            mock_tx_class.return_value = mock_tx
            mock_topic_id.fromString = Mock(return_value=Mock())
            
            # Act
            result = prepaid_service.log_token_issuance_to_hcs(
                topic_id=topic_id,
                token_id=token_id,
                user_id=user_id,
                meter_id=meter_id,
                units_purchased=units_purchased,
                amount_hbar=amount_hbar,
                amount_usdc=None,
                amount_fiat=amount_fiat,
                currency=currency,
                exchange_rate=exchange_rate,
                tariff_rate=tariff_rate,
                tx_id=tx_id
            )
        
        # Assert
        assert result['topic_id'] == topic_id
        assert result['sequence_number'] == 12345
        assert result['message']['type'] == 'PREPAID_TOKEN_ISSUED'
        assert result['message']['token_id'] == token_id
        assert result['message']['meter_id'] == meter_id
        assert result['message']['units_purchased'] == units_purchased
        assert result['message']['amount_hbar'] == amount_hbar
        assert result['message']['amount_usdc'] is None
        assert result['message']['amount_fiat'] == amount_fiat
        assert result['message']['currency'] == currency
        assert result['message']['exchange_rate'] == exchange_rate
        assert result['message']['tariff_rate'] == tariff_rate
        assert result['message']['tx_id'] == tx_id
        assert 'timestamp' in result['message']
        
        # Verify user ID is anonymized
        assert result['message']['user_id'] != user_id
        assert result['message']['user_id'].startswith('user-')
    
    def test_log_token_issuance_success_usdc(self, prepaid_service):
        """
        Test successful HCS logging for USDC token issuance.
        
        Verifies:
        - USDC amount is logged correctly
        - HBAR amount is None
        """
        # Arrange
        topic_id = "0.0.5078302"
        token_id = "TOKEN-US-2026-001"
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        meter_id = "USA-87654321"
        units_purchased = 100.0
        amount_usdc = 50.0
        amount_fiat = 50.0
        currency = "USD"
        exchange_rate = 1.0
        tariff_rate = 0.50
        tx_id = "0.0.654321@9876543210.456"
        
        # Mock HCS response
        mock_receipt = Mock()
        mock_receipt.topicSequenceNumber = 54321
        mock_response = Mock()
        mock_response.getReceipt = Mock(return_value=mock_receipt)
        
        with patch('hedera.TopicMessageSubmitTransaction') as mock_tx_class, \
             patch('hedera.TopicId') as mock_topic_id:
            mock_tx = Mock()
            mock_tx.setTopicId = Mock(return_value=mock_tx)
            mock_tx.setMessage = Mock(return_value=mock_tx)
            mock_tx.execute = Mock(return_value=mock_response)
            mock_tx_class.return_value = mock_tx
            mock_topic_id.fromString = Mock(return_value=Mock())
            
            # Act
            result = prepaid_service.log_token_issuance_to_hcs(
                topic_id=topic_id,
                token_id=token_id,
                user_id=user_id,
                meter_id=meter_id,
                units_purchased=units_purchased,
                amount_hbar=None,
                amount_usdc=amount_usdc,
                amount_fiat=amount_fiat,
                currency=currency,
                exchange_rate=exchange_rate,
                tariff_rate=tariff_rate,
                tx_id=tx_id
            )
        
        # Assert
        assert result['message']['amount_hbar'] is None
        assert result['message']['amount_usdc'] == amount_usdc
        assert result['sequence_number'] == 54321
    
    def test_user_id_anonymization(self, prepaid_service):
        """
        Test that user ID is properly anonymized using hash.
        
        Verifies:
        - User ID is hashed with salt
        - Same user ID produces same anonymized ID (deterministic)
        - Different user IDs produce different anonymized IDs
        """
        # Arrange
        user_id_1 = "550e8400-e29b-41d4-a716-446655440000"
        user_id_2 = "660e8400-e29b-41d4-a716-446655440001"
        
        # Mock HCS response
        mock_receipt = Mock()
        mock_receipt.topicSequenceNumber = 12345
        mock_response = Mock()
        mock_response.getReceipt = Mock(return_value=mock_receipt)
        
        with patch('hedera.TopicMessageSubmitTransaction') as mock_tx_class, \
             patch('hedera.TopicId') as mock_topic_id:
            mock_tx = Mock()
            mock_tx.setTopicId = Mock(return_value=mock_tx)
            mock_tx.setMessage = Mock(return_value=mock_tx)
            mock_tx.execute = Mock(return_value=mock_response)
            mock_tx_class.return_value = mock_tx
            mock_topic_id.fromString = Mock(return_value=Mock())
            
            # Act - Log for user 1 twice
            result_1a = prepaid_service.log_token_issuance_to_hcs(
                topic_id="0.0.5078302",
                token_id="TOKEN-ES-2026-001",
                user_id=user_id_1,
                meter_id="ESP-12345678",
                units_purchased=125.0,
                amount_hbar=147.0,
                amount_usdc=None,
                amount_fiat=50.0,
                currency="EUR",
                exchange_rate=0.34,
                tariff_rate=0.40,
                tx_id="0.0.123456@1234567890.123"
            )
            
            result_1b = prepaid_service.log_token_issuance_to_hcs(
                topic_id="0.0.5078302",
                token_id="TOKEN-ES-2026-002",
                user_id=user_id_1,
                meter_id="ESP-12345678",
                units_purchased=125.0,
                amount_hbar=147.0,
                amount_usdc=None,
                amount_fiat=50.0,
                currency="EUR",
                exchange_rate=0.34,
                tariff_rate=0.40,
                tx_id="0.0.123456@1234567890.124"
            )
            
            # Act - Log for user 2
            result_2 = prepaid_service.log_token_issuance_to_hcs(
                topic_id="0.0.5078302",
                token_id="TOKEN-ES-2026-003",
                user_id=user_id_2,
                meter_id="ESP-87654321",
                units_purchased=125.0,
                amount_hbar=147.0,
                amount_usdc=None,
                amount_fiat=50.0,
                currency="EUR",
                exchange_rate=0.34,
                tariff_rate=0.40,
                tx_id="0.0.123456@1234567890.125"
            )
        
        # Assert
        # Same user ID should produce same anonymized ID (deterministic)
        assert result_1a['message']['user_id'] == result_1b['message']['user_id']
        
        # Different user IDs should produce different anonymized IDs
        assert result_1a['message']['user_id'] != result_2['message']['user_id']
        
        # Anonymized IDs should not contain original user ID
        assert user_id_1 not in result_1a['message']['user_id']
        assert user_id_2 not in result_2['message']['user_id']
        
        # Anonymized IDs should have expected format
        assert result_1a['message']['user_id'].startswith('user-')
        assert result_2['message']['user_id'].startswith('user-')
    
    def test_hcs_logging_failure(self, prepaid_service):
        """
        Test error handling when HCS logging fails.
        
        Verifies:
        - Method returns gracefully instead of raising exception
        - Error details are included in response
        - Status indicates failure
        """
        # Arrange
        with patch('hedera.TopicMessageSubmitTransaction') as mock_tx_class, \
             patch('hedera.TopicId') as mock_topic_id:
            mock_tx = Mock()
            mock_tx.setTopicId = Mock(return_value=mock_tx)
            mock_tx.setMessage = Mock(return_value=mock_tx)
            mock_tx.execute = Mock(side_effect=Exception("HCS network error"))
            mock_tx_class.return_value = mock_tx
            mock_topic_id.fromString = Mock(return_value=Mock())
            
            # Act - Should NOT raise exception
            result = prepaid_service.log_token_issuance_to_hcs(
                topic_id="0.0.5078302",
                token_id="TOKEN-ES-2026-001",
                user_id="550e8400-e29b-41d4-a716-446655440000",
                meter_id="ESP-12345678",
                units_purchased=125.0,
                amount_hbar=147.0,
                amount_usdc=None,
                amount_fiat=50.0,
                currency="EUR",
                exchange_rate=0.34,
                tariff_rate=0.40,
                tx_id="0.0.123456@1234567890.123"
            )
            
            # Assert
            assert result is not None
            assert result['status'] == 'failed'
            assert 'error' in result
            assert "HCS network error" in result['error']
    
    def test_message_format_compliance(self, prepaid_service):
        """
        Test that HCS message format matches specification exactly.
        
        Verifies all required fields are present:
        - type: "PREPAID_TOKEN_ISSUED"
        - token_id, user_id (anonymized), meter_id
        - units_purchased
        - amount_hbar, amount_usdc, amount_fiat
        - currency, exchange_rate, tariff_rate
        - tx_id, timestamp
        """
        # Arrange
        mock_receipt = Mock()
        mock_receipt.topicSequenceNumber = 12345
        mock_response = Mock()
        mock_response.getReceipt = Mock(return_value=mock_receipt)
        
        captured_message = None
        
        def capture_message(msg):
            nonlocal captured_message
            captured_message = msg
            return Mock()
        
        with patch('hedera.TopicMessageSubmitTransaction') as mock_tx_class, \
             patch('hedera.TopicId') as mock_topic_id:
            mock_tx = Mock()
            mock_tx.setTopicId = Mock(return_value=mock_tx)
            mock_tx.setMessage = Mock(side_effect=capture_message)
            mock_tx.execute = Mock(return_value=mock_response)
            mock_tx_class.return_value = mock_tx
            mock_topic_id.fromString = Mock(return_value=Mock())
            
            # Act
            prepaid_service.log_token_issuance_to_hcs(
                topic_id="0.0.5078302",
                token_id="TOKEN-ES-2026-001",
                user_id="550e8400-e29b-41d4-a716-446655440000",
                meter_id="ESP-12345678",
                units_purchased=125.0,
                amount_hbar=147.0,
                amount_usdc=None,
                amount_fiat=50.0,
                currency="EUR",
                exchange_rate=0.34,
                tariff_rate=0.40,
                tx_id="0.0.123456@1234567890.123"
            )
        
        # Assert
        assert captured_message is not None
        message_dict = json.loads(captured_message)
        
        # Verify all required fields
        required_fields = [
            'type', 'token_id', 'user_id', 'meter_id',
            'units_purchased', 'amount_hbar', 'amount_usdc',
            'amount_fiat', 'currency', 'exchange_rate',
            'tariff_rate', 'tx_id', 'timestamp'
        ]
        
        for field in required_fields:
            assert field in message_dict, f"Missing required field: {field}"
        
        # Verify field values
        assert message_dict['type'] == 'PREPAID_TOKEN_ISSUED'
        assert message_dict['token_id'] == 'TOKEN-ES-2026-001'
        assert message_dict['meter_id'] == 'ESP-12345678'
        assert message_dict['units_purchased'] == 125.0
        assert message_dict['amount_hbar'] == 147.0
        assert message_dict['amount_usdc'] is None
        assert message_dict['amount_fiat'] == 50.0
        assert message_dict['currency'] == 'EUR'
        assert message_dict['exchange_rate'] == 0.34
        assert message_dict['tariff_rate'] == 0.40
        assert message_dict['tx_id'] == '0.0.123456@1234567890.123'
        assert isinstance(message_dict['timestamp'], int)
