"""
Script to verify Hedera configuration and HCS topic access
"""
import os
from dotenv import load_dotenv
from hedera import Client, AccountId, PrivateKey, AccountBalanceQuery, TopicInfoQuery, TopicId

# Load environment variables
load_dotenv()

def check_hedera_setup():
    """Check Hedera operator account and HCS topics"""
    
    print("=" * 60)
    print("HEDERA CONFIGURATION CHECK")
    print("=" * 60)
    
    # Get configuration
    network = os.getenv('HEDERA_NETWORK', 'testnet')
    operator_id = os.getenv('HEDERA_OPERATOR_ID')
    operator_key = os.getenv('HEDERA_OPERATOR_KEY')
    
    print(f"\n1. Configuration:")
    print(f"   Network: {network}")
    print(f"   Operator ID: {operator_id}")
    print(f"   Operator Key: {operator_key[:20]}..." if operator_key else "   Operator Key: NOT SET")
    
    if not operator_id or not operator_key:
        print("\n❌ ERROR: Hedera operator credentials not configured!")
        print("   Please set HEDERA_OPERATOR_ID and HEDERA_OPERATOR_KEY in .env")
        return False
    
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
        
        print("\n✅ Client initialized successfully")
        
        # Check account balance
        print("\n2. Checking account balance...")
        balance_query = AccountBalanceQuery().setAccountId(account_id)
        balance = balance_query.execute(client)
        
        print(f"   HBAR Balance: {balance.hbars.toString()}")
        
        if balance.hbars.toTinybars() < 100000000:  # Less than 1 HBAR
            print("   ⚠️  WARNING: Low HBAR balance! You may need to fund your account.")
        else:
            print("   ✅ Sufficient HBAR balance")
        
        # Check HCS topics
        print("\n3. Checking HCS Topics:")
        topics = {
            'EU': os.getenv('HCS_TOPIC_EU'),
            'US': os.getenv('HCS_TOPIC_US'),
            'ASIA': os.getenv('HCS_TOPIC_ASIA'),
            'SA': os.getenv('HCS_TOPIC_SA'),
            'AFRICA': os.getenv('HCS_TOPIC_AFRICA')
        }
        
        for region, topic_id_str in topics.items():
            if not topic_id_str:
                print(f"   ❌ {region}: NOT CONFIGURED")
                continue
            
            try:
                topic_id = TopicId.fromString(topic_id_str)
                topic_info_query = TopicInfoQuery().setTopicId(topic_id)
                topic_info = topic_info_query.execute(client)
                
                print(f"   ✅ {region} ({topic_id_str}):")
                print(f"      Memo: {topic_info.topicMemo}")
                print(f"      Submit Key: {topic_info.submitKey if topic_info.submitKey else 'None (public)'}")
                
                if topic_info.submitKey:
                    print(f"      ⚠️  This topic requires a submit key!")
                    print(f"      Your operator key must match the submit key to post messages.")
                
            except Exception as e:
                print(f"   ❌ {region} ({topic_id_str}): ERROR - {str(e)}")
        
        print("\n" + "=" * 60)
        print("RECOMMENDATIONS:")
        print("=" * 60)
        
        print("\nIf topics have submit keys that don't match your operator key:")
        print("1. Create new HCS topics without submit keys (public topics)")
        print("2. Or use topics where your operator key is the submit key")
        print("\nTo create a new public HCS topic, run:")
        print("   python backend/create_hcs_topics.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    check_hedera_setup()
