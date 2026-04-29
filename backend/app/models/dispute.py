"""
Dispute Database Model
"""
from sqlalchemy import Column, String, DECIMAL, TIMESTAMP, ForeignKey, Integer, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispute_id = Column(String(50), unique=True, nullable=False)  # DISP-NG-2026-001

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("bills.id", ondelete="CASCADE"), nullable=False)

    reason = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    evidence_ipfs_hashes = Column(ARRAY(Text), default=[])

    # Escrow
    escrow_amount_hbar = Column(DECIMAL(18, 8), nullable=True)
    escrow_amount_fiat = Column(DECIMAL(12, 2), nullable=True)
    escrow_currency = Column(String(3), nullable=True)
    escrow_tx_id = Column(String(100), nullable=True)

    # Resolution
    status = Column(String(20), default="pending", nullable=False)
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(TIMESTAMP, nullable=True)

    # Blockchain
    hcs_topic_id = Column(String(50), nullable=True)
    hcs_sequence_number = Column(Integer, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    bill = relationship("Bill")

    def __repr__(self):
        return f"<Dispute(id={self.dispute_id}, bill={self.bill_id}, status={self.status})>"
