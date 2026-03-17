"""
Test CORS preflight request
"""
import requests

# Test CORS preflight
print("Testing CORS preflight request...")

headers = {
    "Origin": "http://172.30.240.1:8080",
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type",
}

try:
    response = requests.options(
        "http://localhost:8000/api/auth/wallet-connect",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    print(f"\nResponse Body: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ CORS preflight successful!")
        if "Access-Control-Allow-Origin" in response.headers:
            print(f"   Allowed origin: {response.headers['Access-Control-Allow-Origin']}")
        else:
            print("   ⚠️ Warning: No Access-Control-Allow-Origin header")
    else:
        print(f"\n❌ CORS preflight failed with status {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")
