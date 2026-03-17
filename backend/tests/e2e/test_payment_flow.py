#!/usr/bin/env python3
"""
Test payment flow for verified meter readings
"""
import requests
import sys
import json
from datetime import datetime

# Import config first
sys.path.append('.')
from config import settings

def test_payment_flow():
    """Test the payment preparation and confirmation flow"""
    
    # Use the test user's auth token
    auth_token = "test_token_790b78b0-aca4-45a3-8b34-2d9261870c5a"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    base_url = "http://localhost:8000/api"
    
    print("Testing payment flow...")
    
    # Use the bill ID we just created
    bill_id = "32e7db43-4694-4a08-b2a9-c5cce32ffad1"
    
    try:
        # Test payment preparation
        print(f"\n1. Preparing payment for bill: {bill_id}")
        prep_response = requests.post(
            f"{base_url}/payments/prepare",
            headers=headers,
            json={"bill_id": bill_id}
        )
        
        if prep_response.status_code == 200:
            prep_data = prep_response.json()
            print(f"   ✅ Payment prepared successfully")
            print(f"   Amount: {prep_data['transaction']['amount_hbar']} HBAR")
            print(f"   Fiat: {prep_data['bill']['total_fiat']} {prep_data['bill']['currency']}")
            print(f"   From: {prep_data['transaction']['from']}")
            print(f"   To: {prep_data['transaction']['to']}")
            
            # Test payment confirmation with mock transaction ID
            print(f"\n2. Confirming payment...")
            mock_tx_id = f"0.0.{int(datetime.now().timestamp())}-test"
            
            confirm_response = requests.post(
                f"{base_url}/payments/confirm",
                headers=headers,
                json={
                    "bill_id": bill_id,
                    "hedera_tx_id": mock_tx_id
                }
            )
            
            if confirm_response.status_code == 200:
                confirm_data = confirm_response.json()
                print(f"   ✅ Payment confirmed successfully")
                print(f"   Payment ID: {confirm_data['payment']['id']}")
                print(f"   Transaction ID: {mock_tx_id}")
                return True
            else:
                print(f"   ❌ Payment confirmation failed: {confirm_response.status_code}")
                print(f"   Response: {confirm_response.text}")
        else:
            print(f"   ❌ Payment preparation failed: {prep_response.status_code}")
            print(f"   Response: {prep_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    success = test_payment_flow()
    if success:
        print("\n🎉 Payment flow is working correctly!")
    else:
        print("\n❌ Payment flow test failed")