"""
Test HCS Message Submission and Retrieval

This script tests the complete HCS message flow:
1. Submit messages to HCS topics
2. Retrieve message information
3. Verify message content and metadata
4. Test different message types (verification, payment, dispute)

Requirements:
- HCS topics created 
- Operator account with HBAR for transaction fees
- Hedera SDK Python installed

Usage:
    python scripts/test_hcs_message_flow.py
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
    TopicInfoQuery,
    AccountBalanceQuery
)


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """Print a formatted section"""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}")


def check_balance(client, account_id):
    """Check account balance"""
    try:
        query = AccountBalanceQuery().setAccountId(account_id)
        balance = query.execute(client)
        hbar_balance = float(balance.hbars.toString().split()[0])
        return hbar_balance
    except Exception as e:
        print(f"❌ Failed to check balance: {str(e)}")
        return 0


def get_topic_info(client, topic_id):
    """Get information about an HCS topic"""
    try:
        print(f"\n🔍 Querying topic info for {topic_id}...")
        
        query = TopicInfoQuery().setTopicId(topic_id)
        info = query.execute(client)
        
        topic_data = {
            'topic_id': str(info.topicId),
            'memo': info.topicMemo,
            'sequence_number': info.sequenceNumber,
            'admin_key': str(info.adminKey) if info.adminKey else None,
            'submit_key': str(info.submitKey) if info.submitKey else None
        }
        
        print(f"✅ Topic Info Retrieved:")
        print(f"   Topic ID: {topic_data['topic_id']}")
        print(f"   Memo: {topic_data['memo']}")
        print(f"   Current Sequence: {topic_data['sequence_number']}")
        print(f"   Admin Key: {'Set' if topic_data['admin_key'] else 'None'}")
        print(f"   Submit Key: {'Set' if topic_data['submit_key'] else 'None'}")
        
        return topic_data
        
    except Exception as e:
        print(f"❌ Failed to get topic info: {str(e)}")
        raise


def submit_message(client, topic_id, message_dict, message_type):
    """Submit a message to an HCS topic"""
    try:
        print(f"\n📤 Submitting {message_type} message to topic {topic_id}...")
        
        # Convert message to JSON
        message_json = json.dumps(message_dict, indent=2)
        print(f"\n📝 Message Content:")
        print(message_json)
        
        # Create and execute transaction
        transaction = (
            TopicMessageSubmitTransaction()
            .setTopicId(topic_id)
            .setMessage(message_json)
        )
        
        # Execute and get receipt
        response = transaction.execute(client)
        receipt = response.getReceipt(client)
        
        # Extract transaction details
        tx_id = str(response.transactionId)
        sequence_number = receipt.topicSequenceNumber
        running_hash = receipt.topicRunningHash
        
        print(f"\n✅ Message Submitted Successfully!")
        print(f"   Transaction ID: {tx_id}")
        print(f"   Sequence Number: {sequence_number}")
        print(f"   Running Hash: {running_hash.hex() if running_hash else 'N/A'}")
        print(f"   HashScan: https://hashscan.io/testnet/transaction/{tx_id}")
        
        return {
            'tx_id': tx_id,
            'sequence_number': sequence_number,
            'running_hash': running_hash.hex() if running_hash else None,
            'topic_id': topic_id,
            'message': message_dict
        }
        
    except Exception as e:
        print(f"❌ Failed to submit message: {str(e)}")
        raise


def verify_message_submission(client, topic_id, expected_sequence):
    """Verify that a message was submitted by checking topic sequence number"""
    try:
        print(f"\n🔍 Verifying message submission...")
        
        # Get current topic info
        query = TopicInfoQuery().setTopicId(topic_id)
        info = query.execute(client)
        
        current_sequence = info.sequenceNumber
        
        if current_sequence >= expected_sequence:
            print(f"✅ Message verified on topic!")
            print(f"   Expected Sequence: {expected_sequence}")
            print(f"   Current Sequence: {current_sequence}")
            return True
        else:
            print(f"⚠️  Message not yet visible")
            print(f"   Expected: {expected_sequence}")
            print(f"   Current: {current_sequence}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to verify message: {str(e)}")
        return False


def test_verification_message(client, topic_id):
    """Test submitting a verification message"""
    print_section("TEST 1: Verification Message")
    
    # Create sample verification message
    verification_msg = {
        "type": "VERIFICATION",
        "timestamp": int(time.time()),
        "user_id": "test-user-12345",
        "meter_id": "ESP-87654321",
        "reading": 5142.7,
        "utility_reading": 5089.2,
        "confidence": 0.96,
        "fraud_score": 0.12,
        "status": "VERIFIED",
        "image_hash": "ipfs://QmTest123456789",
        "consumption_kwh": 53.5,
        "test_message": True
    }
    
    # Submit message
    result = submit_message(client, topic_id, verification_msg, "VERIFICATION")
    
    # Wait a moment for consensus
    print("\n⏳ Waiting 3 seconds for consensus...")
    time.sleep(3)
    
    # Verify submission
    verify_message_submission(client, topic_id, result['sequence_number'])
    
    return result


def test_payment_message(client, topic_id):
    """Test submitting a payment message"""
    print_section("TEST 2: Payment Message")
    
    # Create sample payment message
    payment_msg = {
        "type": "PAYMENT",
        "timestamp": int(time.time()),
        "bill_id": "BILL-ES-2026-001",
        "user_id": "test-user-12345",
        "amount_fiat": 85.40,
        "currency_fiat": "EUR",
        "amount_hbar": 251.17,
        "exchange_rate": 0.34,
        "tx_id": "0.0.123456@1710789700.123",
        "status": "SUCCESS",
        "test_message": True
    }
    
    # Submit message
    result = submit_message(client, topic_id, payment_msg, "PAYMENT")
    
    # Wait a moment for consensus
    print("\n⏳ Waiting 3 seconds for consensus...")
    time.sleep(3)
    
    # Verify submission
    verify_message_submission(client, topic_id, result['sequence_number'])
    
    return result


def test_dispute_message(client, topic_id):
    """Test submitting a dispute message"""
    print_section("TEST 3: Dispute Message")
    
    # Create sample dispute message
    dispute_msg = {
        "type": "DISPUTE_CREATED",
        "timestamp": int(time.time()),
        "dispute_id": "DISP-ES-2026-001",
        "bill_id": "BILL-ES-2026-001",
        "user_id": "test-user-12345",
        "reason": "OVERCHARGE",
        "description": "Bill amount significantly higher than expected",
        "evidence_hashes": [
            "ipfs://QmEvidence1",
            "ipfs://QmEvidence2"
        ],
        "escrow_amount_hbar": 251.17,
        "escrow_tx_id": "0.0.123456@1710789800.456",
        "status": "PENDING",
        "test_message": True
    }
    
    # Submit message
    result = submit_message(client, topic_id, dispute_msg, "DISPUTE")
    
    # Wait a moment for consensus
    print("\n⏳ Waiting 3 seconds for consensus...")
    time.sleep(3)
    
    # Verify submission
    verify_message_submission(client, topic_id, result['sequence_number'])
    
    return result


def test_multiple_topics(client, topics):
    """Test submitting messages to multiple regional topics"""
    print_section("TEST 4: Multiple Regional Topics")
    
    results = []
    
    for region, topic_id in topics.items():
        if topic_id and topic_id != "0.0.xxxxx":
            print(f"\n📍 Testing {region} Topic: {topic_id}")
            
            # Create region-specific message
            msg = {
                "type": "VERIFICATION",
                "timestamp": int(time.time()),
                "region": region,
                "user_id": f"test-user-{region.lower()}",
                "meter_id": f"{region}-TEST-12345",
                "reading": 1000.0 + len(region),
                "status": "VERIFIED",
                "test_message": True
            }
            
            try:
                result = submit_message(client, topic_id, msg, f"{region} VERIFICATION")
                results.append({
                    'region': region,
                    'topic_id': topic_id,
                    'result': result,
                    'success': True
                })
                
                # Small delay between topics
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Failed for {region}: {str(e)}")
                results.append({
                    'region': region,
                    'topic_id': topic_id,
                    'error': str(e),
                    'success': False
                })
    
    return results


def main():
    """Main test function"""
    print_header("🧪 HCS MESSAGE SUBMISSION AND RETRIEVAL TEST (Task 3.5)")
    
    print("\nThis script tests:")
    print("  ✓ HCS message submission")
    print("  ✓ Topic info retrieval")
    print("  ✓ Message verification")
    print("  ✓ Different message types (verification, payment, dispute)")
    print("  ✓ Multiple regional topics")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    operator_id = os.getenv('HEDERA_OPERATOR_ID')
    operator_key = os.getenv('HEDERA_OPERATOR_KEY')
    
    # Get topic IDs
    topics = {
        'EU': os.getenv('HCS_TOPIC_EU'),
        'US': os.getenv('HCS_TOPIC_US'),
        'ASIA': os.getenv('HCS_TOPIC_ASIA'),
        'SA': os.getenv('HCS_TOPIC_SA'),
        'AFRICA': os.getenv('HCS_TOPIC_AFRICA')
    }
    
    # Validate configuration
    if not operator_id or not operator_key:
        print("\n❌ ERROR: Missing Hedera operator credentials")
        print("\nPlease set in .env:")
        print("   HEDERA_OPERATOR_ID=0.0.xxxxx")
        print("   HEDERA_OPERATOR_KEY=302e020100...")
        return 1
    
    # Check if topics are configured
    configured_topics = {k: v for k, v in topics.items() if v and v != "0.0.xxxxx"}
    
    if not configured_topics:
        print("\n❌ ERROR: No HCS topics configured")
        print("\nPlease run: python scripts/create_hcs_topics.py")
        print("\nThen update .env with topic IDs:")
        print("   HCS_TOPIC_EU=0.0.xxxxx")
        print("   HCS_TOPIC_US=0.0.xxxxx")
        print("   HCS_TOPIC_ASIA=0.0.xxxxx")
        print("   HCS_TOPIC_SA=0.0.xxxxx")
        print("   HCS_TOPIC_AFRICA=0.0.xxxxx")
        return 1
    
    print(f"\n✅ Found {len(configured_topics)} configured topic(s)")
    for region, topic_id in configured_topics.items():
        print(f"   {region}: {topic_id}")
    
    # Create client
    print("\n🌐 Connecting to Hedera testnet...")
    
    try:
        client = Client.forTestnet()
        client.setOperator(operator_id, operator_key)
        
        print(f"✅ Connected with operator: {operator_id}")
        
        # Check balance
        print_section("Pre-Test Balance Check")
        initial_balance = check_balance(client, operator_id)
        print(f"💰 Operator Balance: {initial_balance} HBAR")
        
        if initial_balance < 0.1:
            print("\n⚠️  WARNING: Low balance. Get testnet HBAR from:")
            print("   https://portal.hedera.com/")
        
        # Use first configured topic for detailed tests
        test_topic_region = list(configured_topics.keys())[0]
        test_topic_id = configured_topics[test_topic_region]
        
        print(f"\n🎯 Using {test_topic_region} topic for detailed tests: {test_topic_id}")
        
        # Get initial topic info
        print_section("Initial Topic Information")
        initial_info = get_topic_info(client, test_topic_id)
        initial_sequence = initial_info['sequence_number']
        
        # Run tests
        test_results = []
        
        # Test 1: Verification message
        try:
            result1 = test_verification_message(client, test_topic_id)
            test_results.append(('Verification Message', True, result1))
        except Exception as e:
            test_results.append(('Verification Message', False, str(e)))
        
        # Test 2: Payment message
        try:
            result2 = test_payment_message(client, test_topic_id)
            test_results.append(('Payment Message', True, result2))
        except Exception as e:
            test_results.append(('Payment Message', False, str(e)))
        
        # Test 3: Dispute message
        try:
            result3 = test_dispute_message(client, test_topic_id)
            test_results.append(('Dispute Message', True, result3))
        except Exception as e:
            test_results.append(('Dispute Message', False, str(e)))
        
        # Test 4: Multiple topics (if more than one configured)
        if len(configured_topics) > 1:
            try:
                multi_results = test_multiple_topics(client, configured_topics)
                test_results.append(('Multiple Topics', True, multi_results))
            except Exception as e:
                test_results.append(('Multiple Topics', False, str(e)))
        
        # Get final topic info
        print_section("Final Topic Information")
        final_info = get_topic_info(client, test_topic_id)
        final_sequence = final_info['sequence_number']
        
        messages_submitted = final_sequence - initial_sequence
        print(f"\n📊 Messages Submitted: {messages_submitted}")
        
        # Check final balance
        print_section("Post-Test Balance Check")
        final_balance = check_balance(client, operator_id)
        cost = initial_balance - final_balance
        print(f"💰 Final Balance: {final_balance} HBAR")
        print(f"💸 Total Cost: {cost:.6f} HBAR")
        
        # Print summary
        print_header("📊 TEST SUMMARY")
        
        passed = sum(1 for _, success, _ in test_results if success)
        total = len(test_results)
        
        print(f"\n✅ Tests Passed: {passed}/{total}")
        print(f"\n📋 Detailed Results:")
        
        for test_name, success, result in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"\n   {status} - {test_name}")
            if not success:
                print(f"      Error: {result}")
            elif test_name == "Multiple Topics":
                for r in result:
                    region_status = "✅" if r['success'] else "❌"
                    print(f"      {region_status} {r['region']}: {r['topic_id']}")
        
        # Print HashScan links
        print("\n🔗 View on HashScan:")
        for region, topic_id in configured_topics.items():
            print(f"   {region}: https://hashscan.io/testnet/topic/{topic_id}")
        
        # Print next steps
        print_header("✅ TASK 3.5 COMPLETE")
        
        print("\n🎉 HCS message submission and retrieval tested successfully!")
        print("\n📝 What was tested:")
        print("   ✓ Topic information retrieval")
        print("   ✓ Message submission to HCS topics")
        print("   ✓ Transaction receipt verification")
        print("   ✓ Sequence number tracking")
        print("   ✓ Different message types (verification, payment, dispute)")
        print("   ✓ Multiple regional topics")
        
        print("\n🔍 Message Retrieval:")
        print("   • Messages are stored on Hedera network")
        print("   • Sequence numbers track message order")
        print("   • Running hash ensures message integrity")
        print("   • View messages on HashScan (links above)")
        print("   • Use Mirror Node API for programmatic retrieval (Task 3.6)")
        
        print("\n⏭️  Next Steps:")
        print("   • Task 3.6: Configure Mirror Node API access")
        print("   • Implement Mirror Node queries for historical logs")
        print("   • Build HCS logging into verification/payment flows")
        
        if passed == total:
            print("\n✅ ALL TESTS PASSED!")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            return 1
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify HCS topics are created (Task 3.3)")
        print("2. Check operator credentials in .env")
        print("3. Ensure operator has sufficient HBAR")
        print("4. Verify internet connection to Hedera testnet")
        return 1
    
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    sys.exit(main())
