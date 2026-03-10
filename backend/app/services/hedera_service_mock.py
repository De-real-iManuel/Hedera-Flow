"""
Mock Hedera Service for Demo/Offline Mode
Simulates Hedera operations without network connectivity
"""
import logging
import secrets
from datetime import datetime
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class MockHederaService:
    """
    Mock implementation of Hedera service for demo purposes
    
    This service simulates Hedera operations without requiring
    network connectivity or real Hedera accounts.
    """
    
    def __init__(self):
        """Initialize mock Hedera service"""
        self.network = "testnet-mock"
        logger.info("🎭 Mock Hedera Service initialized (Demo Mode)")
    
    def create_account(self, initial_balance: float = 10.0) -> Tuple[str, str]:
        """
        Simulate Hedera account creation
        
        Args:
            initial_balance: Initial HBAR balance (ignored in mock)
            
        Returns:
            Tuple of (account_id, private_key)
        """
        # Generate mock account ID
        account_num = secrets.randbelow(999999) + 100000
        account_id = f"0.0.{account_num}"
        
        # Generate mock private key (not a real key)
        private_key = secrets.token_hex(32)
        
        logger.info(f"🎭 Mock: Created account {account_id} with {initial_balance} HBAR")
        
        return account_id, private_key
    
    def account_exists(self, account_id: str) -> bool:
        """
        Simulate account existence check
        
        Args:
            account_id: Hedera account ID
            
        Returns:
            Always True in mock mode
        """
        logger.debug(f"🎭 Mock: Checking if account {account_id} exists (always True)")
        return True
    
    def verify_signature(
        self,
        account_id: str,
        message: str,
        signature: str
    ) -> bool:
        """
        Simulate signature verification
        
        Args:
            account_id: Hedera account ID
            message: Original message
            signature: Signature to verify
            
        Returns:
            Always True in mock mode (for demo purposes)
        """
        logger.info(f"🎭 Mock: Verifying signature for {account_id} (always True)")
        return True
    
    def get_account_balance(self, account_id: str) -> float:
        """
        Simulate getting account balance
        
        Args:
            account_id: Hedera account ID
            
        Returns:
            Mock balance (100 HBAR)
        """
        mock_balance = 100.0
        logger.debug(f"🎭 Mock: Account {account_id} balance: {mock_balance} HBAR")
        return mock_balance
    
    def transfer_hbar(
        self,
        from_account: str,
        to_account: str,
        amount: float,
        memo: str = ""
    ) -> str:
        """
        Simulate HBAR transfer
        
        Args:
            from_account: Sender account ID
            to_account: Receiver account ID
            amount: Amount in HBAR
            memo: Transaction memo
            
        Returns:
            Mock transaction ID
        """
        # Generate mock transaction ID
        timestamp = int(datetime.utcnow().timestamp())
        nanos = secrets.randbelow(999999999)
        tx_id = f"{from_account}@{timestamp}.{nanos}"
        
        logger.info(
            f"🎭 Mock: Transfer {amount} HBAR from {from_account} to {to_account}\n"
            f"   Memo: {memo}\n"
            f"   TX ID: {tx_id}"
        )
        
        return tx_id
    
    def submit_message_to_topic(
        self,
        topic_id: str,
        message: str
    ) -> Tuple[str, int]:
        """
        Simulate HCS message submission
        
        Args:
            topic_id: HCS topic ID
            message: Message to submit
            
        Returns:
            Tuple of (transaction_id, sequence_number)
        """
        # Generate mock transaction ID
        timestamp = int(datetime.utcnow().timestamp())
        nanos = secrets.randbelow(999999999)
        tx_id = f"0.0.MOCK@{timestamp}.{nanos}"
        
        # Generate mock sequence number
        sequence_number = secrets.randbelow(999999) + 1
        
        logger.info(
            f"🎭 Mock: Submitted message to topic {topic_id}\n"
            f"   TX ID: {tx_id}\n"
            f"   Sequence: {sequence_number}\n"
            f"   Message length: {len(message)} bytes"
        )
        
        return tx_id, sequence_number
    
    def get_transaction_receipt(self, transaction_id: str) -> dict:
        """
        Simulate getting transaction receipt
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Mock receipt data
        """
        receipt = {
            "transaction_id": transaction_id,
            "status": "SUCCESS",
            "consensus_timestamp": datetime.utcnow().isoformat(),
            "transaction_fee": "0.0001",
            "mock": True
        }
        
        logger.debug(f"🎭 Mock: Retrieved receipt for {transaction_id}")
        
        return receipt
    
    def verify_transaction(
        self,
        transaction_id: str,
        expected_amount: Optional[float] = None,
        expected_sender: Optional[str] = None,
        expected_receiver: Optional[str] = None
    ) -> bool:
        """
        Simulate transaction verification
        
        Args:
            transaction_id: Transaction ID to verify
            expected_amount: Expected amount (ignored in mock)
            expected_sender: Expected sender (ignored in mock)
            expected_receiver: Expected receiver (ignored in mock)
            
        Returns:
            Always True in mock mode
        """
        logger.info(f"🎭 Mock: Verifying transaction {transaction_id} (always True)")
        return True


# Singleton instance
_mock_hedera_service = None


def get_mock_hedera_service() -> MockHederaService:
    """
    Get singleton instance of mock Hedera service
    
    Returns:
        MockHederaService instance
    """
    global _mock_hedera_service
    
    if _mock_hedera_service is None:
        _mock_hedera_service = MockHederaService()
    
    return _mock_hedera_service
