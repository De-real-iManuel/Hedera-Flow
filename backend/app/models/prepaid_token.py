"""
Prepaid Token Database Model
SQLAlchemy model for prepaid_tokens table
"""
from sqlalchemy import Column, String, DECIMAL, TIMESTAMP, ForeignKey, BigInteger, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class PrepaidToken(Base):
    """
    Prepaid Token model for prepaid electricity token management
    
    Attributes:
        id: Unique token identifier (UUID)
        token_id: Human-readable token ID (e.g., TOKEN-ES-2026-001)
        user_id: Reference to user who purchased this token
        meter_id: Reference to meter this token is for
        units_purchased: kWh units purchased
        units_remaining: kWh units remaining
        amount_paid_hbar: HBAR amount paid (if HBAR payment)
        amount_paid_usdc: USDC amount paid (if USDC payment)
        amount_paid_fiat: Fiat amount paid
        currency: Currency code (EUR, USD, etc.)
        exchange_rate: Exchange rate at time of purchase
        tariff_rate: Tariff rate used for calculation
        status: Token status (active, depleted, expired, cancelled)
        hedera_tx_id: Hedera transaction ID
        hedera_consensus_timestamp: Hedera consensus timestamp
        hcs_topic_id: HCS topic ID where issuance was logged
        hcs_sequence_number: HCS sequence number
        issued_at: Token issuance timestamp
        expires_at: Token expiry timestamp (1 year from issuance)
        depleted_at: Timestamp when token was depleted
    """
    __tablename__ = "prepaid_tokens"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )
    
    # Token Identification
    token_id = Column(String(50), nullable=False, unique=True, index=True)
    
    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    meter_id = Column(
        UUID(as_uuid=True),
        ForeignKey('meters.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Purchase Details
    units_purchased = Column(DECIMAL(precision=12, scale=2), nullable=False)
    units_remaining = Column(DECIMAL(precision=12, scale=2), nullable=False)
    amount_paid_hbar = Column(DECIMAL(precision=18, scale=8), nullable=True)
    amount_paid_usdc = Column(DECIMAL(precision=18, scale=6), nullable=True)
    amount_paid_fiat = Column(DECIMAL(precision=12, scale=2), nullable=False)
    currency = Column(String(3), nullable=False)
    exchange_rate = Column(DECIMAL(precision=12, scale=6), nullable=False)
    tariff_rate = Column(DECIMAL(precision=12, scale=6), nullable=False)
    
    # Status
    status = Column(String(20), nullable=False, server_default='active', index=True)
    
    # Hedera Transaction
    hedera_tx_id = Column(String(100), nullable=True)
    hedera_consensus_timestamp = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Blockchain Logging (HCS)
    hcs_topic_id = Column(String(50), nullable=True)
    hcs_sequence_number = Column(BigInteger, nullable=True)
    
    # Timestamps
    issued_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), index=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    depleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="prepaid_tokens")
    meter = relationship("Meter", back_populates="prepaid_tokens")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'depleted', 'expired', 'cancelled')",
            name='check_prepaid_token_status'
        ),
        {'schema': None}  # Use default schema
    )
    
    def __repr__(self):
        return f"<PrepaidToken(id={self.id}, token_id={self.token_id}, status={self.status})>"
    
    def to_dict(self):
        """Convert prepaid token to dictionary"""
        return {
            "id": str(self.id),
            "token_id": self.token_id,
            "user_id": str(self.user_id),
            "meter_id": str(self.meter_id),
            "units_purchased": float(self.units_purchased),
            "units_remaining": float(self.units_remaining),
            "amount_paid_hbar": float(self.amount_paid_hbar) if self.amount_paid_hbar else None,
            "amount_paid_usdc": float(self.amount_paid_usdc) if self.amount_paid_usdc else None,
            "amount_paid_fiat": float(self.amount_paid_fiat),
            "currency": self.currency,
            "exchange_rate": float(self.exchange_rate),
            "tariff_rate": float(self.tariff_rate),
            "status": self.status,
            "hedera_tx_id": self.hedera_tx_id,
            "hedera_consensus_timestamp": self.hedera_consensus_timestamp.isoformat() if self.hedera_consensus_timestamp else None,
            "hcs_topic_id": self.hcs_topic_id,
            "hcs_sequence_number": self.hcs_sequence_number,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "depleted_at": self.depleted_at.isoformat() if self.depleted_at else None
        }
