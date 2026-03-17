#!/usr/bin/env python3
"""
Test authentication and bills endpoint
"""
import requests
import json

API_BASE = "http://localhost:8000/api"

def test_auth_and_bills():
    """Test login and bills endpoint"""
    
    print("🔐 Testing Authentication and Bills Access")
    print("=" * 50)
    
    # Test user credentials
    login_data = {
        "username": "nicxbrown35@gmail.com",  # The user from our tests
        "password": "Password123!"  # Strong password
    }
    
    try:
        print("\n1. Testing login...")
        response = requests.post(f"{API_BASE}/auth/login", data=login_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data.get("token")
            user = auth_data.get("user")
            
            print(f"   ✅ Login successful")
            print(f"   User: {user.get('email')} (ID: {user.get('id')})")
            print(f"   Token: {token[:20]}...{token[-10:] if token else 'None'}")
            
            # Test bills endpoint with valid token
            print(f"\n2. Testing bills endpoint...")
            headers = {"Authorization": f"Bearer {token}"}
            
            bills_response = requests.get(f"{API_BASE}/bills", headers=headers)
            print(f"   Status: {bills_response.status_code}")
            
            if bills_response.status_code == 200:
                bills = bills_response.json()
                print(f"   ✅ Bills retrieved successfully")
                print(f"   Found {len(bills)} bills")
                
                for i, bill in enumerate(bills[:3]):  # Show first 3 bills
                    print(f"   Bill {i+1}: {bill['id']} - {bill['amount_due']} {bill['currency']} ({bill['status']})")
                
                return token, bills
            else:
                print(f"   ❌ Bills request failed: {bills_response.text}")
        else:
            print(f"   ❌ Login failed: {response.text}")
            
            # Try to register the user if login fails
            print(f"\n   Trying to register user...")
            register_data = {
                "first_name": "Test",
                "last_name": "User", 
                "email": "nicxbrown35@gmail.com",
                "password": "Password123!",
                "country_code": "NG"
            }
            
            register_response = requests.post(f"{API_BASE}/auth/register", json=register_data)
            print(f"   Register Status: {register_response.status_code}")
            
            if register_response.status_code == 200:
                print(f"   ✅ User registered, try login again")
                return test_auth_and_bills()  # Retry login
            else:
                print(f"   ❌ Registration failed: {register_response.text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None, []

def test_payment_preparation(token, bills):
    """Test payment preparation with valid token"""
    if not token or not bills:
        print("\n⚠️  Skipping payment test - no valid token or bills")
        return
    
    print(f"\n3. Testing payment preparation...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Use the first pending bill
    pending_bills = [b for b in bills if b['status'] == 'pending']
    if not pending_bills:
        print(f"   ⚠️  No pending bills found")
        return
    
    bill = pending_bills[0]
    bill_id = bill['id']
    
    try:
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
        else:
            print(f"   ❌ Payment preparation failed: {prep_response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    token, bills = test_auth_and_bills()
    test_payment_preparation(token, bills)
    
    if token:
        print(f"\n🎉 Valid token for testing: {token}")
        print(f"\n💡 Use this token in your tests:")
        print(f'   headers = {{"Authorization": "Bearer {token}"}}')
    else:
        print(f"\n❌ Could not obtain valid token")
        print(f"\n💡 Make sure the backend server is running:")
        print(f"   cd backend && python -m uvicorn main:app --reload")