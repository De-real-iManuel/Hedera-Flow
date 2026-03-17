"""
Test password hashing implementation
Verifies bcrypt cost factor 12 requirement (Task 6.2)

Requirements:
    - FR-1.5: System shall enforce password requirements (min 8 chars, 1 uppercase, 1 number)
    - NFR-2.2: Passwords shall be hashed with bcrypt (cost factor 12)
"""
import sys
sys.path.insert(0, 'backend')

import bcrypt
from app.utils.auth import hash_password, verify_password


def test_bcrypt_cost_factor():
    """
    Test that password hashing uses bcrypt with cost factor 12
    
    Requirements:
        - NFR-2.2: Passwords shall be hashed with bcrypt (cost factor 12)
    """
    print("Testing bcrypt cost factor...")
    
    password = "TestPassword123"
    hashed = hash_password(password)
    
    # Bcrypt hash format: $2b$12$...
    # Where 12 is the cost factor
    parts = hashed.split('$')
    
    print(f"Password: {password}")
    print(f"Hashed: {hashed}")
    print(f"Hash parts: {parts}")
    
    # Verify hash format
    assert parts[0] == '', "Hash should start with $"
    assert parts[1] == '2b', "Should use bcrypt 2b version"
    assert parts[2] == '12', "Cost factor should be 12"
    
    print(f"✅ Bcrypt version: {parts[1]}")
    print(f"✅ Cost factor: {parts[2]}")
    print(f"✅ Salt: {parts[3][:22]}")
    print()


def test_password_verification():
    """Test that hashed passwords can be verified correctly"""
    print("Testing password verification...")
    
    password = "SecurePass123"
    hashed = hash_password(password)
    
    # Test correct password
    assert verify_password(password, hashed), "Should verify correct password"
    print("✅ Correct password verified")
    
    # Test incorrect password
    assert not verify_password("WrongPass123", hashed), "Should reject incorrect password"
    print("✅ Incorrect password rejected")
    print()


def test_unique_salts():
    """Test that each hash generates a unique salt"""
    print("Testing unique salts...")
    
    password = "SamePassword123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    
    assert hash1 != hash2, "Same password should generate different hashes (unique salts)"
    print("✅ Unique salts generated for same password")
    
    # Both should still verify
    assert verify_password(password, hash1), "Hash 1 should verify"
    assert verify_password(password, hash2), "Hash 2 should verify"
    print("✅ Both hashes verify correctly")
    print()


def test_hash_length():
    """Test that bcrypt hash has expected length"""
    print("Testing hash length...")
    
    password = "TestPass123"
    hashed = hash_password(password)
    
    # Bcrypt hashes are always 60 characters
    assert len(hashed) == 60, f"Bcrypt hash should be 60 characters, got {len(hashed)}"
    print(f"✅ Hash length: {len(hashed)} characters")
    print()


def test_cost_factor_performance():
    """
    Test that cost factor 12 provides adequate security
    
    Cost factor 12 means 2^12 = 4096 iterations
    This should take a noticeable amount of time (security vs usability)
    """
    print("Testing cost factor performance...")
    
    import time
    
    password = "PerformanceTest123"
    
    start = time.time()
    hashed = hash_password(password)
    end = time.time()
    
    duration = end - start
    
    print(f"Hashing time: {duration:.3f} seconds")
    
    # Cost factor 12 should take at least 0.05 seconds (50ms)
    # but less than 1 second on modern hardware
    assert 0.05 <= duration <= 1.0, f"Hashing should take 50ms-1s, took {duration:.3f}s"
    print(f"✅ Hashing time within acceptable range")
    print()


if __name__ == "__main__":
    print("="*70)
    print("Password Hashing Implementation Test (Task 6.2)")
    print("Requirements: FR-1.5, NFR-2.2")
    print("="*70)
    print()
    
    try:
        test_bcrypt_cost_factor()
        test_password_verification()
        test_unique_salts()
        test_hash_length()
        test_cost_factor_performance()
        
        print("="*70)
        print("✅ All tests passed!")
        print("="*70)
        print()
        print("Summary:")
        print("- Bcrypt version: 2b")
        print("- Cost factor: 12 (2^12 = 4096 iterations)")
        print("- Hash length: 60 characters")
        print("- Unique salts: Yes")
        print("- Password verification: Working")
        print()
        
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
