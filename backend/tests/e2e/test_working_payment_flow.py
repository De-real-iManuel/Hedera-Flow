#!/usr/bin/env python3
"""
Test payment flow with current database schema
"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api"

def test_working_payment_flow():
    """Test payment flow with existing bill"""
    
    print("🧪 Testing Working Payment Flow")
    print("=" * 50)
    
    # Login to get token
    login_data = {
        "username": "nicxbrown35@gmail.com",
        "password": "Password123!"
    }
    
    try:
        print("\n1. Logging in...")
        response = requests.post(f"{API_BASE}/auth/login", data=login_data)
        
        if response.status_code != 200:
            print(f"   ❌ Login failed: {response.text}")
            return False
        
        auth_data = response.json()
        token = auth_data.get("token")
        print(f"   ✅ Login successful")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test payment preparation directly with known bill ID
        print(f"\n2. Testing payment preparation...")
        bill_id = "32e7db43-4694-4a08-b2a9-c5cce32ffad1"  # From our test bill
        
        prep_response = requests.post(
            f"{API_BASE}/payments/prepare",
            headers=headers,
            json={"bill_id": bill_id}
        )
        
        print(f"   Status: {prep_response.status_code}")
        
        if prep_response.status_code == 200:
            prep_data = prep_response.json()
            print(f"   ✅ Payment preparation successful")
            print(f"   HBAR Amount: {prep_data['transaction']['amount_hbar']}")
            print(f"   Fiat Amount: {prep_data['bill']['total_fiat']} {prep_data['bill']['currency']}")
            print(f"   From: {prep_data['transaction']['from']}")
            print(f"   To: {prep_data['transaction']['to']}")
            print(f"   Memo: {prep_data['transaction']['memo']}")
            
            # Test payment confirmation
            print(f"\n3. Testing payment confirmation...")
            mock_tx_id = f"0.0.{int(datetime.now().timestamp())}@{datetime.now().timestamp():.9f}"
            
            confirm_response = requests.post(
                f"{API_BASE}/payments/confirm",
                headers=headers,
                json={
                    "bill_id": bill_id,
                    "hedera_tx_id": mock_tx_id
                }
            )
            
            print(f"   Status: {confirm_response.status_code}")
            
            if confirm_response.status_code == 200:
                confirm_data = confirm_response.json()
                print(f"   ✅ Payment confirmation successful")
                print(f"   Payment ID: {confirm_data['payment']['id']}")
                print(f"   Message: {confirm_data['message']}")
                
                # Test receipt retrieval
                print(f"\n4. Testing receipt retrieval...")
                receipt_response = requests.get(
                    f"{API_BASE}/payments/{confirm_data['payment']['id']}/receipt",
                    headers=headers
                )
                
                print(f"   Status: {receipt_response.status_code}")
                
                if receipt_response.status_code == 200:
                    receipt_data = receipt_response.json()
                    print(f"   ✅ Receipt retrieved successfully")
                    print(f"   Receipt ID: {receipt_data['id']}")
                    print(f"   HBAR Amount: {receipt_data['amount_hbar']}")
                    print(f"   Fiat Amount: {receipt_data['amount_fiat']} {receipt_data['currency']}")
                    print(f"   Hedera TX ID: {receipt_data['hedera_tx_id']}")
                    print(f"   Consensus Timestamp: {receipt_data['consensus_timestamp']}")
                    
                    return True
                else:
                    print(f"   ❌ Receipt retrieval failed: {receipt_response.text}")
            else:
                print(f"   ❌ Payment confirmation failed: {confirm_response.text}")
        else:
            print(f"   ❌ Payment preparation failed: {prep_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    success = test_working_payment_flow()
    
    if success:
        print(f"\n🎉 Complete payment flow test PASSED!")
        print(f"\n✅ All systems working:")
        print(f"   - Authentication ✅")
        print(f"   - Payment preparation ✅") 
        print(f"   - Payment confirmation ✅")
        print(f"   - Receipt generation ✅")
        print(f"\n🚀 Ready for frontend testing!")
    else:
        print(f"\n❌ Payment flow test failed")
        print(f"\n💡 Check if backend server is running:")
        print(f"   cd backend && python -m uvicorn main:app --reload")