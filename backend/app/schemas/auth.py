"""
Authentication Schemas
Pydantic models for authentication-related API requests and responses
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


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

    @validator('password')
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

    @validator('hedera_account_id')
    def validate_account_format(cls, v):
        """Validate that the account is either Hedera format or EVM format"""
        import re
        hedera_pattern = r"^0\.0\.\d+$"
        # Accept any 0x address (MetaMask can return mixed-length addresses)
        evm_pattern = r"^0x[a-fA-F0-9]+$"
        if not (re.match(hedera_pattern, v) or re.match(evm_pattern, v)):
            raise ValueError('Must be a valid Hedera account ID (0.0.xxx) or EVM address (0x...)')
        return v


# Response Schemas
class UserResponse(BaseModel):
    """User data in responses"""
    id: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: str
    country_code: CountryCode
    hedera_account_id: Optional[str]
    wallet_type: Optional[WalletType]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool

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
    hedera_account_id: Optional[str]
    exp: int
