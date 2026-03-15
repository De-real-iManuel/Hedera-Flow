"""
Bill Database Model
SQLAlchemy model for electricity bills
"""
from sqlalchemy import Column, String, DECIMAL, TIMESTAMP, ForeignKey, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Bill(Base):
    """
    Bill model for electricity bills
    
    Stores billing information including consumption, charges, payment status,
    and Hedera blockchain transaction details.
    """
    __tablename__ = "bills"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    meter_id = Column(UUID(as_uuid=True), ForeignKey("meters.id", ondelete="CASCADE"), nullable=False)
    verification_id = Column(UUID(as_uuid=True), nullable=True)  # FK to verifications table when implemented
    
    # Billing Data
    consumption_kwh = Column(DECIMAL(12, 2), nullable=False)
    base_charge = Column(DECIMAL(12, 2), nullable=False)
    taxes = Column(DECIMAL(12, 2), nullable=False)
    subsidies = Column(DECIMAL(12, 2), default=0)
    total_fiat = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)  # 'EUR', 'USD', 'INR', 'BRL', 'NGN'
    
    # Tariff Used
    tariff_id = Column(UUID(as_uuid=True), nullable=True)  # FK to tariffs table when implemented
    tariff_snapshot = Column(JSONB, nullable=True)  # Full tariff at time of calculation
    
    # Payment Data
    # FIX: Commented out columns that don't exist in the database migration (20260219_001_initial_schema.py)
    # These columns were added to the model but never migrated to the database.
    # To add these columns, create a new migration. For now, commenting out to fix the error.
    # payment_method = Column(String(20), default='hbar', nullable=False)  # 'hbar', 'usdc_hedera', 'usdc_ethereum'
    amount_hbar = Column(DECIMAL(18, 8), nullable=True)  # HBAR amount (for HBAR payments)
    # amount_usdc = Column(DECIMAL(20, 6), nullable=True)  # USDC amount (for USDC payments) - NOT IN DATABASE
    exchange_rate = Column(DECIMAL(12, 6), nullable=True)  # HBAR/fiat rate used (for HBAR payments)
    exchange_rate_timestamp = Column(TIMESTAMP, nullable=True)
    
    # Token Information (for USDC payments) - NOT IN DATABASE
    # usdc_token_id = Column(String(100), nullable=True)  # Token ID (Hedera) or contract address (Ethereum)
    # payment_network = Column(String(20), nullable=True)  # 'hedera' or 'ethereum'
    
    # Status
    status = Column(
        String(20),
        default='pending',
        nullable=False
    )
    
    # Transaction IDs
    hedera_tx_id = Column(String(100), nullable=True)  # Hedera transaction ID
    # ethereum_tx_hash = Column(String(66), nullable=True)  # Ethereum transaction hash - NOT IN DATABASE
    hedera_consensus_timestamp = Column(TIMESTAMP, nullable=True)
    
    # Blockchain Logging
    hcs_topic_id = Column(String(50), nullable=True)
    hcs_sequence_number = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    paid_at = Column(TIMESTAMP, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="bills")
    meter = relationship("Meter", back_populates="bills")
    
    # Constraints
    # FIX: Removed constraints for columns that don't exist in the database
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'paid', 'disputed', 'refunded')",
            name="check_bill_status"
        ),
        # Commented out - payment_method column doesn't exist in database
        # CheckConstraint(
        #     "payment_method IN ('hbar', 'usdc_hedera', 'usdc_ethereum')",
        #     name="check_payment_method"
        # ),
        # Commented out - payment_network column doesn't exist in database
        # CheckConstraint(
        #     "payment_network IS NULL OR payment_network IN ('hedera', 'ethereum')",
        #     name="check_payment_network"
        # ),
    )
    
    def __repr__(self):
        return f"<Bill(id={self.id}, meter_id={self.meter_id}, total={self.total_fiat} {self.currency}, status={self.status})>"
