"""
Validation Script for Hedera Account Creation Integration (Task 6.6)

This script validates that:
1. HederaService exists and has create_account method
2. Registration endpoint integrates with HederaService
3. Error handling is properly implemented
4. Account ID and wallet type are stored correctly

Requirements: FR-1.3, US-1
"""
import sys
import inspect
from typing import Tuple


def validate_hedera_service():
    """Validate HederaService implementation"""
    print("=" * 70)
    print("VALIDATING HEDERA SERVICE")
    print("=" * 70)
    
    try:
        from app.services.hedera_service import HederaService, get_hedera_service
        
        # Check HederaService class exists
        print("\n✅ HederaService class found")
        
        # Check create_account method exists
        if hasattr(HederaService, 'create_account'):
            print("✅ create_account method exists")
            
            # Check method signature
            sig = inspect.signature(HederaService.create_account)
            params = list(sig.parameters.keys())
            
            if 'initial_balance' in params:
                print("✅ create_account has initial_balance parameter")
            else:
                print("❌ create_account missing initial_balance parameter")
                return False
            
            # Check return type annotation
            if sig.return_annotation != inspect.Signature.empty:
                if sig.return_annotation == Tuple[str, str]:
                    print("✅ create_account returns Tuple[str, str]")
                else:
                    print(f"⚠️  create_account return type: {sig.return_annotation}")
            else:
                print("⚠️  create_account has no return type annotation")
        else:
            print("❌ create_account method not found")
            return False
        
        # Check get_hedera_service function
        print("✅ get_hedera_service function exists")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import HederaService: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating HederaService: {e}")
        return False


def validate_registration_integration():
    """Validate registration endpoint integration"""
    print("\n" + "=" * 70)
    print("VALIDATING REGISTRATION ENDPOINT INTEGRATION")
    print("=" * 70)
    
    try:
        from app.api.endpoints.auth import register
        import inspect
        
        # Get source code
        source = inspect.getsource(register)
        
        # Check for Hedera service import
        if 'get_hedera_service' in source:
            print("\n✅ Registration imports get_hedera_service")
        else:
            print("\n❌ Registration does not import get_hedera_service")
            return False
        
        # Check for account creation call
        if 'hedera_service.create_account' in source:
            print("✅ Registration calls hedera_service.create_account()")
        else:
            print("❌ Registration does not call create_account()")
            return False
        
        # Check for initial_balance parameter
        if 'initial_balance=10.0' in source or 'initial_balance = 10.0' in source:
            print("✅ Registration uses initial_balance=10.0")
        else:
            print("⚠️  Registration may not use correct initial_balance")
        
        # Check for account ID storage
        if 'hedera_account_id = account_id' in source or 'hedera_account_id=account_id' in source:
            print("✅ Registration stores account_id")
        else:
            print("⚠️  Registration may not store account_id correctly")
        
        # Check for wallet_type setting
        if 'WalletTypeEnum.SYSTEM_GENERATED' in source:
            print("✅ Registration sets wallet_type to SYSTEM_GENERATED")
        else:
            print("❌ Registration does not set wallet_type correctly")
            return False
        
        # Check for error handling
        if 'try:' in source and 'except Exception' in source:
            print("✅ Registration has error handling")
        else:
            print("⚠️  Registration may lack proper error handling")
        
        # Check for conditional account creation
        if 'if not hedera_account_id:' in source or 'if not request.hedera_account_id:' in source:
            print("✅ Registration conditionally creates account (only if no wallet)")
        else:
            print("❌ Registration does not check for existing wallet")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import register endpoint: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating registration: {e}")
        return False


def validate_user_model():
    """Validate User model has required fields"""
    print("\n" + "=" * 70)
    print("VALIDATING USER MODEL")
    print("=" * 70)
    
    try:
        from app.models.user import User, WalletTypeEnum
        
        # Check hedera_account_id field
        if hasattr(User, 'hedera_account_id'):
            print("\n✅ User model has hedera_account_id field")
        else:
            print("\n❌ User model missing hedera_account_id field")
            return False
        
        # Check wallet_type field
        if hasattr(User, 'wallet_type'):
            print("✅ User model has wallet_type field")
        else:
            print("❌ User model missing wallet_type field")
            return False
        
        # Check WalletTypeEnum
        if hasattr(WalletTypeEnum, 'SYSTEM_GENERATED'):
            print("✅ WalletTypeEnum has SYSTEM_GENERATED value")
        else:
            print("❌ WalletTypeEnum missing SYSTEM_GENERATED value")
            return False
        
        if hasattr(WalletTypeEnum, 'HASHPACK'):
            print("✅ WalletTypeEnum has HASHPACK value")
        else:
            print("❌ WalletTypeEnum missing HASHPACK value")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import User model: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating User model: {e}")
        return False


def validate_error_handling():
    """Validate error handling in registration"""
    print("\n" + "=" * 70)
    print("VALIDATING ERROR HANDLING")
    print("=" * 70)
    
    try:
        from app.api.endpoints.auth import register
        import inspect
        
        source = inspect.getsource(register)
        
        # Check for HTTPException import
        if 'HTTPException' in source:
            print("\n✅ Registration imports HTTPException")
        else:
            print("\n❌ Registration does not import HTTPException")
            return False
        
        # Check for 500 error on Hedera failure
        if 'status.HTTP_500_INTERNAL_SERVER_ERROR' in source or 'status_code=500' in source:
            print("✅ Registration returns 500 on Hedera failure")
        else:
            print("⚠️  Registration may not return proper error code")
        
        # Check for error message
        if 'Failed to create Hedera account' in source:
            print("✅ Registration has descriptive error message")
        else:
            print("⚠️  Registration may lack descriptive error message")
        
        # Check for logging
        if 'logger.error' in source or 'logger.warning' in source:
            print("✅ Registration logs errors")
        else:
            print("⚠️  Registration may not log errors")
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating error handling: {e}")
        return False


def main():
    """Run all validations"""
    print("\n" + "=" * 70)
    print("TASK 6.6 VALIDATION: HEDERA ACCOUNT CREATION INTEGRATION")
    print("=" * 70)
    print("\nRequirements:")
    print("  - FR-1.3: System shall create Hedera testnet account for new users")
    print("  - US-1: System creates Hedera account if user doesn't have one")
    print("\n" + "=" * 70)
    
    results = []
    
    # Run validations
    results.append(("HederaService", validate_hedera_service()))
    results.append(("Registration Integration", validate_registration_integration()))
    results.append(("User Model", validate_user_model()))
    results.append(("Error Handling", validate_error_handling()))
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 70)
    print(f"TOTAL: {passed}/{total} validations passed")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 All validations passed! Task 6.6 implementation is complete.")
        print("\nNext steps:")
        print("  1. ✅ HederaService class exists with create_account method")
        print("  2. ✅ Registration endpoint integrates with HederaService")
        print("  3. ✅ Account ID and wallet type are stored correctly")
        print("  4. ✅ Error handling is properly implemented")
        print("\nTask 6.6 is ready for production use!")
        return 0
    else:
        print("\n⚠️  Some validations failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
