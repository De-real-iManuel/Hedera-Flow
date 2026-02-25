"""
User Database Model
SQLAlchemy model for users table
"""
from sqlalchemy import Column, String, Boolean, TIMESTAMP, Enum as SQLEnum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class CountryCodeEnum(str, enum.Enum):
    """Supported country codes"""
    ES = "ES"  # Spain
    US = "US"  # USA
    IN = "IN"  # India
    BR = "BR"  # Brazil
    NG = "NG"  # Nigeria


class WalletTypeEnum(str, enum.Enum):
    """Wallet types"""
    HASHPACK = "hashpack"
    SYSTEM_GENERATED = "system_generated"


class User(Base):
    """
    User model for authentication and profile management
    
    Attributes:
        id: Unique user identifier (UUID)
        email: User's email address (unique)
        password_hash: Hashed password (NULL for wallet-only auth)
        country_code: User's country (ES, US, IN, BR, NG)
        hedera_account_id: Hedera account ID (0.0.xxxxx format)
        wallet_type: Type of wallet (hashpack or system_generated)
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        last_login: Last login timestamp
        is_active: Account active status
    """
    __tablename__ = "users"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # NULL for wallet-only auth
    
    # Profile
    country_code = Column(
        SQLEnum(CountryCodeEnum, name="country_code_enum"),
        nullable=False,
        index=True
    )
    
    # Hedera Integration
    hedera_account_id = Column(String(50), unique=True, nullable=True, index=True)
    wallet_type = Column(
        SQLEnum(WalletTypeEnum, name="wallet_type_enum"),
        default=WalletTypeEnum.HASHPACK,
        nullable=True
    )
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_login = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True, unique=True)
    email_verification_expires = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Relationships
    bills = relationship("Bill", back_populates="user", cascade="all, delete-orphan")
    meters = relationship("Meter", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, country={self.country_code})>"
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            "id": str(self.id),
            "email": self.email,
            "country_code": self.country_code.value if isinstance(self.country_code, CountryCodeEnum) else self.country_code,
            "hedera_account_id": self.hedera_account_id,
            "wallet_type": self.wallet_type.value if isinstance(self.wallet_type, WalletTypeEnum) else self.wallet_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active
        }
