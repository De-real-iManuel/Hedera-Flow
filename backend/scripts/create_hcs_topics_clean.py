"""
Create HCS Topics for Regional Blockchain Logging

This script creates 5 Hedera Consensus Service (HCS) topics for logging
verifications and payments by region:

1. EU Topic - Europe (Spain, etc.)
2. US Topic - United States
3. Asia Topic - Asia (India, etc.)
4. SA Topic - South America (Brazil, etc.)
5. Africa Topic - Africa (Nigeria, etc.)

Each topic logs:
- Verification events (meter readings, OCR results, fraud scores)
- Payment events (HBAR transfers, fiat equivalents, exchange rates)
- Dispute events (creation, resolution)

Requirements:
- Hedera SDK Python installed (hedera-sdk-python)
- Operator account with sufficient HBAR for topic creation fees
- Internet connection to Hedera testnet

Usage:
    python scripts/create_hcs_topics.py

Output:
    - Topic IDs printed to console
    - Instructions for updating .env file
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hedera import (
    Client,
    TopicCreateTransaction,
    TopicInfoQuery,
    AccountBalanceQuery
)


def create_hcs_topic(client, topic_name, memo):
    """
    Create a new HCS topic
    
    Args:
        client: Hedera Client instance
        topic_name: Human-readable name for the topic
        memo: Description of the topic's purpose
        
    Returns:
        str: Topic ID (e.g., "0.0.12345")
    """
    print(f"\n📝 Creating HCS topic: {topic_name}")
    print(f"   Memo: {memo}")
    
    try:
        # Create topic transaction
        transaction = (
            TopicCreateTransaction()
            .setTopicMemo(memo)
            .setAdminKey(client.operatorPublicKey)  # Allow topic updates
            .setSubmitKey(client.operatorPublicKey)  # Control who can submit messages
        )
        
        # Execute transaction
        response = transaction.execute(client)
        
        # Get receipt
        receipt = response.getReceipt(client)
        topic_id = receipt.topicId
        
        print(f"✅ Topic created: {topic_id}")
        
        return str(topic_id)
        
    except Exception as e:
        print(f"❌ Failed to create topic: {str(e)}")
        raise


def verify_topic(client, topic_id):
    """
    Verify that a topic exists and get its info
    
    Args:
        client: Hedera Client instance
        topic_id: Topic ID to verify
        
    Returns:
        dict: Topic information
    """
    print(f"\n🔍 Verifying topic {topic_id}...")
    
    try:
        query = TopicInfoQuery().setTopicId(topic_id)
        info = query.execute(client)
        
        print(f"✅ Topic verified:")
        print(f"   Topic ID: {info.topicId}")
        print(f"   Memo: {info.topicMemo}")
        print(f"   Sequence Number: {info.sequenceNumber}")
        
        return {
            'topic_id': str(info.topicId),
            'memo': info.topicMemo,
            'sequence_number': info.sequenceNumber
        }
        
    except Exception as e:
        print(f"❌ Failed to verify topic: {str(e)}")
        raise


def check_operator_balance(client, operator_id):
    """
    Check operator account balance
    
    Args:
        client: Hedera Client instance
        operator_id: Operator account ID
        
    Returns:
        float: Balance in HBAR
    """
    print(f"\n💰 Checking operator balance...")
    
    try:
        query = AccountBalanceQuery().setAccountId(operator_id)
        balance = query.execute(client)
        
        hbar_balance = float(balance.hbars.toString().split()[0])
        
        print(f"✅ Operator balance: {hbar_balance} HBAR")
        
        return hbar_balance
        
    except Exception as e:
        print(f"❌ Failed to check balance: {str(e)}")
        raise


def main():
    """
    Main function to create all 5 regional HCS topics
    """
    print("=" * 70)
    print("HEDERA CONSENSUS SERVICE (HCS) TOPIC CREATION")
    print("=" * 70)
    print("\nThis script will create 5 HCS topics for regional logging:")
    print("1. EU Topic - Europe (Spain, etc.)")
    print("2. US Topic - United States")
    print("3. Asia Topic - Asia (India, etc.)")
    print("4. SA Topic - South America (Brazil, etc.)")
    print("5. Africa Topic - Africa (Nigeria, etc.)")
    print("\nIMPORTANT: Save the output! You'll need it for .env file")
    print("=" * 70)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    operator_id = os.getenv('HEDERA_OPERATOR_ID')
    operator_key = os.getenv('HEDERA_OPERATOR_KEY')
    
    if not operator_id or not operator_key:
        print("\n[ERROR] Missing Hedera operator credentials")
        print("\nPlease set the following in your .env file:")
        print("   HEDERA_OPERATOR_ID=0.0.xxxxx")
        print("   HEDERA_OPERATOR_KEY=302e020100300506032b657004220420...")
        print("\nRun 'python scripts/create_hedera_accounts.py' first if you haven't.")
        return 1
    
    # Create client
    print("\nConnecting to Hedera testnet...")
    
    try:
        from hedera import PrivateKey, AccountId
        
        client = Client.forTestnet()
        
        # Parse operator ID
        operator_account_id = AccountId.fromString(operator_id)
        
        # Parse operator key - handle both hex and DER formats
        if operator_key.startswith('0x'):
            # Remove 0x prefix and use fromStringECDSA
            hex_key = operator_key[2:]
            operator_private_key = PrivateKey.fromStringECDSA(hex_key)
        elif operator_key.startswith('302e'):
            # DER format
            operator_private_key = PrivateKey.fromString(operator_key)
        else:
            # Try as ECDSA hex without prefix
            operator_private_key = PrivateKey.fromStringECDSA(operator_key)
        
        client.setOperator(operator_account_id, operator_private_key)
        
        print(f"[OK] Connected with operator: {operator_id}")
        
        # Check balance
        balance = check_operator_balance(client, operator_id)
        
        # Estimate cost: ~$0.01 per topic = ~0.03 HBAR per topic (at $0.30/HBAR)
        # Total: ~0.15 HBAR for 5 topics + fees
        required_balance = 1.0  # 1 HBAR to be safe
        
        if balance < required_balance:
            print(f"\n❌ ERROR: Insufficient balance")
            print(f"   Current: {balance} HBAR")
            print(f"   Required: At least {required_balance} HBAR")
            print(f"\n   Get testnet HBAR from: https://portal.hedera.com/")
            return 1
        
        print(f"\n✅ Sufficient balance for topic creation")
        
        # Define topics
        topics = [
            {
                'name': 'EU Topic',
                'region': 'Europe',
                'countries': 'Spain, etc.',
                'memo': 'Hedera Flow - EU Region: Verifications, payments, disputes for European countries (ES)'
            },
            {
                'name': 'US Topic',
                'region': 'United States',
                'countries': 'USA',
                'memo': 'Hedera Flow - US Region: Verifications, payments, disputes for United States (US)'
            },
            {
                'name': 'Asia Topic',
                'region': 'Asia',
                'countries': 'India, etc.',
                'memo': 'Hedera Flow - Asia Region: Verifications, payments, disputes for Asian countries (IN)'
            },
            {
                'name': 'SA Topic',
                'region': 'South America',
                'countries': 'Brazil, etc.',
                'memo': 'Hedera Flow - SA Region: Verifications, payments, disputes for South American countries (BR)'
            },
            {
                'name': 'Africa Topic',
                'region': 'Africa',
                'countries': 'Nigeria, etc.',
                'memo': 'Hedera Flow - Africa Region: Verifications, payments, disputes for African countries (NG)'
            }
        ]
        
        # Create topics
        created_topics = {}
        
        for i, topic_config in enumerate(topics, 1):
            print("\n" + "=" * 70)
            print(f"{i}️⃣  CREATING {topic_config['name'].upper()}")
            print("=" * 70)
            print(f"   Region: {topic_config['region']}")
            print(f"   Countries: {topic_config['countries']}")
            
            topic_id = create_hcs_topic(
                client,
                topic_config['name'],
                topic_config['memo']
            )
            
            # Verify topic
            topic_info = verify_topic(client, topic_id)
            
            # Store topic ID
            key = topic_config['name'].split()[0].upper()  # EU, US, ASIA, SA, AFRICA
            created_topics[key] = topic_id
            
            print(f"\n✅ {topic_config['name']} ready for logging")
        
        # Print summary
        print("\n" + "=" * 70)
        print("✅ SUCCESS! ALL 5 HCS TOPICS CREATED")
        print("=" * 70)
        
        print("\n📋 TOPIC IDs:")
        print(f"   EU Topic:     {created_topics['EU']}")
        print(f"   US Topic:     {created_topics['US']}")
        print(f"   Asia Topic:   {created_topics['ASIA']}")
        print(f"   SA Topic:     {created_topics['SA']}")
        print(f"   Africa Topic: {created_topics['AFRICA']}")
        
        print("\n" + "=" * 70)
        print("📝 NEXT STEPS:")
        print("=" * 70)
        print("\n1. Update your backend/.env file with these values:")
        print(f"\n   HCS_TOPIC_EU={created_topics['EU']}")
        print(f"   HCS_TOPIC_US={created_topics['US']}")
        print(f"   HCS_TOPIC_ASIA={created_topics['ASIA']}")
        print(f"   HCS_TOPIC_SA={created_topics['SA']}")
        print(f"   HCS_TOPIC_AFRICA={created_topics['AFRICA']}")
        
        print("\n2. Verify topics on HashScan:")
        for key, topic_id in created_topics.items():
            print(f"   {key}: https://hashscan.io/testnet/topic/{topic_id}")
        
        print("\n3. Test HCS message submission:")
        print("   python scripts/test_hcs_topics.py")
        
        print("\n📊 TOPIC USAGE:")
        print("   - EU Topic: Spain (ES) → Logs verifications/payments for Spanish users")
        print("   - US Topic: USA (US) → Logs verifications/payments for US users")
        print("   - Asia Topic: India (IN) → Logs verifications/payments for Indian users")
        print("   - SA Topic: Brazil (BR) → Logs verifications/payments for Brazilian users")
        print("   - Africa Topic: Nigeria (NG) → Logs verifications/payments for Nigerian users")
        
        print("\n💡 MESSAGE FORMAT:")
        print("   Each topic will log JSON messages containing:")
        print("   - Verification events: user_id, meter_reading, confidence, fraud_score, status")
        print("   - Payment events: bill_id, amount_hbar, amount_fiat, exchange_rate, tx_id")
        print("   - Dispute events: dispute_id, bill_id, reason, evidence_hashes")
        
        print("\n" + "=" * 70)
        
        # Check final balance
        final_balance = check_operator_balance(client, operator_id)
        cost = balance - final_balance
        print(f"\n💰 Total cost: {cost:.4f} HBAR")
        
    except Exception as e:
        print(f"\n[ERROR]: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify operator account has sufficient HBAR")
        print("2. Check operator credentials in .env file")
        print("3. Ensure internet connection to Hedera testnet")
        print("4. Visit https://portal.hedera.com/ for testnet HBAR")
        return 1
    
    finally:
        if 'client' in locals():
            client.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
