"""
Test sign_consumption() method implementation

Tests the signature generation functionality for smart meter consumption data.

Requirements: FR-9.4, FR-9.5, Task 2.3
Spec: prepaid-smart-meter-mvp
"""
import pytest
from sqlalchemy.orm import Session

from app.services.smart_meter_service import SmartMeterService, SmartMeterError


@pytest.fixture
def smart_meter_service(db_session: Session):
    """Create smart meter service instance"""
    return SmartMeterService(db_session)


@pytest.fixture
def test_meter_id(smart_meter_service):
    """Generate test meter with keypair"""
    import uuid
    meter_id = str(uuid.uuid4())
    smart_meter_service.generate_keypair(meter_id)
    return meter_id


class TestSignConsumption:
    """Test sign_consumption() method"""
    
    def test_sign_consumption_basic(self, smart_meter_service, test_meter_id):
        """Test basic signature generation"""
        result = smart_meter_service.sign_consumption(
            meter_id=test_meter_id,
            consumption_kwh=15.5,
            timestamp=1234567890
        )
        
        # Verify all required fields present
        assert 'meter_id' in result
        assert 'consumption_kwh' in result
        assert 'timestamp' in result
        assert 'signature' in result
        assert 'public_key' in result
        assert 'message_hash' in result
        
        # Verify values
        assert result['meter_id'] == test_meter_id
        assert result['consumption_kwh'] == 15.5
        assert result['timestamp'] == 1234567890
        assert len(result['signature']) > 0
        assert len(result['message_hash']) > 0
    
    def test_message_format_consistent(self, smart_meter_service, test_meter_id):
        """Test that message format is meter_id + consumption + timestamp"""
        result = smart_meter_service.sign_consumption(
            meter_id=test_meter_id,
            consumption_kwh=10.0,
            timestamp=1000000000
        )
        
        # Message should be: meter_id + consumption + timestamp
        expected_message = f"{test_meter_id}10.01000000000"
        
        # Verify message hash is consistent
        import hashlib
        expected_hash = hashlib.sha256(expected_message.encode()).hexdigest()
        assert result['message_hash'] == expected_hash
    
    def test_signature_is_hex_encoded(self, smart_meter_service, test_meter_id):
        """Test that signature is hex-encoded"""
        result = smart_meter_service.sign_consumption(
            meter_id=test_meter_id,
            consumption_kwh=20.0,
            timestamp=1234567890
        )
        
        # Should be able to decode from hex
        try:
            signature_bytes = bytes.fromhex(result['signature'])
            assert len(signature_bytes) > 0
        except ValueError:
            pytest.fail("Signature should be hex-encoded")
    
    def test_signature_is_deterministic(self, smart_meter_service, test_meter_id):
        """Test that same input produces same signature"""
        # Sign same data twice
        result1 = smart_meter_service.sign_consumption(
            meter_id=test_meter_id,
            consumption_kwh=15.5,
            timestamp=1234567890
        )
        
        result2 = smart_meter_service.sign_consumption(
            meter_id=test_meter_id,
            consumption_kwh=15.5,
            timestamp=1234567890
        )
        
        # Signatures should be identical
        assert result1['signature'] == result2['signature']
        assert result1['message_hash'] == result2['message_hash']
    
    def test_different_input_produces_different_signature(
        self, smart_meter_service, test_meter_id
    ):
        """Test that different input produces different signature"""
        result1 = smart_meter_service.sign_consumption(
            meter_id=test_meter_id,
            consumption_kwh=15.5,
            timestamp=1234567890
        )
        
        result2 = smart_meter_service.sign_consumption(
            meter_id=test_meter_id,
            consumption_kwh=20.0,  # Different consumption
            timestamp=1234567890
        )
        
        # Signatures should be different
        assert result1['signature'] != result2['signature']
        assert result1['message_hash'] != result2['message_hash']
    
    def test_sign_with_optional_readings(self, smart_meter_service, test_meter_id):
        """Test signing with optional meter readings"""
        result = smart_meter_service.sign_consumption(
            meter_id=test_meter_id,
            consumption_kwh=15.5,
            timestamp=1234567890,
            reading_before=5000.0,
            reading_after=5015.5
        )
        
        # Verify optional fields included
        assert result['reading_before'] == 5000.0
        assert result['reading_after'] == 5015.5
        
        # Signature should still be generated
        assert len(result['signature']) > 0
    
    def test_sign_consumption_uses_sha256(self, smart_meter_service, test_meter_id):
        """Test that SHA-256 is used for hashing"""
        result = smart_meter_service.sign_consumption(
            meter_id=test_meter_id,
            consumption_kwh=15.5,
            timestamp=1234567890
        )
        
        # SHA-256 produces 64 hex characters (32 bytes)
        assert len(result['message_hash']) == 64
    
    def test_sign_consumption_without_keypair_fails(self, smart_meter_service):
        """Test that signing fails if no keypair exists"""
        import uuid
        non_existent_meter = str(uuid.uuid4())
        
        with pytest.raises(SmartMeterError):
            smart_meter_service.sign_consumption(
                meter_id=non_existent_meter,
                consumption_kwh=15.5,
                timestamp=1234567890
            )
    
    def test_public_key_included_in_result(self, smart_meter_service, test_meter_id):
        """Test that public key is included in signature result"""
        result = smart_meter_service.sign_consumption(
            meter_id=test_meter_id,
            consumption_kwh=15.5,
            timestamp=1234567890
        )
        
        # Verify public key is PEM format
        assert '-----BEGIN PUBLIC KEY-----' in result['public_key']
        assert '-----END PUBLIC KEY-----' in result['public_key']
    
    def test_signature_length_is_valid(self, smart_meter_service, test_meter_id):
        """Test that ED25519 signature has correct length"""
        result = smart_meter_service.sign_consumption(
            meter_id=test_meter_id,
            consumption_kwh=15.5,
            timestamp=1234567890
        )
        
        # ED25519 signatures are 64 bytes = 128 hex characters
        assert len(result['signature']) == 128


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
