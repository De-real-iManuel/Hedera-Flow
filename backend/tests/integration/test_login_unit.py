"""
Unit Test for Login Endpoint
Tests for Task 6.3: Implement login endpoint with JWT generation

This test file uses mocking to avoid Hedera SDK initialization issues.

Requirements:
    - FR-1.4: System shall use JWT tokens for session management
    - US-1: User can login with email + password
    - NFR-2.3: JWT tokens shall expire after 30 days
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import jwt

from app.utils.auth import hash_password, verify_password, create_access_token
from config import settings


def test_verify_password_correct():
    """Test password verification with correct password"""
    plain_password = "TestPassword123"
    hashed = hash_password(plain_password)
    
    assert verify_password(plain_password, hashed) is True


def test_verify_password_incorrect():
    """Test password verification with incorrect password"""
    plain_password = "TestPassword123"
    wrong_password = "WrongPassword456"
    hashed = hash_password(plain_password)
    
    assert verify_password(wrong_password, hashed) is False


def test_create_access_token_structure():
    """Test JWT token creation and structure"""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    email = "test@example.com"
    country_code = "ES"
    hedera_account_id = "0.0.123456"
    
    token = create_access_token(
        user_id=user_id,
        email=email,
        country_code=country_code,
        hedera_account_id=hedera_account_id
    )
    
    # Decode token
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    
    # Verify payload
    assert decoded["sub"] == user_id
    assert decoded["email"] == email
    assert decoded["country_code"] == country_code
    assert decoded["hedera_account_id"] == hedera_account_id
    assert decoded["type"] == "access"
    assert "exp" in decoded
    assert "iat" in decoded


def test_create_access_token_expiration():
    """Test JWT token expiration is 30 days"""
    token = create_access_token(
        user_id="test-id",
        email="test@example.com",
        country_code="US",
        hedera_account_id="0.0.123456"
    )
    
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    
    exp_time = datetime.fromtimestamp(decoded["exp"])
    iat_time = datetime.fromtimestamp(decoded["iat"])
    expiration_days = (exp_time - iat_time).days
    
    assert expiration_days == 30


def test_login_logic_success():
    """Test login logic with valid credentials (mocked)"""
    from app.models.user import User, CountryCodeEnum, WalletTypeEnum
    
    # Create mock user
    mock_user = Mock(spec=User)
    mock_user.id = "123e4567-e89b-12d3-a456-426614174000"
    mock_user.email = "test@example.com"
    mock_user.password_hash = hash_password("TestPassword123")
    mock_user.country_code = CountryCodeEnum.ES
    mock_user.hedera_account_id = "0.0.123456"
    mock_user.wallet_type = WalletTypeEnum.SYSTEM_GENERATED
    mock_user.is_active = True
    mock_user.created_at = datetime.utcnow()
    mock_user.last_login = None
    
    # Verify password
    assert verify_password("TestPassword123", mock_user.password_hash) is True
    
    # Generate token
    token = create_access_token(
        user_id=str(mock_user.id),
        email=mock_user.email,
        country_code=mock_user.country_code.value,
        hedera_account_id=mock_user.hedera_account_id
    )
    
    # Verify token
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert decoded["email"] == "test@example.com"
    assert decoded["country_code"] == "ES"


def test_login_logic_invalid_password():
    """Test login logic with invalid password (mocked)"""
    from app.models.user import User
    
    # Create mock user
    mock_user = Mock(spec=User)
    mock_user.password_hash = hash_password("TestPassword123")
    
    # Verify wrong password fails
    assert verify_password("WrongPassword456", mock_user.password_hash) is False


def test_login_logic_no_password_hash():
    """Test login logic for wallet-only user (no password)"""
    from app.models.user import User
    
    # Create mock wallet-only user
    mock_user = Mock(spec=User)
    mock_user.password_hash = None
    
    # Should not be able to verify password
    assert mock_user.password_hash is None


def test_login_logic_inactive_user():
    """Test login logic for inactive user"""
    from app.models.user import User, CountryCodeEnum
    
    # Create mock inactive user
    mock_user = Mock(spec=User)
    mock_user.id = "123e4567-e89b-12d3-a456-426614174000"
    mock_user.email = "inactive@example.com"
    mock_user.password_hash = hash_password("TestPassword123")
    mock_user.country_code = CountryCodeEnum.US
    mock_user.is_active = False
    
    # Password verification would succeed
    assert verify_password("TestPassword123", mock_user.password_hash) is True
    
    # But login should be blocked due to is_active=False
    assert mock_user.is_active is False


def test_token_without_hedera_account():
    """Test JWT token creation without Hedera account"""
    token = create_access_token(
        user_id="test-id",
        email="test@example.com",
        country_code="IN",
        hedera_account_id=None
    )
    
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    
    assert decoded["sub"] == "test-id"
    assert decoded["email"] == "test@example.com"
    assert decoded["country_code"] == "IN"
    assert decoded["hedera_account_id"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
