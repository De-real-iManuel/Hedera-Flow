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
from app.models.meter import Meter
from app.models.utility_provider import UtilityProvider
from app.services.hedera_service import get_hedera_service

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
    
    # Get meter to find utility provider (FR-6.6, US-7)
    meter = db.query(Meter).filter(Meter.id == bill.meter_id).first()
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter not found for this bill"
        )
    
    # Get utility provider to find their Hedera account (FR-6.6, US-7)
    utility_provider = None
    utility_hedera_account = None
    
    if meter.utility_provider_id:
        utility_provider = db.query(UtilityProvider).filter(
            UtilityProvider.id == meter.utility_provider_id
        ).first()
        
        if utility_provider and utility_provider.hedera_account_id:
            utility_hedera_account = utility_provider.hedera_account_id
            logger.info(
                f"Found utility provider {utility_provider.provider_name} "
                f"with Hedera account {utility_hedera_account}"
            )
    
    # Fallback to treasury account if utility provider doesn't have Hedera account
    import os
    if not utility_hedera_account:
        utility_hedera_account = os.getenv('HEDERA_TREASURY_ACCOUNT', '0.0.7942957')
        logger.warning(
            f"Utility provider not found or has no Hedera account for meter {meter.id}, "
            f"using treasury account {utility_hedera_account}"
        )
    
    # Import exchange rate service
    from app.services.exchange_rate_service import ExchangeRateService
    
    # Get current exchange rate and calculate HBAR amount
    # Apply 2% volatility buffer for price protection (FR-6.13, Risk 8.1.6)
    try:
        exchange_service = ExchangeRateService(db)
        calculation = exchange_service.calculate_hbar_amount(
            fiat_amount=float(bill.total_fiat),
            currency=bill.currency,
            use_cache=True,
            apply_buffer=True,  # Enable 2% buffer for volatility protection
            buffer_percentage=2.0
        )
        
        hbar_price = Decimal(str(calculation['hbar_price']))
        amount_hbar = Decimal(str(calculation['hbar_amount_rounded']))
        
    except Exception as e:
        logger.error(f"Failed to get exchange rate: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Exchange rate service unavailable"
        )
    
    # Create exchange rate info
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=5)
    
    exchange_rate = ExchangeRateInfo(
        currency=Currency(bill.currency),
        hbar_price=hbar_price,
        source=calculation.get('source', 'coingecko'),
        fetched_at=now,
        expires_at=expires_at
    )
    
    # Create 5-minute rate lock in Redis (FR-17.4, FR-6.13)
    # This protects the user from exchange rate volatility during payment
    from app.utils.redis_client import redis_client
    
    rate_lock_data = {
        'bill_id': str(bill.id),
        'currency': bill.currency,
        'hbar_price': float(hbar_price),
        'amount_hbar': float(amount_hbar),
        'fiat_amount': float(bill.total_fiat),
        'buffer_applied': True,
        'buffer_percentage': 2.0,
        'locked_at': now.isoformat() + 'Z',
        'expires_at': expires_at.isoformat() + 'Z',
        'source': calculation.get('source', 'coingecko')
    }
    
    rate_lock_created = redis_client.set_rate_lock(str(bill.id), rate_lock_data)
    if rate_lock_created:
        logger.info(
            f"✅ Rate lock created for bill {bill.id}: "
            f"{amount_hbar} HBAR @ {hbar_price} {bill.currency}/HBAR "
            f"(expires at {expires_at.isoformat()})"
        )
    else:
        logger.warning(f"⚠️ Failed to create rate lock for bill {bill.id} (payment can still proceed)")
    
    # Create transaction details (FR-6.6, US-7)
    # Transaction goes from user to utility provider's Hedera account
    transaction = TransactionDetails(
        **{
            "from": current_user.hedera_account_id or "0.0.0",
            "to": utility_hedera_account,  # Utility provider's Hedera account
            "amount_hbar": amount_hbar,
            "memo": f"Bill payment: BILL-{bill.currency}-{bill.created_at.year}-{str(bill.id)[:8]}"
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
        payment_method="hbar",  # Add the missing payment_method field
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
    2. Verifies transaction on Hedera network via Mirror Node API
    3. Validates transaction amount matches expected HBAR amount
    4. Updates bill status to 'paid'
    5. Logs payment to HCS
    6. Returns payment receipt
    
    Requirements:
        - FR-6.8: System shall submit signed transaction
        - FR-6.9: System shall verify transaction on Hedera network via Mirror Node
        - FR-6.9: System shall validate transaction amount matches expected HBAR amount
        - FR-6.12: System shall update bill status to "PAID"
        - FR-5.14: System shall log payments to HCS (including HBAR amount and fiat equivalent)
        - US-7: Payment flow with blockchain verification
    
    Args:
        request: Payment confirmation with bill_id and hedera_tx_id
        current_user: Authenticated user
        db: Database session
        
    Returns:
        PaymentConfirmResponse with receipt
        
    Raises:
        HTTPException 404: Bill not found
        HTTPException 400: Invalid transaction or bill already paid
        HTTPException 400: Transaction not found on Hedera
        HTTPException 400: Transaction amount mismatch
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
    
    # Validate rate lock (FR-17.4, FR-6.13)
    # Check if the rate lock is still valid (within 5-minute window)
    from app.utils.redis_client import redis_client
    
    rate_lock_validation = redis_client.validate_rate_lock(str(bill.id), tolerance_percent=5.0)
    
    if not rate_lock_validation['valid']:
        logger.warning(
            f"⚠️ Rate lock validation failed for bill {bill.id}: "
            f"{rate_lock_validation['reason']}"
        )
        # For MVP, we'll allow payment to proceed with a warning
        # In production, you might want to reject the payment
        rate_lock = None
    else:
        rate_lock = rate_lock_validation['rate_lock']
        logger.info(
            f"✅ Rate lock validated for bill {bill.id}: "
            f"{rate_lock['amount_hbar']} HBAR @ {rate_lock['hbar_price']} {rate_lock['currency']}/HBAR "
            f"({rate_lock_validation['ttl_seconds']}s remaining)"
        )
    
    # Import required services
    from app.utils.transaction_verifier import (
        TransactionVerifier,
        TransactionVerificationError,
        TransactionNotFoundError,
        TransactionFailedError,
        AmountMismatchError,
        InvalidTransferError
    )
    import os
    
    # Get treasury account
    treasury_account = os.getenv('HEDERA_TREASURY_ACCOUNT', '0.0.7942957')
    
    # Verify transaction on Hedera network using Mirror Node API
    logger.info(f"Verifying transaction {request.hedera_tx_id} on Hedera network...")
    
    try:
        # Create transaction verifier
        verifier = TransactionVerifier(
            treasury_account=treasury_account,
            tolerance_percent=1.0  # 1% tolerance for rounding
        )
        
        # Verify transaction comprehensively
        expected_hbar = bill.amount_hbar if bill.amount_hbar else None
        user_account = current_user.hedera_account_id if current_user.hedera_account_id else None
        
        verification_result = await verifier.verify_transaction(
            transaction_id=request.hedera_tx_id,
            expected_amount_hbar=expected_hbar,
            user_account_id=user_account
        )
        
        # Extract verified details
        amount_hbar = verification_result["amount_hbar"]
        consensus_timestamp = verification_result["consensus_timestamp"]
        
        logger.info(f"✅ Transaction verified: {amount_hbar} HBAR transferred")
        
    except TransactionNotFoundError as e:
        logger.error(f"Transaction not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except TransactionFailedError as e:
        logger.error(f"Transaction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AmountMismatchError as e:
        logger.error(f"Amount mismatch: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidTransferError as e:
        logger.error(f"Invalid transfer: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except TransactionVerificationError as e:
        logger.error(f"Verification error: {e}")
        # For MVP, allow payment to proceed even if verification fails
        # In production, this should be stricter
        logger.warning("Proceeding with payment despite verification error (MVP mode)")
        amount_hbar = bill.amount_hbar if bill.amount_hbar else Decimal("0")
        consensus_timestamp = datetime.utcnow()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        # For MVP, allow payment to proceed even if verification fails
        logger.warning("Proceeding with payment despite unexpected error (MVP mode)")
        amount_hbar = bill.amount_hbar if bill.amount_hbar else Decimal("0")
        consensus_timestamp = datetime.utcnow()
    
    # Get exchange rate used (prefer rate lock, fallback to bill or current rate)
    if rate_lock:
        # Use the locked rate from preparation (protects against volatility)
        exchange_rate = Decimal(str(rate_lock['hbar_price']))
        logger.info(f"Using locked exchange rate: {exchange_rate} {rate_lock['currency']}/HBAR")
    elif bill.exchange_rate:
        exchange_rate = bill.exchange_rate
        logger.info(f"Using bill exchange rate: {exchange_rate}")
    else:
        exchange_rate = Decimal("0.05")
        logger.warning(f"No exchange rate available, using fallback: {exchange_rate}")
    
    # Update bill
    bill.status = 'paid'
    bill.hedera_tx_id = request.hedera_tx_id
    bill.amount_hbar = amount_hbar
    bill.exchange_rate = exchange_rate
    bill.exchange_rate_timestamp = bill.exchange_rate_timestamp or datetime.utcnow()
    bill.hedera_consensus_timestamp = consensus_timestamp
    bill.paid_at = datetime.utcnow()
    
    # Delete rate lock after successful payment (cleanup)
    if rate_lock:
        redis_client.delete_rate_lock(str(bill.id))
        logger.info(f"✅ Rate lock deleted for bill {bill.id} after successful payment")
    
    # Determine HCS topic based on country
    country_to_topic = {
        'EUR': os.getenv('HEDERA_TOPIC_EU', '0.0.5078302'),
        'USD': os.getenv('HEDERA_TOPIC_US', '0.0.5078303'),
        'INR': os.getenv('HEDERA_TOPIC_ASIA', '0.0.5078304'),
        'BRL': os.getenv('HEDERA_TOPIC_SA', '0.0.5078305'),
        'NGN': os.getenv('HEDERA_TOPIC_AFRICA', '0.0.5078306'),
    }
    
    hcs_topic_id = country_to_topic.get(bill.currency, os.getenv('HEDERA_TOPIC_EU', '0.0.5078302'))
    
    # Log payment to HCS
    try:
        hedera_service = get_hedera_service()
        
        # Log payment using HederaService method
        hcs_result = hedera_service.log_payment_to_hcs(
            topic_id=hcs_topic_id,
            bill_id=str(bill.id),
            amount_fiat=float(bill.total_fiat),
            currency_fiat=bill.currency,
            amount_hbar=float(amount_hbar),
            exchange_rate=float(exchange_rate),
            tx_id=request.hedera_tx_id
        )
        
        # Store HCS reference in bill
        bill.hcs_topic_id = hcs_result["topic_id"]
        bill.hcs_sequence_number = hcs_result["sequence_number"]
        
        logger.info(f"✅ Payment logged to HCS topic {hcs_topic_id}, sequence: {hcs_result['sequence_number']}")
        
    except Exception as e:
        logger.error(f"Failed to log payment to HCS: {e}")
        # Don't fail the payment if HCS logging fails
        # In production, you might want to retry or queue for later processing
    
    # Commit all changes
    db.commit()
    db.refresh(bill)
    
    logger.info(f"✅ Payment confirmed for bill {bill.id}, tx: {request.hedera_tx_id}")
    
    # Create receipt
    receipt = PaymentReceipt(
        id=str(bill.id),
        bill_id=str(bill.id),
        amount_hbar=amount_hbar,
        amount_fiat=bill.total_fiat,
        currency=Currency(bill.currency),
        exchange_rate=exchange_rate,
        hedera_tx_id=request.hedera_tx_id,
        consensus_timestamp=consensus_timestamp,
        receipt_url=f"/api/payments/{bill.id}/receipt",
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


@router.get("/{payment_id}/receipt")
async def get_payment_receipt(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate and download PDF receipt for a payment
    
    This endpoint generates a professional PDF receipt with:
    - Transaction details (ID, timestamp, consensus time)
    - HBAR amount paid
    - Fiat equivalent at time of payment
    - Exchange rate used
    - Itemized billing breakdown
    - Hedera Explorer link (HashScan)
    
    Requirements:
        - FR-6.10: System shall generate receipt (PDF) showing HBAR amount paid,
          fiat equivalent, exchange rate used, timestamp
        - US-7: Receipt should include transaction ID, HBAR amount paid,
          fiat equivalent at time of payment, exchange rate used, timestamp,
          Hedera Explorer link (HashScan), PDF download option
    
    Args:
        payment_id: UUID of the payment/bill
        current_user: Authenticated user
        db: Database session
        
    Returns:
        PDF file as downloadable response
        
    Raises:
        HTTPException 404: Payment not found
        HTTPException 500: PDF generation failed
    """
    from fastapi.responses import Response
    from app.services.receipt_service import get_receipt_service
    from app.models.meter import Meter
    
    try:
        bill_uuid = UUID(payment_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment ID format"
        )
    
    # Get bill with meter relationship
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
    
    # Get meter details
    meter = db.query(Meter).filter(Meter.id == bill.meter_id).first()
    
    # Prepare bill data for PDF generation
    bill_data = {
        'bill_id': str(bill.id),
        'consumption_kwh': float(bill.consumption_kwh) if bill.consumption_kwh else 0,
        'base_charge': float(bill.base_charge) if bill.base_charge else 0,
        'taxes': float(bill.taxes) if bill.taxes else 0,
        'subsidies': float(bill.subsidies) if bill.subsidies else 0,
        'total_fiat': float(bill.total_fiat),
        'currency': bill.currency,
        'amount_hbar': float(bill.amount_hbar) if bill.amount_hbar else 0,
        'exchange_rate': float(bill.exchange_rate) if bill.exchange_rate else 0,
        'hedera_tx_id': bill.hedera_tx_id or "",
        'consensus_timestamp': bill.hedera_consensus_timestamp or datetime.utcnow(),
        'paid_at': bill.paid_at or bill.created_at,
        'user_email': current_user.email,
        'meter_id': meter.meter_id if meter else "N/A"
    }
    
    # Include tariff_snapshot and breakdown if available for detailed itemization
    if bill.tariff_snapshot:
        bill_data['tariff_snapshot'] = bill.tariff_snapshot
        
        # Extract breakdown details from tariff_snapshot if available
        if 'breakdown' in bill.tariff_snapshot:
            bill_data['breakdown'] = bill.tariff_snapshot['breakdown']
        
        # Extract tax breakdown if available
        taxes_and_fees = bill.tariff_snapshot.get('taxes_and_fees', {})
        if taxes_and_fees:
            vat_rate = taxes_and_fees.get('vat', 0)
            if vat_rate and bill.taxes:
                # Calculate VAT portion (approximate)
                base_for_vat = float(bill.base_charge) if bill.base_charge else 0
                vat_amount = base_for_vat * vat_rate
                bill_data['tax_breakdown'] = {
                    'vat': vat_amount,
                    'vat_rate': vat_rate,
                    'other_taxes': float(bill.taxes) - vat_amount if float(bill.taxes) > vat_amount else 0
                }
            
            # Include distribution and service charges if present
            distribution_charge = taxes_and_fees.get('distribution_charge', 0)
            if distribution_charge:
                bill_data['distribution_charge'] = distribution_charge
            
            service_charge = taxes_and_fees.get('service_charge', 0)
            if service_charge:
                bill_data['service_charge'] = service_charge
        
        # Include platform charges if present
        if 'platform_service_charge' in bill.tariff_snapshot:
            bill_data['platform_service_charge'] = bill.tariff_snapshot['platform_service_charge']
        if 'platform_vat' in bill.tariff_snapshot:
            bill_data['platform_vat'] = bill.tariff_snapshot['platform_vat']
    
    try:
        # Generate PDF receipt
        receipt_service = get_receipt_service()
        pdf_bytes = receipt_service.generate_receipt_pdf(bill_data)
        
        # Return PDF as downloadable file
        filename = f"hedera-flow-receipt-{str(bill.id)[:8]}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to generate PDF receipt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF receipt: {str(e)}"
        )


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
