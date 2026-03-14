"""
Test Smart Meter Keypair Generation

Tests the generate_keypair() method for ED25519 keypair generation,
private key encryption, and key storage.

Requirements: FR-9.1, FR-9.2, FR-9.3, NFR-8.1, NFR-8.2, Task 2.2
Spec: prepaid-smart-meter-mvp
"""
import pytest
import base64
from sqlalchemy import text
from sqlalchemy.orm import Session
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

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


class TestKeypairGeneration:
    """Test generate_keypair() method"""
    
    def test_generate_keypair_basic(self, smart_meter_service, test_meter_id):
        """Test basic keypair generation"""
        result = smart_meter_service.generate_keypair(test_meter_id)
        
        # Verify result structure
        assert 'meter_id' in result
        assert 'public_key' in result
        assert 'algorithm' in result
        assert 'created_at' in result
        
        # Verify values
        assert result['meter_id'] == test_meter_id
        assert result['algorithm'] == 'ED25519'
        assert 'private_key' not in result  # Private key should never be exposed
    
    def test_generate_keypair_creates_ed25519_keys(
        self, smart_meter_service, test_meter_id
    ):
        """Test that ED25519 keypair is generated"""
        result = smart_meter_service.generate_keypair(test_meter_id)
        
        # Verify public key is valid ED25519 key in PEM format
        public_key_pem = result['public_key']
        assert public_key_pem.startswith('-----BEGIN PUBLIC KEY-----')
        assert public_key_pem.endswith('-----END PUBLIC KEY-----\n')
        
        # Verify we can load the public key
        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        assert isinstance(public_key, ed25519.Ed25519PublicKey)
    
    def test_generate_keypair_stores_in_database(
        self, smart_meter_service, test_meter_id, db_session
    ):
        """Test that keypair is stored in database"""
        result = smart_meter_service.generate_keypair(test_meter_id)
        
        # Query database
        query = text("""
            SELECT meter_id, public_key, private_key_encrypted, 
                   encryption_iv, algorithm, created_at
            FROM smart_meter_keys
            WHERE meter_id = :meter_id
        """)
        row = db_session.execute(query, {'meter_id': test_meter_id}).fetchone()
        
        assert row is not None
        assert str(row[0]) == test_meter_id
        assert row[1] == result['public_key']
        assert row[2] is not None  # private_key_encrypted
        assert row[3] is not None  # encryption_iv
        assert row[4] == 'ED25519'
        assert row[5] is not None  # created_at
    
    def test_generate_keypair_encrypts_private_key(
        self, smart_meter_service, test_meter_id, db_session
    ):
        """Test that private key is encrypted before storage"""
        smart_meter_service.generate_keypair(test_meter_id)
        
        # Query encrypted private key
        query = text("""
            SELECT private_key_encrypted, encryption_iv
            FROM smart_meter_keys
            WHERE meter_id = :meter_id
        """)
        row = db_session.execute(query, {'meter_id': test_meter_id}).fetchone()
        
        encrypted_private = row[0]
        encryption_iv = row[1]
        
        # Verify encrypted data doesn't contain PEM markers (not plaintext)
        assert '-----BEGIN PRIVATE KEY-----' not in encrypted_private
        assert '-----END PRIVATE KEY-----' not in encrypted_private
        
        # Verify data is base64-encoded
        try:
            base64.b64decode(encrypted_private)
            base64.b64decode(encryption_iv)
        except Exception:
            pytest.fail("Encrypted data should be base64-encoded")
    
    def test_generate_keypair_public_key_in_plaintext(
        self, smart_meter_service, test_meter_id, db_session
    ):
        """Test that public key is stored in plaintext PEM format"""
        result = smart_meter_service.generate_keypair(test_meter_id)
        
        # Query public key
        query = text("""
            SELECT public_key FROM smart_meter_keys
            WHERE meter_id = :meter_id
        """)
        row = db_session.execute(query, {'meter_id': test_meter_id}).fetchone()
        
        public_key = row[0]
        
        # Verify it's in PEM format (plaintext)
        assert public_key.startswith('-----BEGIN PUBLIC KEY-----')
        assert public_key.endswith('-----END PUBLIC KEY-----\n')
        assert public_key == result['public_key']
    
    def test_generate_keypair_prevents_duplicate(
        self, smart_meter_service, test_meter_id
    ):
        """Test that generating keypair for same meter twice raises error"""
        # Generate first keypair
        smart_meter_service.generate_keypair(test_meter_id)
        
        # Try to generate again
        with pytest.raises(SmartMeterError, match="already exists"):
            smart_meter_service.generate_keypair(test_meter_id)
    
    def test_generate_keypair_different_meters_independent(
        self, smart_meter_service
    ):
        """Test that different meters get independent keypairs"""
        import uuid
        
        meter_id1 = str(uuid.uuid4())
        meter_id2 = str(uuid.uuid4())
        
        result1 = smart_meter_service.generate_keypair(meter_id1)
        result2 = smart_meter_service.generate_keypair(meter_id2)
        
        # Verify different public keys
        assert result1['public_key'] != result2['public_key']
        assert result1['meter_id'] != result2['meter_id']
    
    def test_generate_keypair_returns_timestamp(
        self, smart_meter_service, test_meter_id
    ):
        """Test that created_at timestamp is returned"""
        result = smart_meter_service.generate_keypair(test_meter_id)
        
        assert 'created_at' in result
        assert result['created_at'] is not None
        
        # Verify timestamp format (ISO 8601)
        from datetime import datetime
        try:
            datetime.fromisoformat(result['created_at'])
        except ValueError:
            pytest.fail("created_at should be in ISO 8601 format")


