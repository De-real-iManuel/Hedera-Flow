"""
Test JWT Verification Middleware
Tests for Task 6.5: JWT verification middleware for protected routes
"""
import pytest
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import jwt

from app.core.dependencies import get_current_user, get_current_user_optional
from app.core.database import Base, get_db
from app.models.user import User, CountryCodeEnum, WalletTypeEnum
from app.utils.auth import create_access_token, hash_password
from config import settings


# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_jwt_middleware.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Create test FastAPI app
app = FastAPI()
app.dependency_overrides[get_db] = override_get_db


@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    """Protected route that requires authentication"""
    return {
        "message": "Access granted",
        "user_id": str(current_user.id),
        "email": current_user.email
    }


@app.get("/optional-auth")
async def optional_auth_route(current_user: User = Depends(get_current_user_optional)):
    """Route with optional authentication"""
    if current_user:
        return {
            "authenticated": True,
            "user_id": str(current_user.id),
            "email": current_user.email
        }
    return {"authenticated": False}


# Test client
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Create test database and tables"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(setup_database):
    """Create a test user in the database"""
    db = TestingSessionLocal()
    try:
        user = User(
            email="test@example.com",
            password_hash=hash_password("TestPassword123"),
            country_code=CountryCodeEnum.ES,
            hedera_account_id="0.0.12345",
            wallet_type=WalletTypeEnum.SYSTEM_GENERATED,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture
def inactive_user(setup_database):
    """Create an inactive test user"""
    db = TestingSessionLocal()
    try:
        user = User(
            email="inactive@example.com",
            password_hash=hash_password("TestPassword123"),
            country_code=CountryCodeEnum.US,
            hedera_account_id="0.0.67890",
            wallet_type=WalletTypeEnum.HASHPACK,
            is_active=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def test_protected_route_without_token(setup_database):
    """Test accessing protected route without authentication token"""
    response = client.get("/protected")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_protected_route_with_invalid_token(setup_database):
    """Test accessing protected route with invalid token"""
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 401
    assert "Invalid authentication token" in response.json()["detail"]


def test_protected_route_with_expired_token(test_user):
    """Test accessing protected route with expired token"""
    # Create an expired token (expired 1 day ago)
    expiration = datetime.utcnow() - timedelta(days=1)
    payload = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "country_code": test_user.country_code.value,
        "hedera_account_id": test_user.hedera_account_id,
        "exp": int(expiration.timestamp()),
        "iat": int((datetime.utcnow() - timedelta(days=2)).timestamp()),
        "type": "access"
    }
    expired_token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_protected_route_with_valid_token(test_user):
    """Test accessing protected route with valid token"""
    # Create valid token
    token = create_access_token(
        user_id=str(test_user.id),
        email=test_user.email,
        country_code=test_user.country_code.value,
        hedera_account_id=test_user.hedera_account_id
    )
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Access granted"
    assert data["user_id"] == str(test_user.id)
    assert data["email"] == test_user.email


def test_protected_route_with_inactive_user(inactive_user):
    """Test accessing protected route with inactive user account"""
    # Create valid token for inactive user
    token = create_access_token(
        user_id=str(inactive_user.id),
        email=inactive_user.email,
        country_code=inactive_user.country_code.value,
        hedera_account_id=inactive_user.hedera_account_id
    )
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()


def test_protected_route_with_wrong_token_type(test_user):
    """Test accessing protected route with wrong token type"""
    # Create token with wrong type
    expiration = datetime.utcnow() + timedelta(days=30)
    payload = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "country_code": test_user.country_code.value,
        "hedera_account_id": test_user.hedera_account_id,
        "exp": int(expiration.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "type": "refresh"  # Wrong type
    }
    wrong_type_token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    
    headers = {"Authorization": f"Bearer {wrong_type_token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 401
    assert "Invalid token type" in response.json()["detail"]


def test_protected_route_with_missing_bearer_prefix(test_user):
    """Test accessing protected route without 'Bearer' prefix"""
    token = create_access_token(
        user_id=str(test_user.id),
        email=test_user.email,
        country_code=test_user.country_code.value,
        hedera_account_id=test_user.hedera_account_id
    )
    
    # Send token without Bearer prefix
    headers = {"Authorization": token}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 401


def test_optional_auth_without_token(setup_database):
    """Test optional auth route without token"""
    response = client.get("/optional-auth")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False


def test_optional_auth_with_valid_token(test_user):
    """Test optional auth route with valid token"""
    token = create_access_token(
        user_id=str(test_user.id),
        email=test_user.email,
        country_code=test_user.country_code.value,
        hedera_account_id=test_user.hedera_account_id
    )
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/optional-auth", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True
    assert data["user_id"] == str(test_user.id)
    assert data["email"] == test_user.email


def test_optional_auth_with_invalid_token(setup_database):
    """Test optional auth route with invalid token (should not fail)"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/optional-auth", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False


def test_token_extraction_from_user_info(test_user):
    """Test that user info is correctly extracted from token"""
    token = create_access_token(
        user_id=str(test_user.id),
        email=test_user.email,
        country_code=test_user.country_code.value,
        hedera_account_id=test_user.hedera_account_id
    )
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Verify all user info is accessible
    assert data["user_id"] == str(test_user.id)
    assert data["email"] == test_user.email


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
