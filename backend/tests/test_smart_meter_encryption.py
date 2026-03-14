"""
Test Smart Meter Private Key Encryption (AES-256)

Tests the AES-256 encryption and decryption of ED25519 private keys
for smart meter signature functionality.

Requirements: FR-9.2, NFR-8.1, NFR-8.2, Task 2.2
Spec: prepaid-smart-meter-mvp
"""
import pytest
import os
import base64
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.smart_meter_service import SmartMeterService, SmartMeterError


@pytest.fixture
def smart_meter_service(db_session: Session):
    """Create smart meter service instance"""
    return SmartMeterService(db_session)


@pytest.fixture
def test_meter_id():
    """Generate test meter ID"""
    import uuid
    return str(uuid.uuid4())


class TestPrivateKeyEncryption:
    """Test AES-256 encryption for private keys"""
    
    def test_encryption_key_setup(self, smart_meter_service):
        """Test that encryption key is properly set up"""
        # Verify encryption key exists and is 32 bytes (256 bits)
        assert hasattr(smart_meter_service, 'encryption_key')
        assert len(smart_meter_service.encryption_key) == 32
        assert isinstance(smart_meter_service.encryption_key, bytes)
    
    def test_encrypt_decrypt_roundtrip(self, smart_meter_service):
        """Test that encryption and decryption work correctly"""
        # Create test data
        test_data = b"This is a test private key in PEM format"
        
        # Encrypt
        encrypted, iv = smart_meter_service._encrypt_private_key(test_data)
        
        # Verify encrypted data is different from original
        assert encrypted != base64.b64encode(test_data).decode()
        assert len(encrypted) > 0
        assert len(iv) > 0
        
        # Decrypt
        decrypted = smart_meter_service._decrypt_private_key(encrypted, iv)
        
        # Verify decrypted data matches original
        assert decrypted == test_data
    
    def test_encryption_produces_different_ciphertext(self, smart_meter_service):
        """Test that encrypting same data twice produces different ciphertext (due to random IV)"""
        test_data = b"Same private key data"
        
        # Encrypt twice
        encrypted1, iv1 = smart_meter_service._encrypt_private_key(test_data)
        encrypted2, iv2 = smart_meter_service._encrypt_private_key(test_data)
        
        # Verify different IVs and ciphertexts
        assert iv1 != iv2
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same plaintext
        decrypted1 = smart_meter_service._decrypt_private_key(encrypted1, iv1)
        decrypted2 = smart_meter_service._decrypt_private_key(encrypted2, iv2)
        assert decrypted1 == test_data
        assert decrypted2 == test_data
    
    def test_keypair_generation_encrypts_private_key(
        self, smart_meter_service, test_meter_id, db_session
    ):
        """Test that generate_keypair encrypts the private key"""
        # Generate keypair
        result = smart_meter_service.generate_keypair(test_meter_id)
        
        # Verify result contains public key but not private key
        assert 'public_key' in result
        assert 'private_key' not in result
        assert result['algorithm'] == 'ED25519'
        
        # Verify private key is encrypted in database
        query = text("""
            SELECT private_key_encrypted, encryption_iv, public_key
            FROM smart_meter_keys
            WHERE meter_id = :meter_id
        """)
        row = db_session.execute(query, {'meter_id': test_meter_id}).fetchone()
        
        assert row is not None
        encrypted_private = row[0]
        encryption_iv = row[1]
        public_key = row[2]
        
        # Verify encrypted data exists
        assert encrypted_private is not None
        assert encryption_iv is not None
        assert len(encrypted_private) > 0
        assert len(encryption_iv) > 0
        
        # Verify encrypted data is base64-encoded
        try:
            base64.b64decode(encrypted_private)
            base64.b64decode(encryption_iv)
        except Exception:
            pytest.fail("Encrypted data should be base64-encoded")
        
        # Verify public key is in plaintext PEM format
        assert public_key.startswith('-----BEGIN PUBLIC KEY-----')
        assert public_key.endswith('-----END PUBLIC KEY-----\n')
    
    def test_private_key_retrieval_and_decryption(
        self, smart_meter_service, test_meter_id
    ):
        """Test that private key can be retrieved and decrypted"""
        # Generate keypair
        smart_meter_service.generate_keypair(test_meter_id)
        
        # Retrieve private key (internal method)
        private_key = smart_meter_service._get_private_key(test_meter_id)
        
        # Verify it's a valid ED25519 private key
        from cryptography.hazmat.primitives.asymmetric import ed25519
        assert isinstance(private_key, ed25519.Ed25519PrivateKey)
        
        # Verify we can get the public key from it
        public_key = private_key.public_key()
        assert isinstance(public_key, ed25519.Ed25519PublicKey)
    
    def test_sign_consumption_uses_encrypted_key(
        self, smart_meter_service, test_meter_id
    ):
        """Test that signing consumption data uses the encrypted private key"""
        # Generate keypair
        smart_meter_service.generate_keypair(test_meter_id)
        
        # Sign consumption data
        result = smart_meter_service.sign_consumption(
            meter_id=test_meter_id,
            consumption_kwh=15.5,
            timestamp=1234567890
        )
        
        # Verify signature was created
        assert 'signature' in result
        assert len(result['signature']) > 0
        assert result['meter_id'] == test_meter_id
        
        # Verify signature is hex-encoded
        try:
            bytes.fromhex(result['signature'])
        except ValueError:
            pytest.fail("Signature should be hex-encoded")
    
    def test_invalid_decryption_fails_gracefully(self, smart_meter_service):
        """Test that decryption with wrong IV fails gracefully"""
        test_data = b"Test private key"
        
        # Encrypt with one IV
        encrypted, iv1 = smart_meter_service._encrypt_private_key(test_data)
        
        # Try to decrypt with different IV
        _, iv2 = smart_meter_service._encrypt_private_key(test_data)
        
        with pytest.raises(SmartMeterError):
            smart_meter_service._decrypt_private_key(encrypted, iv2)
    
    def test_private_key_never_exposed_via_api(
        self, smart_meter_service, test_meter_id
    ):
        """Test that private key is never exposed through public methods"""
        # Generate keypair
        result = smart_meter_service.generate_keypair(test_meter_id)
        
        # Verify private key not in result
        assert 'private_key' not in result
        assert 'private_key_encrypted' not in result
        assert 'encryption_iv' not in result
        
        # Verify only public key is returned
        assert 'public_key' in result
        
        # Get public key
        public_key = smart_meter_service.get_public_key(test_meter_id)
        assert public_key is not None
        assert '-----BEGIN PUBLIC KEY-----' in public_key
    
    def test_encryption_key_from_environment(self, db_session):
        """Test that encryption key can be loaded from environment"""
        # Set custom encryption key
        custom_key = base64.b64encode(os.urandom(32)).decode()
        os.environ['METER_KEY_ENCRYPTION_KEY'] = custom_key
        
        # Create service
        service = SmartMeterService(db_session)
        
        # Verify key was loaded
        expected_key = base64.b64decode(custom_key)
        assert service.encryption_key == expected_key
        
        # Clean up
        del os.environ['METER_KEY_ENCRYPTION_KEY']
    
    def test_encryption_uses_aes_256_cbc(self, smart_meter_service):
        """Test that encryption uses AES-256-CBC mode"""
        test_data = b"Test private key data for AES-256-CBC"
        
        # Encrypt
        encrypted, iv = smart_meter_service._encrypt_private_key(test_data)
        
        # Verify IV is 16 bytes (AES block size)
        iv_bytes = base64.b64decode(iv)
        assert len(iv_bytes) == 16
        
        # Verify encrypted data is padded to AES block size (16 bytes)
        encrypted_bytes = base64.b64decode(encrypted)
        assert len(encrypted_bytes) % 16 == 0
    
    def test_last_used_timestamp_updated_on_key_access(
        self, smart_meter_service, test_meter_id, db_session
    ):
        """Test that last_used_at is updated when private key is accessed"""
        # Generate keypair
        smart_meter_service.generate_keypair(test_meter_id)
        
        # Get initial last_used_at
        query = text("""
            SELECT last_used_at FROM smart_meter_keys
            WHERE meter_id = :meter_id
        """)
        result1 = db_session.execute(query, {'meter_id': test_meter_id}).fetchone()
        initial_last_used = result1[0]
        
        # Access private key (via signing)
        import time
        time.sleep(0.1)  # Small delay to ensure timestamp difference
        smart_meter_service.sign_consumption(
            meter_id=test_meter_id,
            consumption_kwh=10.0,
            timestamp=1234567890
        )
        
        # Get updated last_used_at
        result2 = db_session.execute(query, {'meter_id': test_meter_id}).fetchone()
        updated_last_used = result2[0]
        
        # Verify timestamp was updated
        if initial_last_used is not None:
            assert updated_last_used > initial_last_used
        else:
            assert updated_last_used is not None


