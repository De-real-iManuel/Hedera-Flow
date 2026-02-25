"""
Hedera Mirror Node Client Utility

Provides access to Hedera Mirror Node REST API for querying historical data.
Supports querying HCS topic messages, transactions, and account information.
"""

import aiohttp
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MirrorNodeClient:
    """
    Client for interacting with Hedera Mirror Node REST API
    
    Provides methods to query historical blockchain data including:
    - HCS topic messages
    - Transaction details
    - Account information
    """
    
    def __init__(self, base_url: str = "https://testnet.mirrornode.hedera.com"):
        """
        Initialize Mirror Node client
        
        Args:
            base_url: Base URL for Mirror Node API (default: testnet)
        """
        self.base_url = base_url.rstrip('/')
        self.api_version = "api/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info(f"Mirror Node client initialized with base URL: {self.base_url}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("Mirror Node client session closed")
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP GET request to Mirror Node API
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            dict: JSON response
            
        Raises:
            Exception: If request fails
        """
        url = f"{self.base_url}/{self.api_version}/{endpoint}"
        
        try:
            session = await self._get_session()
            
            logger.debug(f"Mirror Node request: GET {url}")
            if params:
                logger.debug(f"Query params: {params}")
            
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                logger.debug(f"Mirror Node response: {response.status}")
                return data
                
        except aiohttp.ClientError as e:
            logger.error(f"Mirror Node request failed: {str(e)}")
            raise Exception(f"Mirror Node API error: {str(e)}")
    
    async def get_topic_messages(
        self,
        topic_id: str,
        limit: int = 10,
        order: str = "desc",
        sequence_number: Optional[int] = None,
        timestamp_from: Optional[str] = None,
        timestamp_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get messages from an HCS topic
        
        Args:
            topic_id: Topic ID (e.g., "0.0.12345")
            limit: Maximum number of messages to return (default: 10, max: 100)
            order: Sort order - "asc" or "desc" (default: "desc")
            sequence_number: Filter by specific sequence number
            timestamp_from: Filter messages after this timestamp (format: seconds.nanoseconds)
            timestamp_to: Filter messages before this timestamp
            
        Returns:
            dict: Response containing messages array and pagination links
            
        Example response:
            {
                "messages": [
                    {
                        "consensus_timestamp": "1234567890.123456789",
                        "topic_id": "0.0.12345",
                        "message": "base64_encoded_message",
                        "running_hash": "base64_hash",
                        "running_hash_version": 3,
                        "sequence_number": 1
                    }
                ],
                "links": {
                    "next": "/api/v1/topics/0.0.12345/messages?limit=10&order=desc"
                }
            }
        """
        try:
            logger.info(f"Querying messages for topic {topic_id}...")
            
            # Build query parameters
            params = {
                "limit": min(limit, 100),  # Cap at 100
                "order": order
            }
            
            if sequence_number is not None:
                params["sequencenumber"] = sequence_number
            
            if timestamp_from:
                params["timestamp"] = f"gte:{timestamp_from}"
            
            if timestamp_to:
                if "timestamp" in params:
                    params["timestamp"] = f"{params['timestamp']}&lte:{timestamp_to}"
                else:
                    params["timestamp"] = f"lte:{timestamp_to}"
            
            # Make request
            endpoint = f"topics/{topic_id}/messages"
            data = await self._make_request(endpoint, params)
            
            # Decode messages
            if "messages" in data:
                for msg in data["messages"]:
                    if "message" in msg:
                        # Decode base64 message
                        import base64
                        try:
                            decoded = base64.b64decode(msg["message"]).decode('utf-8')
                            msg["message_decoded"] = json.loads(decoded)
                        except Exception as e:
                            logger.warning(f"Failed to decode message: {str(e)}")
                            msg["message_decoded"] = None
            
            logger.info(f"✅ Retrieved {len(data.get('messages', []))} messages from topic {topic_id}")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to query topic messages: {str(e)}")
            raise
    
    async def get_topic_message_by_sequence(
        self,
        topic_id: str,
        sequence_number: int
    ) -> Dict[str, Any]:
        """
        Get a specific message from a topic by sequence number
        
        Args:
            topic_id: Topic ID
            sequence_number: Message sequence number
            
        Returns:
            dict: Message data
        """
        try:
            logger.info(f"Querying message {sequence_number} from topic {topic_id}...")
            
            endpoint = f"topics/{topic_id}/messages/{sequence_number}"
            data = await self._make_request(endpoint)
            
            # Decode message
            if "message" in data:
                import base64
                try:
                    decoded = base64.b64decode(data["message"]).decode('utf-8')
                    data["message_decoded"] = json.loads(decoded)
                except Exception as e:
                    logger.warning(f"Failed to decode message: {str(e)}")
                    data["message_decoded"] = None
            
            logger.info(f"✅ Retrieved message {sequence_number} from topic {topic_id}")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to query topic message: {str(e)}")
            raise
    
    async def get_transaction(
        self,
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        Get transaction details by transaction ID
        
        Args:
            transaction_id: Transaction ID (e.g., "0.0.12345@1234567890.123456789")
            
        Returns:
            dict: Transaction data
        """
        try:
            logger.info(f"Querying transaction {transaction_id}...")
            
            endpoint = f"transactions/{transaction_id}"
            data = await self._make_request(endpoint)
            
            logger.info(f"✅ Retrieved transaction {transaction_id}")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to query transaction: {str(e)}")
            raise
    
    async def get_account_info(
        self,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Get account information
        
        Args:
            account_id: Account ID (e.g., "0.0.12345")
            
        Returns:
            dict: Account data including balance
        """
        try:
            logger.info(f"Querying account info for {account_id}...")
            
            endpoint = f"accounts/{account_id}"
            data = await self._make_request(endpoint)
            
            logger.info(f"✅ Retrieved account info for {account_id}")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to query account info: {str(e)}")
            raise
    
    async def get_account_transactions(
        self,
        account_id: str,
        limit: int = 10,
        order: str = "desc",
        transaction_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get transactions for an account
        
        Args:
            account_id: Account ID
            limit: Maximum number of transactions (default: 10, max: 100)
            order: Sort order - "asc" or "desc"
            transaction_type: Filter by transaction type (e.g., "CRYPTOTRANSFER")
            
        Returns:
            dict: Response containing transactions array
        """
        try:
            logger.info(f"Querying transactions for account {account_id}...")
            
            params = {
                "account.id": account_id,
                "limit": min(limit, 100),
                "order": order
            }
            
            if transaction_type:
                params["transactiontype"] = transaction_type
            
            endpoint = "transactions"
            data = await self._make_request(endpoint, params)
            
            logger.info(f"✅ Retrieved {len(data.get('transactions', []))} transactions for {account_id}")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to query account transactions: {str(e)}")
            raise
    
    async def search_verification_logs(
        self,
        topic_id: str,
        user_id: Optional[str] = None,
        meter_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search verification logs in HCS topic
        
        Args:
            topic_id: HCS topic ID
            user_id: Filter by user ID (anonymized)
            meter_id: Filter by meter ID
            status: Filter by status (VERIFIED, WARNING, DISCREPANCY)
            limit: Maximum results
            
        Returns:
            list: Filtered verification logs
        """
        try:
            logger.info(f"Searching verification logs in topic {topic_id}...")
            
            # Get messages from topic
            response = await self.get_topic_messages(
                topic_id=topic_id,
                limit=limit,
                order="desc"
            )
            
            messages = response.get("messages", [])
            
            # Filter messages
            filtered = []
            for msg in messages:
                decoded = msg.get("message_decoded")
                if not decoded or decoded.get("type") != "VERIFICATION":
                    continue
                
                # Apply filters
                if user_id and decoded.get("userId") != user_id:
                    continue
                
                if meter_id and decoded.get("meterId") != meter_id:
                    continue
                
                if status and decoded.get("status") != status:
                    continue
                
                filtered.append({
                    "sequence_number": msg["sequence_number"],
                    "consensus_timestamp": msg["consensus_timestamp"],
                    "data": decoded
                })
            
            logger.info(f"✅ Found {len(filtered)} matching verification logs")
            
            return filtered
            
        except Exception as e:
            logger.error(f"❌ Failed to search verification logs: {str(e)}")
            raise
    
    async def search_payment_logs(
        self,
        topic_id: str,
        bill_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search payment logs in HCS topic
        
        Args:
            topic_id: HCS topic ID
            bill_id: Filter by bill ID
            limit: Maximum results
            
        Returns:
            list: Filtered payment logs
        """
        try:
            logger.info(f"Searching payment logs in topic {topic_id}...")
            
            # Get messages from topic
            response = await self.get_topic_messages(
                topic_id=topic_id,
                limit=limit,
                order="desc"
            )
            
            messages = response.get("messages", [])
            
            # Filter messages
            filtered = []
            for msg in messages:
                decoded = msg.get("message_decoded")
                if not decoded or decoded.get("type") != "PAYMENT":
                    continue
                
                # Apply filters
                if bill_id and decoded.get("billId") != bill_id:
                    continue
                
                filtered.append({
                    "sequence_number": msg["sequence_number"],
                    "consensus_timestamp": msg["consensus_timestamp"],
                    "data": decoded
                })
            
            logger.info(f"✅ Found {len(filtered)} matching payment logs")
            
            return filtered
            
        except Exception as e:
            logger.error(f"❌ Failed to search payment logs: {str(e)}")
            raise


# Global instance
mirror_node_client = MirrorNodeClient()


# Convenience functions
async def get_topic_messages(
    topic_id: str,
    limit: int = 10,
    sequence_number: Optional[int] = None
) -> Dict[str, Any]:
    """Get messages from HCS topic"""
    return await mirror_node_client.get_topic_messages(
        topic_id=topic_id,
        limit=limit,
        sequence_number=sequence_number
    )


async def get_topic_message(topic_id: str, sequence_number: int) -> Dict[str, Any]:
    """Get specific message by sequence number"""
    return await mirror_node_client.get_topic_message_by_sequence(
        topic_id=topic_id,
        sequence_number=sequence_number
    )


async def get_transaction(transaction_id: str) -> Dict[str, Any]:
    """Get transaction details"""
    return await mirror_node_client.get_transaction(transaction_id)


async def get_account_info(account_id: str) -> Dict[str, Any]:
    """Get account information"""
    return await mirror_node_client.get_account_info(account_id)


async def search_verifications(
    topic_id: str,
    meter_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Search verification logs"""
    return await mirror_node_client.search_verification_logs(
        topic_id=topic_id,
        meter_id=meter_id,
        status=status,
        limit=limit
    )


async def search_payments(
    topic_id: str,
    bill_id: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Search payment logs"""
    return await mirror_node_client.search_payment_logs(
        topic_id=topic_id,
        bill_id=bill_id,
        limit=limit
    )
