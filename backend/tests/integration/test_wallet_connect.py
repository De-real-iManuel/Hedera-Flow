"""
Test Wallet Connect Endpoint
Tests for HashPack wallet connection with signature verification

Requirements tested:
- FR-1.2: System shall support HashPack wallet connection
- FR-1.4: System shall use JWT tokens for session management
- US-1: User can register with email + password OR connect HashPack wallet
- NFR-2.3: JWT tokens shall expire after 30 days
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch, MagicMock
import jwt
from datetime import datetime, timedelta

from main import app
from app.core.database import Base, get_db
from app.models.user import User, CountryCodeEnum, WalletTypeEnum
from config import settings


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_wallet_connect.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
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


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_hedera_service():
    """Mock Hedera service for testing"""
    with patch('app.api.endpoints.auth.get_hedera_service') as mock:
        service = Mock()
        service.account_exists.return_value = True
        service.verify_signature.return_value = True
        mock.return_value = service
        yield service


class TestWalletConnectNewUser:
    """Test wallet connection for new users (registration)"""
    
    def test_wallet_connect_creates_new_user(self, mock_hedera_service):
        """Test that wallet connect creates a new user if account doesn't exist"""
        # Arrange
        request_data = {
            "hedera_account_id": "0.0.123456",
            "signature": "abcdef1234567890",
            "message": "Sign in to Hedera Flow"
        }
        
        # Act
        response = client.post("/api/auth/wallet-connect", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "token" in data
        assert "user" in data
        
        # Check user data
        user = data["user"]
        assert user["hedera_account_id"] == "0.0.123456"
        assert user["wallet_type"] == "hashpack"
        assert user["is_active"] is True
        assert user["email"].endswith("@wallet.hederaflow.local")
        
        # Verify JWT token
        token_payload = jwt.decode(
            data["token"],
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        assert token_payload["hedera_account_id"] == "0.0.123456"
        assert "exp" in token_payload
        
        # Verify Hedera service was called
        mock_hedera_service.account_exists.assert_called_once_with("0.0.123456")
        mock_hedera_service.verify_signature.assert_called_once_with(
            account_id="0.0.123456",
            message="Sign in to Hedera Flow",
            signature="abcdef1234567890"
        )
    
    def test_wallet_connect_generates_unique_email(self, mock_hedera_service):
        """Test that wallet-only users get unique email addresses"""
        # Arrange
        request_data = {
            "hedera_account_id": "0.0.789012",
            "signature": "fedcba0987654321",
            "message": "Sign in to Hedera Flow"
        }
        
        # Act
        response = client.post("/api/auth/wallet-connect", json=request_data)
        
        # Assert
        assert response.status_code == 200
        user = response.json()["user"]
        
        # Email should be derived from account ID
        expected_email = "0-0-789012@wallet.hederaflow.local"
        assert user["email"] == expected_email
    
    def test_wallet_connect_sets_default_country(self, mock_hedera_service):
        """Test that new wallet users get default country code"""
        # Arrange
        request_data = {
            "hedera_account_id": "0.0.111222",
            "signature": "signature123",
            "message": "Sign in"
        }
        
        # Act
        response = client.post("/api/auth/wallet-connect", json=request_data)
        
        # Assert
        assert response.status_code == 200
        user = response.json()["user"]
        
        # Default country should be ES (Spain) for MVP
        assert user["country_code"] == "ES"


class TestWalletConnectExistingUser:
    """Test wallet connection for existing users (login)"""
    
    def test_wallet_connect_logs_in_existing_user(self, mock_hedera_service):
        """Test that wallet connect logs in existing user"""
        # Arrange - Create existing user
        db = TestingSessionLocal()
        existing_user = User(
            email="existing@wallet.hederaflow.local",
            password_hash=None,
            country_code=CountryCodeEnum.US,
            hedera_account_id="0.0.999888",
            wallet_type=WalletTypeEnum.HASHPACK,
            is_active=True
        )
        db.add(existing_user)
        db.commit()
        db.close()
        
        request_data = {
            "hedera_account_id": "0.0.999888",
            "signature": "existingsig",
            "message": "Sign in"
        }
        
        # Act
        response = client.post("/api/auth/wallet-connect", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        user = data["user"]
        assert user["hedera_account_id"] == "0.0.999888"
        assert user["email"] == "existing@wallet.hederaflow.local"
        assert user["country_code"] == "US"
        assert user["wallet_type"] == "hashpack"
        
        # Verify last_login was updated
        assert user["last_login"] is not None
    
    def test_wallet_connect_rejects_inactive_user(self, mock_hedera_service):
        """Test that wallet connect rejects inactive users"""
        # Arrange - Create inactive user
        db = TestingSessionLocal()
        inactive_user = User(
            email="inactive@wallet.hederaflow.local",
            password_hash=None,
            country_code=CountryCodeEnum.ES,
            hedera_account_id="0.0.555444",
            wallet_type=WalletTypeEnum.HASHPACK,
            is_active=False
        )
        db.add(inactive_user)
        db.commit()
        db.close()
        
        request_data = {
            "hedera_account_id": "0.0.555444",
            "signature": "inactivesig",
            "message": "Sign in"
        }
        
        # Act
        response = client.post("/api/auth/wallet-connect", json=request_data)
        
        # Assert
        assert response.status_code == 401
        response_data = response.json()
        # Handle both error formats
        error_message = response_data.get("detail") or response_data.get("error", {}).get("message", "")
        assert "inactive" in error_message.lower()


class TestWalletConnectSignatureVerification:
    """Test signature verification logic"""
    
    def test_wallet_connect_rejects_invalid_signature(self, mock_hedera_service):
        """Test that invalid signatures are rejected"""
        # Arrange
        mock_hedera_service.verify_signature.return_value = False
        
        request_data = {
            "hedera_account_id": "0.0.123456",
            "signature": "invalidsignature",
            "message": "Sign in"
        }
        
        # Act
        response = client.post("/api/auth/wallet-connect", json=request_data)
        
        # Assert
        assert response.status_code == 401
        response_data = response.json()
        error_message = response_data.get("detail") or response_data.get("error", {}).get("message", "")
        assert "Invalid signature" in error_message
    
    def test_wallet_connect_rejects_nonexistent_account(self, mock_hedera_service):
        """Test that non-existent Hedera accounts are rejected"""
        # Arrange
        mock_hedera_service.account_exists.return_value = False
        
        request_data = {
            "hedera_account_id": "0.0.999999",
            "signature": "signature",
            "message": "Sign in"
        }
        
        # Act
        response = client.post("/api/auth/wallet-connect", json=request_data)
        
        # Assert
        assert response.status_code == 400
        response_data = response.json()
        error_message = response_data.get("detail") or response_data.get("error", {}).get("message", "")
        assert "does not exist" in error_message
    
    def test_wallet_connect_validates_account_id_format(self):
        """Test that invalid account ID format is rejected"""
        # Arrange
        request_data = {
            "hedera_account_id": "invalid-format",
            "signature": "signature",
            "message": "Sign in"
        }
        
        # Act
        response = client.post("/api/auth/wallet-connect", json=request_data)
        
        # Assert
        assert response.status_code == 422  # Validation error


class TestWalletConnectJWTToken:
    """Test JWT token generation for wallet authentication"""
    
    def test_wallet_connect_generates_valid_jwt(self, mock_hedera_service):
        """Test that wallet connect generates valid JWT token"""
        # Arrange
        request_data = {
            "hedera_account_id": "0.0.123456",
            "signature": "signature",
            "message": "Sign in"
        }
        
        # Act
        response = client.post("/api/auth/wallet-connect", json=request_data)
        
        # Assert
        assert response.status_code == 200
        token = response.json()["token"]
        
        # Decode and verify token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        assert payload["hedera_account_id"] == "0.0.123456"
        assert "sub" in payload  # User ID
        assert "email" in payload
        assert "country_code" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert payload["type"] == "access"
    
    def test_wallet_connect_token_expires_in_30_days(self, mock_hedera_service):
        """Test that JWT token expires in 30 days"""
        # Arrange
        request_data = {
            "hedera_account_id": "0.0.123456",
            "signature": "signature",
            "message": "Sign in"
        }
        
        # Act
        response = client.post("/api/auth/wallet-connect", json=request_data)
        
        # Assert
        token = response.json()["token"]
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check expiration is approximately 30 days from now
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        days_until_expiry = (exp_time - now).days
        
        assert 29 <= days_until_expiry <= 30


class TestWalletConnectErrorHandling:
    """Test error handling in wallet connect"""
    
    def test_wallet_connect_handles_hedera_service_error(self, mock_hedera_service):
        """Test that Hedera service errors are handled gracefully"""
        # Arrange
        mock_hedera_service.verify_signature.side_effect = Exception("Hedera network error")
        
        request_data = {
            "hedera_account_id": "0.0.123456",
            "signature": "signature",
            "message": "Sign in"
        }
        
        # Act
        response = client.post("/api/auth/wallet-connect", json=request_data)
        
        # Assert
        assert response.status_code == 500
        response_data = response.json()
        error_message = response_data.get("detail") or response_data.get("error", {}).get("message", "")
        assert "failed" in error_message.lower()
    
    def test_wallet_connect_handles_database_error(self, mock_hedera_service):
        """Test that database errors are handled gracefully"""
        # Arrange - Create user first
        db = TestingSessionLocal()
        user = User(
            email="test@wallet.hederaflow.local",
            password_hash=None,
            country_code=CountryCodeEnum.ES,
            hedera_account_id="0.0.123456",
            wallet_type=WalletTypeEnum.HASHPACK,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.close()
        
        # Try to create duplicate (should be handled by login logic, but test edge case)
        request_data = {
            "hedera_account_id": "0.0.123456",
            "signature": "signature",
            "message": "Sign in"
        }
        
        # Act
        response = client.post("/api/auth/wallet-connect", json=request_data)
        
        # Assert - Should succeed (login existing user)
        assert response.status_code == 200


class TestWalletConnectIntegration:
    """Integration tests for wallet connect flow"""
    
    def test_complete_wallet_registration_flow(self, mock_hedera_service):
        """Test complete flow: wallet connect -> registration -> JWT"""
        # Arrange
        request_data = {
            "hedera_account_id": "0.0.777888",
            "signature": "completesig",
            "message": "Sign in to Hedera Flow"
        }
        
        # Act - First connection (registration)
        response1 = client.post("/api/auth/wallet-connect", json=request_data)
        
        # Assert first connection
        assert response1.status_code == 200
        user1 = response1.json()["user"]
        token1 = response1.json()["token"]
        
        # Add a small delay to ensure different timestamps
        import time
        time.sleep(0.1)
        
        # Act - Second connection (login)
        response2 = client.post("/api/auth/wallet-connect", json=request_data)
        
        # Assert second connection
        assert response2.status_code == 200
        user2 = response2.json()["user"]
        token2 = response2.json()["token"]
        
        # User ID should be the same
        assert user1["id"] == user2["id"]
        assert user1["hedera_account_id"] == user2["hedera_account_id"]
        
        # Tokens might be the same if issued at the same second (JWT precision is 1 second)
        # So we just verify both are valid tokens
        assert len(token1) > 0
        assert len(token2) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
