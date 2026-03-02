import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hedera import Client, TopicCreateTransaction, AccountId, PrivateKey, Hbar
from config import settings

topics = [
    ('US', 'Hedera Flow - United States - Verifications & Payments'),
    ('ASIA', 'Hedera Flow - Asia (India) - Verifications & Payments'),
    ('SA', 'Hedera Flow - South America (Brazil) - Verifications & Payments'),
    ('AFRICA', 'Hedera Flow - Africa (Nigeria) - Verifications & Payments')
]

print("Connecting to Hedera testnet...")
client = Client.forTestnet()
client.setOperator(
    AccountId.fromString(settings.hedera_operator_id),
    PrivateKey.fromString(settings.hedera_operator_key)
)

created = {}

for region, memo in topics:
    print(f"\nCreating {region} topic...")
    try:
        transaction = (
            TopicCreateTransaction()
            .setTopicMemo(memo)
            .setMaxTransactionFee(Hbar(1))
        )
        
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        topic_id = receipt.topicId
        topic_id_str = f"{topic_id.shard}.{topic_id.realm}.{topic_id.num}"
        
        print(f"✅ {region}: {topic_id_str}")
        created[region] = topic_id_str
        
        # Wait between creations
        time.sleep(2)
        
    except Exception as e:
        print(f"❌ {region} failed: {e}")
        continue

client.close()

print("\n" + "="*60)
print("CREATED TOPICS:")
print("="*60)
print("HCS_TOPIC_EU=0.0.8052384")
for region, topic_id in created.items():
    print(f"HCS_TOPIC_{region}={topic_id}")
