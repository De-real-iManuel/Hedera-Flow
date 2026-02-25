"""
Payment Schemas
Pydantic models for payment-related API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from .bills import Currency


# Request Schemas
class PaymentPrepareRequest(BaseModel):
    """Prepare payment request"""
    bill_id: str


class PaymentConfirmRequest(BaseModel):
    """Confirm payment request"""
    bill_id: str
    hedera_tx_id: str = Field(..., pattern=r"^0\.0\.\d+@\d+\.\d+$")


# Response Schemas
class TransactionDetails(BaseModel):
    """Hedera transaction details for payment"""
    from_account: str = Field(..., alias="from")
    to_account: str = Field(..., alias="to")
    amount_hbar: Decimal
    memo: str

    class Config:
        populate_by_name = True


class ExchangeRateInfo(BaseModel):
    """Exchange rate information"""
    currency: Currency
    hbar_price: Decimal = Field(..., description="Price of 1 HBAR in fiat currency")
    source: str  # 'coingecko', 'coinmarketcap'
    fetched_at: datetime
    expires_at: datetime  # 5 minutes from fetched_at


class PaymentPrepareResponse(BaseModel):
    """Payment preparation response"""
    bill: dict  # Bill details
    transaction: TransactionDetails
    exchange_rate: ExchangeRateInfo
    minimum_hbar: Decimal = Field(..., description="Minimum HBAR amount required")


class PaymentReceipt(BaseModel):
    """Payment receipt data"""
    id: str
    bill_id: str
    amount_hbar: Decimal
    amount_fiat: Decimal
    currency: Currency
    exchange_rate: Decimal
    hedera_tx_id: str
    consensus_timestamp: datetime
    receipt_url: str  # PDF download URL
    created_at: datetime


class PaymentConfirmResponse(BaseModel):
    """Payment confirmation response"""
    payment: PaymentReceipt
    message: str = "Payment confirmed successfully"


class ExchangeRateResponse(BaseModel):
    """Exchange rate query response"""
    currency: Currency
    hbar_price: Decimal = Field(..., description="Price of 1 HBAR in fiat currency")
    source: str
    fetched_at: datetime
    cache_expires_in_seconds: int


class InsufficientBalanceResponse(BaseModel):
    """Response when user has insufficient HBAR balance"""
    error: str = "Insufficient HBAR balance"
    required_hbar: Decimal
    current_balance: Decimal
    deficit_hbar: Decimal
    top_up_instructions: dict  # Links to exchanges, QR code, etc.
