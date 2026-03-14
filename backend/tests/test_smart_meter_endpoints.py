"""
Integration tests for Smart Meter API endpoints
Tests all endpoints: generate-keypair, consume, verify-signature, get-public-key

Requirements: Task 2.6 - API Endpoints - Smart Meter
Spec: prepaid-smart-meter-mvp
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4
import time

from app.core.app import app
from app.models.user import User
from app.models.meter import Meter
from app.models.smart_meter_key import SmartMeterKey
from app.services.smart_meter_service import SmartMeterService


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user"""
    user = User(
        id=uuid4(),
        email="smartmeter@test.com",
        hashed_password="hashed_password",
        full_name="Smart Meter Test User",
        hedera_account_id="0.0.TEST123",
        country_code="ES"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_meter(db_session: Session, test_user: User):
    """Create a test meter"""
    meter = Meter(
        id=uuid4(),
        user_id=test_user.id,
        meter_number="SMART-TEST-001",
        utility_provider_id=uuid4(),
        country_code="ES",
        is_active=True
    )
    db_session.add(meter)
    db_session.commit()
    db_session.refresh(meter)
    return meter


@pytest.fixture
def smart_meter_service(db_session: Session):
    """Create smart meter service instance"""
    return SmartMeterService(db_session)


class TestGenerateKeypairEndpoint:
    """Tests for POST /api/smart-meter/generate-keypair"""
    
    def test_generate_keypair_success(
        self,
        client: TestClient,
        db_session: Session,
        test_meter: Meter,
        test_user: User
    ):
        """Test successful keypair generation"""
        # Mock authentication
        from app.core.dependencies import get_current_user
        
        async def mock_get_current_user():
            return test_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            response = client.post(
                "/api/smart-meter/generate-keypair",
                json={"meter_id": str(test_meter.id)}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["meter_id"] == str(test_meter.id)
            assert "public_key" in data
            assert data["algorithm"] == "ED25519"
            assert "created_at" in data
            assert "private_key" not in data  # Private key should never be exposed
            
            # Verify keypair was stored in database
            keypair = db_session.query(SmartMeterKey).filter_by(
                meter_id=test_meter.id
            ).first()
            assert keypair is not None
            assert keypair.public_key == data["public_key"]
            
        finally:
            app.dependency_overrides.clear()
    
    def test_generate_keypair_already_exists(
        self,
        client: TestClient,
        db_session: Session,
        test_meter: Meter,
        test_user: User,
        smart_meter_service: SmartMeterService
    ):
        """Test error when keypair already exists"""
        from app.core.dependencies import get_current_user
        
        async def mock_get_current_user():
            return test_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            # Generate first keypair
            smart_meter_service.generate_keypair(str(test_meter.id))
            
            # Try to generate again
            response = client.post(
                "/api/smart-meter/generate-keypair",
                json={"meter_id": str(test_meter.id)}
            )
            
            assert response.status_code == 400
            assert "already exists" in response.json()["detail"].lower()
            
        finally:
            app.dependency_overrides.clear()
    
    def test_generate_keypair_invalid_meter_id(
        self,
        client: TestClient,
        test_user: User
    ):
        """Test error with invalid meter ID format"""
        from app.core.dependencies import get_current_user
        
        async def mock_get_current_user():
            return test_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            response = client.post(
                "/api/smart-meter/generate-keypair",
                json={"meter_id": "invalid-uuid"}
            )
            
            assert response.status_code == 400
            assert "invalid" in response.json()["detail"].lower()
            
        finally:
            app.dependency_overrides.clear()
    
    def test_generate_keypair_meter_not_found(
        self,
        client: TestClient,
        test_user: User
    ):
        """Test error when meter doesn't exist"""
        from app.core.dependencies import get_current_user
        
        async def mock_get_current_user():
            return test_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            non_existent_meter_id = str(uuid4())
            response = client.post(
                "/api/smart-meter/generate-keypair",
                json={"meter_id": non_existent_meter_id}
            )
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
            
        finally:
            app.dependency_overrides.clear()


class TestVerifySignatureEndpoint:
    """Tests for POST /api/smart-meter/verify-signature"""
    
    def test_verify_signature_valid(
        self,
        client: TestClient,
        db_session: Session,
        test_meter: Meter,
        test_user: User,
        smart_meter_service: SmartMeterService
    ):
        """Test verification of valid signature"""
        from app.core.dependencies import get_current_user
        
        async def mock_get_current_user():
            return test_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            # Generate keypair and sign data
            keypair = smart_meter_service.generate_keypair(str(test_meter.id))
            
            consumption_kwh = 15.5
            timestamp = int(time.time())
            
            signature = smart_meter_service.sign_consumption(
                meter_id=str(test_meter.id),
                consumption_data={
                    "meter_id": str(test_meter.id),
                    "consumption_kwh": consumption_kwh,
                    "timestamp": timestamp
                }
            )
            
            # Verify signature
            response = client.post(
                "/api/smart-meter/verify-signature",
                json={
                    "meter_id": str(test_meter.id),
                    "consumption_kwh": consumption_kwh,
                    "timestamp": timestamp,
                    "signature": signature,
                    "public_key": keypair["public_key"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["valid"] is True
            assert data["meter_id"] == str(test_meter.id)
            assert data["consumption_kwh"] == consumption_kwh
            assert data["timestamp"] == timestamp
            assert "message_hash" in data
            assert data["algorithm"] == "ED25519"
            assert data["error"] is None
            
        finally:
            app.dependency_overrides.clear()
    
    def test_verify_signature_invalid(
        self,
        client: TestClient,
        db_session: Session,
        test_meter: Meter,
        test_user: User,
        smart_meter_service: SmartMeterService
    ):
        """Test verification of invalid signature"""
        from app.core.dependencies import get_current_user
        
        async def mock_get_current_user():
            return test_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            # Generate keypair
            keypair = smart_meter_service.generate_keypair(str(test_meter.id))
            
            # Verify invalid signature
            response = client.post(
                "/api/smart-meter/verify-signature",
                json={
                    "meter_id": str(test_meter.id),
                    "consumption_kwh": 15.5,
                    "timestamp": int(time.time()),
                    "signature": "0" * 128,  # Invalid signature
                    "public_key": keypair["public_key"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["valid"] is False
            assert "error" in data
            assert data["error"] is not None
            
        finally:
            app.dependency_overrides.clear()
    
    def test_verify_signature_tampered_data(
        self,
        client: TestClient,
        db_session: Session,
        test_meter: Meter,
        test_user: User,
        smart_meter_service: SmartMeterService
    ):
        """Test that tampered data is detected"""
        from app.core.dependencies import get_current_user
        
        async def mock_get_current_user():
            return test_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            # Generate keypair and sign data
            keypair = smart_meter_service.generate_keypair(str(test_meter.id))
            
            consumption_kwh = 15.5
            timestamp = int(time.time())
            
            signature = smart_meter_service.sign_consumption(
                meter_id=str(test_meter.id),
                consumption_data={
                    "meter_id": str(test_meter.id),
                    "consumption_kwh": consumption_kwh,
                    "timestamp": timestamp
                }
            )
            
            # Verify with tampered consumption value
            response = client.post(
                "/api/smart-meter/verify-signature",
                json={
                    "meter_id": str(test_meter.id),
                    "consumption_kwh": 99.9,  # Tampered value
                    "timestamp": timestamp,
                    "signature": signature,
                    "public_key": keypair["public_key"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Signature should be invalid because data was tampered
            assert data["valid"] is False
            
        finally:
            app.dependency_overrides.clear()


class TestGetPublicKeyEndpoint:
    """Tests for GET /api/smart-meter/public-key/{meter_id}"""
    
    def test_get_public_key_success(
        self,
        client: TestClient,
        db_session: Session,
        test_meter: Meter,
        test_user: User,
        smart_meter_service: SmartMeterService
    ):
        """Test successful public key retrieval"""
        from app.core.dependencies import get_current_user
        
        async def mock_get_current_user():
            return test_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            # Generate keypair
            keypair = smart_meter_service.generate_keypair(str(test_meter.id))
            
            # Get public key
            response = client.get(
                f"/api/smart-meter/public-key/{test_meter.id}"
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["meter_id"] == str(test_meter.id)
            assert data["public_key"] == keypair["public_key"]
            assert data["algorithm"] == "ED25519"
            
        finally:
            app.dependency_overrides.clear()
    
    def test_get_public_key_not_found(
        self,
        client: TestClient,
        db_session: Session,
        test_meter: Meter,
        test_user: User
    ):
        """Test error when no keypair exists"""
        from app.core.dependencies import get_current_user
        
        async def mock_get_current_user():
            return test_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            response = client.get(
                f"/api/smart-meter/public-key/{test_meter.id}"
            )
            
            assert response.status_code == 404
            assert "no keypair" in response.json()["detail"].lower()
            
        finally:
            app.dependency_overrides.clear()
    
    def test_get_public_key_invalid_meter_id(
        self,
        client: TestClient,
        test_user: User
    ):
        """Test error with invalid meter ID format"""
        from app.core.dependencies import get_current_user
        
        async def mock_get_current_user():
            return test_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            response = client.get(
                "/api/smart-meter/public-key/invalid-uuid"
            )
            
            assert response.status_code == 400
            assert "invalid" in response.json()["detail"].lower()
            
        finally:
            app.dependency_overrides.clear()


class TestEndToEndFlow:
    """End-to-end tests for complete smart meter flow"""
    
    def test_complete_flow(
        self,
        client: TestClient,
        db_session: Session,
        test_meter: Meter,
        test_user: User,
        smart_meter_service: SmartMeterService
    ):
        """Test complete flow: generate keypair → get public key → sign → verify"""
        from app.core.dependencies import get_current_user
        
        async def mock_get_current_user():
            return test_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            # Step 1: Generate keypair
            response = client.post(
                "/api/smart-meter/generate-keypair",
                json={"meter_id": str(test_meter.id)}
            )
            assert response.status_code == 200
            public_key = response.json()["public_key"]
            
            # Step 2: Get public key
            response = client.get(
                f"/api/smart-meter/public-key/{test_meter.id}"
            )
            assert response.status_code == 200
            assert response.json()["public_key"] == public_key
            
            # Step 3: Sign consumption data
            consumption_kwh = 20.0
            timestamp = int(time.time())
            
            signature = smart_meter_service.sign_consumption(
                meter_id=str(test_meter.id),
                consumption_data={
                    "meter_id": str(test_meter.id),
                    "consumption_kwh": consumption_kwh,
                    "timestamp": timestamp
                }
            )
            
            # Step 4: Verify signature (standalone)
            response = client.post(
                "/api/smart-meter/verify-signature",
                json={
                    "meter_id": str(test_meter.id),
                    "consumption_kwh": consumption_kwh,
                    "timestamp": timestamp,
                    "signature": signature,
                    "public_key": public_key
                }
            )
            assert response.status_code == 200
            assert response.json()["valid"] is True
            
        finally:
            app.dependency_overrides.clear()
