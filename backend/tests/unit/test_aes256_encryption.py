"""
Test AES-256 encryption implementation for smart meter private keys.

This test verifies:
1. AES-256 key setup (32 bytes)
2. Private key encryption with AES-256-CBC
3. Private key decryption
4. Round-trip encryption/decryption
5. IV uniqueness
"""
import os
import sys
import base64

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from app.services.smart_meter_service import SmartMeterService
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def test_aes256_encryption():
    """Test AES-256 encryption for private keys"""
    
    print("=" * 70)
    print("TEST: AES-256 Encryption for Smart Meter Private Keys")
    print("=" * 70)
    
    # Setup database connection
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/hedera_flow')
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Generate a 32-byte (256-bit) encryption key
        encryption_key = base64.b64encode(os.urandom(32)).decode()
        os.environ['METER_KEY_ENCRYPTION_KEY'] = encryption_key
        
        print(f"\n1. Generated AES-256 encryption key (32 bytes)")
        print(f"   Key (base64): {encryption_key[:32]}...")
        
        # Initialize service
        service = SmartMeterService(db)
        
        # Verify key length
        assert len(service.encryption_key) == 32, f"Expected 32 bytes, got {len(service.encryption_key)}"
        print(f"   ✅ Encryption key is 32 bytes (AES-256)")
        
        # Generate a test ED25519 keypair
        print(f"\n2. Generating test ED25519 keypair...")
        private_key = ed25519.Ed25519PrivateKey.generate()
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        print(f"   ✅ Generated ED25519 private key ({len(private_pem)} bytes)")
        
        # Test encryption
        print(f"\n3. Testing AES-256-CBC encryption...")
        encrypted_data, iv = service._encrypt_private_key(private_pem)
        print(f"   ✅ Encrypted private key")
        print(f"   Encrypted data length: {len(encrypted_data)} chars (base64)")
        print(f"   IV length: {len(iv)} chars (base64)")
        print(f"   IV (base64): {iv}")
        
        # Verify IV is 16 bytes (128 bits) when decoded
        iv_bytes = base64.b64decode(iv)
        assert len(iv_bytes) == 16, f"Expected 16-byte IV, got {len(iv_bytes)}"
        print(f"   ✅ IV is 16 bytes (128 bits)")
        
        # Test decryption
        print(f"\n4. Testing AES-256-CBC decryption...")
        decrypted_pem = service._decrypt_private_key(encrypted_data, iv)
        print(f"   ✅ Decrypted private key ({len(decrypted_pem)} bytes)")
        
        # Verify round-trip
        print(f"\n5. Verifying round-trip encryption/decryption...")
        assert decrypted_pem == private_pem, "Decrypted key does not match original"
        print(f"   ✅ Round-trip successful: decrypted key matches original")
        
        # Test IV uniqueness
        print(f"\n6. Testing IV uniqueness...")
        encrypted_data2, iv2 = service._encrypt_private_key(private_pem)
        assert iv != iv2, "IVs should be unique for each encryption"
        print(f"   ✅ Each encryption generates unique IV")
        print(f"   IV 1: {iv}")
        print(f"   IV 2: {iv2}")
        
        # Test that different IVs produce different ciphertexts
        assert encrypted_data != encrypted_data2, "Different IVs should produce different ciphertexts"
        print(f"   ✅ Different IVs produce different ciphertexts")
        
        # Test decryption with wrong IV fails
        print(f"\n7. Testing decryption with wrong IV...")
        try:
            service._decrypt_private_key(encrypted_data, iv2)
            print(f"   ❌ ERROR: Decryption with wrong IV should fail")
            return False
        except Exception as e:
            print(f"   ✅ Decryption with wrong IV correctly fails")
            print(f"   Error: {str(e)[:50]}...")
        
        print(f"\n" + "=" * 70)
        print(f"✅ ALL TESTS PASSED - AES-256 Encryption Working Correctly")
        print(f"=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = test_aes256_encryption()
    sys.exit(0 if success else 1)
