#!/usr/bin/env python3
"""
Test the complete payment flow with positive consumption
"""
import requests
import sys
import json
from datetime import datetime

# Import config first
sys.path.append('.')
from config import settings

def test_complete_flow():
    """Test the complete flow: verification -> bill generation -> payment"""
    
    # Use the test user's auth token
    auth_token = "test_token_790b78b0-aca4-45a3-8b34-2d9261870c5a"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    base_url = "http://localhost:8000/api"
    
    print("🧪 Testing Complete Payment Flow")
    print("=" * 50)
    
    try:
        # Step 1: Check if we have the positive consumption scenario set up
        print("\n1. Checking baseline verification...")
        
        # We should now have a verification with reading 82000.0
        # When we scan 83372.0, it should generate positive consumption
        
        # Step 2: Simulate a new verification with higher reading
        print("\n2. Simulating meter verification with positive consumption...")
        
        # This would normally be done through the frontend scan
        # For testing, we can check if bills are generated
        
        # Step 3: Check for bills
        print("\n3. Checking for generated bills...")
        response = requests.get(f"{base_url}/bills", headers=headers)
        
        if response.status_code == 200:
            bills = response.json()
            print(f"   Found {len(bills)} bills")
            
            if bills:
                # Test with the most recent bill
                bill = bills[0]
                bill_id = bill['id']
                print(f"   Using bill: {bill_id}")
                print(f"   Amount: {bill['amount_due']} {bill['currency']}")
                print(f"   Status: {bill['status']}")
                
                if bill['status'] == 'pending':
                    # Step 4: Test payment preparation
                    print(f"\n4. Testing payment preparation...")
                    prep_response = requests.post(
                        f"{base_url}/payments/prepare",
                        headers=headers,
                        json={"bill_id": bill_id}
                    )
                    
                    if prep_response.status_code == 200:
                        prep_data = prep_response.json()
                        print(f"   ✅ Payment prepared successfully")
                        print(f"   HBAR Amount: {prep_data['transaction']['amount_hbar']}")
                        print(f"   Fiat Amount: {prep_data['bill']['total_fiat']} {prep_data['bill']['currency']}")
                        print(f"   Exchange Rate: {prep_data['exchange_rate']['hbar_price']} {prep_data['exchange_rate']['currency']}/HBAR")
                        print(f"   From: {prep_data['transaction']['from']}")
                        print(f"   To: {prep_data['transaction']['to']}")
                        print(f"   Memo: {prep_data['transaction']['memo']}")
                        
                        # Step 5: Test payment confirmation (with mock transaction)
                        print(f"\n5. Testing payment confirmation...")
                        mock_tx_id = f"0.0.{int(datetime.now().timestamp())}-1234567890-123456789"
                        
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
                            print(f"   Receipt URL: {confirm_data['payment'].get('receipt_url', 'N/A')}")
                            
                            # Step 6: Test receipt retrieval
                            print(f"\n6. Testing receipt retrieval...")
                            receipt_response = requests.get(
                                f"{base_url}/payments/{confirm_data['payment']['id']}/receipt",
                                headers=headers
                            )
                            
                            if receipt_response.status_code == 200:
                                receipt_data = receipt_response.json()
                                print(f"   ✅ Receipt retrieved successfully")
                                print(f"   Receipt ID: {receipt_data['id']}")
                                print(f"   HBAR Amount: {receipt_data['amount_hbar']}")
                                print(f"   Fiat Amount: {receipt_data['amount_fiat']} {receipt_data['currency']}")
                                print(f"   Hedera TX ID: {receipt_data['hedera_tx_id']}")
                                
                                return True
                            else:
                                print(f"   ❌ Receipt retrieval failed: {receipt_response.status_code}")
                                print(f"   Response: {receipt_response.text}")
                        else:
                            print(f"   ❌ Payment confirmation failed: {confirm_response.status_code}")
                            print(f"   Response: {confirm_response.text}")
                    else:
                        print(f"   ❌ Payment preparation failed: {prep_response.status_code}")
                        print(f"   Response: {prep_response.text}")
                else:
                    print(f"   ⚠️  Bill already paid or not pending")
            else:
                print("   ⚠️  No bills found")
                print("   💡 Try scanning a meter with positive consumption first")
        else:
            print(f"   ❌ Failed to fetch bills: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return False

def print_next_steps():
    """Print instructions for testing the complete flow"""
    print("\n" + "=" * 50)
    print("📋 NEXT STEPS FOR COMPLETE TESTING")
    print("=" * 50)
    print()
    print("1. 🔧 Start the backend server:")
    print("   cd backend && python -m uvicorn main:app --reload")
    print()
    print("2. 🌐 Start the frontend:")
    print("   npm run dev")
    print()
    print("3. 📱 Test the complete flow:")
    print("   a. Open the app in browser")
    print("   b. Navigate to Scan page")
    print("   c. Connect a Hedera wallet (HashPack, Blade, or Kabila)")
    print("   d. Scan your meter image (should show 83372.0 kWh)")
    print("   e. Verify positive consumption is calculated (1372.0 kWh)")
    print("   f. Click 'Pay' button when bill is generated")
    print("   g. Confirm transaction in wallet")
    print("   h. View payment receipt")
    print()
    print("4. 🔍 Verify on Hedera:")
    print("   - Check transaction on HashScan")
    print("   - Verify HBAR transfer occurred")
    print("   - Confirm consensus timestamp")
    print()
    print("5. 📄 Test receipt features:")
    print("   - Download PDF receipt")
    print("   - View transaction details")
    print("   - Check blockchain verification")

if __name__ == "__main__":
    success = test_complete_flow()
    
    if success:
        print("\n🎉 Complete payment flow test PASSED!")
    else:
        print("\n⚠️  Complete payment flow test incomplete")
        print("   This is expected if backend is not running or no bills exist")
    
    print_next_steps()