"""
Unit tests for PrepaidTokenService.process_hbar_payment()

Tests the HBAR payment processing flow:
- Exchange rate fetching
- HBAR amount calculation
- Transaction submission to Hedera testnet
- Consensus waiting
- Transaction ID storage

Requirements: FR-8.1, US-13, Task 1.3
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from app.services.prepaid_token_service import PrepaidTokenService, PrepaidTokenError


class TestProcessHbarPayment:
    """Test suite for process_hbar_payment method"""
    
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
    @patch('time.time')
    def test_process_hbar_payment_success(
        self,
        mock_time,
        mock_hbar,
        mock_account_id,
        mock_transfer_tx,
        mock_get_hbar_price,
        service
    ):
        """Test successful HBAR payment processing"""
        # Arrange
        mock_get_hbar_price.return_value = 0.34  # 1 HBAR = 0.34 EUR
        
        # Mock time for consensus measurement
        mock_time.time.side_effect = [0, 2.5]  # 2.5 seconds for consensus
        
        # Mock Hedera transaction
        mock_tx_instance = Mock()
        mock_transfer_tx.return_value = mock_tx_instance
        mock_tx_instance.addHbarTransfer.return_value = mock_tx_instance
        mock_tx_instance.setTransactionMemo.return_value = mock_tx_instance
        mock_tx_instance.setMaxTransactionFee.return_value = mock_tx_instance
        
        # Mock transaction response
        mock_response = Mock()
        mock_tx_instance.execute.return_value = mock_response
        mock_response.transactionId = "0.0.123456@1234567890.123"
        
        # Mock receipt
        mock_receipt = Mock()
        mock_receipt.consensusTimestamp = "2026-03-03T10:00:00.000Z"
        mock_response.getReceipt.return_value = mock_receipt
        
        # Mock AccountId
        mock_from_account = Mock()
        mock_to_account = Mock()
        mock_account_id.fromString.side_effect = [mock_from_account, mock_to_account]
        
        # Mock Hbar
        mock_hbar.side_effect = lambda x: Mock(value=x)
        
        # Act
        result = service.process_hbar_payment(
            user_account_id="0.0.USER123",
            treasury_account_id="0.0.TREASURY",
            amount_fiat=50.0,
            currency="EUR",
            meter_id="meter-uuid-123",
            token_id="TOKEN-ES-2026-001",
            use_cache=True
        )
        
        # Assert
        assert result['status'] == 'SUCCESS'
        assert result['amount_hbar'] == pytest.approx(147.06, rel=0.01)  # 50 / 0.34
        assert result['exchange_rate'] == 0.34
        assert result['tx_id'] == "0.0.123456@1234567890.123"
        assert result['consensus_timestamp'] == "2026-03-03T10:00:00.000Z"
        assert result['consensus_time_seconds'] == 2.5
        
        # Verify transaction was created correctly
        mock_transfer_tx.assert_called_once()
        mock_tx_instance.addHbarTransfer.assert_any_call(mock_from_account, mock_hbar.return_value)
        mock_tx_instance.addHbarTransfer.assert_any_call(mock_to_account, mock_hbar.return_value)
        mock_tx_instance.setTransactionMemo.assert_called_once_with("Prepaid token: TOKEN-ES-2026-001")
        mock_tx_instance.execute.assert_called_once()
    
    @patch('app.services.prepaid_token_service.get_hbar_price')
    def test_process_hbar_payment_exchange_rate_failure(
        self,
        mock_get_hbar_price,
        service
    ):
        """Test HBAR payment fails when exchange rate fetch fails"""
        # Arrange
        mock_get_hbar_price.side_effect = Exception("Exchange rate API unavailable")
        
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
        
        assert "Failed to fetch exchange rate" in str(exc_info.value)
    
    @patch('app.services.prepaid_token_service.get_hbar_price')
    @patch('hedera.TransferTransaction')
    @patch('hedera.AccountId')
    @patch('hedera.Hbar')
    def test_process_hbar_payment_transaction_failure(
        self,
        mock_hbar,
        mock_account_id,
        mock_transfer_tx,
        mock_get_hbar_price,
        service
    ):
        """Test HBAR payment fails when transaction submission fails"""
        # Arrange
        mock_get_hbar_price.return_value = 0.34
        
        # Mock transaction failure
        mock_tx_instance = Mock()
        mock_transfer_tx.return_value = mock_tx_instance
        mock_tx_instance.addHbarTransfer.return_value = mock_tx_instance
        mock_tx_instance.setTransactionMemo.return_value = mock_tx_instance
        mock_tx_instance.setMaxTransactionFee.return_value = mock_tx_instance
        mock_tx_instance.execute.side_effect = Exception("Insufficient balance")
        
        # Mock AccountId
        mock_account_id.fromString.return_value = Mock()
        
        # Mock Hbar
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
        
        assert "HBAR payment failed" in str(exc_info.value)
    
    @patch('app.services.prepaid_token_service.get_hbar_price')
    @patch('hedera.TransferTransaction')
    @patch('hedera.AccountId')
    @patch('hedera.Hbar')
    @patch('time.time')
    def test_process_hbar_payment_slow_consensus(
        self,
        mock_time,
        mock_hbar,
        mock_account_id,
        mock_transfer_tx,
        mock_get_hbar_price,
        service
    ):
        """Test HBAR payment with slow consensus (> 5 seconds)"""
        # Arrange
        mock_get_hbar_price.return_value = 0.34
        
        # Mock time for slow consensus
        mock_time.time.side_effect = [0, 7.5]  # 7.5 seconds for consensus
        
        # Mock Hedera transaction
        mock_tx_instance = Mock()
        mock_transfer_tx.return_value = mock_tx_instance
        mock_tx_instance.addHbarTransfer.return_value = mock_tx_instance
        mock_tx_instance.setTransactionMemo.return_value = mock_tx_instance
        mock_tx_instance.setMaxTransactionFee.return_value = mock_tx_instance
        
        # Mock transaction response
        mock_response = Mock()
        mock_tx_instance.execute.return_value = mock_response
        mock_response.transactionId = "0.0.123456@1234567890.123"
        
        # Mock receipt
        mock_receipt = Mock()
        mock_receipt.consensusTimestamp = "2026-03-03T10:00:00.000Z"
        mock_response.getReceipt.return_value = mock_receipt
        
        # Mock AccountId
        mock_account_id.fromString.return_value = Mock()
        
        # Mock Hbar
        mock_hbar.return_value = Mock()
        
        # Act
        result = service.process_hbar_payment(
            user_account_id="0.0.USER123",
            treasury_account_id="0.0.TREASURY",
            amount_fiat=50.0,
            currency="EUR",
            meter_id="meter-uuid-123",
            token_id="TOKEN-ES-2026-001"
        )
        
        # Assert - should still succeed but log warning
        assert result['status'] == 'SUCCESS'
        assert result['consensus_time_seconds'] == 7.5
    
    @patch('app.services.prepaid_token_service.get_hbar_price')
    @patch('hedera.TransferTransaction')
    @patch('hedera.AccountId')
    @patch('hedera.Hbar')
    @patch('time.time')
    def test_process_hbar_payment_different_currencies(
        self,
        mock_time,
        mock_hbar,
        mock_account_id,
        mock_transfer_tx,
        mock_get_hbar_price,
        service
    ):
        """Test HBAR payment with different currencies"""
        # Test data for different currencies
        test_cases = [
            ("USD", 0.30, 50.0, 166.67),  # 50 USD / 0.30 = 166.67 HBAR
            ("INR", 25.0, 500.0, 20.0),   # 500 INR / 25 = 20 HBAR
            ("BRL", 1.5, 50.0, 33.33),    # 50 BRL / 1.5 = 33.33 HBAR
            ("NGN", 120.0, 5000.0, 41.67) # 5000 NGN / 120 = 41.67 HBAR
        ]
        
        for currency, exchange_rate, amount_fiat, expected_hbar in test_cases:
            # Arrange
            mock_get_hbar_price.return_value = exchange_rate
            mock_time.time.side_effect = [0, 2.0]
            
            # Mock Hedera transaction
            mock_tx_instance = Mock()
            mock_transfer_tx.return_value = mock_tx_instance
            mock_tx_instance.addHbarTransfer.return_value = mock_tx_instance
            mock_tx_instance.setTransactionMemo.return_value = mock_tx_instance
            mock_tx_instance.setMaxTransactionFee.return_value = mock_tx_instance
            
            # Mock transaction response
            mock_response = Mock()
            mock_tx_instance.execute.return_value = mock_response
            mock_response.transactionId = "0.0.123456@1234567890.123"
            
            # Mock receipt
            mock_receipt = Mock()
            mock_receipt.consensusTimestamp = "2026-03-03T10:00:00.000Z"
            mock_response.getReceipt.return_value = mock_receipt
            
            # Mock AccountId
            mock_account_id.fromString.return_value = Mock()
            
            # Mock Hbar
            mock_hbar.return_value = Mock()
            
            # Act
            result = service.process_hbar_payment(
                user_account_id="0.0.USER123",
                treasury_account_id="0.0.TREASURY",
                amount_fiat=amount_fiat,
                currency=currency,
                meter_id="meter-uuid-123",
                token_id=f"TOKEN-{currency}-2026-001"
            )
            
            # Assert
            assert result['status'] == 'SUCCESS'
            assert result['amount_hbar'] == pytest.approx(expected_hbar, rel=0.01)
            assert result['exchange_rate'] == exchange_rate
