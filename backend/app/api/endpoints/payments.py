"""
Payment Endpoints
HBAR payment processing and confirmation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.payments import (
    PaymentPrepareRequest,
    PaymentPrepareResponse,
    PaymentConfirmRequest,
    PaymentConfirmResponse,
    TransactionDetails,
    ExchangeRateInfo,
    PaymentReceipt
)
from app.schemas.bills import Currency
from app.models.user import User
from app.models.bill import Bill

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/prepare", response_model=PaymentPrepareResponse)
async def prepare_payment(
    request: PaymentPrepareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Prepare a payment for a bill
    
    This endpoint:
    1. Validates the bill exists and belongs to the user
    2. Fetches current HBAR exchange rate
    3. Calculates HBAR amount needed
    4. Returns transaction details for user to sign
    
    Args:
        request: Payment preparation request with bill_id
        current_user: Authenticated user
        db: Database session
        
    Returns:
        PaymentPrepareResponse with transaction details and exchange rate
        
    Raises:
        HTTPException 404: Bill not found
        HTTPException 400: Bill already paid or invalid status
    """
    try:
        bill_uuid = UUID(request.bill_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bill ID format"
        )
    
    # Get bill
    bill = db.query(Bill).filter(
        Bill.id == bill_uuid,
        Bill.user_id == current_user.id
    ).first()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )
    
    if bill.status == 'paid':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bill already paid"
        )
    
    # TODO: Fetch real exchange rate from CoinGecko/CoinMarketCap
    # For now, use mock rate
    mock_hbar_price = Decimal("0.05")  # $0.05 per HBAR
    
    # Calculate HBAR amount needed
    amount_hbar = bill.total_fiat / mock_hbar_price
    
    # Create exchange rate info
    now = datetime.utcnow()
    exchange_rate = ExchangeRateInfo(
        currency=Currency(bill.currency),
        hbar_price=mock_hbar_price,
        source="mock",  # TODO: Use real source
        fetched_at=now,
        expires_at=now + timedelta(minutes=5)
    )
    
    # Create transaction details
    # TODO: Get treasury account from config
    treasury_account = "0.0.7942957"  # Mock treasury account
    
    transaction = TransactionDetails(
        **{
            "from": current_user.hedera_account_id or "0.0.0",
            "to": treasury_account,
            "amount_hbar": amount_hbar,
            "memo": f"Bill payment: {bill.id}"
        }
    )
    
    # Return preparation response
    return PaymentPrepareResponse(
        bill={
            "id": str(bill.id),
            "total_fiat": float(bill.total_fiat),
            "currency": bill.currency,
            "consumption_kwh": float(bill.consumption_kwh)
        },
        transaction=transaction,
        exchange_rate=exchange_rate,
        minimum_hbar=amount_hbar
    )


@router.post("/confirm", response_model=PaymentConfirmResponse)
async def confirm_payment(
    request: PaymentConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm a payment after Hedera transaction is submitted
    
    This endpoint:
    1. Validates the bill and transaction ID
    2. Verifies transaction on Hedera network (TODO)
    3. Updates bill status to 'paid'
    4. Returns payment receipt
    
    Args:
        request: Payment confirmation with bill_id and hedera_tx_id
        current_user: Authenticated user
        db: Database session
        
    Returns:
        PaymentConfirmResponse with receipt
        
    Raises:
        HTTPException 404: Bill not found
        HTTPException 400: Invalid transaction or bill already paid
    """
    try:
        bill_uuid = UUID(request.bill_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bill ID format"
        )
    
    # Get bill
    bill = db.query(Bill).filter(
        Bill.id == bill_uuid,
        Bill.user_id == current_user.id
    ).first()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )
    
    if bill.status == 'paid':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bill already paid"
        )
    
    # TODO: Verify transaction on Hedera network using Mirror Node API
    # For now, accept the transaction ID
    
    # TODO: Get real exchange rate used
    mock_exchange_rate = Decimal("0.05")
    amount_hbar = bill.total_fiat / mock_exchange_rate
    
    # Update bill
    bill.status = 'paid'
    bill.hedera_tx_id = request.hedera_tx_id
    bill.amount_hbar = amount_hbar
    bill.exchange_rate = mock_exchange_rate
    bill.exchange_rate_timestamp = datetime.utcnow()
    bill.hedera_consensus_timestamp = datetime.utcnow()
    bill.paid_at = datetime.utcnow()
    
    db.commit()
    db.refresh(bill)
    
    logger.info(f"Payment confirmed for bill {bill.id}, tx: {request.hedera_tx_id}")
    
    # Create receipt
    receipt = PaymentReceipt(
        id=str(bill.id),
        bill_id=str(bill.id),
        amount_hbar=amount_hbar,
        amount_fiat=bill.total_fiat,
        currency=Currency(bill.currency),
        exchange_rate=mock_exchange_rate,
        hedera_tx_id=request.hedera_tx_id,
        consensus_timestamp=bill.hedera_consensus_timestamp,
        receipt_url=f"/api/payments/{bill.id}/receipt",  # TODO: Generate PDF
        created_at=bill.paid_at
    )
    
    return PaymentConfirmResponse(
        payment=receipt,
        message="Payment confirmed successfully"
    )


@router.get("/{payment_id}", response_model=PaymentReceipt)
async def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment details (same as bill for now since payment info is in bill)
    
    Args:
        payment_id: UUID of the payment/bill
        current_user: Authenticated user
        db: Database session
        
    Returns:
        PaymentReceipt with payment details
    """
    try:
        bill_uuid = UUID(payment_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment ID format"
        )
    
    bill = db.query(Bill).filter(
        Bill.id == bill_uuid,
        Bill.user_id == current_user.id,
        Bill.status == 'paid'
    ).first()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return PaymentReceipt(
        id=str(bill.id),
        bill_id=str(bill.id),
        amount_hbar=bill.amount_hbar or Decimal("0"),
        amount_fiat=bill.total_fiat,
        currency=Currency(bill.currency),
        exchange_rate=bill.exchange_rate or Decimal("0"),
        hedera_tx_id=bill.hedera_tx_id or "",
        consensus_timestamp=bill.hedera_consensus_timestamp or datetime.utcnow(),
        receipt_url=f"/api/payments/{bill.id}/receipt",
        created_at=bill.paid_at or bill.created_at
    )


@router.get("/{payment_id}/receipt", response_model=PaymentReceipt)
async def get_payment_receipt(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment receipt (same as get_payment for now)
    
    TODO: Generate PDF receipt
    """
    return await get_payment(payment_id, current_user, db)


@router.get("", response_model=List[PaymentReceipt])
async def list_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all payments (paid bills) for the authenticated user
    
    Returns:
        List of PaymentReceipt objects
    """
    bills = db.query(Bill).filter(
        Bill.user_id == current_user.id,
        Bill.status == 'paid'
    ).order_by(Bill.paid_at.desc()).all()
    
    return [
        PaymentReceipt(
            id=str(bill.id),
            bill_id=str(bill.id),
            amount_hbar=bill.amount_hbar or Decimal("0"),
            amount_fiat=bill.total_fiat,
            currency=Currency(bill.currency),
            exchange_rate=bill.exchange_rate or Decimal("0"),
            hedera_tx_id=bill.hedera_tx_id or "",
            consensus_timestamp=bill.hedera_consensus_timestamp or datetime.utcnow(),
            receipt_url=f"/api/payments/{bill.id}/receipt",
            created_at=bill.paid_at or bill.created_at
        )
        for bill in bills
    ]
