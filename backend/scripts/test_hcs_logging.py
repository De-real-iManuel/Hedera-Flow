#!/usr/bin/env python3
"""
Test HCS Logging

Quick test to verify HCS topics are working and can receive messages.
"""
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.hedera_client import hedera_client
from config import settings
import json
from datetime import datetime

async def test_hcs_logging():
    """Test HCS logging to all regional topics"""
    
    print("="*60)
    print("HCS LOGGING TEST")
    print("="*60)
    print()
    
    # Test topics
    topics = {
        'EU': settings.hcs_topic_eu,
        'US': settings.hcs_topic_us,
        'ASIA': settings.hcs_topic_asia,
        'SA': settings.hcs_topic_sa,
        'AFRICA': settings.hcs_topic_africa
    }
    
    print("Configured Topics:")
    for region, topic_id in topics.items():
        print(f"  {region}: {topic_id}")
    print()
    
    # Test message
    test_message = {
        'type': 'TEST',
        'timestamp': int(datetime.utcnow().timestamp()),
        'message': 'HCS logging test from Hedera Flow',
        'test_id': 'test-001'
    }
    
    results = {}
    
    for region, topic_id in topics.items():
        if topic_id and topic_id != "0.0.xxxxx":
            try:
                print(f"Testing {region} topic ({topic_id})...")
                
                result = await hedera_client.submit_hcs_message(
                    topic_id=topic_id,
                    message=test_message
                )
                
                print(f"✅ {region}: Success")
                print(f"   Sequence: {result['sequence_number']}")
                print(f"   TX ID: {result['tx_id']}")
                print(f"   View: https://hashscan.io/testnet/topic/{topic_id}")
                print()
                
                results[region] = {
                    'success': True,
                    'sequence': result['sequence_number'],
                    'tx_id': result['tx_id'],
                    'topic_id': topic_id
                }
                
            except Exception as e:
                print(f"❌ {region}: Failed - {e}")
                print()
                results[region] = {
                    'success': False,
                    'error': str(e)
                }
        else:
            print(f"⚠️  {region}: Not configured (topic_id: {topic_id})")
            print()
    
    # Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    successful = sum(1 for r in results.values() if r.get('success'))
    total = len(results)
    
    print(f"Successful: {successful}/{total}")
    print()
    
    if successful > 0:
        print("✅ HCS logging is working!")
        print()
        print("View your messages on HashScan:")
        for region, result in results.items():
            if result.get('success'):
                topic_id = result['topic_id']
                print(f"  {region}: https://hashscan.io/testnet/topic/{topic_id}")
    else:
        print("❌ HCS logging failed for all topics")
        print()
        print("Troubleshooting:")
        print("1. Check HBAR balance in operator account")
        print("2. Verify topic IDs are correct")
        print("3. Check network connectivity")
    
    print()

if __name__ == "__main__":
    asyncio.run(test_hcs_logging())
