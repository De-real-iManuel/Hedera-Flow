#!/usr/bin/env python3
"""
Test Hedera SDK Integration
Quick test to verify that the hiero-sdk-python is working properly
"""
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_hedera_import():
    """Test if we can import the Hedera SDK"""
    try:
        from hiero_sdk_python import (
            Client,
            Network,
            PrivateKey,
            AccountId,
            AccountBalanceQuery,
            Hbar
        )
        print("✅ Hedera SDK imports successful")
        return True
    except ImportError as e:
        print(f"❌ Failed to import Hedera SDK: {e}")
        return False

def test_hedera_service():
    """Test if we can create a Hedera service instance"""
    try:
        from app.services.hedera_service import HederaService
        
        # Create service instance
        service = HederaService()
        print("✅ Hedera service created successfully")
        
        # Test account balance query
        balance = service.get_account_balance("0.0.7942957")
        print(f"✅ Operator account balance: {balance} HBAR")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create Hedera service: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Hedera SDK Integration...")
    print("=" * 50)
    
    # Test 1: Import test
    print("\n1. Testing Hedera SDK imports...")
    import_success = test_hedera_import()
    
    if not import_success:
        print("❌ Cannot proceed with service tests - imports failed")
        return False
    
    # Test 2: Service test
    print("\n2. Testing Hedera service...")
    service_success = test_hedera_service()
    
    print("\n" + "=" * 50)
    if import_success and service_success:
        print("🎉 All tests passed! Hedera integration is working.")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)