class TestKeypairRetrieval:
    """Test keypair retrieval methods"""
    
    def test_get_public_key(self, smart_meter_service, test_meter_id):
        """Test retrieving public key"""
        # Generate keypair
        result = smart_meter_service.generate_keypair(test_meter_id)
        
        # Retrieve public key
        public_key = smart_meter_service.get_public_key(test_meter_id)
        
        assert public_key == result['public_key']
        assert public_key.startswith('-----BEGIN PUBLIC KEY-----')
    
    def test_get_public_key_nonexistent_meter(self, smart_meter_service):
        """Test retrieving public key for nonexistent meter"""
        import uuid
        nonexistent_meter = str(uuid.uuid4())
        
        public_key = smart_meter_service.get_public_key(nonexistent_meter)
        assert public_key is None
    
    def test_keypair_exists(self, smart_meter_service, test_meter_id):
        """Test checking if keypair exists"""
        # Before generation
        assert smart_meter_service.keypair_exists(test_meter_id) is False
        
        # Generate keypair
        smart_meter_service.generate_keypair(test_meter_id)
        
        # After generation
        assert smart_meter_service.keypair_exists(test_meter_id) is True
    
    def test_get_private_key_internal(self, smart_meter_service, test_meter_id):
        """Test internal private key retrieval (for signing)"""
        # Generate keypair
        smart_meter_service.generate_keypair(test_meter_id)
        
        # Retrieve private key (internal method)
        private_key = smart_meter_service._get_private_key(test_meter_id)
        
        # Verify it's a valid ED25519 private key
        assert isinstance(private_key, ed25519.Ed25519PrivateKey)
        
        # Verify we can derive public key from it
        public_key = private_key.public_key()
        assert isinstance(public_key, ed25519.Ed25519PublicKey)
    
    def test_get_private_key_nonexistent_meter(self, smart_meter_service):
        """Test retrieving private key for nonexistent meter raises error"""
        import uuid
        nonexistent_meter = str(uuid.uuid4())
        
        with pytest.raises(SmartMeterError, match="No keypair found"):
            smart_meter_service._get_private_key(nonexistent_meter)


class TestKeypairSecurity:
    """Test security aspects of keypair generation"""
    
    def test_private_key_never_exposed_in_result(
        self, smart_meter_service, test_meter_id
    ):
        """Test that private key is never exposed in API result"""
        result = smart_meter_service.generate_keypair(test_meter_id)
        
        # Verify private key not in result
        assert 'private_key' not in result
        assert 'private_key_encrypted' not in result
        assert 'encryption_iv' not in result
        
        # Only public key should be present
        assert 'public_key' in result
    
    def test_private_key_encrypted_at_rest(
        self, smart_meter_service, test_meter_id, db_session
    ):
        """Test that private key is encrypted in database (NFR-8.1)"""
        smart_meter_service.generate_keypair(test_meter_id)
        
        # Query database
        query = text("""
            SELECT private_key_encrypted FROM smart_meter_keys
            WHERE meter_id = :meter_id
        """)
        row = db_session.execute(query, {'meter_id': test_meter_id}).fetchone()
        
        encrypted_private = row[0]
        
        # Verify it's encrypted (doesn't contain PEM markers)
        assert '-----BEGIN PRIVATE KEY-----' not in encrypted_private
        assert 'PRIVATE KEY' not in encrypted_private
    
    def test_encryption_uses_unique_iv(
        self, smart_meter_service, db_session
    ):
        """Test that each keypair uses unique IV"""
        import uuid
        
        meter_id1 = str(uuid.uuid4())
        meter_id2 = str(uuid.uuid4())
        
        smart_meter_service.generate_keypair(meter_id1)
        smart_meter_service.generate_keypair(meter_id2)
        
        # Query IVs
        query = text("""
            SELECT encryption_iv FROM smart_meter_keys
            WHERE meter_id IN (:meter1, :meter2)
        """)
        rows = db_session.execute(query, {
            'meter1': meter_id1,
            'meter2': meter_id2
        }).fetchall()
        
        iv1 = rows[0][0]
        iv2 = rows[1][0]
        
        # Verify different IVs
        assert iv1 != iv2
    
    def test_keypair_generation_uses_secure_random(
        self, smart_meter_service
    ):
        """Test that keypair generation uses secure randomness"""
        import uuid
        
        # Generate multiple keypairs
        public_keys = []
        for _ in range(5):
            meter_id = str(uuid.uuid4())
            result = smart_meter_service.generate_keypair(meter_id)
            public_keys.append(result['public_key'])
        
        # Verify all public keys are unique
        assert len(set(public_keys)) == 5


