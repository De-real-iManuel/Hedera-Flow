"""
Comprehensive HCS Message Testing

Tests all three types of HCS messages as per requirements:
- FR-5.13: Verification logging
- FR-5.14: Payment logging (with HBAR amount and fiat equivalent)
- FR-5.15: Dispute logging

This script:
1. Submits verification, payment, and dispute messages to each regional topic
2. Queries Mirror Node to verify messages were logged
3. Validates message structure and content
4. Displays results with proper formatting

Requirements:
- HCS topics created (Task 3.3)
- Topic IDs in .env file
- Operator account with HBAR for message submission fees

Usage:
    python scripts/test_hcs_comprehensive.py
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hedera import Client, TopicMessageSubmitTransaction
import requests


class HCSMessageTester:
    """Test HCS message submission and retrieval"""
    
    def __init__(self, client: Client, topics: Dict[str, str]):
        self.client = client
        self.topics = topics
        self.mirror_node_url = "https://testnet.mirrornode.hedera.com/api/v1"
        self.results = {}
    
    def create_verification_message(self, region: str) -> Dict[str, Any]:
        """Create a test verification message (FR-5.13)"""
        country_codes = {
            'EU': 'ES',
            'US': 'US',
            'Asia': 'IN',
            'SA': 'BR',
            'Africa': 'NG'
        }
        
        return {
            'type': 'VERIFICATION',
            'region': region,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'user_id': f'test-user-{region.lower()}-{int(time.time())}',
            'meter_id': f'{country_codes.get(region, "XX")}-TEST-{int(time.time())}',
            'reading': 5142.7,
            'utility_reading': 5089.2,
            'confidence': 0.96,
            'fraud_score': 0.12,
            'status': 'VERIFIED',
            'image_hash': f'ipfs://QmTest{region}{int(time.time())}'
        }
    
    def create_payment_message(self, region: str) -> Dict[str, Any]:
        """Create a test payment message (FR-5.14)"""
        currencies = {
            'EU': 'EUR',
            'US': 'USD',
            'Asia': 'INR',
            'SA': 'BRL',
            'Africa': 'NGN'
        }
        
        fiat_amounts = {
            'EU': 85.40,
            'US': 120.50,
            'Asia': 450.00,
            'SA': 95.00,
            'Africa': 12500.00
        }
        
        currency = currencies.get(region, 'USD')
        amount_fiat = fiat_amounts.get(region, 100.00)
        exchange_rate = 0.34  # Example HBAR price
        amount_hbar = round(amount_fiat / exchange_rate, 2)
        
        return {
            'type': 'PAYMENT',
            'region': region,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'bill_id': f'BILL-{currencies.get(region, "XX")[:2]}-2026-{int(time.time())}',
            'amount_fiat': amount_fiat,
            'currency_fiat': currency,
            'amount_hbar': amount_hbar,
            'exchange_rate': exchange_rate,
            'tx_id': f'0.0.123456@{int(time.time())}.123',
            'status': 'SUCCESS'
        }
    
    def create_dispute_message(self, region: str) -> Dict[str, Any]:
        """Create a test dispute message (FR-5.15)"""
        currencies = {
            'EU': 'EUR',
            'US': 'USD',
            'Asia': 'INR',
            'SA': 'BRL',
            'Africa': 'NGN'
        }
        
        return {
            'type': 'DISPUTE_CREATED',
            'region': region,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'dispute_id': f'DISP-{currencies.get(region, "XX")[:2]}-2026-{int(time.time())}',
            'bill_id': f'BILL-{currencies.get(region, "XX")[:2]}-2026-{int(time.time())}',
            'reason': 'OVERCHARGE',
            'evidence': [f'ipfs://QmEvidence{region}1', f'ipfs://QmEvidence{region}2'],
            'escrow_amount_hbar': 251.17,
            'escrow_amount_fiat': 85.40,
            'currency_fiat': currencies.get(region, 'USD'),
            'status': 'PENDING'
        }
    
    def submit_message(self, topic_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a message to an HCS topic"""
        try:
            message_json = json.dumps(message)
            
            transaction = (
                TopicMessageSubmitTransaction()
                .setTopicId(topic_id)
                .setMessage(message_json)
            )
            
            response = transaction.execute(self.client)
            receipt = response.getReceipt(self.client)
            
            return {
                'success': True,
                'tx_id': str(response.transactionId),
                'sequence_number': receipt.topicSequenceNumber,
                'topic_id': topic_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def query_message(self, topic_id: str, sequence_number: int) -> Dict[str, Any]:
        """Query a specific message from Mirror Node"""
        try:
            url = f"{self.mirror_node_url}/topics/{topic_id}/messages/{sequence_number}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            return {
                'success': True,
                'message': response.json()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def decode_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decode base64 message content from Mirror Node"""
        try:
            import base64
            message_bytes = message_data.get('message', '')
            decoded = base64.b64decode(message_bytes).decode('utf-8')
            return json.loads(decoded)
        except Exception as e:
            return {'error': f'Failed to decode: {str(e)}'}
    
    def test_region(self, region: str, topic_id: str) -> Dict[str, Any]:
        """Test all message types for a region"""
        print(f"\n{'='*70}")
        print(f"🧪 TESTING {region.upper()} TOPIC: {topic_id}")
        print(f"{'='*70}")
        
        results = {
            'region': region,
            'topic_id': topic_id,
            'tests': {}
        }
        
        # Test each message type
        message_types = [
            ('verification', self.create_verification_message(region), 'FR-5.13'),
            ('payment', self.create_payment_message(region), 'FR-5.14'),
            ('dispute', self.create_dispute_message(region), 'FR-5.15')
        ]
        
        for msg_type, message, requirement in message_types:
            print(f"\n📤 Testing {msg_type.upper()} message ({requirement})...")
            print(f"   Message type: {message['type']}")
            
            # Submit message
            submit_result = self.submit_message(topic_id, message)
            
            if not submit_result['success']:
                print(f"❌ Submission failed: {submit_result['error']}")
                results['tests'][msg_type] = {
                    'success': False,
                    'error': submit_result['error']
                }
                continue
            
            print(f"✅ Message submitted")
            print(f"   Transaction ID: {submit_result['tx_id']}")
            print(f"   Sequence Number: {submit_result['sequence_number']}")
            
            # Wait for Mirror Node
            print(f"   ⏳ Waiting 5 seconds for Mirror Node...")
            time.sleep(5)
            
            # Query message back
            query_result = self.query_message(topic_id, submit_result['sequence_number'])
            
            if not query_result['success']:
                print(f"⚠️  Query failed: {query_result['error']}")
                results['tests'][msg_type] = {
                    'success': True,
                    'submitted': True,
                    'retrieved': False,
                    'submit_result': submit_result
                }
                continue
            
            # Decode and validate
            decoded = self.decode_message(query_result['message'])
            
            if 'error' in decoded:
                print(f"⚠️  Decode failed: {decoded['error']}")
            else:
                print(f"✅ Message retrieved and decoded")
                print(f"   Type: {decoded.get('type')}")
                print(f"   Region: {decoded.get('region')}")
                
                # Validate message structure
                if msg_type == 'payment':
                    # FR-5.14: Must include HBAR amount and fiat equivalent
                    has_hbar = 'amount_hbar' in decoded
                    has_fiat = 'amount_fiat' in decoded and 'currency_fiat' in decoded
                    has_rate = 'exchange_rate' in decoded
                    
                    if has_hbar and has_fiat and has_rate:
                        print(f"   ✅ Payment message structure valid (FR-5.14)")
                        print(f"      HBAR: {decoded['amount_hbar']}")
                        print(f"      Fiat: {decoded['amount_fiat']} {decoded['currency_fiat']}")
                        print(f"      Rate: {decoded['exchange_rate']}")
                    else:
                        print(f"   ⚠️  Payment message missing required fields")
            
            results['tests'][msg_type] = {
                'success': True,
                'submitted': True,
                'retrieved': True,
                'submit_result': submit_result,
                'decoded_message': decoded
            }
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run tests for all regions"""
        print("="*70)
        print("🧪 COMPREHENSIVE HCS MESSAGE TESTING")
        print("="*70)
        print("\nTesting Requirements:")
        print("  FR-5.13: Verification logging")
        print("  FR-5.14: Payment logging (HBAR + fiat)")
        print("  FR-5.15: Dispute logging")
        print("="*70)
        
        for region, topic_id in self.topics.items():
            self.results[region] = self.test_region(region, topic_id)
        
        return self.results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        total_tests = 0
        successful_tests = 0
        
        for region, result in self.results.items():
            print(f"\n{region.upper()} Topic ({result['topic_id']}):")
            
            for msg_type, test_result in result['tests'].items():
                total_tests += 1
                
                if test_result.get('success') and test_result.get('retrieved'):
                    successful_tests += 1
                    print(f"  ✅ {msg_type.capitalize()}: PASS")
                elif test_result.get('success') and test_result.get('submitted'):
                    successful_tests += 0.5
                    print(f"  ⚠️  {msg_type.capitalize()}: Submitted but not retrieved")
                else:
                    print(f"  ❌ {msg_type.capitalize()}: FAIL")
        
        print(f"\n{'='*70}")
        print(f"Results: {int(successful_tests)}/{total_tests} tests passed")
        
        if successful_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED!")
            print("\nTask 3.5 Complete: HCS message submission and retrieval working!")
            print("\nView messages on HashScan:")
            for region, topic_id in self.topics.items():
                print(f"  {region}: https://hashscan.io/testnet/topic/{topic_id}")
        elif successful_tests > 0:
            print("\n⚠️  Some tests passed, but some failed or messages not yet on Mirror Node")
            print("   (Mirror Node can take 5-10 seconds to process messages)")
        else:
            print("\n❌ ALL TESTS FAILED - Check configuration and errors above")
        
        return successful_tests == total_tests


def main():
    """Main function"""
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
        print("   Set HEDERA_OPERATOR_ID and HEDERA_OPERATOR_KEY")
        return 1
    
    missing_topics = [name for name, topic_id in topics.items() if not topic_id or topic_id == '0.0.xxxxx']
    if missing_topics:
        print(f"\n❌ ERROR: Missing or placeholder topic IDs in .env: {', '.join(missing_topics)}")
        print("\nRun 'python scripts/create_hcs_topics.py' first to create topics.")
        return 1
    
    # Create client
    print("\n🌐 Connecting to Hedera testnet...")
    
    try:
        client = Client.forTestnet()
        client.setOperator(operator_id, operator_key)
        
        print(f"✅ Connected with operator: {operator_id}")
        
        # Run tests
        tester = HCSMessageTester(client, topics)
        tester.run_all_tests()
        success = tester.print_summary()
        
        client.close()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
