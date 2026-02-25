"""
Test HCS Topics - Submit and Query Messages

This script tests the 5 regional HCS topics by:
1. Submitting test messages to each topic
2. Querying the Mirror Node to verify messages were logged
3. Displaying message content and metadata

Requirements:
- HCS topics created (run create_hcs_topics.py first)
- Topic IDs in .env file
- Operator account with HBAR for message submission fees

Usage:
    python scripts/test_hcs_topics.py
"""

import sys
import os
import json
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hedera import (
    Client,
    TopicMessageSubmitTransaction,
    TopicInfoQuery
)
import requests


def submit_message_to_topic(client, topic_id, message_dict):
    """
    Submit a message to an HCS topic
    
    Args:
        client: Hedera Client instance
        topic_id: Topic ID to submit to
        message_dict: Dictionary to convert to JSON and submit
        
    Returns:
        dict: Transaction info (tx_id, sequence_number, timestamp)
    """
    print(f"\n📤 Submitting message to topic {topic_id}...")
    
    try:
        # Convert message to JSON
        message_json = json.dumps(message_dict, indent=2)
        
        print(f"   Message content:")
        print(f"   {message_json}")
        
        # Create and execute transaction
        transaction = (
            TopicMessageSubmitTransaction()
            .setTopicId(topic_id)
            .setMessage(message_json)
        )
        
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        tx_id = str(response.transactionId)
        sequence_number = receipt.topicSequenceNumber
        
        print(f"✅ Message submitted successfully")
        print(f"   Transaction ID: {tx_id}")
        print(f"   Sequence Number: {sequence_number}")
        
        return {
            'tx_id': tx_id,
            'sequence_number': sequence_number,
            'topic_id': topic_id
        }
        
    except Exception as e:
        print(f"❌ Failed to submit message: {str(e)}")
        raise


def query_topic_messages(topic_id, sequence_number=None):
    """
    Query messages from a topic using Mirror Node API
    
    Args:
        topic_id: Topic ID to query
        sequence_number: Optional specific sequence number to query
        
    Returns:
        list: Messages from the topic
    """
    print(f"\n🔍 Querying messages from topic {topic_id}...")
    
    try:
        # Mirror Node API endpoint
        base_url = "https://testnet.mirrornode.hedera.com/api/v1"
        
        if sequence_number:
            url = f"{base_url}/topics/{topic_id}/messages/{sequence_number}"
        else:
            url = f"{base_url}/topics/{topic_id}/messages?limit=5&order=desc"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if sequence_number:
            # Single message response
            messages = [data]
        else:
            # Multiple messages response
            messages = data.get('messages', [])
        
        print(f"✅ Retrieved {len(messages)} message(s)")
        
        return messages
        
    except Exception as e:
        print(f"❌ Failed to query messages: {str(e)}")
        return []


def display_message(message):
    """
    Display a message in a readable format
    
    Args:
        message: Message object from Mirror Node
    """
    print("\n" + "-" * 60)
    print(f"📨 Message Details:")
    print(f"   Sequence Number: {message.get('sequence_number')}")
    print(f"   Consensus Timestamp: {message.get('consensus_timestamp')}")
    
    # Decode message content
    message_bytes = message.get('message', '')
    if message_bytes:
        try:
            # Mirror Node returns base64 encoded message
            import base64
            decoded = base64.b64decode(message_bytes).decode('utf-8')
            message_json = json.loads(decoded)
            
            print(f"   Message Content:")
            print(f"   {json.dumps(message_json, indent=6)}")
        except Exception as e:
            print(f"   Raw Message: {message_bytes}")
            print(f"   (Could not decode: {e})")
    
    print("-" * 60)


def main():
    """
    Main function to test all HCS topics
    """
    print("=" * 70)
    print("🧪 HCS TOPICS TEST")
    print("=" * 70)
    print("\nThis script will test all 5 regional HCS topics by:")
    print("1. Submitting test messages to each topic")
    print("2. Querying Mirror Node to verify messages")
    print("3. Displaying message content")
    print("=" * 70)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    operator_id = os.getenv('HEDERA_OPERATOR_ID')
    operator_key = os.getenv('HEDERA_OPERATOR_KEY')
    
    # Get topic IDs
    topics = {
        'EU': os.getenv('HCS_TOPIC_EU'),
        'US': os.getenv('HCS_TOPIC_US'),
        'Asia': os.getenv('HCS_TOPIC_ASIA'),
        'SA': os.getenv('HCS_TOPIC_SA'),
        'Africa': os.getenv('HCS_TOPIC_AFRICA')
    }
    
    # Validate configuration
    if not operator_id or not operator_key:
        print("\n❌ ERROR: Missing operator credentials in .env")
        return 1
    
    missing_topics = [name for name, topic_id in topics.items() if not topic_id]
    if missing_topics:
        print(f"\n❌ ERROR: Missing topic IDs in .env: {', '.join(missing_topics)}")
        print("\nRun 'python scripts/create_hcs_topics.py' first to create topics.")
        return 1
    
    # Create client
    print("\n🌐 Connecting to Hedera testnet...")
    
    try:
        client = Client.forTestnet()
        client.setOperator(operator_id, operator_key)
        
        print(f"✅ Connected with operator: {operator_id}")
        
        # Test each topic
        results = {}
        
        for region, topic_id in topics.items():
            print("\n" + "=" * 70)
            print(f"🧪 TESTING {region.upper()} TOPIC: {topic_id}")
            print("=" * 70)
            
            # Create test message based on region
            test_message = {
                'type': 'TEST_VERIFICATION',
                'region': region,
                'timestamp': datetime.utcnow().isoformat(),
                'test_data': {
                    'user_id': f'test-user-{region.lower()}',
                    'meter_reading': 5142.7,
                    'confidence': 0.96,
                    'fraud_score': 0.12,
                    'status': 'VERIFIED',
                    'country_code': {
                        'EU': 'ES',
                        'US': 'US',
                        'Asia': 'IN',
                        'SA': 'BR',
                        'Africa': 'NG'
                    }.get(region, 'XX')
                }
            }
            
            try:
                # Submit message
                result = submit_message_to_topic(client, topic_id, test_message)
                results[region] = result
                
                # Wait a few seconds for Mirror Node to process
                print("\n⏳ Waiting 5 seconds for Mirror Node to process...")
                time.sleep(5)
                
                # Query the message back
                messages = query_topic_messages(topic_id, result['sequence_number'])
                
                if messages:
                    display_message(messages[0])
                else:
                    print("⚠️  Message not yet available on Mirror Node (may take a few seconds)")
                
            except Exception as e:
                print(f"\n❌ Test failed for {region} topic: {str(e)}")
                results[region] = {'error': str(e)}
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        success_count = sum(1 for r in results.values() if 'error' not in r)
        total_count = len(results)
        
        print(f"\n✅ Successful: {success_count}/{total_count}")
        
        for region, result in results.items():
            if 'error' in result:
                print(f"   ❌ {region}: {result['error']}")
            else:
                print(f"   ✅ {region}: Sequence #{result['sequence_number']}")
        
        if success_count == total_count:
            print("\n🎉 ALL TESTS PASSED!")
            print("\nYou can view your messages on HashScan:")
            for region, topic_id in topics.items():
                print(f"   {region}: https://hashscan.io/testnet/topic/{topic_id}")
        else:
            print("\n⚠️  Some tests failed. Check the errors above.")
        
        client.close()
        
        return 0 if success_count == total_count else 1
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())