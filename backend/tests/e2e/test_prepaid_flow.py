"""
Test script to verify prepaid token purchase and confirmation flow with EVM transactions.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_prepaid_flow():
    """Test the complete prepaid token flow"""
    
    print("=" * 80)
    print("TESTING PREPAID TOKEN FLOW WITH EVM TRANSACTION")
    print("=" * 80)
    
    # Step 1: Check existing token
    token_id = "TOKEN-NG-2026-010"
    print(f"\n1. Checking existing token: {token_id}")
    print("-" * 80)
    
    # We'll simulate the flow by confirming with an EVM transaction
    # In real flow, frontend would:
    # 1. Call /api/prepaid/buy to create token (status='pending')
    # 2. User signs MetaMask transaction
    # 3. Call /api/prepaid/confirm-payment with EVM tx hash
    
    # Step 2: Test confirm endpoint with EVM transaction
    evm_tx_hash = "0xb86ff5eaef4812c6427ed5056b8f4f3c5f6c938e0917d0a04c782d11daa7d7d8"
    
    print(f"\n2. Testing confirm endpoint with EVM transaction")
    print(f"   Token ID: {token_id}")
    print(f"   EVM TX Hash: {evm_tx_hash}")
    print("-" * 80)
    
    # Prepare form data
    form_data = {
        'token_id': token_id,
        'hedera_tx_id': evm_tx_hash
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/prepaid/confirm-payment",
            data=form_data
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\n✅ SUCCESS! Token confirmed with EVM transaction")
        else:
            print(f"\n❌ FAILED with status {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_prepaid_flow()
