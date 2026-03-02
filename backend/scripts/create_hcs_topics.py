#!/usr/bin/env python3
"""
Create HCS Topics for Regional Logging

This script creates 5 HCS topics for logging verifications and payments
by region: EU, US, Asia, South America, and Africa.

Requirements:
- FR-5.12: System shall use HCS topics for regional blockchain logging
- US-8: Verifications and payments logged to HCS by region

Usage:
    python scripts/create_hcs_topics.py
"""
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hedera import (
    Client,
    TopicCreateTransaction,
    AccountId,
    PrivateKey,
    Hbar
)
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_hcs_topic(client: Client, memo: str) -> str:
    """
    Create an HCS topic
    
    Args:
        client: Hedera client
        memo: Topic memo/description
        
    Returns:
        Topic ID as string (e.g., "0.0.12345")
    """
    try:
        logger.info(f"Creating HCS topic: {memo}")
        
        # Create topic transaction
        transaction = (
            TopicCreateTransaction()
            .setTopicMemo(memo)
            .setMaxTransactionFee(Hbar(2))
        )
        
        # Execute transaction
        response = transaction.execute(client)
        
        # Get receipt
        receipt = response.getReceipt(client)
        
        # Get topic ID
        topic_id = receipt.topicId
        topic_id_str = f"{topic_id.shard}.{topic_id.realm}.{topic_id.num}"
        
        logger.info(f"✅ Topic created: {topic_id_str}")
        logger.info(f"   Memo: {memo}")
        
        return topic_id_str
        
    except Exception as e:
        logger.error(f"Failed to create topic: {e}")
        raise


def main():
    """Create all 5 regional HCS topics"""
    try:
        logger.info("=" * 60)
        logger.info("HCS TOPIC CREATION SCRIPT")
        logger.info("=" * 60)
        
        # Initialize Hedera client
        logger.info(f"Connecting to Hedera {settings.hedera_network}...")
        
        if settings.hedera_network == "testnet":
            client = Client.forTestnet()
        else:
            client = Client.forMainnet()
        
        # Set operator
        operator_id = AccountId.fromString(settings.hedera_operator_id)
        operator_key = PrivateKey.fromString(settings.hedera_operator_key)
        client.setOperator(operator_id, operator_key)
        
        logger.info(f"✅ Connected with operator: {settings.hedera_operator_id}")
        logger.info("")
        
        # Create 5 regional topics
        topics = {
            'EU': 'Hedera Flow - Europe (Spain) - Verifications & Payments',
            'US': 'Hedera Flow - United States - Verifications & Payments',
            'ASIA': 'Hedera Flow - Asia (India) - Verifications & Payments',
            'SA': 'Hedera Flow - South America (Brazil) - Verifications & Payments',
            'AFRICA': 'Hedera Flow - Africa (Nigeria) - Verifications & Payments'
        }
        
        created_topics = {}
        
        for region, memo in topics.items():
            topic_id = create_hcs_topic(client, memo)
            created_topics[region] = topic_id
            logger.info("")
        
        # Print summary
        logger.info("=" * 60)
        logger.info("✅ ALL TOPICS CREATED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Add these to your backend/.env file:")
        logger.info("")
        logger.info(f"HCS_TOPIC_EU={created_topics['EU']}")
        logger.info(f"HCS_TOPIC_US={created_topics['US']}")
        logger.info(f"HCS_TOPIC_ASIA={created_topics['ASIA']}")
        logger.info(f"HCS_TOPIC_SA={created_topics['SA']}")
        logger.info(f"HCS_TOPIC_AFRICA={created_topics['AFRICA']}")
        logger.info("")
        logger.info("View topics on HashScan:")
        for region, topic_id in created_topics.items():
            logger.info(f"  {region}: https://hashscan.io/testnet/topic/{topic_id}")
        logger.info("")
        
        # Close client
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
