"""
Exchange Rate Model
"""
from sqlalchemy import Column, String, DECIMAL, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class ExchangeRate(Base):
    """Exchange rate cache table"""
    
    __tablename__ = "exchange_rates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    currency = Column(String(3), nullable=False)
    hbar_price = Column(DECIMAL(12, 6), nullable=False)
    source = Column(String(50), nullable=False)
    fetched_at = Column(TIMESTAMP, server_default=text("NOW()"))
