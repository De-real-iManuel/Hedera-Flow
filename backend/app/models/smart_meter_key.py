"""
Smart Meter Key Database Model
SQLAlchemy model for smart_meter_keys table
"""
from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class SmartMeterKey(Base):
    """
    Smart Meter Key model for storing meter cryptographic keys
    
    Attributes:
        id: Unique key identifier (UUID)
        meter_id: Reference to meter
        public_key_pem: Public key in PEM format
        encrypted_private_key: Encrypted private key
        algorithm: Cryptographic algorithm (ED25519)
        created_at: Key generation timestamp
    """
    __tablename__ = "smart_meter_keys"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )
    
    # Foreign Key
    meter_id = Column(
        UUID(as_uuid=True),
        ForeignKey('meters.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Key Data
    public_key = Column(Text, nullable=False)
    private_key_encrypted = Column(Text, nullable=False)
    encryption_iv = Column(Text, nullable=False)
    algorithm = Column(String(20), nullable=False, default='ED25519')
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<SmartMeterKey(id={self.id}, meter_id={self.meter_id}, algorithm={self.algorithm})>"
