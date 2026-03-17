#!/usr/bin/env python3
"""
Test IPFS access for uploaded verification images
"""
import requests
import sys

# Import config first
sys.path.append('.')
from config import settings

def test_ipfs_access():
    """Test accessing the uploaded verification image"""
    
    # IPFS hash from the successful verification
    ipfs_hash = "bafkreihhslilzlwxfrsn3wq6f22tszib6wwretf7frgdxzoplqsozskil4"
    
    print(f"Testing IPFS access for hash: {ipfs_hash}")
    
    # Test different IPFS gateways
    gateways = [
        f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}",
        f"https://ipfs.io/ipfs/{ipfs_hash}",
        f"https://cloudflare-ipfs.com/ipfs/{ipfs_hash}",
    ]
    
    for gateway_url in gateways:
        try:
            print(f"\nTesting gateway: {gateway_url}")
            response = requests.get(gateway_url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Success! Image accessible via {gateway_url}")
                print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                
                # Check if it's a valid image
                if response.headers.get('content-type', '').startswith('image/'):
                    print(f"   ✅ Valid image format")
                else:
                    print(f"   ⚠️  Unexpected content type")
                    
                return True
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    success = test_ipfs_access()
    if success:
        print("\n🎉 IPFS storage is working correctly!")
    else:
        print("\n❌ IPFS access failed - images may not be publicly accessible")