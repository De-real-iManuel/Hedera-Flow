"""
Utility Provider Database Model
SQLAlchemy model for utility_providers table
"""
from sqlalchemy import Column, String, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class UtilityProvider(Base):
    """
    Utility Provider model for electricity distribution companies
    
    Attributes:
        id: Unique provider identifier (UUID)
        country_code: ISO 3166-1 alpha-2 country code (ES, US, IN, BR, NG)
        state_province: State or province name
        provider_name: Full name of the utility provider
        provider_code: Short code for the provider (e.g., IKEDP, PGE)
        service_areas: Array of cities/zones served by this provider
        is_active: Whether the provider is currently active
        created_at: Provider creation timestamp
    """
    __tablename__ = "utility_providers"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )
    
    # Provider Information
    country_code = Column(String(2), nullable=False, index=True)
    state_province = Column(String(100), nullable=False, index=True)
    provider_name = Column(String(100), nullable=False)
    provider_code = Column(String(20), nullable=False, index=True)
    service_areas = Column(ARRAY(String), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    # Unique constraint
    __table_args__ = (
        {'schema': None}  # Use default schema
    )
    
    def __repr__(self):
        return f"<UtilityProvider(id={self.id}, provider_name={self.provider_name}, country={self.country_code})>"
    
    def to_dict(self):
        """Convert utility provider to dictionary"""
        return {
            "id": str(self.id),
            "country_code": self.country_code,
            "state_province": self.state_province,
            "provider_name": self.provider_name,
            "provider_code": self.provider_code,
            "service_areas": self.service_areas,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
