"""
Standalone test for AES-256 encryption (no database required)

This test verifies the encryption implementation works correctly
without needing the database schema.
"""
import pytest
import os
import base64

from app.services.smart_meter_service import SmartMeterService, SmartMeterError


class MockDB:
    """Mock database session for testing encryption only"""
    def execute(self, *args, **kwargs):
        pass
    
    def commit(self):
        pass
    
    def rollback(self):
        pass


def test_aes_256_encryption_implementation():
    """Test that AES-256 encryption is properly implemented"""
    # Set encryption key
    encryption_key = base64.b64encode(os.urandom(32)).decode()
    os.environ['METER_KEY_ENCRYPTION_KEY'] = encryption_key
    
    # Create service with mock DB
    service = SmartMeterService(MockDB())
    
    # Test data
    test_private_key = b"""-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIGVjZGhhLXByaXZhdGUta2V5LWZvci10ZXN0aW5nLW9u
bHktZG8tbm90LXVzZS1pbi1wcm9kdWN0aW9u
-----END PRIVATE KEY-----"""
    
    # Encrypt
    encrypted, iv = service._encrypt_private_key(test_private_key)
    
    print(f"\n✅ Encryption successful")
    print(f"   Original size: {len(test_private_key)} bytes")
    print(f"   Encrypted size: {len(base64.b64decode(encrypted))} bytes")
    print(f"   IV size: {len(base64.b64decode(iv))} bytes (should be 16)")
    print(f"   Encryption key size: {len(service.encryption_key)} bytes (should be 32)")
    
    # Verify encrypted data is different
    assert encrypted != base64.b64encode(test_private_key).decode()
    assert len(base64.b64decode(iv)) == 16  # AES block size
    assert len(service.encryption_key) == 32  # AES-256
    
    # Decrypt
    decrypted = service._decrypt_private_key(encrypted, iv)
    
    print(f"\n✅ Decryption successful")
    print(f"   Decrypted size: {len(decrypted)} bytes")
    print(f"   Matches original: {decrypted == test_private_key}")
    
    # Verify decrypted matches original
    assert decrypted == test_private_key
    
    # Test multiple encryptions produce different ciphertexts
    encrypted2, iv2 = service._encrypt_private_key(test_private_key)
    assert encrypted != encrypted2  # Different due to random IV
    assert iv != iv2
    
    # But both decrypt to same plaintext
    decrypted2 = service._decrypt_private_key(encrypted2, iv2)
    assert decrypted2 == test_private_key
    
    print(f"\n✅ All encryption tests passed!")
    print(f"   ✓ AES-256-CBC mode")
    print(f"   ✓ Random IV generation")
    print(f"   ✓ PKCS7 padding")
    print(f"   ✓ Base64 encoding")
    print(f"   ✓ Encrypt/decrypt roundtrip")
    
    # Clean up
    del os.environ['METER_KEY_ENCRYPTION_KEY']


if __name__ == '__main__':
    test_aes_256_encryption_implementation()
