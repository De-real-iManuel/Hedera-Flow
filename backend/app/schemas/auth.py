"""
Authentication Schemas
Pydantic models for authentication-related API requests and responses
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum
import re


class CountryCode(str, Enum):
    """Supported country codes"""
    ES = "ES"  # Spain
    US = "US"  # USA
    IN = "IN"  # India
    BR = "BR"  # Brazil
    NG = "NG"  # Nigeria


class WalletType(str, Enum):
    """Wallet types"""
    HASHPACK = "hashpack"
    SYSTEM_GENERATED = "system_generated"


# Request Schemas
class RegisterRequest(BaseModel):
    """User registration request"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: Optional[str] = Field(None, min_length=8)
    country_code: CountryCode
    hedera_account_id: Optional[str] = Field(None, pattern=r"^0\.0\.\d+$")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if v is not None:
            if not any(c.isupper() for c in v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not any(c.isdigit() for c in v):
                raise ValueError('Password must contain at least one number')
        return v


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class WalletConnectRequest(BaseModel):
    """Wallet connection request"""
    hedera_account_id: str = Field(..., description="Hedera account ID (0.0.xxx) or EVM address (0x...)")
    signature: str
    message: str

    @field_validator('hedera_account_id')
    @classmethod
    def validate_account_format(cls, v):
        """Validate that the account is either Hedera format or EVM format"""
        hedera_pattern = r"^0\.0\.\d+$"
        evm_pattern = r"^0x[a-fA-F0-9]+$"
        if not (re.match(hedera_pattern, v) or re.match(evm_pattern, v)):
            raise ValueError('Must be a valid Hedera account ID (0.0.xxx) or EVM address (0x...)')
        return v


# Response Schemas
class UserResponse(BaseModel):
    """User data in responses — uses str for enum fields to avoid model/schema enum mismatch"""
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    country_code: str  # str avoids Pydantic validation error when DB enum != schema enum
    hedera_account_id: Optional[str] = None
    wallet_type: Optional[str] = None  # str avoids Pydantic validation error
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool
    # Token included in body as fallback for cross-origin cookie issues
    access_token: Optional[str] = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Authentication response with token and user data"""
    token: str
    user: UserResponse


class TokenPayload(BaseModel):
    """JWT token payload structure"""
    user_id: str
    email: str
    country_code: str
    hedera_account_id: Optional[str] = None
    exp: int
