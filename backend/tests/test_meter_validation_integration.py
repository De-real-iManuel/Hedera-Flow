"""
Integration Tests for Meter ID Validation in API Endpoints

Tests that meter ID validation is properly integrated into the meters API endpoint.

Requirements:
    - FR-2.2: System shall validate meter ID format per region
    - US-2: Meter registration with validation
"""
import pytest
import os
import sys

# Set test environment variables before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-testing-only'
os.environ['HEDERA_OPERATOR_ID'] = '0.0.12345'
os.environ['HEDERA_OPERATOR_KEY'] = 'test-key'

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.app import app
from app.core.database import Base, get_db
from app.models.user import User, CountryCode
from app.models.utility_provider import UtilityProvider
from app.utils.auth import hash_password, create_access_token


# Test database setup
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


@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def spain_user_token(test_db):
    """Create Spain user and return auth token"""
    db = TestingSessionLocal()
    
    # Create user
    user = User(
        email="spain@test.com",
        password_hash=hash_password("Test123!"),
        country_code=CountryCode.ES,
        hedera_account_id="0.0.12345"
    )
    db.add(user)
    
    # Create utility provider
    utility = UtilityProvider(
        country_code="ES",
        state_province="Madrid",
        provider_name="Iberdrola",
        provider_code="IBE",
        service_areas=["Madrid", "Toledo"],
        is_active=True
    )
    db.add(utility)
    
    db.commit()
    db.refresh(user)
    db.refresh(utility)
    
    token = create_access_token({"sub": user.email})
    
    db.close()
    return token, str(utility.id)


@pytest.fixture
def usa_user_token(test_db):
    """Create USA user and return auth token"""
    db = TestingSessionLocal()
    
    # Create user
    user = User(
        email="usa@test.com",
        password_hash=hash_password("Test123!"),
        country_code=CountryCode.US,
        hedera_account_id="0.0.12346"
    )
    db.add(user)
    
    # Create utility provider
    utility = UtilityProvider(
        country_code="US",
        state_province="California",
        provider_name="Pacific Gas & Electric",
        provider_code="PGE",
        service_areas=["San Francisco", "Oakland"],
        is_active=True
    )
    db.add(utility)
    
    db.commit()
    db.refresh(user)
    db.refresh(utility)
    
    token = create_access_token({"sub": user.email})
    
    db.close()
    return token, str(utility.id)


@pytest.fixture
def nigeria_user_token(test_db):
    """Create Nigeria user and return auth token"""
    db = TestingSessionLocal()
    
    # Create user
    user = User(
        email="nigeria@test.com",
        password_hash=hash_password("Test123!"),
        country_code=CountryCode.NG,
        hedera_account_id="0.0.12347"
    )
    db.add(user)
    
    # Create utility provider
    utility = UtilityProvider(
        country_code="NG",
        state_province="Lagos",
        provider_name="Ikeja Electric",
        provider_code="IKEDC",
        service_areas=["Ikeja", "Victoria Island"],
        is_active=True
    )
    db.add(utility)
    
    db.commit()
    db.refresh(user)
    db.refresh(utility)
    
    token = create_access_token({"sub": user.email})
    
    db.close()
    return token, str(utility.id)


