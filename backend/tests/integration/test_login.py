"""
Test Login Endpoint
Tests for Task 6.3: Implement login endpoint with JWT generation

Requirements:
    - FR-1.4: System shall use JWT tokens for session management
    - US-1: User can login with email + password
    - NFR-2.3: JWT tokens shall expire after 30 days
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import jwt

from main import app
from app.core.database import Base, get_db
from app.models.user import User, CountryCodeEnum, WalletTypeEnum
from app.utils.auth import hash_password
from config import settings

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_login.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user():
    """Create a test user in the database"""
    db = TestingSessionLocal()
    try:
        user = User(
            email="testuser@example.com",
            password_hash=hash_password("TestPassword123"),
            country_code=CountryCodeEnum.ES,
            hedera_account_id="0.0.123456",
            wallet_type=WalletTypeEnum.SYSTEM_GENERATED,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def test_login_success(test_user):
    """Test successful login with valid credentials"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "token" in data
    assert "user" in data
    
    # Check user data
    user_data = data["user"]
    assert user_data["email"] == "testuser@example.com"
    assert user_data["country_code"] == "ES"
    assert user_data["hedera_account_id"] == "0.0.123456"
    assert user_data["is_active"] is True
    assert "last_login" in user_data
    
    # Verify JWT token
    token = data["token"]
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    
    assert decoded["email"] == "testuser@example.com"
    assert decoded["country_code"] == "ES"
    assert decoded["hedera_account_id"] == "0.0.123456"
    assert "exp" in decoded
    assert "iat" in decoded
    
    # Check token expiration (should be 30 days)
    exp_time = datetime.fromtimestamp(decoded["exp"])
    iat_time = datetime.fromtimestamp(decoded["iat"])
    expiration_days = (exp_time - iat_time).days
    assert expiration_days == 30


def test_login_invalid_password(test_user):
    """Test login with incorrect password"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "WrongPassword123"
        }
    )
    
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_user_not_found():
    """Test login with non-existent email"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "TestPassword123"
        }
    )
    
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_login_wallet_only_user():
    """Test login attempt for wallet-only user (no password)"""
    db = TestingSessionLocal()
    try:
        # Create wallet-only user (no password)
        user = User(
            email="walletuser@example.com",
            password_hash=None,  # No password
            country_code=CountryCodeEnum.US,
            hedera_account_id="0.0.789012",
            wallet_type=WalletTypeEnum.HASHPACK,
            is_active=True
        )
        db.add(user)
        db.commit()
    finally:
        db.close()
    
    response = client.post(
        "/api/auth/login",
        json={
            "email": "walletuser@example.com",
            "password": "AnyPassword123"
        }
    )
    
    assert response.status_code == 401
    assert "wallet authentication only" in response.json()["detail"]


def test_login_inactive_user():
    """Test login with inactive account"""
    db = TestingSessionLocal()
    try:
        user = User(
            email="inactive@example.com",
            password_hash=hash_password("TestPassword123"),
            country_code=CountryCodeEnum.IN,
            hedera_account_id="0.0.345678",
            wallet_type=WalletTypeEnum.SYSTEM_GENERATED,
            is_active=False  # Inactive account
        )
        db.add(user)
        db.commit()
    finally:
        db.close()
    
    response = client.post(
        "/api/auth/login",
        json={
            "email": "inactive@example.com",
            "password": "TestPassword123"
        }
    )
    
    assert response.status_code == 401
    assert "Account is inactive" in response.json()["detail"]


def test_login_updates_last_login(test_user):
    """Test that login updates the last_login timestamp"""
    # First login
    response1 = client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123"
        }
    )
    
    assert response1.status_code == 200
    last_login_1 = response1.json()["user"]["last_login"]
    assert last_login_1 is not None
    
    # Wait a moment and login again
    import time
    time.sleep(1)
    
    response2 = client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123"
        }
    )
    
    assert response2.status_code == 200
    last_login_2 = response2.json()["user"]["last_login"]
    
    # Second login timestamp should be later
    assert last_login_2 > last_login_1


def test_login_invalid_email_format():
    """Test login with invalid email format"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "not-an-email",
            "password": "TestPassword123"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_login_missing_password():
    """Test login with missing password"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com"
        }
    )
    
    assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
