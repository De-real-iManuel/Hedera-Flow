"""
Meter Database Model
SQLAlchemy model for meters table
"""
from sqlalchemy import Column, String, Boolean, TIMESTAMP, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class MeterTypeEnum(str, enum.Enum):
    """Meter types"""
    PREPAID = "prepaid"
    POSTPAID = "postpaid"


class BandClassificationEnum(str, enum.Enum):
    """Nigeria band classification"""
    A = "A"  # 20+ hours supply
    B = "B"  # 16-20 hours
    C = "C"  # 12-16 hours
    D = "D"  # 8-12 hours
    E = "E"  # <8 hours


class Meter(Base):
    """
    Meter model for electricity meter management
    
    Attributes:
        id: Unique meter identifier (UUID)
        user_id: Reference to user who owns this meter
        meter_id: Meter identification number (from utility company)
        utility_provider_id: Reference to utility provider
        state_province: State or province where meter is located
        utility_provider: Utility provider name (denormalized for quick access)
        meter_type: Type of meter (prepaid or postpaid)
        band_classification: Nigeria band classification (A-E)
        address: Physical address of the meter
        is_primary: Whether this is the user's primary meter
        created_at: Meter registration timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "meters"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )
    
    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    utility_provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey('utility_providers.id'),
        nullable=True,
        index=True
    )
    
    # Meter Information
    meter_id = Column(String(50), nullable=False, index=True)
    state_province = Column(String(100), nullable=True)
    utility_provider = Column(String(100), nullable=False)  # Denormalized
    
    meter_type = Column(
        SQLEnum(MeterTypeEnum, name="meter_type_enum"),
        nullable=False
    )
    
    band_classification = Column(
        SQLEnum(BandClassificationEnum, name="band_classification_enum"),
        nullable=True
    )
    
    address = Column(Text, nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    user = relationship("User", back_populates="meters")
    bills = relationship("Bill", back_populates="meter", cascade="all, delete-orphan")
    
    # Unique constraint: user cannot register same meter_id twice
    __table_args__ = (
        {'schema': None}  # Use default schema
    )
    
    def __repr__(self):
        return f"<Meter(id={self.id}, meter_id={self.meter_id}, user_id={self.user_id})>"
    
    def to_dict(self):
        """Convert meter to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "meter_id": self.meter_id,
            "utility_provider_id": str(self.utility_provider_id) if self.utility_provider_id else None,
            "state_province": self.state_province,
            "utility_provider": self.utility_provider,
            "meter_type": self.meter_type.value if isinstance(self.meter_type, MeterTypeEnum) else self.meter_type,
            "band_classification": self.band_classification.value if isinstance(self.band_classification, BandClassificationEnum) else self.band_classification,
            "address": self.address,
            "is_primary": self.is_primary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
