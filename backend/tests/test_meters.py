"""
Tests for meter management endpoints
Tests FR-2.1: System shall allow users to register multiple meters
Tests US-2: User can register meter with state/utility dropdowns
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from app.core.database import Base, get_db
from app.models.user import User, CountryCodeEnum
from app.models.meter import Meter, MeterTypeEnum
from app.models.utility_provider import UtilityProvider
from app.utils.auth import hash_password, create_access_token

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(setup_database):
    """Create a test user"""
    db = TestingSessionLocal()
    
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPassword123!"),
        country_code=CountryCodeEnum.ES,
        hedera_account_id="0.0.12345"
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate token
    token = create_access_token({"sub": user.email})
    
    yield {"user": user, "token": token}
    
    db.close()


@pytest.fixture
def test_utility_provider(setup_database):
    """Create a test utility provider"""
    db = TestingSessionLocal()
    
    provider = UtilityProvider(
        country_code="ES",
        state_province="Madrid",
        provider_name="Iberdrola",
        provider_code="IBERDROLA",
        service_areas=["Madrid", "Toledo"],
        is_active=True
    )
    
    db.add(provider)
    db.commit()
    db.refresh(provider)
    
    yield provider
    
    db.close()


@pytest.fixture
def test_meters(test_user, test_utility_provider):
    """Create test meters for the user"""
    db = TestingSessionLocal()
    
    user = test_user["user"]
    provider = test_utility_provider
    
    # Create 3 meters
    meter1 = Meter(
        user_id=user.id,
        meter_id="ES-MAD-11111111",
        utility_provider_id=provider.id,
        state_province="Madrid",
        utility_provider="Iberdrola",
        meter_type=MeterTypeEnum.POSTPAID,
        address="Calle Principal 123, Madrid",
        is_primary=True
    )
    
    meter2 = Meter(
        user_id=user.id,
        meter_id="ES-MAD-22222222",
        utility_provider_id=provider.id,
        state_province="Madrid",
        utility_provider="Iberdrola",
        meter_type=MeterTypeEnum.PREPAID,
        address="Avenida Secundaria 456, Madrid",
        is_primary=False
    )
    
    meter3 = Meter(
        user_id=user.id,
        meter_id="ES-MAD-33333333",
        utility_provider_id=provider.id,
        state_province="Madrid",
        utility_provider="Iberdrola",
        meter_type=MeterTypeEnum.POSTPAID,
        address="Plaza Tercera 789, Madrid",
        is_primary=False
    )
    
    db.add_all([meter1, meter2, meter3])
    db.commit()
    
    meters = [meter1, meter2, meter3]
    for meter in meters:
        db.refresh(meter)
    
    yield meters
    
    db.close()


class TestListMetersEndpoint:
    """Tests for GET /api/meters endpoint"""
    
    def test_list_meters_no_auth(self, setup_database):
        """Test that listing meters requires authentication"""
        response = client.get("/api/meters")
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_list_meters_invalid_token(self, setup_database):
        """Test that invalid token is rejected"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/meters", headers=headers)
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_list_meters_empty(self, test_user):
        """Test listing meters when user has no meters"""
        token = test_user["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/meters", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_list_meters_single(self, test_user, test_utility_provider):
        """Test listing meters when user has one meter"""
        token = test_user["token"]
        user = test_user["user"]
        provider = test_utility_provider
        
        # Create a meter
        db = TestingSessionLocal()
        meter = Meter(
            user_id=user.id,
            meter_id="ES-MAD-11111111",
            utility_provider_id=provider.id,
            state_province="Madrid",
            utility_provider="Iberdrola",
            meter_type=MeterTypeEnum.POSTPAID,
            is_primary=True
        )
        db.add(meter)
        db.commit()
        db.close()
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/meters", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        
        # Verify meter data
        meter_data = data[0]
        assert meter_data["meter_id"] == "ES-MAD-11111111"
        assert meter_data["utility_provider"] == "Iberdrola"
        assert meter_data["state_province"] == "Madrid"
        assert meter_data["meter_type"] == "postpaid"
        assert meter_data["is_primary"] is True
        
        # Verify all required fields are present
        required_fields = [
            "id", "user_id", "meter_id", "utility_provider_id",
            "state_province", "utility_provider", "meter_type",
            "is_primary", "created_at", "updated_at"
        ]
        for field in required_fields:
            assert field in meter_data, f"Missing required field: {field}"
    
    def test_list_meters_multiple(self, test_user, test_meters):
        """Test listing multiple meters"""
        token = test_user["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/meters", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        
        # Verify all meters are returned
        meter_ids = [meter["meter_id"] for meter in data]
        assert "ES-MAD-11111111" in meter_ids
        assert "ES-MAD-22222222" in meter_ids
        assert "ES-MAD-33333333" in meter_ids
    
    def test_list_meters_ordering(self, test_user, test_meters):
        """Test that primary meter is listed first"""
        token = test_user["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/meters", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # First meter should be the primary one
        assert data[0]["is_primary"] is True
        assert data[0]["meter_id"] == "ES-MAD-11111111"
        
        # Other meters should not be primary
        assert data[1]["is_primary"] is False
        assert data[2]["is_primary"] is False
    
    def test_list_meters_user_isolation(self, test_user, test_utility_provider):
        """Test that users only see their own meters"""
        # Create first user's meter
        token1 = test_user["token"]
        user1 = test_user["user"]
        provider = test_utility_provider
        
        db = TestingSessionLocal()
        meter1 = Meter(
            user_id=user1.id,
            meter_id="ES-MAD-USER1",
            utility_provider_id=provider.id,
            state_province="Madrid",
            utility_provider="Iberdrola",
            meter_type=MeterTypeEnum.POSTPAID,
            is_primary=True
        )
        db.add(meter1)
        
        # Create second user
        user2 = User(
            email="user2@example.com",
            password_hash=hash_password("TestPassword123!"),
            country_code=CountryCodeEnum.ES,
            hedera_account_id="0.0.67890"
        )
        db.add(user2)
        db.commit()
        db.refresh(user2)
        
        # Create second user's meter
        meter2 = Meter(
            user_id=user2.id,
            meter_id="ES-MAD-USER2",
            utility_provider_id=provider.id,
            state_province="Madrid",
            utility_provider="Iberdrola",
            meter_type=MeterTypeEnum.POSTPAID,
            is_primary=True
        )
        db.add(meter2)
        db.commit()
        db.close()
        
        # User 1 should only see their meter
        headers1 = {"Authorization": f"Bearer {token1}"}
        response1 = client.get("/api/meters", headers=headers1)
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1) == 1
        assert data1[0]["meter_id"] == "ES-MAD-USER1"
        
        # User 2 should only see their meter
        token2 = create_access_token({"sub": user2.email})
        headers2 = {"Authorization": f"Bearer {token2}"}
        response2 = client.get("/api/meters", headers=headers2)
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2) == 1
        assert data2[0]["meter_id"] == "ES-MAD-USER2"
    
    def test_list_meters_response_structure(self, test_user, test_meters):
        """Test that response has correct structure and data types"""
        token = test_user["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/meters", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response is a list
        assert isinstance(data, list)
        
        # Verify each meter has correct structure
        for meter in data:
            # String fields
            assert isinstance(meter["id"], str)
            assert isinstance(meter["user_id"], str)
            assert isinstance(meter["meter_id"], str)
            assert isinstance(meter["utility_provider_id"], str)
            assert isinstance(meter["state_province"], str)
            assert isinstance(meter["utility_provider"], str)
            assert isinstance(meter["meter_type"], str)
            
            # Boolean field
            assert isinstance(meter["is_primary"], bool)
            
            # Datetime fields (ISO format strings)
            assert isinstance(meter["created_at"], str)
            assert isinstance(meter["updated_at"], str)
            
            # Optional fields
            if "address" in meter and meter["address"] is not None:
                assert isinstance(meter["address"], str)
            
            if "band_classification" in meter and meter["band_classification"] is not None:
                assert isinstance(meter["band_classification"], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