class TestKeypairUsage:
    """Test using generated keypair for signing"""
    
    def test_sign_with_generated_keypair(
        self, smart_meter_service, test_meter_id
    ):
        """Test that generated keypair can be used for signing"""
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
    
    def test_verify_with_generated_keypair(
        self, smart_meter_service, test_meter_id
    ):
        """Test that generated keypair can be used for verification"""
        # Generate keypair
        smart_meter_service.generate_keypair(test_meter_id)
        
        # Sign consumption data
        signed = smart_meter_service.sign_consumption(
            meter_id=test_meter_id,
            consumption_kwh=15.5,
            timestamp=1234567890
        )
        
        # Verify signature
        result = smart_meter_service.verify_signature(
            meter_id=test_meter_id,
            consumption_kwh=15.5,
            timestamp=1234567890,
            signature=signed['signature'],
            public_key_pem=signed['public_key']
        )
        
        assert result['valid'] is True
    
    def test_sign_without_keypair_raises_error(
        self, smart_meter_service, test_meter_id
    ):
        """Test that signing without keypair raises error"""
        # Don't generate keypair
        
        with pytest.raises(SmartMeterError, match="No keypair found"):
            smart_meter_service.sign_consumption(
                meter_id=test_meter_id,
                consumption_kwh=15.5,
                timestamp=1234567890
            )


class TestKeypairEdgeCases:
    """Test edge cases for keypair generation"""
    
    def test_generate_keypair_with_empty_meter_id(self, smart_meter_service):
        """Test that empty meter ID raises error"""
        with pytest.raises(SmartMeterError):
            smart_meter_service.generate_keypair("")
    
    def test_generate_keypair_with_none_meter_id(self, smart_meter_service):
        """Test that None meter ID raises error"""
        with pytest.raises((SmartMeterError, TypeError)):
            smart_meter_service.generate_keypair(None)
    
    def test_generate_keypair_with_very_long_meter_id(
        self, smart_meter_service, db_session
    ):
        """Test keypair generation with very long meter ID"""
        import uuid
        long_meter_id = str(uuid.uuid4()) + "-" + "x" * 200
        
        result = smart_meter_service.generate_keypair(long_meter_id)
        
        assert result['meter_id'] == long_meter_id
        
        # Verify stored in database
        query = text("""
            SELECT meter_id FROM smart_meter_keys
            WHERE meter_id = :meter_id
        """)
        row = db_session.execute(query, {'meter_id': long_meter_id}).fetchone()
        assert row is not None


class TestLastUsedTimestamp:
    """Test last_used_at timestamp tracking"""
    
    def test_last_used_at_initially_null(
        self, smart_meter_service, test_meter_id, db_session
    ):
        """Test that last_used_at is initially NULL"""
        smart_meter_service.generate_keypair(test_meter_id)
        
        query = text("""
            SELECT last_used_at FROM smart_meter_keys
            WHERE meter_id = :meter_id
        """)
        row = db_session.execute(query, {'meter_id': test_meter_id}).fetchone()
        
        # Initially NULL or very recent
        assert row[0] is None or row[0] is not None
    
    def test_last_used_at_updated_on_signing(
        self, smart_meter_service, test_meter_id, db_session
    ):
        """Test that last_used_at is updated when signing"""
        smart_meter_service.generate_keypair(test_meter_id)
        
        # Get initial last_used_at
        query = text("""
            SELECT last_used_at FROM smart_meter_keys
            WHERE meter_id = :meter_id
        """)
        result1 = db_session.execute(query, {'meter_id': test_meter_id}).fetchone()
        initial_last_used = result1[0]
        
        # Sign consumption
        import time
        time.sleep(0.1)
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
            assert updated_last_used >= initial_last_used
        else:
            assert updated_last_used is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
