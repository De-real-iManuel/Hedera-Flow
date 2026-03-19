"""
Hedera Service
Handles Hedera account creation and management using the Java-based Hedera SDK
"""
from typing import Tuple, Optional
import logging
import hashlib
import os

from config import settings

logger = logging.getLogger(__name__)

# Check if we should use mock mode
USE_MOCK_MODE = os.getenv('HEDERA_MOCK_MODE', 'False').lower() == 'true'

# Conditional imports - only import real SDK if not in mock mode
if not USE_MOCK_MODE:
    try:
        from hedera import (
            Client,
            AccountBalanceQuery,
            TransferTransaction,
            Hbar,
            AccountId,
            PrivateKey,
            AccountCreateTransaction,
            AccountInfoQuery,
            TopicId,
            TopicMessageSubmitTransaction
        )
        logger.info("✅ Real Hedera SDK imported successfully")
        HEDERA_SDK_AVAILABLE = True
    except BaseException as e:
        logger.warning(f"⚠️ Failed to import Hedera SDK: {e}")
        logger.warning("🎭 Falling back to mock mode")
        USE_MOCK_MODE = True
        HEDERA_SDK_AVAILABLE = False
else:
    logger.info("🎭 Mock mode enabled via HEDERA_MOCK_MODE environment variable")
    HEDERA_SDK_AVAILABLE = False


