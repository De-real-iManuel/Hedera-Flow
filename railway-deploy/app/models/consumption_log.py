"""
Consumption Log Database Model
SQLAlchemy model for consumption_logs table
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class ConsumptionLog(Base):
    """
    Consumption Log model for storing smart meter consumption records
    
    Attributes:
        id: Unique log identifier (UUID)
        meter_id: Reference to meter
        consumption_kwh: Energy consumed in kWh
        timestamp: Unix timestamp of consumption
        signature: Cryptographic signature from meter
        signature_valid: Whether signature was verified
        public_key_pem: Public key used for verification
        token_id: Reference to prepaid token (if deducted)
        units_deducted: Units deducted from token
        units_remaining: Remaining units after deduction
        reading_before: Meter reading before consumption
        reading_after: Meter reading after consumption
        hcs_topic_id: Hedera topic ID where logged
        hcs_sequence_number: Sequence number in HCS topic
        created_at: Log creation timestamp
    """
    __tablename__ = "consumption_logs"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )
    
    # Foreign Keys
    meter_id = Column(
        UUID(as_uuid=True),
        ForeignKey('meters.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    token_id = Column(
        UUID(as_uuid=True),
        ForeignKey('prepaid_tokens.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Consumption Data
    consumption_kwh = Column(Float, nullable=False)
    reading_before = Column(Float, nullable=True)
    reading_after = Column(Float, nullable=True)
    timestamp = Column(Integer, nullable=False, index=True)
    
    # Signature Data
    signature = Column(Text, nullable=False)
    public_key = Column(Text, nullable=False)
    signature_valid = Column(Boolean, nullable=False)
    
    # Token Deduction
    units_deducted = Column(Float, nullable=True)
    units_remaining = Column(Float, nullable=True)
    
    # Meter Readings
    reading_before = Column(Float, nullable=True)
    reading_after = Column(Float, nullable=True)
    
    # HCS Data
    hcs_topic_id = Column(String(100), nullable=True)
    hcs_sequence_number = Column(Integer, nullable=True)
    
    # Timestamp
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ConsumptionLog(id={self.id}, meter_id={self.meter_id}, consumption_kwh={self.consumption_kwh})>"
