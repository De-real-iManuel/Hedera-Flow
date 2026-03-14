"""
Hedera Blockchain Schemas
Pydantic models for Hedera-related data structures
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


class HCSMessageType(str, Enum):
    """HCS message types"""
    VERIFICATION = "VERIFICATION"
    PAYMENT = "PAYMENT"
    DISPUTE_CREATED = "DISPUTE_CREATED"
    DISPUTE_RESOLVED = "DISPUTE_RESOLVED"
    PREPAID_TOKEN_ISSUED = "PREPAID_TOKEN_ISSUED"
    SMART_METER_CONSUMPTION = "SMART_METER_CONSUMPTION"


class HCSTopicRegion(str, Enum):
    """HCS topic regions"""
    EU = "EU"
    US = "US"
    ASIA = "ASIA"
    SA = "SA"
    AFRICA = "AFRICA"


# HCS Message Schemas
class VerificationLogMessage(BaseModel):
    """Verification log message for HCS"""
    type: str = "VERIFICATION"
    timestamp: int
    user_id: str  # Anonymized
    meter_id: str
    reading: Decimal
    utility_reading: Optional[Decimal]
    confidence: Decimal
    fraud_score: Decimal
    status: str  # 'VERIFIED', 'WARNING', 'DISCREPANCY'
    image_hash: str  # IPFS hash


class PaymentLogMessage(BaseModel):
    """Payment log message for HCS"""
    type: str = "PAYMENT"
    timestamp: int
    bill_id: str
    amount_fiat: Decimal
    currency_fiat: str
    amount_hbar: Decimal
    exchange_rate: Decimal
    tx_id: str
    status: str  # 'SUCCESS', 'FAILED'


class DisputeCreatedLogMessage(BaseModel):
    """Dispute created log message for HCS"""
    type: str = "DISPUTE_CREATED"
    timestamp: int
    dispute_id: str
    bill_id: str
    reason: str
    evidence_hashes: list[str]  # IPFS hashes
    escrow_amount_hbar: Decimal
    status: str


class DisputeResolvedLogMessage(BaseModel):
    """Dispute resolved log message for HCS"""
    type: str = "DISPUTE_RESOLVED"
    timestamp: int
    dispute_id: str
    bill_id: str
    winner: str  # 'user' or 'utility'
    resolution_notes: str
    escrow_released_hbar: Decimal
    status: str


class PrepaidTokenIssuedLogMessage(BaseModel):
    """Prepaid token issuance log message for HCS"""
    type: str = "PREPAID_TOKEN_ISSUED"
    token_id: str
    user_id: str  # Anonymized
    meter_id: str
    units_purchased: float
    amount_hbar: Optional[float]
    amount_usdc: Optional[float]
    amount_fiat: float
    currency: str
    exchange_rate: float
    tariff_rate: float
    tx_id: str
    timestamp: int


class SmartMeterConsumptionLogMessage(BaseModel):
    """Smart meter consumption log message for HCS"""
    type: str = "SMART_METER_CONSUMPTION"
    meter_id: str
    consumption_kwh: float
    timestamp: int
    reading_before: Optional[float]
    reading_after: Optional[float]
    signature: str
    public_key: str
    signature_valid: bool
    token_id: Optional[str]
    units_deducted: Optional[float]
    units_remaining: Optional[float]


# Hedera Transaction Schemas
class HederaAccountInfo(BaseModel):
    """Hedera account information"""
    account_id: str = Field(..., pattern=r"^0\.0\.\d+$")
    balance_hbar: Optional[Decimal] = None
    public_key: Optional[str] = None


class HederaTransactionInfo(BaseModel):
    """Hedera transaction information"""
    transaction_id: str
    consensus_timestamp: datetime
    status: str  # 'SUCCESS', 'FAILED'
    memo: Optional[str]
    transfers: list[Dict[str, Any]]


class HCSMessageInfo(BaseModel):
    """HCS message information"""
    topic_id: str = Field(..., pattern=r"^0\.0\.\d+$")
    sequence_number: int
    consensus_timestamp: datetime
    message: str  # JSON string
    running_hash: str


class MirrorNodeQueryResponse(BaseModel):
    """Mirror Node API query response"""
    messages: list[HCSMessageInfo]
    links: Optional[Dict[str, str]] = None


# Smart Contract Schemas
class SmartContractCallRequest(BaseModel):
    """Smart contract function call request"""
    contract_id: str = Field(..., pattern=r"^0\.0\.\d+$")
    function_name: str
    parameters: Dict[str, Any]
    gas_limit: int = 150000


class SmartContractCallResponse(BaseModel):
    """Smart contract function call response"""
    transaction_id: str
    status: str
    result: Optional[Any] = None
    gas_used: int
    consensus_timestamp: datetime