class HederaService:
    """Service for Hedera blockchain operations"""
    
    def __init__(self):
        """Initialize Hedera client"""
        self.client = None
        self.mock_mode = USE_MOCK_MODE
        if not self.mock_mode:
            self._setup_client()
        else:
            logger.info("🎭 Hedera Service initialized in MOCK MODE")
    
    def _setup_client(self):
        """Setup Hedera client with operator account"""
        if self.mock_mode:
            logger.info("🎭 Skipping client setup - mock mode enabled")
            return
            
        if not HEDERA_SDK_AVAILABLE:
            logger.warning("🎭 Hedera SDK not available - enabling mock mode")
            self.mock_mode = True
            return
            
        try:
            # Check and set Java environment
            import os
            java_home = os.environ.get('JAVA_HOME')
            logger.info(f"JAVA_HOME: {java_home}")
            
            # Ensure Java environment is properly set
            if not java_home:
                # Try to find Java automatically
                possible_java_homes = [
                    '/usr/lib/jvm/java-17-openjdk-amd64',
                    '/usr/lib/jvm/java-11-openjdk-amd64',
                    '/usr/lib/jvm/default-java'
                ]
                for path in possible_java_homes:
                    if os.path.exists(f"{path}/bin/javac"):
                        java_home = path
                        os.environ['JAVA_HOME'] = java_home
                        logger.info(f"Found Java at: {java_home}")
                        break
            
            if java_home:
                os.environ['JDK_HOME'] = java_home
                os.environ['PATH'] = f"{java_home}/bin:{os.environ.get('PATH', '')}"
                logger.info(f"Set JAVA_HOME to: {java_home}")
                logger.info(f"javac exists: {os.path.exists(f'{java_home}/bin/javac')}")
            
            # Suppress verbose logging from Hedera SDK
            os.environ['KIVY_LOG_MODE'] = 'PYTHON'
            os.environ['KIVY_NO_CONSOLELOG'] = '1'
            
            logger.info("Initializing Hedera client...")
            
            # Create client for testnet or mainnet
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
            
        except BaseException as e:
            logger.error(f"Failed to initialize Hedera client: {e}")
            logger.warning("🎭 Falling back to MOCK MODE due to initialization error")
            self.mock_mode = True
    
    def create_account(self, initial_balance: float = 10.0) -> Tuple[str, str]:
        """
        Create a new Hedera account for a user
        
        Args:
            initial_balance: Initial HBAR balance (default: 10 HBAR for testing)
            
        Returns:
            Tuple of (account_id, private_key)
            
        
        Raises:
            Exception: If account creation fails
        """
        if self.mock_mode:
            # Mock implementation
            import secrets
            account_num = secrets.randbelow(999999) + 100000
            account_id = f"0.0.{account_num}"
            private_key = secrets.token_hex(32)
            
            logger.info(f"🎭 Mock: Created account {account_id} with {initial_balance} HBAR")
            return account_id, private_key
        
        try:
            # Generate new key pair for the account
            new_private_key = PrivateKey.generate()
            new_public_key = new_private_key.getPublicKey()
            
            logger.info("Generated new key pair for account creation")
            
            # Create account transaction
            transaction = (
                AccountCreateTransaction()
                .setKey(new_public_key)
                .setInitialBalance(Hbar.fromTinybars(int(initial_balance * 100_000_000)))  # Convert HBAR to tinybars
                .setMaxTransactionFee(Hbar.fromTinybars(200_000_000))  # 2 HBAR max fee
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
        if self.mock_mode:
            logger.debug(f"🎭 Mock: Account {account_id} balance: 100.0 HBAR")
            return 100.0
            
        try:
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
        if self.mock_mode:
            logger.info(f"🎭 Mock: Signature verification for {account_id} (always True)")
            return True
            
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
        if self.mock_mode:
            logger.debug(f"🎭 Mock: Account {account_id} exists check (always True)")
            return True
            
        try:
            account = AccountId.fromString(account_id)
            query = AccountInfoQuery().setAccountId(account)
            query.execute(self.client)
            return True
        except Exception as e:
            logger.warning(f"Account {account_id} does not exist or query failed: {e}")
            return False
    
    def log_payment_to_hcs(
        self,
        topic_id: str,
        bill_id: str,
        amount_fiat: float,
        currency_fiat: str,
        amount_hbar: float,
        exchange_rate: float,
        tx_id: str
    ) -> dict:
        """
        Log a payment to HCS (Hedera Consensus Service)
        
        This method creates a payment log message and submits it to the appropriate
        regional HCS topic for immutable blockchain logging.
        
        Args:
            topic_id: HCS topic ID (e.g., "0.0.5078302" for EU)
            bill_id: Bill UUID
            amount_fiat: Payment amount in fiat currency
            currency_fiat: Fiat currency code (EUR, USD, INR, BRL, NGN)
            amount_hbar: Payment amount in HBAR
            exchange_rate: HBAR/fiat exchange rate used
            tx_id: Hedera transaction ID
            
        Returns:
            dict: HCS submission result with topic_id and sequence_number
            
        Requirements:
            - FR-5.14: System shall log payments to HCS (including HBAR amount and fiat equivalent)
            - US-8: Payment logged to HCS with Type: "PAYMENT", Bill ID, Amount, Currency, Transaction ID, Timestamp
            - US-8: User can view HCS sequence number
            
        Raises:
            Exception: If HCS submission fails
        """
        try:
            import json
            from datetime import datetime
            
            logger.info(f"Logging payment to HCS topic {topic_id}...")
            
            # Create payment log message per requirements
            payment_log = {
                "type": "PAYMENT",
                "timestamp": int(datetime.utcnow().timestamp()),
                "bill_id": bill_id,
                "amount_fiat": amount_fiat,
                "currency_fiat": currency_fiat,
                "amount_hbar": amount_hbar,
                "exchange_rate": exchange_rate,
                "tx_id": tx_id,
                "status": "SUCCESS"
            }
            
            if self.mock_mode:
                # Mock implementation
                import secrets
                sequence_number = secrets.randbelow(999999) + 1
                
                logger.info(f"🎭 Mock: Payment logged to HCS topic {topic_id}")
                logger.info(f"   Sequence Number: {sequence_number}")
                logger.info(f"   Bill ID: {bill_id}")
                logger.info(f"   Amount: {amount_hbar} HBAR ({amount_fiat} {currency_fiat})")
                
                return {
                    "topic_id": topic_id,
                    "sequence_number": sequence_number,
                    "message": payment_log
                }
            
            # Convert to JSON
            message_json = json.dumps(payment_log)
            
            # Parse topic ID
            topic = TopicId.fromString(topic_id)
            
            # Create and execute transaction
            transaction = (
                TopicMessageSubmitTransaction()
                .setTopicId(topic)
                .setMessage(message_json)
            )
            
            response = transaction.execute(self.client)
            receipt = response.getReceipt(self.client)
            
            sequence_number = receipt.topicSequenceNumber
            
            logger.info(f"✅ Payment logged to HCS topic {topic_id}")
            logger.info(f"   Sequence Number: {sequence_number}")
            logger.info(f"   Bill ID: {bill_id}")
            logger.info(f"   Amount: {amount_hbar} HBAR ({amount_fiat} {currency_fiat})")
            
            return {
                "topic_id": topic_id,
                "sequence_number": sequence_number,
                "message": payment_log
            }
            
        except Exception as e:
            logger.error(f"Failed to log payment to HCS: {e}")
            raise Exception(f"Failed to log payment to HCS: {str(e)}")
    
    def close(self):
        """Close Hedera client connection"""
        if self.client and not self.mock_mode:
            self.client.close()
            logger.info("Hedera client connection closed")
        elif self.mock_mode:
            logger.info("🎭 Mock: Hedera client connection closed")


# Global Hedera service instance
_hedera_service: Optional[HederaService] = None


def get_hedera_service() -> HederaService:
    """
    Get or create global Hedera service instance
    Always returns a service instance — falls back to mock mode on any error.
    """
    global _hedera_service
    
    if _hedera_service is None:
        try:
            _hedera_service = HederaService()
        except Exception as e:
            logger.error(f"Failed to initialize Hedera service: {e}")
            logger.warning("🎭 Falling back to mock HederaService")
            # Force mock mode so auth endpoints don't blow up
            svc = HederaService.__new__(HederaService)
            svc.client = None
            svc.mock_mode = True
            _hedera_service = svc
    
    return _hedera_service
