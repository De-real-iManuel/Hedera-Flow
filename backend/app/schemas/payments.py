"""
Payment Schemas
Pydantic models for payment-related API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal
from .bills import Currency

# Type definitions
PaymentMethod = Literal["hbar", "usdc_hedera", "usdc_ethereum"]
PaymentNetwork = Literal["hedera", "ethereum"]


# Request Schemas
class PaymentPrepareRequest(BaseModel):
    """Prepare payment request"""
    bill_id: str
    payment_method: PaymentMethod = "hbar"  # Default to HBAR for backward compatibility


class PaymentConfirmRequest(BaseModel):
    """Confirm payment request"""
    bill_id: str
    hedera_tx_id: str = Field(..., pattern=r"^0\.0\.\d+@\d+\.\d+$")


# Response Schemas
class TransactionDetails(BaseModel):
    """Hedera transaction details for HBAR payment"""
    from_account: str = Field(..., alias="from")
    to_account: str = Field(..., alias="to")
    amount_hbar: Decimal
    memo: str

    class Config:
        populate_by_name = True


class USDCTransactionDetails(BaseModel):
    """USDC transaction details for payment"""
    from_account: str = Field(..., alias="from")
    to_account: str = Field(..., alias="to")
    amount_usdc: Decimal
    token_id: str  # Token contract address (Ethereum) or token ID (Hedera)
    network: PaymentNetwork
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
    payment_method: PaymentMethod
    transaction: Optional[TransactionDetails] = None  # For HBAR payments
    usdc_transaction: Optional[USDCTransactionDetails] = None  # For USDC payments
    exchange_rate: Optional[ExchangeRateInfo] = None  # For HBAR payments
    minimum_hbar: Optional[Decimal] = Field(None, description="Minimum HBAR amount required (for HBAR payments)")
    minimum_usdc: Optional[Decimal] = Field(None, description="Minimum USDC amount required (for USDC payments)")


class PaymentReceipt(BaseModel):
    """Payment receipt data"""
    id: str
    bill_id: str
    payment_method: PaymentMethod = "hbar"
    amount_hbar: Optional[Decimal] = None
    amount_usdc: Optional[Decimal] = None
    amount_fiat: Decimal
    currency: Currency
    exchange_rate: Optional[Decimal] = None  # For HBAR payments
    hedera_tx_id: Optional[str] = None
    ethereum_tx_hash: Optional[str] = None
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
