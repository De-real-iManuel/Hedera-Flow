"""
Test authentication utilities without database connection
"""
import sys
sys.path.insert(0, 'backend')

from app.utils.auth import hash_password, verify_password, validate_password_strength, create_access_token

def test_password_hashing():
    """Test password hashing and verification"""
    print("Testing password hashing...")
    
    password = "TestPass123"
    hashed = hash_password(password)
    
    print(f"Original password: {password}")
    print(f"Hashed password: {hashed[:50]}...")
    print(f"Hash length: {len(hashed)}")
    
    # Verify correct password
    is_valid = verify_password(password, hashed)
    print(f"Verify correct password: {'✅ PASS' if is_valid else '❌ FAIL'}")
    
    # Verify incorrect password
    is_invalid = verify_password("WrongPass123", hashed)
    print(f"Verify incorrect password: {'✅ PASS' if not is_invalid else '❌ FAIL'}")
    print()


def test_password_validation():
    """Test password strength validation"""
    print("Testing password validation...")
    
    test_cases = [
        ("TestPass123", True, "Valid password"),
        ("short", False, "Too short"),
        ("nouppercase123", False, "No uppercase"),
        ("NoNumbers", False, "No numbers"),
        ("ValidPass1", True, "Valid password"),
    ]
    
    for password, expected_valid, description in test_cases:
        is_valid, error = validate_password_strength(password)
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"
        print(f"{status} - {description}: {password}")
        if error:
            print(f"  Error: {error}")
    print()


def test_jwt_token():
    """Test JWT token creation"""
    print("Testing JWT token creation...")
    
    token = create_access_token(
        user_id="123e4567-e89b-12d3-a456-426614174000",
        email="test@example.com",
        country_code="ES",
        hedera_account_id="0.0.123456"
    )
    
    print(f"Generated token: {token[:50]}...")
    print(f"Token length: {len(token)}")
    print("✅ Token created successfully")
    print()


if __name__ == "__main__":
    print("="*60)
    print("Authentication Utilities Test")
    print("="*60)
    print()
    
    test_password_hashing()
    test_password_validation()
    test_jwt_token()
    
    print("="*60)
    print("All tests completed!")
    print("="*60)
