"""
Smart Meter Key — SQLAlchemy model
Supports both KMS-backed keys (kms_key_id set, private_key_encrypted null)
and local AES-256 fallback (private_key_encrypted + encryption_iv set).
"""
from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
import uuid

from app.core.database import Base


class SmartMeterKey(Base):
    __tablename__ = "smart_meter_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    meter_id = Column(UUID(as_uuid=True), ForeignKey('meters.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    public_key = Column(Text, nullable=False)

    # KMS path — key lives in HSM, only the key ID is stored
    kms_key_id = Column(String(255), nullable=True)

    # Local AES-256 fallback — nullable when KMS is used
    private_key_encrypted = Column(Text, nullable=True)
    encryption_iv = Column(Text, nullable=True)

    algorithm = Column(String(20), nullable=False, default='ED25519')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)

    def __repr__(self):
        mode = "KMS" if self.kms_key_id else "local"
        return f"<SmartMeterKey(meter_id={self.meter_id}, algorithm={self.algorithm}, mode={mode})>"
