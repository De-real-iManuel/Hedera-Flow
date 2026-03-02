#!/usr/bin/env python3
"""Quick test to create a single HCS topic"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hedera import Client, TopicCreateTransaction, AccountId, PrivateKey, Hbar
from config import settings

print("Connecting to Hedera testnet...")
client = Client.forTestnet()
client.setOperator(
    AccountId.fromString(settings.hedera_operator_id),
    PrivateKey.fromString(settings.hedera_operator_key)
)

print(f"Operator: {settings.hedera_operator_id}")
print("Creating topic...")

try:
    transaction = (
        TopicCreateTransaction()
        .setTopicMemo("Hedera Flow - Test Topic")
        .setMaxTransactionFee(Hbar(1))
    )
    
    print("Executing transaction...")
    response = transaction.execute(client)
    
    print("Getting receipt...")
    receipt = response.getReceipt(client)
    
    topic_id = receipt.topicId
    topic_id_str = f"{topic_id.shard}.{topic_id.realm}.{topic_id.num}"
    print(f"✅ Topic created: {topic_id_str}")
    print(f"View on HashScan: https://hashscan.io/testnet/topic/{topic_id_str}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

client.close()
