"""
Tests for HCS error handling in prepaid token service.

This module tests that HCS logging failures do not prevent token creation.
When HCS logging fails, the system should:
1. Log the error
2. Return a failure status
3. Allow token creation to proceed

This is critical because payment has already been processed, and we don't
want to lose the token due to audit logging issues.

Requirements:
    - Task 1.4: Add error handling for HCS failures
    - FR-8.7: System shall log token issuance to HCS (but not block on failure)
"""

import pytest
from unittest.mock import Mock, patch
from app.services.prepaid_token_service import PrepaidTokenService


class TestHCSErrorHandling:
    """Test suite for HCS error handling"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def mock_hedera_service(self):
        """Mock Hedera service"""
        service = Mock()
        service.client = Mock()
        return service
    
    @pytest.fixture
    def prepaid_service(self, mock_db, mock_hedera_service):
        """Create PrepaidTokenService with mocked dependencies"""
        with patch('app.services.prepaid_token_service.get_hedera_service', return_value=mock_hedera_service):
            service = PrepaidTokenService(mock_db)
            return service
    
    def test_hcs_network_error_does_not_raise_exception(self, prepaid_service):
        """
        Test that HCS network errors do not raise exceptions.
        
        Verifies:
        - Method returns gracefully instead of raising
        - Result contains error information
        - Result indicates failure status
        """
        # Arrange
        with patch('hedera.TopicMessageSubmitTransaction') as mock_tx_class, \
             patch('hedera.TopicId') as mock_topic_id:
            mock_tx = Mock()
            mock_tx.setTopicId = Mock(return_value=mock_tx)
            mock_tx.setMessage = Mock(return_value=mock_tx)
            mock_tx.execute = Mock(side_effect=Exception("Network timeout"))
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
        assert result['topic_id'] == "0.0.5078302"
        assert result['sequence_number'] is None
        assert result['message'] is None
        assert 'error' in result
        assert 'Network timeout' in result['error']
    
    def test_hcs_consensus_error_returns_failure_status(self, prepaid_service):
        """
        Test that HCS consensus errors return failure status.
        
        Verifies:
        - Consensus failures are handled gracefully
        - Error details are captured
        """
        # Arrange
        with patch('hedera.TopicMessageSubmitTransaction') as mock_tx_class, \
             patch('hedera.TopicId') as mock_topic_id:
            mock_tx = Mock()
            mock_tx.setTopicId = Mock(return_value=mock_tx)
            mock_tx.setMessage = Mock(return_value=mock_tx)
            mock_response = Mock()
            mock_response.getReceipt = Mock(side_effect=Exception("Consensus timeout"))
            mock_tx.execute = Mock(return_value=mock_response)
            mock_tx_class.return_value = mock_tx
            mock_topic_id.fromString = Mock(return_value=Mock())
            
            # Act
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
        assert result['status'] == 'failed'
        assert 'Consensus timeout' in result['error']
    
    def test_hcs_invalid_topic_error_returns_failure_status(self, prepaid_service):
        """
        Test that invalid topic ID errors return failure status.
        
        Verifies:
        - Invalid topic IDs are handled gracefully
        - Error details are captured
        """
        # Arrange
        with patch('hedera.TopicMessageSubmitTransaction') as mock_tx_class, \
             patch('hedera.TopicId') as mock_topic_id:
            mock_topic_id.fromString = Mock(side_effect=Exception("Invalid topic ID"))
            mock_tx_class.return_value = Mock()
            
            # Act
            result = prepaid_service.log_token_issuance_to_hcs(
                topic_id="invalid-topic",
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
        assert result['status'] == 'failed'
        assert 'Invalid topic ID' in result['error']
    
    def test_hcs_success_returns_sequence_number(self, prepaid_service):
        """
        Test that successful HCS logging returns sequence number.
        
        Verifies:
        - Success case still works correctly
        - No 'status' or 'error' fields in success response
        """
        # Arrange
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
        assert result['topic_id'] == "0.0.5078302"
        assert result['sequence_number'] == 12345
        assert result['message'] is not None
        assert 'status' not in result  # Success doesn't have status field
        assert 'error' not in result   # Success doesn't have error field
    
    def test_hcs_failure_preserves_topic_id(self, prepaid_service):
        """
        Test that HCS failures preserve the topic ID in the result.
        
        This is important for debugging and manual audit log entry.
        
        Verifies:
        - Topic ID is included in failure response
        - Allows caller to know which topic failed
        """
        # Arrange
        with patch('hedera.TopicMessageSubmitTransaction') as mock_tx_class, \
             patch('hedera.TopicId') as mock_topic_id:
            mock_tx = Mock()
            mock_tx.setTopicId = Mock(return_value=mock_tx)
            mock_tx.setMessage = Mock(return_value=mock_tx)
            mock_tx.execute = Mock(side_effect=Exception("HCS unavailable"))
            mock_tx_class.return_value = mock_tx
            mock_topic_id.fromString = Mock(return_value=Mock())
            
            # Act
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
        assert result['topic_id'] == "0.0.5078302"
        assert result['status'] == 'failed'
    
    def test_multiple_hcs_failures_all_handled_gracefully(self, prepaid_service):
        """
        Test that multiple consecutive HCS failures are all handled gracefully.
        
        Verifies:
        - System can handle repeated failures
        - Each failure returns proper error information
        """
        # Arrange
        error_messages = [
            "Network timeout",
            "Consensus failed",
            "Topic unavailable"
        ]
        
        results = []
        
        for error_msg in error_messages:
            with patch('hedera.TopicMessageSubmitTransaction') as mock_tx_class, \
                 patch('hedera.TopicId') as mock_topic_id:
                mock_tx = Mock()
                mock_tx.setTopicId = Mock(return_value=mock_tx)
                mock_tx.setMessage = Mock(return_value=mock_tx)
                mock_tx.execute = Mock(side_effect=Exception(error_msg))
                mock_tx_class.return_value = mock_tx
                mock_topic_id.fromString = Mock(return_value=Mock())
                
                # Act
                result = prepaid_service.log_token_issuance_to_hcs(
                    topic_id="0.0.5078302",
                    token_id=f"TOKEN-ES-2026-{len(results)+1:03d}",
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
                results.append(result)
        
        # Assert
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result['status'] == 'failed'
            assert error_messages[i] in result['error']
            assert result['sequence_number'] is None
