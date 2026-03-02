"""
Transaction Verification Utility

Provides comprehensive verification of Hedera transactions via Mirror Node API.
Implements FR-6.9: Verify transaction on Hedera network via Mirror Node.

This module encapsulates all transaction verification logic including:
- Transaction existence verification
- Transaction status validation
- Amount validation with tolerance
- Account validation
- Timestamp extraction
"""

import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from app.utils.mirror_node_client import mirror_node_client

logger = logging.getLogger(__name__)


class TransactionVerificationError(Exception):
    """Base exception for transaction verification errors"""
    pass


class TransactionNotFoundError(TransactionVerificationError):
    """Transaction not found on Hedera network"""
    pass


class TransactionFailedError(TransactionVerificationError):
    """Transaction failed on Hedera network"""
    pass


class AmountMismatchError(TransactionVerificationError):
    """Transaction amount does not match expected amount"""
    pass


class InvalidTransferError(TransactionVerificationError):
    """Transaction does not contain expected transfer"""
    pass


class TransactionVerifier:
    """
    Utility class for verifying Hedera transactions via Mirror Node API
    
    Provides methods to:
    - Verify transaction exists and succeeded
    - Extract transaction details (amount, timestamp, etc.)
    - Validate transaction amount matches expected
    - Validate payment went to correct account
    """
    
    def __init__(self, treasury_account: str, tolerance_percent: float = 1.0):
        """
        Initialize transaction verifier
        
        Args:
            treasury_account: Hedera account ID that should receive payments
            tolerance_percent: Allowed percentage difference for amount validation (default: 1%)
        """
        self.treasury_account = treasury_account
        self.tolerance_percent = tolerance_percent
        self.mirror_client = mirror_node_client
    
    async def verify_transaction(
        self,
        transaction_id: str,
        expected_amount_hbar: Optional[Decimal] = None,
        user_account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify a Hedera transaction comprehensively
        
        This method:
        1. Queries transaction from Mirror Node API
        2. Verifies transaction exists
        3. Verifies transaction succeeded
        4. Extracts transaction details
        5. Validates amount (if expected_amount provided)
        6. Validates sender (if user_account_id provided)
        
        Args:
            transaction_id: Hedera transaction ID (format: 0.0.xxxxx@timestamp.nanoseconds)
            expected_amount_hbar: Expected HBAR amount (optional)
            user_account_id: Expected sender account ID (optional)
            
        Returns:
            dict: Verified transaction details
                {
                    "transaction_id": str,
                    "result": str,
                    "consensus_timestamp": datetime,
                    "amount_hbar": Decimal,
                    "from_account": str,
                    "to_account": str,
                    "memo": str (optional),
                    "charged_fee": int
                }
        
        Raises:
            TransactionNotFoundError: Transaction not found on network
            TransactionFailedError: Transaction failed
            AmountMismatchError: Amount doesn't match expected
            InvalidTransferError: Transfer not found or invalid
        """
        logger.info(f"Verifying transaction {transaction_id}...")
        
        # Step 1: Query transaction from Mirror Node
        try:
            tx_data = await self.mirror_client.get_transaction(transaction_id)
        except Exception as e:
            logger.error(f"Failed to query Mirror Node: {e}")
            raise TransactionVerificationError(f"Mirror Node API error: {str(e)}")
        
        # Step 2: Verify transaction exists
        transactions = tx_data.get("transactions", [])
        if not transactions:
            raise TransactionNotFoundError(f"Transaction {transaction_id} not found on Hedera network")
        
        tx = transactions[0]
        
        # Step 3: Verify transaction succeeded
        result = tx.get("result")
        if result != "SUCCESS":
            raise TransactionFailedError(f"Transaction failed with result: {result}")
        
        # Step 4: Extract consensus timestamp
        consensus_timestamp = self._extract_consensus_timestamp(tx)
        
        # Step 5: Extract HBAR amount and accounts
        amount_hbar, from_account, to_account = self._extract_transfer_details(tx)
        
        # Step 6: Validate amount if expected amount provided
        if expected_amount_hbar is not None:
            self._validate_amount(amount_hbar, expected_amount_hbar)
        
        # Step 7: Validate sender if user account provided
        if user_account_id is not None:
            self._validate_sender(from_account, user_account_id)
        
        # Step 8: Extract memo (optional)
        memo = self._extract_memo(tx)
        
        # Step 9: Extract fee
        charged_fee = tx.get("charged_tx_fee", 0)
        
        logger.info(f"✅ Transaction verified: {amount_hbar} HBAR from {from_account} to {to_account}")
        
        return {
            "transaction_id": transaction_id,
            "result": result,
            "consensus_timestamp": consensus_timestamp,
            "amount_hbar": amount_hbar,
            "from_account": from_account,
            "to_account": to_account,
            "memo": memo,
            "charged_fee": charged_fee
        }
    
    def _extract_consensus_timestamp(self, tx: Dict[str, Any]) -> datetime:
        """
        Extract consensus timestamp from transaction
        
        Args:
            tx: Transaction data from Mirror Node
            
        Returns:
            datetime: Consensus timestamp
        """
        consensus_timestamp_str = tx.get("consensus_timestamp")
        if not consensus_timestamp_str:
            logger.warning("No consensus timestamp found, using current time")
            return datetime.utcnow()
        
        try:
            # Format: "seconds.nanoseconds"
            timestamp_parts = consensus_timestamp_str.split(".")
            timestamp = datetime.fromtimestamp(int(timestamp_parts[0]))
            return timestamp
        except Exception as e:
            logger.warning(f"Failed to parse consensus timestamp: {e}")
            return datetime.utcnow()
    
    def _extract_transfer_details(self, tx: Dict[str, Any]) -> Tuple[Decimal, str, str]:
        """
        Extract transfer details from transaction
        
        Args:
            tx: Transaction data from Mirror Node
            
        Returns:
            tuple: (amount_hbar, from_account, to_account)
            
        Raises:
            InvalidTransferError: If transfer not found or invalid
        """
        transfers = tx.get("transfers", [])
        if not transfers:
            raise InvalidTransferError("No transfers found in transaction")
        
        # Find transfer to treasury account
        amount_hbar = None
        from_account = None
        to_account = None
        
        for transfer in transfers:
            account = transfer.get("account")
            amount = transfer.get("amount", 0)
            
            # Find payment to treasury (positive amount)
            if account == self.treasury_account and amount > 0:
                # Convert from tinybars to HBAR (1 HBAR = 100,000,000 tinybars)
                amount_hbar = Decimal(amount) / Decimal("100000000")
                to_account = account
            
            # Find payment from user (negative amount)
            elif amount < 0:
                from_account = account
        
        if amount_hbar is None:
            raise InvalidTransferError(f"No payment transfer found to treasury account {self.treasury_account}")
        
        if from_account is None:
            raise InvalidTransferError("No sender account found in transfers")
        
        return amount_hbar, from_account, to_account
    
    def _validate_amount(self, actual_amount: Decimal, expected_amount: Decimal) -> None:
        """
        Validate transaction amount matches expected amount within tolerance
        
        Args:
            actual_amount: Actual HBAR amount from transaction
            expected_amount: Expected HBAR amount
            
        Raises:
            AmountMismatchError: If amounts don't match within tolerance
        """
        if expected_amount == 0:
            logger.warning("Expected amount is 0, skipping validation")
            return
        
        difference_percent = abs((actual_amount - expected_amount) / expected_amount * 100)
        
        if difference_percent > self.tolerance_percent:
            raise AmountMismatchError(
                f"Transaction amount mismatch: expected {expected_amount} HBAR, "
                f"got {actual_amount} HBAR (difference: {difference_percent:.2f}%)"
            )
        
        logger.info(f"Amount validated: {actual_amount} HBAR (difference: {difference_percent:.2f}%)")
    
    def _validate_sender(self, actual_sender: str, expected_sender: str) -> None:
        """
        Validate transaction sender matches expected sender
        
        Args:
            actual_sender: Actual sender account ID
            expected_sender: Expected sender account ID
            
        Raises:
            InvalidTransferError: If sender doesn't match
        """
        if actual_sender != expected_sender:
            raise InvalidTransferError(
                f"Transaction sender mismatch: expected {expected_sender}, got {actual_sender}"
            )
        
        logger.info(f"Sender validated: {actual_sender}")
    
    def _extract_memo(self, tx: Dict[str, Any]) -> Optional[str]:
        """
        Extract memo from transaction
        
        Args:
            tx: Transaction data from Mirror Node
            
        Returns:
            str or None: Decoded memo if present
        """
        memo_base64 = tx.get("memo_base64")
        if not memo_base64:
            return None
        
        try:
            import base64
            memo = base64.b64decode(memo_base64).decode('utf-8')
            return memo
        except Exception as e:
            logger.warning(f"Failed to decode memo: {e}")
            return None
    
    async def get_transaction_status(self, transaction_id: str) -> str:
        """
        Get transaction status without full verification
        
        Args:
            transaction_id: Hedera transaction ID
            
        Returns:
            str: Transaction result status (SUCCESS, INSUFFICIENT_ACCOUNT_BALANCE, etc.)
            
        Raises:
            TransactionNotFoundError: Transaction not found
        """
        try:
            tx_data = await self.mirror_client.get_transaction(transaction_id)
            transactions = tx_data.get("transactions", [])
            
            if not transactions:
                raise TransactionNotFoundError(f"Transaction {transaction_id} not found")
            
            return transactions[0].get("result", "UNKNOWN")
            
        except Exception as e:
            logger.error(f"Failed to get transaction status: {e}")
            raise
    
    async def get_transaction_amount(self, transaction_id: str) -> Decimal:
        """
        Get transaction amount without full verification
        
        Args:
            transaction_id: Hedera transaction ID
            
        Returns:
            Decimal: HBAR amount transferred to treasury
            
        Raises:
            TransactionNotFoundError: Transaction not found
            InvalidTransferError: Transfer not found
        """
        try:
            tx_data = await self.mirror_client.get_transaction(transaction_id)
            transactions = tx_data.get("transactions", [])
            
            if not transactions:
                raise TransactionNotFoundError(f"Transaction {transaction_id} not found")
            
            tx = transactions[0]
            amount_hbar, _, _ = self._extract_transfer_details(tx)
            
            return amount_hbar
            
        except Exception as e:
            logger.error(f"Failed to get transaction amount: {e}")
            raise


# Convenience function for quick verification
async def verify_payment_transaction(
    transaction_id: str,
    expected_amount_hbar: Decimal,
    treasury_account: str,
    user_account_id: Optional[str] = None,
    tolerance_percent: float = 1.0
) -> Dict[str, Any]:
    """
    Convenience function to verify a payment transaction
    
    Args:
        transaction_id: Hedera transaction ID
        expected_amount_hbar: Expected HBAR amount
        treasury_account: Treasury account that should receive payment
        user_account_id: Expected sender account (optional)
        tolerance_percent: Allowed percentage difference (default: 1%)
        
    Returns:
        dict: Verified transaction details
        
    Raises:
        TransactionVerificationError: If verification fails
    """
    verifier = TransactionVerifier(
        treasury_account=treasury_account,
        tolerance_percent=tolerance_percent
    )
    
    return await verifier.verify_transaction(
        transaction_id=transaction_id,
        expected_amount_hbar=expected_amount_hbar,
        user_account_id=user_account_id
    )
