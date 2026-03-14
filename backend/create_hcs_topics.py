"""
Script to create new HCS topics for smart meter consumption logging
"""
import os
from dotenv import load_dotenv
from hedera import (
    Client,
    AccountId,
    PrivateKey,
    TopicCreateTransaction,
    Hbar
)

# Load environment variables
load_dotenv()

def create_hcs_topics():
    """Create HCS topics for each region"""
    
    print("=" * 60)
    print("CREATING HCS TOPICS FOR SMART METER CONSUMPTION")
    print("=" * 60)
    
    # Get configuration
    network = os.getenv('HEDERA_NETWORK', 'testnet')
    operator_id = os.getenv('HEDERA_OPERATOR_ID')
    operator_key = os.getenv('HEDERA_OPERATOR_KEY')
    
    if not operator_id or not operator_key:
        print("\n❌ ERROR: Hedera operator credentials not configured!")
        return
    
    try:
        # Create client
        if network == "testnet":
            client = Client.forTestnet()
        else:
            client = Client.forMainnet()
        
        # Set operator
        account_id = AccountId.fromString(operator_id)
        private_key = PrivateKey.fromString(operator_key)
        client.setOperator(account_id, private_key)
        
        print(f"\n✅ Connected to {network}")
        print(f"   Operator: {operator_id}")
        
        # Define regions
        regions = [
            ('EU', 'Europe - Smart Meter Consumption Logs'),
            ('US', 'United States - Smart Meter Consumption Logs'),
            ('ASIA', 'Asia - Smart Meter Consumption Logs'),
            ('SA', 'South America - Smart Meter Consumption Logs'),
            ('AFRICA', 'Africa - Smart Meter Consumption Logs')
        ]
        
        print("\n" + "=" * 60)
        print("Creating Topics...")
        print("=" * 60)
        
        topic_ids = {}
        
        for region_code, memo in regions:
            print(f"\nCreating topic for {region_code}...")
            print(f"   Memo: {memo}")
            
            # Create topic transaction
            # Note: No submitKey means it's a public topic (anyone can submit)
            transaction = (
                TopicCreateTransaction()
                .setTopicMemo(memo)
                .setMaxTransactionFee(Hbar(2))
            )
            
            # Execute transaction
            response = transaction.execute(client)
            receipt = response.getReceipt(client)
            topic_id = receipt.topicId
            
            topic_ids[region_code] = str(topic_id)
            
            print(f"   ✅ Created: {topic_id}")
        
        # Print environment variables to add to .env
        print("\n" + "=" * 60)
        print("ADD THESE TO YOUR .env FILE:")
        print("=" * 60)
        print()
        for region_code, topic_id in topic_ids.items():
            print(f"HCS_TOPIC_{region_code}={topic_id}")
        
        print("\n" + "=" * 60)
        print("✅ ALL TOPICS CREATED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    create_hcs_topics()
