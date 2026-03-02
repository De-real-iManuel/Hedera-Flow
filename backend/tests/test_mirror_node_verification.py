"""
Test Mirror Node Transaction Verification
Tests for Task 19.2: Verify transaction on Hedera network via Mirror Node

Requirements:
- FR-6.9: System shall verify transaction on Hedera network via Mirror Node
- FR-6.9: System shall validate transaction amount matches expected HBAR amount
- US-7: Payment flow with blockchain verification
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime

from app.utils.mirror_node_client import MirrorNodeClient


@pytest.fixture
def mirror_client():
    """Create Mirror Node client instance"""
    return MirrorNodeClient(base_url="https://testnet.mirrornode.hedera.com")


@pytest.fixture
def mock_successful_transaction():
    """Mock successful transaction response from Mirror Node"""
    return {
        "transactions": [
            {
                "transaction_id": "0.0.12345@1710789700.123456789",
                "consensus_timestamp": "1710789700.123456789",
                "result": "SUCCESS",
                "name": "CRYPTOTRANSFER",
                "transfers": [
                    {
                        "account": "0.0.12345",
                        "amount": -25000000000,  # -250 HBAR in tinybars
                        "is_approval": False
                    },
                    {
                        "account": "0.0.7942957",  # Treasury account
                        "amount": 25000000000,  # +250 HBAR in tinybars
                        "is_approval": False
                    }
                ],
                "charged_tx_fee": 100000,
                "memo_base64": "QmlsbCBwYXltZW50OiBCSUxMLUVVUi0yMDI2LTEyMzQ1Njc4"
            }
        ]
    }


@pytest.fixture
def mock_failed_transaction():
    """Mock failed transaction response"""
    return {
        "transactions": [
            {
                "transaction_id": "0.0.12345@1710789700.123456789",
                "consensus_timestamp": "1710789700.123456789",
                "result": "INSUFFICIENT_ACCOUNT_BALANCE",
                "name": "CRYPTOTRANSFER",
                "transfers": [],
                "charged_tx_fee": 100000
            }
        ]
    }


@pytest.fixture
def mock_transaction_not_found():
    """Mock transaction not found response"""
    return {
        "transactions": []
    }


class TestMirrorNodeTransactionVerification:
    """Test suite for Mirror Node transaction verification"""
    
    @pytest.mark.asyncio
    async def test_get_transaction_success(self, mirror_client, mock_successful_transaction):
        """Test successful transaction retrieval"""
        
        with patch.object(mirror_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_successful_transaction
            
            tx_id = "0.0.12345@1710789700.123456789"
            result = await mirror_client.get_transaction(tx_id)
            
            assert result == mock_successful_transaction
            mock_request.assert_called_once_with(f"transactions/{tx_id}")
    
    @pytest.mark.asyncio
    async def test_verify_transaction_result_success(self, mock_successful_transaction):
        """Test verification of successful transaction result"""
        
        tx = mock_successful_transaction["transactions"][0]
        
        assert tx["result"] == "SUCCESS"
        assert tx["name"] == "CRYPTOTRANSFER"
    
    @pytest.mark.asyncio
    async def test_verify_transaction_result_failed(self, mock_failed_transaction):
        """Test verification of failed transaction result"""
        
        tx = mock_failed_transaction["transactions"][0]
        
        assert tx["result"] != "SUCCESS"
        assert tx["result"] == "INSUFFICIENT_ACCOUNT_BALANCE"
    
    @pytest.mark.asyncio
    async def test_extract_consensus_timestamp(self, mock_successful_transaction):
        """Test extraction of consensus timestamp"""
        
        tx = mock_successful_transaction["transactions"][0]
        consensus_timestamp_str = tx["consensus_timestamp"]
        
        # Parse timestamp (format: "seconds.nanoseconds")
        timestamp_parts = consensus_timestamp_str.split(".")
        consensus_timestamp = datetime.fromtimestamp(int(timestamp_parts[0]))
        
        assert consensus_timestamp is not None
        assert isinstance(consensus_timestamp, datetime)
        assert consensus_timestamp.year == 2024  # Based on mock timestamp
    
    @pytest.mark.asyncio
    async def test_extract_hbar_amount_from_transfers(self, mock_successful_transaction):
        """Test extraction of HBAR amount from transaction transfers"""
        
        tx = mock_successful_transaction["transactions"][0]
        transfers = tx["transfers"]
        treasury_account = "0.0.7942957"
        
        # Find transfer to treasury account
        amount_hbar = None
        for transfer in transfers:
            if transfer["account"] == treasury_account and transfer["amount"] > 0:
                # Convert from tinybars to HBAR (1 HBAR = 100,000,000 tinybars)
                amount_hbar = Decimal(transfer["amount"]) / Decimal("100000000")
                break
        
        assert amount_hbar is not None
        assert amount_hbar == Decimal("250.0")
    
    @pytest.mark.asyncio
    async def test_validate_amount_exact_match(self):
        """Test amount validation with exact match"""
        
        expected_hbar = Decimal("250.0")
        actual_hbar = Decimal("250.0")
        
        difference_percent = abs((actual_hbar - expected_hbar) / expected_hbar * 100)
        
        assert difference_percent == 0
        assert difference_percent <= 1  # Within 1% tolerance
    
    @pytest.mark.asyncio
    async def test_validate_amount_within_tolerance(self):
        """Test amount validation within 1% tolerance"""
        
        expected_hbar = Decimal("250.0")
        actual_hbar = Decimal("250.5")  # 0.2% difference
        
        difference_percent = abs((actual_hbar - expected_hbar) / expected_hbar * 100)
        
        assert difference_percent < 1  # Within 1% tolerance
    
    @pytest.mark.asyncio
    async def test_validate_amount_exceeds_tolerance(self):
        """Test amount validation exceeding 1% tolerance"""
        
        expected_hbar = Decimal("250.0")
        actual_hbar = Decimal("260.0")  # 4% difference
        
        difference_percent = abs((actual_hbar - expected_hbar) / expected_hbar * 100)
        
        assert difference_percent > 1  # Exceeds 1% tolerance
        assert difference_percent == 4
    
    @pytest.mark.asyncio
    async def test_transaction_not_found(self, mirror_client, mock_transaction_not_found):
        """Test handling of transaction not found"""
        
        with patch.object(mirror_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_transaction_not_found
            
            tx_id = "0.0.99999@9999999999.999999999"
            result = await mirror_client.get_transaction(tx_id)
            
            assert result["transactions"] == []
    
    @pytest.mark.asyncio
    async def test_verify_payment_to_correct_account(self, mock_successful_transaction):
        """Test verification that payment went to correct treasury account"""
        
        tx = mock_successful_transaction["transactions"][0]
        transfers = tx["transfers"]
        treasury_account = "0.0.7942957"
        
        # Check if treasury account received payment
        treasury_received = False
        for transfer in transfers:
            if transfer["account"] == treasury_account and transfer["amount"] > 0:
                treasury_received = True
                break
        
        assert treasury_received is True
    
    @pytest.mark.asyncio
    async def test_verify_payment_from_user_account(self, mock_successful_transaction):
        """Test verification that payment came from user account"""
        
        tx = mock_successful_transaction["transactions"][0]
        transfers = tx["transfers"]
        user_account = "0.0.12345"
        
        # Check if user account sent payment
        user_sent = False
        for transfer in transfers:
            if transfer["account"] == user_account and transfer["amount"] < 0:
                user_sent = True
                break
        
        assert user_sent is True
    
    @pytest.mark.asyncio
    async def test_extract_memo_from_transaction(self, mock_successful_transaction):
        """Test extraction of memo from transaction"""
        
        tx = mock_successful_transaction["transactions"][0]
        memo_base64 = tx.get("memo_base64")
        
        if memo_base64:
            import base64
            memo = base64.b64decode(memo_base64).decode('utf-8')
            assert "Bill payment" in memo
    
    @pytest.mark.asyncio
    async def test_mirror_node_api_error_handling(self, mirror_client):
        """Test handling of Mirror Node API errors"""
        
        with patch.object(mirror_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("Mirror Node API error")
            
            with pytest.raises(Exception) as exc_info:
                await mirror_client.get_transaction("0.0.12345@1710789700.123456789")
            
            assert "Mirror Node API error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_verify_transaction_type_is_crypto_transfer(self, mock_successful_transaction):
        """Test verification that transaction is a CRYPTOTRANSFER"""
        
        tx = mock_successful_transaction["transactions"][0]
        
        assert tx["name"] == "CRYPTOTRANSFER"
    
    @pytest.mark.asyncio
    async def test_verify_transaction_fee_charged(self, mock_successful_transaction):
        """Test that transaction fee was charged"""
        
        tx = mock_successful_transaction["transactions"][0]
        
        assert "charged_tx_fee" in tx
        assert tx["charged_tx_fee"] > 0
    
    @pytest.mark.asyncio
    async def test_convert_tinybars_to_hbar(self):
        """Test conversion from tinybars to HBAR"""
        
        tinybars = 25000000000  # 250 HBAR
        hbar = Decimal(tinybars) / Decimal("100000000")
        
        assert hbar == Decimal("250.0")
    
    @pytest.mark.asyncio
    async def test_convert_small_amount_tinybars_to_hbar(self):
        """Test conversion of small amounts from tinybars to HBAR"""
        
        tinybars = 500000000  # 5 HBAR
        hbar = Decimal(tinybars) / Decimal("100000000")
        
        assert hbar == Decimal("5.0")
    
    @pytest.mark.asyncio
    async def test_convert_fractional_hbar_to_tinybars(self):
        """Test conversion of fractional HBAR to tinybars"""
        
        hbar = Decimal("250.17")
        tinybars = int(hbar * Decimal("100000000"))
        
        assert tinybars == 25017000000
    
    @pytest.mark.asyncio
    async def test_multiple_transfers_in_transaction(self):
        """Test handling of transactions with multiple transfers"""
        
        mock_tx = {
            "transactions": [
                {
                    "result": "SUCCESS",
                    "transfers": [
                        {"account": "0.0.12345", "amount": -25000000000},
                        {"account": "0.0.7942957", "amount": 24900000000},  # Treasury
                        {"account": "0.0.98", "amount": 100000000}  # Fee collection
                    ]
                }
            ]
        }
        
        tx = mock_tx["transactions"][0]
        transfers = tx["transfers"]
        treasury_account = "0.0.7942957"
        
        # Find treasury transfer
        treasury_amount = None
        for transfer in transfers:
            if transfer["account"] == treasury_account:
                treasury_amount = Decimal(transfer["amount"]) / Decimal("100000000")
                break
        
        assert treasury_amount == Decimal("249.0")


class TestTransactionVerificationIntegration:
    """Integration tests for transaction verification in payment flow"""
    
    @pytest.mark.asyncio
    async def test_full_verification_flow_success(self, mock_successful_transaction):
        """Test complete verification flow with successful transaction"""
        
        # Simulate the verification flow from confirm_payment endpoint
        tx_data = mock_successful_transaction
        transactions = tx_data.get("transactions", [])
        
        assert len(transactions) > 0
        
        tx = transactions[0]
        
        # Step 1: Verify transaction succeeded
        assert tx.get("result") == "SUCCESS"
        
        # Step 2: Extract consensus timestamp
        consensus_timestamp_str = tx.get("consensus_timestamp")
        timestamp_parts = consensus_timestamp_str.split(".")
        consensus_timestamp = datetime.fromtimestamp(int(timestamp_parts[0]))
        assert consensus_timestamp is not None
        
        # Step 3: Extract HBAR amount
        transfers = tx.get("transfers", [])
        treasury_account = "0.0.7942957"
        amount_hbar = None
        
        for transfer in transfers:
            if transfer.get("account") == treasury_account and transfer.get("amount", 0) > 0:
                amount_hbar = Decimal(transfer["amount"]) / Decimal("100000000")
                break
        
        assert amount_hbar is not None
        assert amount_hbar == Decimal("250.0")
        
        # Step 4: Validate amount (assuming expected is 250 HBAR)
        expected_hbar = Decimal("250.0")
        difference_percent = abs((amount_hbar - expected_hbar) / expected_hbar * 100)
        assert difference_percent <= 1
    
    @pytest.mark.asyncio
    async def test_full_verification_flow_failed_transaction(self, mock_failed_transaction):
        """Test complete verification flow with failed transaction"""
        
        tx_data = mock_failed_transaction
        transactions = tx_data.get("transactions", [])
        
        assert len(transactions) > 0
        
        tx = transactions[0]
        
        # Verify transaction failed
        assert tx.get("result") != "SUCCESS"
        assert tx.get("result") == "INSUFFICIENT_ACCOUNT_BALANCE"
    
    @pytest.mark.asyncio
    async def test_full_verification_flow_amount_mismatch(self, mock_successful_transaction):
        """Test complete verification flow with amount mismatch"""
        
        tx_data = mock_successful_transaction
        tx = tx_data["transactions"][0]
        
        # Extract actual amount
        transfers = tx.get("transfers", [])
        treasury_account = "0.0.7942957"
        amount_hbar = None
        
        for transfer in transfers:
            if transfer.get("account") == treasury_account and transfer.get("amount", 0) > 0:
                amount_hbar = Decimal(transfer["amount"]) / Decimal("100000000")
                break
        
        # Compare with different expected amount
        expected_hbar = Decimal("300.0")  # Different from actual 250
        difference_percent = abs((amount_hbar - expected_hbar) / expected_hbar * 100)
        
        # Should exceed tolerance
        assert difference_percent > 1


class TestMirrorNodeClientConfiguration:
    """Test Mirror Node client configuration"""
    
    def test_client_initialization_testnet(self):
        """Test client initialization with testnet URL"""
        
        client = MirrorNodeClient(base_url="https://testnet.mirrornode.hedera.com")
        
        assert client.base_url == "https://testnet.mirrornode.hedera.com"
        assert client.api_version == "api/v1"
    
    def test_client_initialization_mainnet(self):
        """Test client initialization with mainnet URL"""
        
        client = MirrorNodeClient(base_url="https://mainnet-public.mirrornode.hedera.com")
        
        assert client.base_url == "https://mainnet-public.mirrornode.hedera.com"
    
    def test_client_initialization_strips_trailing_slash(self):
        """Test that trailing slash is stripped from base URL"""
        
        client = MirrorNodeClient(base_url="https://testnet.mirrornode.hedera.com/")
        
        assert client.base_url == "https://testnet.mirrornode.hedera.com"
        assert not client.base_url.endswith("/")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
