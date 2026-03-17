"""
Test script for Mirror Node client

Tests the Mirror Node API access functionality.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.mirror_node_client import MirrorNodeClient
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_mirror_node_client():
    """Test Mirror Node client functionality"""
    
    print("\n" + "="*60)
    print("HEDERA MIRROR NODE CLIENT TEST")
    print("="*60 + "\n")
    
    # Initialize client
    client = MirrorNodeClient()
    
    try:
        # Test 1: Get account info for operator account
        print("\n📋 Test 1: Get Account Info")
        print("-" * 60)
        
        operator_id = os.getenv("HEDERA_OPERATOR_ID", "0.0.7942971")
        print(f"Querying account: {operator_id}")
        
        try:
            account_info = await client.get_account_info(operator_id)
            print(f"✅ Account found!")
            print(f"   Account ID: {account_info.get('account')}")
            print(f"   Balance: {account_info.get('balance', {}).get('balance', 0) / 100000000} HBAR")
            print(f"   Created: {account_info.get('created_timestamp')}")
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
        
        # Test 2: Get recent transactions for operator account
        print("\n📋 Test 2: Get Account Transactions")
        print("-" * 60)
        
        try:
            transactions = await client.get_account_transactions(
                account_id=operator_id,
                limit=5,
                order="desc"
            )
            
            tx_list = transactions.get("transactions", [])
            print(f"✅ Found {len(tx_list)} recent transactions")
            
            for i, tx in enumerate(tx_list[:3], 1):
                print(f"\n   Transaction {i}:")
                print(f"   - ID: {tx.get('transaction_id')}")
                print(f"   - Type: {tx.get('name')}")
                print(f"   - Timestamp: {tx.get('consensus_timestamp')}")
                print(f"   - Result: {tx.get('result')}")
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
        
        # Test 3: Query HCS topic (if topic ID is set)
        print("\n📋 Test 3: Query HCS Topic Messages")
        print("-" * 60)
        
        # Try to get topic from environment
        topic_id = os.getenv("HCS_TOPIC_EU")
        
        if topic_id and topic_id != "0.0.xxxxx":
            print(f"Querying topic: {topic_id}")
            
            try:
                messages = await client.get_topic_messages(
                    topic_id=topic_id,
                    limit=5,
                    order="desc"
                )
                
                msg_list = messages.get("messages", [])
                print(f"✅ Found {len(msg_list)} messages")
                
                for i, msg in enumerate(msg_list[:3], 1):
                    print(f"\n   Message {i}:")
                    print(f"   - Sequence: {msg.get('sequence_number')}")
                    print(f"   - Timestamp: {msg.get('consensus_timestamp')}")
                    
                    decoded = msg.get("message_decoded")
                    if decoded:
                        print(f"   - Type: {decoded.get('type')}")
                        print(f"   - Data: {str(decoded)[:100]}...")
                    else:
                        print(f"   - Raw message: {msg.get('message')[:50]}...")
            except Exception as e:
                print(f"❌ Failed: {str(e)}")
        else:
            print("⚠️  No HCS topic configured (HCS_TOPIC_EU not set)")
            print("   Skipping topic message test")
        
        # Test 4: Test pagination
        print("\n📋 Test 4: Test Pagination")
        print("-" * 60)
        
        try:
            # Get first page
            page1 = await client.get_account_transactions(
                account_id=operator_id,
                limit=2,
                order="desc"
            )
            
            print(f"✅ First page: {len(page1.get('transactions', []))} transactions")
            
            # Check for next link
            next_link = page1.get("links", {}).get("next")
            if next_link:
                print(f"   Next page available: {next_link[:50]}...")
            else:
                print("   No more pages")
                
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
        
        # Test 5: Search functionality (mock test)
        print("\n📋 Test 5: Search Verification Logs")
        print("-" * 60)
        
        if topic_id and topic_id != "0.0.xxxxx":
            try:
                verifications = await client.search_verification_logs(
                    topic_id=topic_id,
                    status="VERIFIED",
                    limit=5
                )
                
                print(f"✅ Found {len(verifications)} verification logs")
                
                for i, log in enumerate(verifications[:2], 1):
                    print(f"\n   Log {i}:")
                    print(f"   - Sequence: {log.get('sequence_number')}")
                    data = log.get('data', {})
                    print(f"   - Status: {data.get('status')}")
                    print(f"   - Meter ID: {data.get('meterId')}")
                    print(f"   - Reading: {data.get('reading')}")
            except Exception as e:
                print(f"❌ Failed: {str(e)}")
        else:
            print("⚠️  No HCS topic configured")
            print("   Skipping verification search test")
        
        print("\n" + "="*60)
        print("✅ MIRROR NODE CLIENT TESTS COMPLETED")
        print("="*60 + "\n")
        
    finally:
        # Close client session
        await client.close()


async def test_specific_transaction():
    """Test querying a specific transaction"""
    
    print("\n📋 Bonus Test: Query Specific Transaction")
    print("-" * 60)
    
    client = MirrorNodeClient()
    
    try:
        # This is a sample transaction ID - replace with actual one
        # Format: accountId@timestamp
        tx_id = "0.0.7942971@1234567890.123456789"
        
        print(f"Note: Using sample transaction ID: {tx_id}")
        print("Replace with actual transaction ID to test")
        
        # Uncomment to test with real transaction ID
        # tx_data = await client.get_transaction(tx_id)
        # print(f"✅ Transaction found!")
        # print(f"   Type: {tx_data.get('name')}")
        # print(f"   Result: {tx_data.get('result')}")
        
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
    finally:
        await client.close()


if __name__ == "__main__":
    print("\n🚀 Starting Mirror Node Client Tests...\n")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run tests
    asyncio.run(test_mirror_node_client())
    
    print("\n✅ All tests completed!\n")
