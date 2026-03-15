"""
Billing Schemas
Pydantic models for billing-related API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class BillStatus(str, Enum):
    """Bill status types"""
    PENDING = "pending"
    PAID = "paid"
    DISPUTED = "disputed"
    REFUNDED = "refunded"


class Currency(str, Enum):
    """Supported currencies"""
    EUR = "EUR"  # Euro (Spain)
    USD = "USD"  # US Dollar (USA)
    INR = "INR"  # Indian Rupee (India)
    BRL = "BRL"  # Brazilian Real (Brazil)
    NGN = "NGN"  # Nigerian Naira (Nigeria)


# Response Schemas
class BillBreakdown(BaseModel):
    """Itemized bill breakdown"""
    consumption_kwh: Decimal
    base_charge: Decimal
    taxes: Decimal
    subsidies: Decimal = Decimal("0")
    total_fiat: Decimal
    currency: Currency
    
    # Tariff details
    rate_structure_type: str  # 'flat', 'tiered', 'time_of_use', 'band_based'
    rate_details: Optional[dict] = None


class BillResponse(BaseModel):
    """Bill data in responses"""
    id: str
    user_id: str
    meter_id: str
    verification_id: Optional[str]
    
    # Billing data
    consumption_kwh: Decimal
    base_charge: Decimal
    taxes: Decimal
    subsidies: Decimal
    total_fiat: Decimal
    currency: Currency
    
    # Tariff used
    tariff_id: str
    tariff_snapshot: Optional[dict]
    
    # Payment data
    amount_hbar: Optional[Decimal]
    exchange_rate: Optional[Decimal]
    exchange_rate_timestamp: Optional[datetime]
    
    # Status
    status: BillStatus
    
    # Hedera transaction
    hedera_tx_id: Optional[str]
    hedera_consensus_timestamp: Optional[datetime]
    
    # Blockchain logging
    hcs_topic_id: Optional[str]
    hcs_sequence_number: Optional[int]
    
    created_at: datetime
    paid_at: Optional[datetime]

    class Config:
        from_attributes = True


class BillListResponse(BaseModel):
    """List of bills response"""
    bills: list[BillResponse]
    total: int


class BillSummary(BaseModel):
    """Simplified bill data for lists"""
    id: str
    total_fiat: Decimal
    currency: Currency
    status: BillStatus
    created_at: datetime
    paid_at: Optional[datetime]

    class Config:
        from_attributes = True
