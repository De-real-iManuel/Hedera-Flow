"""
Hedera Service
Handles Hedera account creation and management
"""
from hedera import (
    Client,
    PrivateKey,
    PublicKey,
    AccountCreateTransaction,
    Hbar,
    AccountId,
    AccountInfoQuery
)
from typing import Tuple, Optional
import logging
import hashlib

from config import settings

logger = logging.getLogger(__name__)


class HederaService:
    """Service for Hedera blockchain operations"""
    
    def __init__(self):
        """Initialize Hedera client"""
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup Hedera client with operator account"""
        try:
            # Create client for testnet
            if settings.hedera_network == "testnet":
                self.client = Client.forTestnet()
            elif settings.hedera_network == "mainnet":
                self.client = Client.forMainnet()
            else:
                raise ValueError(f"Invalid Hedera network: {settings.hedera_network}")
            
            # Set operator account
            operator_id = AccountId.fromString(settings.hedera_operator_id)
            operator_key = PrivateKey.fromString(settings.hedera_operator_key)
            
            self.client.setOperator(operator_id, operator_key)
            
            logger.info(f"Hedera client initialized for {settings.hedera_network}")
            logger.info(f"Operator account: {settings.hedera_operator_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Hedera client: {e}")
            raise
    
    def create_account(self, initial_balance: float = 10.0) -> Tuple[str, str]:
        """
        Create a new Hedera account for a user
        
        Args:
            initial_balance: Initial HBAR balance (default: 10 HBAR for testing)
            
        Returns:
            Tuple of (account_id, private_key)
            
        Requirements:
            - FR-1.3: System shall create Hedera testnet account for new users without wallet
            - US-1: System creates Hedera account (testnet) if user doesn't have one
            
        Raises:
            Exception: If account creation fails
        """
        try:
            # Generate new key pair for the account
            new_private_key = PrivateKey.generate()
            new_public_key = new_private_key.getPublicKey()
            
            logger.info("Generated new key pair for account creation")
            
            # Create account transaction
            transaction = (
                AccountCreateTransaction()
                .setKey(new_public_key)
                .setInitialBalance(Hbar(initial_balance))
                .setMaxTransactionFee(Hbar(2))  # Max fee for account creation
            )
            
            # Execute transaction
            response = transaction.execute(self.client)
            
            # Get receipt to confirm success
            receipt = response.getReceipt(self.client)
            
            # Get new account ID
            new_account_id = receipt.accountId
            
            logger.info(f"Successfully created Hedera account: {new_account_id}")
            logger.info(f"Initial balance: {initial_balance} HBAR")
            
            return (
                str(new_account_id),
                str(new_private_key)
            )
            
        except Exception as e:
            logger.error(f"Failed to create Hedera account: {e}")
            raise Exception(f"Failed to create Hedera account: {str(e)}")
    
    def get_account_balance(self, account_id: str) -> float:
        """
        Get HBAR balance for an account
        
        Args:
            account_id: Hedera account ID (0.0.xxxxx format)
            
        Returns:
            Account balance in HBAR
        """
        try:
            from hedera import AccountBalanceQuery
            
            account = AccountId.fromString(account_id)
            balance = AccountBalanceQuery().setAccountId(account).execute(self.client)
            
            return float(balance.hbars.toString())
            
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            raise
    
    def verify_signature(self, account_id: str, message: str, signature: str) -> bool:
        """
        Verify a signature from a Hedera account
        
        This method verifies that a message was signed by the private key
        associated with the given Hedera account ID.
        
        Args:
            account_id: Hedera account ID (0.0.xxxxx format)
            message: Original message that was signed
            signature: Hex-encoded signature to verify
            
        Returns:
            True if signature is valid, False otherwise
            
        Requirements:
            - FR-1.2: System shall support HashPack wallet connection
            - US-1: User can connect HashPack wallet with signature verification
        """
        try:
            # Get account info to retrieve public key
            account = AccountId.fromString(account_id)
            query = AccountInfoQuery().setAccountId(account)
            account_info = query.execute(self.client)
            
            # Get the account's public key
            public_key = account_info.key
            
            # Convert message to bytes
            message_bytes = message.encode('utf-8')
            
            # Convert hex signature to bytes
            signature_bytes = bytes.fromhex(signature)
            
            # Verify signature
            is_valid = public_key.verify(message_bytes, signature_bytes)
            
            logger.info(f"Signature verification for account {account_id}: {is_valid}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Failed to verify signature for account {account_id}: {e}")
            return False
    
    def account_exists(self, account_id: str) -> bool:
        """
        Check if a Hedera account exists
        
        Args:
            account_id: Hedera account ID (0.0.xxxxx format)
            
        Returns:
            True if account exists, False otherwise
        """
        try:
            account = AccountId.fromString(account_id)
            query = AccountInfoQuery().setAccountId(account)
            query.execute(self.client)
            return True
        except Exception as e:
            logger.warning(f"Account {account_id} does not exist or query failed: {e}")
            return False
    
    def close(self):
        """Close Hedera client connection"""
        if self.client:
            self.client.close()
            logger.info("Hedera client connection closed")


# Global Hedera service instance
_hedera_service: Optional[HederaService] = None


def get_hedera_service() -> HederaService:
    """
    Get or create global Hedera service instance
    
    Returns:
        HederaService instance
    """
    global _hedera_service
    
    if _hedera_service is None:
        _hedera_service = HederaService()
    
    return _hedera_service
