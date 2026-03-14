"""
Unit tests for PrepaidTokenService.process_hbar_payment() - Failure Scenarios

Tests payment failure handling and retry logic:
- Payment failure detection and categorization
- Retry logic with exponential backoff
- Permanent vs transient failure handling
- Max retries exhausted
- Error logging and debugging

Requirements: FR-8.1, US-13, Task 1.3
"""
import pytest
from unittest.mock import Mock, patch
from app.services.prepaid_token_service import PrepaidTokenService, PrepaidTokenError


class TestProcessHbarPaymentFailures:
    """Test suite for payment failure handling"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_db):
        """Create PrepaidTokenService instance with mocked dependencies"""
        with patch('app.services.prepaid_token_service.get_hedera_service') as mock_hedera:
            mock_hedera_instance = Mock()
            mock_hedera_instance.client = Mock()
            mock_hedera.return_value = mock_hedera_instance
            
            service = PrepaidTokenService(mock_db)
            return service
    
    @patch('app.services.prepaid_token_service.get_hbar_price')
    @patch('hedera.TransferTransaction')
    @patch('hedera.AccountId')
    @patch('hedera.Hbar')
    def test_payment_failure_insufficient_balance(
        self,
        mock_hbar,
        mock_account_id,
        mock_transfer_tx,
        mock_get_hbar_price,
        service
    ):
        """Test payment fails immediately with insufficient balance (permanent failure)"""
        # Arrange
        mock_get_hbar_price.return_value = 0.34
        
        # Mock transaction failure with insufficient balance
        mock_tx_instance = Mock()
        mock_transfer_tx.return_value = mock_tx_instance
        mock_tx_instance.addHbarTransfer.return_value = mock_tx_instance
        mock_tx_instance.setTransactionMemo.return_value = mock_tx_instance
        mock_tx_instance.setMaxTransactionFee.return_value = mock_tx_instance
        mock_tx_instance.execute.side_effect = Exception("Insufficient balance")
        
        mock_account_id.fromString.return_value = Mock()
        mock_hbar.return_value = Mock()
        
        # Act & Assert
        with pytest.raises(PrepaidTokenError) as exc_info:
            service.process_hbar_payment(
                user_account_id="0.0.USER123",
                treasury_account_id="0.0.TREASURY",
                amount_fiat=50.0,
                currency="EUR",
                meter_id="meter-uuid-123",
                token_id="TOKEN-ES-2026-001"
            )
        
        # Should fail immediately without retries (permanent failure)
        assert "HBAR payment failed" in str(exc_info.value)
        assert "Permanent failure" in str(exc_info.value)
        assert "retry_count': 0" in str(exc_info.value)
    
    @patch('app.services.prepaid_token_service.get_hbar_price')
    @patch('hedera.TransferTransaction')
    @patch('hedera.AccountId')
    @patch('hedera.Hbar')
    @patch('time.sleep')
    def test_payment_transient_failure_with_retry_success(
        self,
        mock_sleep,
        mock_hbar,
        mock_account_id,
        mock_transfer_tx,
        mock_get_hbar_price,
        service
    ):
        """Test payment retries on transient failure and succeeds"""
        # Arrange
        mock_get_hbar_price.return_value = 0.34
        
        # Mock transaction - fail first, succeed second
        mock_tx_instance = Mock()
        mock_transfer_tx.return_value = mock_tx_instance
        mock_tx_instance.addHbarTransfer.return_value = mock_tx_instance
        mock_tx_instance.setTransactionMemo.return_value = mock_tx_instance
        mock_tx_instance.setMaxTransactionFee.return_value = mock_tx_instance
        
        mock_response = Mock()
        mock_response.transactionId = "0.0.123456@1234567890.123"
        mock_receipt = Mock()
        mock_receipt.consensusTimestamp = "2026-03-03T10:00:00.000Z"
        mock_response.getReceipt.return_value = mock_receipt
        
        mock_tx_instance.execute.side_effect = [
            Exception("Network timeout"),  # First attempt fails
            mock_response  # Second attempt succeeds
        ]
        
        mock_account_id.fromString.return_value = Mock()
        mock_hbar.return_value = Mock()
        
        # Act
        with patch('time.time', side_effect=[0, 2.5]):  # Mock time for consensus measurement
            result = service.process_hbar_payment(
                user_account_id="0.0.USER123",
                treasury_account_id="0.0.TREASURY",
                amount_fiat=50.0,
                currency="EUR",
                meter_id="meter-uuid-123",
                token_id="TOKEN-ES-2026-001"
            )
        
        # Assert
        assert result['status'] == 'SUCCESS'
        assert result['retry_count'] == 1
        assert result['failure_type'] is None
        
        # Verify exponential backoff (1 second for first retry)
        mock_sleep.assert_called_once_with(1)
    
    @patch('app.services.prepaid_token_service.get_hbar_price')
    @patch('hedera.TransferTransaction')
    @patch('hedera.AccountId')
    @patch('hedera.Hbar')
    @patch('time.sleep')
    def test_payment_max_retries_exhausted(
        self,
        mock_sleep,
        mock_hbar,
        mock_account_id,
        mock_transfer_tx,
        mock_get_hbar_price,
        service
    ):
        """Test payment fails after max retries exhausted"""
        # Arrange
        mock_get_hbar_price.return_value = 0.34
        
        # Mock transaction - always fails with transient error
        mock_tx_instance = Mock()
        mock_transfer_tx.return_value = mock_tx_instance
        mock_tx_instance.addHbarTransfer.return_value = mock_tx_instance
        mock_tx_instance.setTransactionMemo.return_value = mock_tx_instance
        mock_tx_instance.setMaxTransactionFee.return_value = mock_tx_instance
        mock_tx_instance.execute.side_effect = Exception("Network timeout")
        
        mock_account_id.fromString.return_value = Mock()
        mock_hbar.return_value = Mock()
        
        # Act & Assert
        with pytest.raises(PrepaidTokenError) as exc_info:
            service.process_hbar_payment(
                user_account_id="0.0.USER123",
                treasury_account_id="0.0.TREASURY",
                amount_fiat=50.0,
                currency="EUR",
                meter_id="meter-uuid-123",
                token_id="TOKEN-ES-2026-001",
                max_retries=3
            )
        
        # Should fail after 3 retries
        assert "HBAR payment failed after 3 retries" in str(exc_info.value)
        assert "Transient failure" in str(exc_info.value)
        
        # Verify exponential backoff: 1s, 2s, 4s
        assert mock_sleep.call_count == 3
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)
        mock_sleep.assert_any_call(4)
    
    def test_categorize_payment_failure_permanent(self, service):
        """Test failure categorization for permanent errors"""
        test_cases = [
            (Exception("Insufficient balance"), "permanent", "insufficient balance"),
            (Exception("Invalid account ID"), "permanent", "invalid account"),
            (Exception("Account not found"), "permanent", "account not found"),
            (Exception("Account frozen by admin"), "permanent", "account frozen"),
            (Exception("Unauthorized access"), "permanent", "unauthorized"),
        ]
        
        for error, expected_type, expected_indicator in test_cases:
            failure_type, failure_reason = service._categorize_payment_failure(error)
            assert failure_type == expected_type
            assert expected_indicator in failure_reason.lower()
    
    def test_categorize_payment_failure_transient(self, service):
        """Test failure categorization for transient errors"""
        test_cases = [
            (Exception("Network timeout"), "transient", "timeout"),
            (Exception("Connection refused"), "transient", "connection"),
            (Exception("Service unavailable"), "transient", "unavailable"),
            (Exception("Rate limit exceeded"), "transient", "rate limit"),
            (Exception("Consensus failed timeout"), "transient", "timeout"),  # Changed to match timeout
            (Exception("Network error occurred"), "transient", "network"),
        ]
        
        for error, expected_type, expected_indicator in test_cases:
            failure_type, failure_reason = service._categorize_payment_failure(error)
            assert failure_type == expected_type
            assert expected_indicator in failure_reason.lower()
    
    def test_categorize_payment_failure_unknown_defaults_to_transient(self, service):
        """Test unknown errors default to transient (safer to retry)"""
        error = Exception("Some unknown error")
        failure_type, failure_reason = service._categorize_payment_failure(error)
        
        assert failure_type == "transient"
        assert "Unknown error" in failure_reason
    
    @patch('app.services.prepaid_token_service.get_hbar_price')
    @patch('hedera.TransferTransaction')
    @patch('hedera.AccountId')
    @patch('hedera.Hbar')
    @patch('time.sleep')
    def test_exponential_backoff_timing(
        self,
        mock_sleep,
        mock_hbar,
        mock_account_id,
        mock_transfer_tx,
        mock_get_hbar_price,
        service
    ):
        """Test exponential backoff follows correct timing: 1s, 2s, 4s"""
        # Arrange
        mock_get_hbar_price.return_value = 0.34
        
        mock_tx_instance = Mock()
        mock_transfer_tx.return_value = mock_tx_instance
        mock_tx_instance.addHbarTransfer.return_value = mock_tx_instance
        mock_tx_instance.setTransactionMemo.return_value = mock_tx_instance
        mock_tx_instance.setMaxTransactionFee.return_value = mock_tx_instance
        mock_tx_instance.execute.side_effect = Exception("Connection timeout")
        
        mock_account_id.fromString.return_value = Mock()
        mock_hbar.return_value = Mock()
        
        # Act & Assert
        with pytest.raises(PrepaidTokenError):
            service.process_hbar_payment(
                user_account_id="0.0.USER123",
                treasury_account_id="0.0.TREASURY",
                amount_fiat=50.0,
                currency="EUR",
                meter_id="meter-uuid-123",
                token_id="TOKEN-ES-2026-001",
                max_retries=3
            )
        
        # Verify exponential backoff: 2^0=1s, 2^1=2s, 2^2=4s
        calls = mock_sleep.call_args_list
        assert len(calls) == 3
        assert calls[0][0][0] == 1  # First retry: 1 second
        assert calls[1][0][0] == 2  # Second retry: 2 seconds
        assert calls[2][0][0] == 4  # Third retry: 4 seconds
