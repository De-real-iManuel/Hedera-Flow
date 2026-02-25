"""
Dispute Schemas
Pydantic models for dispute-related API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum
from .bills import Currency


class DisputeReason(str, Enum):
    """Dispute reason types"""
    OVERCHARGE = "OVERCHARGE"
    METER_ERROR = "METER_ERROR"
    TARIFF_ERROR = "TARIFF_ERROR"
    OTHER = "OTHER"


class DisputeStatus(str, Enum):
    """Dispute status types"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    RESOLVED_USER = "resolved_user"
    RESOLVED_UTILITY = "resolved_utility"
    CANCELLED = "cancelled"


# Request Schemas
class DisputeCreateRequest(BaseModel):
    """Create dispute request (multipart form data)"""
    bill_id: str
    reason: DisputeReason
    description: str = Field(..., min_length=10, max_length=2000)
    # evidence: List[File] - handled separately in FastAPI endpoint


class DisputeResolveRequest(BaseModel):
    """Resolve dispute request (admin only)"""
    dispute_id: str
    winner: str = Field(..., pattern=r"^(user|utility)$")
    resolution_notes: str = Field(..., min_length=10, max_length=2000)


# Response Schemas
class DisputeResponse(BaseModel):
    """Dispute data in responses"""
    id: str
    dispute_id: str  # DISP-{COUNTRY}-{YEAR}-{ID}
    user_id: str
    bill_id: str
    
    # Dispute details
    reason: DisputeReason
    description: str
    evidence_ipfs_hashes: List[str]
    
    # Escrow
    escrow_amount_hbar: Decimal
    escrow_amount_fiat: Decimal
    escrow_currency: Currency
    escrow_tx_id: str
    
    # Resolution
    status: DisputeStatus
    resolution_notes: Optional[str]
    resolved_by: Optional[str]  # Admin user ID
    resolved_at: Optional[datetime]
    
    # Blockchain
    hcs_topic_id: str
    hcs_sequence_number: int
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DisputeListResponse(BaseModel):
    """List of disputes response"""
    disputes: List[DisputeResponse]
    total: int


class DisputeSummary(BaseModel):
    """Simplified dispute data for lists"""
    id: str
    dispute_id: str
    reason: DisputeReason
    status: DisputeStatus
    escrow_amount_fiat: Decimal
    escrow_currency: Currency
    created_at: datetime

    class Config:
        from_attributes = True


class DisputeResolveResponse(BaseModel):
    """Dispute resolution response"""
    dispute: DisputeResponse
    message: str = "Dispute resolved successfully"
    escrow_released_to: str  # 'user' or 'utility'
    release_tx_id: str
