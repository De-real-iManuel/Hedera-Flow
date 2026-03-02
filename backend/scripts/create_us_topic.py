#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hedera import Client, TopicCreateTransaction, AccountId, PrivateKey, Hbar
from config import settings

client = Client.forTestnet()
client.setOperator(
    AccountId.fromString(settings.hedera_operator_id),
    PrivateKey.fromString(settings.hedera_operator_key)
)

print("Creating US topic...")
tx = TopicCreateTransaction().setTopicMemo('Hedera Flow - United States - Verifications & Payments').setMaxTransactionFee(Hbar(1))
resp = tx.execute(client)
receipt = resp.getReceipt(client)
tid = receipt.topicId
topic_str = f"{tid.shard}.{tid.realm}.{tid.num}"
print(f"✅ US Topic: {topic_str}")
print(f"Update .env: HCS_TOPIC_US={topic_str}")
client.close()
