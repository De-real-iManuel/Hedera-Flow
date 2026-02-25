"""
Hedera Client Utility

Provides a singleton Hedera client for interacting with the Hedera network.
Handles account management, transactions, and HCS operations.
"""
import os
import logging

# Suppress verbose JNIus/Kivy logging BEFORE importing Hedera
os.environ['KIVY_LOG_MODE'] = 'PYTHON'
os.environ['KIVY_NO_CONSOLELOG'] = '1'

# Configure logging for this module
logging.getLogger('kivy').setLevel(logging.ERROR)
logging.getLogger('kivy.jnius').setLevel(logging.ERROR)
logging.getLogger('kivy.jnius.reflect').setLevel(logging.ERROR)
logging.getLogger('jnius').setLevel(logging.ERROR)

from hedera import (
    Client,
    AccountBalanceQuery,
    TransferTransaction,
    Hbar,
    AccountId,
    PrivateKey,
    TopicMessageSubmitTransaction,
    TopicInfoQuery,
    TopicId
)
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)


class HederaClient:
    """
    Singleton Hedera client for the application
    
    Manages connections to Hedera testnet and provides utility methods
    for common operations like balance queries and transfers.
    """
    
    _instance: Optional['HederaClient'] = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the Hedera client (singleton pattern)"""
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Hedera client with operator credentials"""
        from config import settings
        import os
        
        try:
            logger.info("Initializing Hedera client for testnet...")
            
            # Workaround for Windows DNS issues with Java
            # Prefer IPv4 to avoid DNS resolution problems
            os.environ['JAVA_TOOL_OPTIONS'] = '-Djava.net.preferIPv4Stack=true -Djava.net.preferIPv4Addresses=true'
            
            # Create client for testnet
            self._client = Client.forTestnet()
            
            # Convert string credentials to proper Hedera objects
            operator_id = AccountId.fromString(settings.hedera_operator_id)
            operator_key = PrivateKey.fromString(settings.hedera_operator_key)
            
            # Set operator account
            self._client.setOperator(operator_id, operator_key)
            
            logger.info(f"✅ Hedera client initialized with operator: {settings.hedera_operator_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Hedera client: {str(e)}")
            raise
    
    @property
    def client(self) -> Client:
        """Get the Hedera client instance"""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    async def get_account_balance(self, account_id: str) -> Hbar:
        """
        Get the HBAR balance of an account
        
        Args:
            account_id: Hedera account ID (e.g., "0.0.12345")
            
        Returns:
            Hbar: Account balance
            
        Raises:
            Exception: If query fails
        """
        try:
            logger.info(f"Querying balance for account {account_id}...")
            
            # Convert string to AccountId object
            account = AccountId.fromString(account_id)
            query = AccountBalanceQuery().setAccountId(account)
            balance = query.execute(self.client)
            
            logger.info(f"✅ Balance for {account_id}: {balance.hbars} HBAR")
            return balance.hbars
            
        except Exception as e:
            logger.error(f"❌ Failed to query balance for {account_id}: {str(e)}")
            raise
    
    async def transfer_hbar(
        self,
        from_account_id: str,
        from_private_key: str,
        to_account_id: str,
        amount_hbar: float,
        memo: Optional[str] = None
    ) -> str:
        """
        Transfer HBAR between accounts
        
        Args:
            from_account_id: Source account ID
            from_private_key: Source account private key
            to_account_id: Destination account ID
            amount_hbar: Amount to transfer in HBAR
            memo: Optional transaction memo
            
        Returns:
            str: Transaction ID
            
        Raises:
            Exception: If transfer fails
        """
        try:
            logger.info(f"Transferring {amount_hbar} HBAR from {from_account_id} to {to_account_id}...")
            
            # Convert strings to proper Hedera objects
            from_account = AccountId.fromString(from_account_id)
            from_key = PrivateKey.fromString(from_private_key)
            to_account = AccountId.fromString(to_account_id)
            
            # Create a temporary client with the sender's credentials
            temp_client = Client.forTestnet()
            temp_client.setOperator(from_account, from_key)
            
            # Create transfer transaction
            transaction = (
                TransferTransaction()
                .addHbarTransfer(from_account, Hbar(-amount_hbar))
                .addHbarTransfer(to_account, Hbar(amount_hbar))
            )
            
            # Add memo if provided
            if memo:
                transaction.setTransactionMemo(memo)
            
            # Execute transaction
            response = transaction.execute(temp_client)
            
            # Get receipt
            receipt = response.getReceipt(temp_client)
            
            # Get transaction ID
            tx_id = str(response.transactionId)
            
            logger.info(f"✅ Transfer successful: {tx_id}")
            logger.info(f"   Status: {receipt.status}")
            
            temp_client.close()
            
            return tx_id
            
        except Exception as e:
            logger.error(f"❌ Transfer failed: {str(e)}")
            raise
    
    async def verify_account(account_id: str) -> bool:
        """
        Verify that an account exists on the network
        
        Args:
            account_id: Hedera account ID to verify
            
        Returns:
            bool: True if account exists, False otherwise
        """
        try:
            await self.get_account_balance(account_id)
            return True
        except Exception:
            return False
    
    async def submit_hcs_message(
        self,
        topic_id: str,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit a message to an HCS topic
        
        Args:
            topic_id: HCS topic ID (e.g., "0.0.12345")
            message: Dictionary to convert to JSON and submit
            
        Returns:
            dict: Transaction info with tx_id, sequence_number, timestamp
            
        Raises:
            Exception: If submission fails
        """
        try:
            logger.info(f"Submitting message to HCS topic {topic_id}...")
            
            # Convert message to JSON
            message_json = json.dumps(message)
            
            # Convert topic_id string to TopicId object
            topic = TopicId.fromString(topic_id)
            
            # Create and execute transaction
            transaction = (
                TopicMessageSubmitTransaction()
                .setTopicId(topic)
                .setMessage(message_json)
            )
            
            response = transaction.execute(self.client)
            receipt = response.getReceipt(self.client)
            
            tx_id = str(response.transactionId)
            sequence_number = receipt.topicSequenceNumber
            
            logger.info(f"✅ Message submitted to topic {topic_id}")
            logger.info(f"   Transaction ID: {tx_id}")
            logger.info(f"   Sequence Number: {sequence_number}")
            
            return {
                'tx_id': tx_id,
                'sequence_number': sequence_number,
                'topic_id': topic_id,
                'timestamp': receipt.topicRunningHash
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to submit message to topic {topic_id}: {str(e)}")
            raise
    
    async def get_topic_info(self, topic_id: str) -> Dict[str, Any]:
        """
        Get information about an HCS topic
        
        Args:
            topic_id: HCS topic ID
            
        Returns:
            dict: Topic information
            
        Raises:
            Exception: If query fails
        """
        try:
            logger.info(f"Querying info for topic {topic_id}...")
            
            # Convert topic_id string to TopicId object
            topic = TopicId.fromString(topic_id)
            
            query = TopicInfoQuery().setTopicId(topic)
            info = query.execute(self.client)
            
            topic_data = {
                'topic_id': str(info.topicId),
                'memo': info.topicMemo,
                'sequence_number': info.sequenceNumber,
                'admin_key': str(info.adminKey) if info.adminKey else None,
                'submit_key': str(info.submitKey) if info.submitKey else None
            }
            
            logger.info(f"✅ Topic info retrieved for {topic_id}")
            logger.info(f"   Memo: {topic_data['memo']}")
            logger.info(f"   Sequence Number: {topic_data['sequence_number']}")
            
            return topic_data
            
        except Exception as e:
            logger.error(f"❌ Failed to query topic info for {topic_id}: {str(e)}")
            raise
    
    async def query_mirror_node_messages(
        self,
        topic_id: str,
        limit: int = 10,
        sequence_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Query historical HCS messages from Mirror Node
        
        Args:
            topic_id: HCS topic ID
            limit: Maximum number of messages to retrieve
            sequence_number: Optional specific sequence number
            
        Returns:
            dict: Messages from Mirror Node
            
        Note:
            This method uses the Mirror Node REST API to query historical messages.
            For real-time message submission, use submit_hcs_message().
        """
        from .mirror_node_client import mirror_node_client
        
        try:
            logger.info(f"Querying Mirror Node for topic {topic_id} messages...")
            
            if sequence_number:
                # Get specific message
                result = await mirror_node_client.get_topic_message_by_sequence(
                    topic_id=topic_id,
                    sequence_number=sequence_number
                )
            else:
                # Get multiple messages
                result = await mirror_node_client.get_topic_messages(
                    topic_id=topic_id,
                    limit=limit,
                    order="desc"
                )
            
            logger.info(f"✅ Mirror Node query successful")
            return result
            
        except Exception as e:
            logger.error(f"❌ Mirror Node query failed: {str(e)}")
            raise
    
    def close(self):
        """Close the Hedera client connection"""
        if self._client:
            logger.info("Closing Hedera client...")
            self._client.close()
            self._client = None
            logger.info("✅ Hedera client closed")


# Global instance
hedera_client = HederaClient()


# Convenience functions
async def get_balance(account_id: str) -> Hbar:
    """Get account balance"""
    return await hedera_client.get_account_balance(account_id)


async def transfer(
    from_account: str,
    from_key: str,
    to_account: str,
    amount: float,
    memo: Optional[str] = None
) -> str:
    """Transfer HBAR between accounts"""
    return await hedera_client.transfer_hbar(
        from_account,
        from_key,
        to_account,
        amount,
        memo
    )


async def verify_account(account_id: str) -> bool:
    """Verify account exists"""
    return await hedera_client.verify_account_exists(account_id)


async def submit_message(topic_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
    """Submit message to HCS topic"""
    return await hedera_client.submit_hcs_message(topic_id, message)


async def get_topic_info(topic_id: str) -> Dict[str, Any]:
    """Get HCS topic information"""
    return await hedera_client.get_topic_info(topic_id)


async def query_mirror_node(
    topic_id: str,
    limit: int = 10,
    sequence_number: Optional[int] = None
) -> Dict[str, Any]:
    """Query historical HCS messages from Mirror Node"""
    return await hedera_client.query_mirror_node_messages(
        topic_id=topic_id,
        limit=limit,
        sequence_number=sequence_number
    )