class TestSpainMeterValidationAPI:
    """Test Spain meter ID validation via API"""
    
    def test_create_meter_with_valid_spain_id(self, client, spain_user_token):
        """Test creating meter with valid Spain meter ID"""
        token, utility_id = spain_user_token
        
        response = client.post(
            "/api/meters",
            json={
                "meter_id": "ES-12345678",
                "utility_provider_id": utility_id,
                "state_province": "Madrid",
                "utility_provider": "Iberdrola",
                "meter_type": "postpaid",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["meter_id"] == "ES-12345678"
    
    def test_create_meter_with_invalid_spain_id(self, client, spain_user_token):
        """Test creating meter with invalid Spain meter ID"""
        token, utility_id = spain_user_token
        
        response = client.post(
            "/api/meters",
            json={
                "meter_id": "12345678",  # Missing prefix
                "utility_provider_id": utility_id,
                "state_province": "Madrid",
                "utility_provider": "Iberdrola",
                "meter_type": "postpaid",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "Invalid meter ID format" in response.json()["detail"]
        assert "Spain" in response.json()["detail"]
    
    def test_create_meter_with_normalized_spain_id(self, client, spain_user_token):
        """Test that Spain meter IDs are normalized"""
        token, utility_id = spain_user_token
        
        # Submit without hyphen
        response = client.post(
            "/api/meters",
            json={
                "meter_id": "ES12345678",
                "utility_provider_id": utility_id,
                "state_province": "Madrid",
                "utility_provider": "Iberdrola",
                "meter_type": "postpaid",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        # Should be normalized with hyphen
        assert data["meter_id"] == "ES-12345678"


class TestUSAMeterValidationAPI:
    """Test USA meter ID validation via API"""
    
    def test_create_meter_with_valid_usa_id(self, client, usa_user_token):
        """Test creating meter with valid USA meter ID"""
        token, utility_id = usa_user_token
        
        response = client.post(
            "/api/meters",
            json={
                "meter_id": "PGE12345678",
                "utility_provider_id": utility_id,
                "state_province": "California",
                "utility_provider": "Pacific Gas & Electric",
                "meter_type": "postpaid",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["meter_id"] == "PGE12345678"
    
    def test_create_meter_with_invalid_usa_id(self, client, usa_user_token):
        """Test creating meter with invalid USA meter ID"""
        token, utility_id = usa_user_token
        
        response = client.post(
            "/api/meters",
            json={
                "meter_id": "PGE-12345678",  # Hyphen not allowed
                "utility_provider_id": utility_id,
                "state_province": "California",
                "utility_provider": "Pacific Gas & Electric",
                "meter_type": "postpaid",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "Invalid meter ID format" in response.json()["detail"]
        assert "USA" in response.json()["detail"]
    
    def test_create_meter_with_normalized_usa_id(self, client, usa_user_token):
        """Test that USA meter IDs are normalized to uppercase"""
        token, utility_id = usa_user_token
        
        response = client.post(
            "/api/meters",
            json={
                "meter_id": "pge12345678",  # Lowercase
                "utility_provider_id": utility_id,
                "state_province": "California",
                "utility_provider": "Pacific Gas & Electric",
                "meter_type": "postpaid",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        # Should be normalized to uppercase
        assert data["meter_id"] == "PGE12345678"


class TestNigeriaMeterValidationAPI:
    """Test Nigeria meter ID validation via API"""
    
    def test_create_meter_with_valid_nigeria_id(self, client, nigeria_user_token):
        """Test creating meter with valid Nigeria meter ID"""
        token, utility_id = nigeria_user_token
        
        response = client.post(
            "/api/meters",
            json={
                "meter_id": "12345678901",
                "utility_provider_id": utility_id,
                "state_province": "Lagos",
                "utility_provider": "Ikeja Electric",
                "meter_type": "prepaid",
                "band_classification": "B",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["meter_id"] == "12345678901"
        assert data["band_classification"] == "B"
    
    def test_create_meter_with_invalid_nigeria_id(self, client, nigeria_user_token):
        """Test creating meter with invalid Nigeria meter ID"""
        token, utility_id = nigeria_user_token
        
        response = client.post(
            "/api/meters",
            json={
                "meter_id": "1234567890",  # Too short (10 digits)
                "utility_provider_id": utility_id,
                "state_province": "Lagos",
                "utility_provider": "Ikeja Electric",
                "meter_type": "prepaid",
                "band_classification": "B",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "Invalid meter ID format" in response.json()["detail"]
        assert "Nigeria" in response.json()["detail"]
    
    def test_nigeria_meter_requires_band_classification(self, client, nigeria_user_token):
        """Test that Nigeria meters require band classification"""
        token, utility_id = nigeria_user_token
        
        response = client.post(
            "/api/meters",
            json={
                "meter_id": "12345678901",
                "utility_provider_id": utility_id,
                "state_province": "Lagos",
                "utility_provider": "Ikeja Electric",
                "meter_type": "prepaid",
                # Missing band_classification
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "Band classification is required" in response.json()["detail"]


class TestCrossCountryValidation:
    """Test that meter IDs are validated against user's country"""
    
    def test_spain_meter_id_for_spain_user(self, client, spain_user_token):
        """Test Spain meter ID works for Spain user"""
        token, utility_id = spain_user_token
        
        response = client.post(
            "/api/meters",
            json={
                "meter_id": "ES-12345678",
                "utility_provider_id": utility_id,
                "state_province": "Madrid",
                "utility_provider": "Iberdrola",
                "meter_type": "postpaid",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
    
    def test_usa_meter_id_for_spain_user_fails(self, client, spain_user_token):
        """Test USA meter ID fails for Spain user"""
        token, utility_id = spain_user_token
        
        response = client.post(
            "/api/meters",
            json={
                "meter_id": "PGE12345678",  # USA format
                "utility_provider_id": utility_id,
                "state_province": "Madrid",
                "utility_provider": "Iberdrola",
                "meter_type": "postpaid",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "Invalid meter ID format" in response.json()["detail"]
        assert "Spain" in response.json()["detail"]


class TestMeterValidationErrorMessages:
    """Test that API returns helpful error messages"""
    
    def test_error_message_includes_format_info(self, client, spain_user_token):
        """Test that error messages include format information"""
        token, utility_id = spain_user_token
        
        response = client.post(
            "/api/meters",
            json={
                "meter_id": "123",
                "utility_provider_id": utility_id,
                "state_province": "Madrid",
                "utility_provider": "Iberdrola",
                "meter_type": "postpaid",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        # Should include format description
        assert "Spain" in error_detail
        assert any(word in error_detail.lower() for word in ["format", "expected", "digit", "letter"])
    
    def test_error_message_includes_examples(self, client, spain_user_token):
        """Test that error messages include examples"""
        token, utility_id = spain_user_token
        
        response = client.post(
            "/api/meters",
            json={
                "meter_id": "INVALID",
                "utility_provider_id": utility_id,
                "state_province": "Madrid",
                "utility_provider": "Iberdrola",
                "meter_type": "postpaid",
                "is_primary": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        # Should include examples
        assert "ES-" in error_detail or "ESP-" in error_detail
