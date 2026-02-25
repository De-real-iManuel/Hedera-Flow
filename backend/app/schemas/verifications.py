"""
Verification Schemas
Pydantic models for verification-related API requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class VerificationStatus(str, Enum):
    """Verification status types"""
    VERIFIED = "VERIFIED"
    WARNING = "WARNING"
    DISCREPANCY = "DISCREPANCY"
    FRAUD_DETECTED = "FRAUD_DETECTED"


class OCREngine(str, Enum):
    """OCR engine types"""
    TESSERACT = "tesseract"
    GOOGLE_VISION = "google_vision"


# Request Schemas
class VerificationCreateRequest(BaseModel):
    """Create verification request (multipart form data)"""
    meter_id: str
    ocr_reading: Optional[Decimal] = Field(None, ge=0, le=100000)
    ocr_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    # image: File - handled separately in FastAPI endpoint


# Response Schemas
class FraudDetectionResult(BaseModel):
    """Fraud detection analysis result"""
    fraud_score: Decimal = Field(..., ge=0, le=1)
    flags: List[str] = []
    recommendation: str  # 'PROCEED', 'REVIEW', 'BLOCK'


class VerificationResponse(BaseModel):
    """Verification result response"""
    id: str
    user_id: str
    meter_id: str
    reading_value: Decimal
    previous_reading: Optional[Decimal]
    consumption_kwh: Optional[Decimal]
    image_ipfs_hash: str
    ocr_engine: OCREngine
    confidence: Decimal = Field(..., ge=0, le=1)
    raw_ocr_text: Optional[str]
    fraud_score: Decimal = Field(..., ge=0, le=1)
    fraud_flags: Optional[dict]
    utility_reading: Optional[Decimal]
    utility_api_response: Optional[dict]
    status: VerificationStatus
    hcs_topic_id: str
    hcs_sequence_number: int
    hcs_timestamp: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class VerificationListResponse(BaseModel):
    """List of verifications response"""
    verifications: List[VerificationResponse]
    total: int


class VerificationSummary(BaseModel):
    """Simplified verification data for lists"""
    id: str
    reading_value: Decimal
    confidence: Decimal
    status: VerificationStatus
    created_at: datetime

    class Config:
        from_attributes = True
