#!/usr/bin/env python3
"""
Test CORS and server accessibility
"""
import requests
import sys

def test_server_accessibility():
    """Test if the backend server is running and accessible"""
    
    print("🧪 Testing Backend Server Accessibility")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    try:
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        response = requests.get(f"{base_url}/api/health", timeout=5)
        
        if response.status_code == 200:
            print(f"   ✅ Health check successful: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection failed - Backend server is not running")
        print(f"   💡 Start the backend server:")
        print(f"      cd backend && python -m uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    try:
        # Test CORS preflight request (OPTIONS)
        print(f"\n2. Testing CORS preflight request...")
        headers = {
            'Origin': 'http://localhost:8080',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'authorization,content-type'
        }
        
        response = requests.options(f"{base_url}/api/bills", headers=headers, timeout=5)
        
        print(f"   Status: {response.status_code}")
        print(f"   CORS Headers:")
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
        }
        
        for header, value in cors_headers.items():
            if value:
                print(f"      {header}: {value}")
            else:
                print(f"      {header}: ❌ Missing")
        
        if cors_headers['Access-Control-Allow-Origin'] in ['*', 'http://localhost:8080']:
            print(f"   ✅ CORS properly configured for localhost:8080")
        else:
            print(f"   ❌ CORS not configured for localhost:8080")
            
    except Exception as e:
        print(f"   ❌ CORS test failed: {e}")
        return False
    
    try:
        # Test actual API endpoint
        print(f"\n3. Testing API endpoint without auth...")
        response = requests.get(f"{base_url}/api/utility-providers", timeout=5)
        
        print(f"   Status: {response.status_code}")
        print(f"   Origin header: {response.headers.get('Access-Control-Allow-Origin', 'Missing')}")
        
        if response.status_code in [200, 401]:  # 401 is expected without auth
            print(f"   ✅ API endpoint accessible")
        else:
            print(f"   ❌ API endpoint issue: {response.text}")
            
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_server_accessibility()
    
    if success:
        print(f"\n🎉 Backend server is running and CORS is configured!")
        print(f"\n💡 If frontend still has CORS issues:")
        print(f"   1. Check browser console for specific error details")
        print(f"   2. Try hard refresh (Ctrl+F5)")
        print(f"   3. Clear browser cache")
        print(f"   4. Check if frontend is running on http://localhost:8080")
    else:
        print(f"\n❌ Backend server issues detected")
        print(f"\n🔧 Troubleshooting steps:")
        print(f"   1. Start backend: cd backend && python -m uvicorn main:app --reload")
        print(f"   2. Check backend logs for errors")
        print(f"   3. Verify port 8000 is not blocked by firewall")