class TestEncryptionSecurity:
    """Test security aspects of encryption"""
    
    def test_encryption_key_length_validation(self, db_session):
        """Test that invalid encryption key length is rejected"""
        # Set invalid key (wrong length)
        os.environ['METER_KEY_ENCRYPTION_KEY'] = base64.b64encode(b"short").decode()
        
        # Should raise error
        with pytest.raises(SmartMeterError):
            SmartMeterService(db_session)
        
        # Clean up
        del os.environ['METER_KEY_ENCRYPTION_KEY']
    
    def test_encrypted_data_is_not_plaintext(self, smart_meter_service, test_meter_id, db_session):
        """Test that encrypted private key in database is not plaintext"""
        # Generate keypair
        smart_meter_service.generate_keypair(test_meter_id)
        
        # Get encrypted private key from database
        query = text("""
            SELECT private_key_encrypted FROM smart_meter_keys
            WHERE meter_id = :meter_id
        """)
        result = db_session.execute(query, {'meter_id': test_meter_id}).fetchone()
        encrypted_private = result[0]
        
        # Verify it doesn't contain PEM markers (not plaintext)
        assert '-----BEGIN PRIVATE KEY-----' not in encrypted_private
        assert '-----END PRIVATE KEY-----' not in encrypted_private
        
        # Verify it's base64-encoded
        try:
            decoded = base64.b64decode(encrypted_private)
            # Verify decoded data doesn't contain PEM markers either
            assert b'-----BEGIN PRIVATE KEY-----' not in decoded
        except Exception:
            pytest.fail("Encrypted data should be base64-encoded")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
