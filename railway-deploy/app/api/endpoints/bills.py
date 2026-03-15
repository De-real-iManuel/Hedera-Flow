"""
Bill Management Endpoints
View and manage electricity bills
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from uuid import UUID
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.bills import BillResponse, BillBreakdown, BillListResponse, Currency
from app.models.user import User
from app.models.bill import Bill
from app.models.meter import Meter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[BillResponse])
async def list_bills(
    meter_id: Optional[str] = Query(None, description="Filter by meter ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of bills to return"),
    offset: int = Query(0, ge=0, description="Number of bills to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all bills for the authenticated user
    
    Args:
        meter_id: Optional filter by meter ID
        status: Optional filter by status (pending, paid, disputed, refunded)
        limit: Maximum number of bills to return
        offset: Number of bills to skip (for pagination)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of BillResponse objects
    """
    try:
        query = db.query(Bill).filter(Bill.user_id == current_user.id)
        
        # Apply filters
        if meter_id:
            try:
                meter_uuid = UUID(meter_id)
                # Verify meter belongs to user
                meter = db.query(Meter).filter(
                    Meter.id == meter_uuid,
                    Meter.user_id == current_user.id
                ).first()
                if not meter:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Meter not found"
                    )
                query = query.filter(Bill.meter_id == meter_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid meter ID format"
                )
        
        if status:
            if status not in ['pending', 'paid', 'disputed', 'refunded']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status. Must be one of: pending, paid, disputed, refunded"
                )
            query = query.filter(Bill.status == status)
        
        # Order by created_at descending and apply pagination
        bills = query.order_by(Bill.created_at.desc()).offset(offset).limit(limit).all()
        
        return [
            BillResponse(
                id=str(bill.id),
                user_id=str(bill.user_id),
                meter_id=str(bill.meter_id),
                verification_id=str(bill.verification_id) if bill.verification_id else None,
                consumption_kwh=bill.consumption_kwh,
                base_charge=bill.base_charge,
                taxes=bill.taxes,
                subsidies=bill.subsidies,
                total_fiat=bill.total_fiat,
                currency=Currency(bill.currency),
                tariff_id=str(bill.tariff_id) if bill.tariff_id else None,
                tariff_snapshot=bill.tariff_snapshot,
                amount_hbar=bill.amount_hbar,
                exchange_rate=bill.exchange_rate,
                exchange_rate_timestamp=bill.exchange_rate_timestamp,
                status=bill.status,
                hedera_tx_id=bill.hedera_tx_id,
                hedera_consensus_timestamp=bill.hedera_consensus_timestamp,
                hcs_topic_id=bill.hcs_topic_id,
                hcs_sequence_number=bill.hcs_sequence_number,
                created_at=bill.created_at,
                paid_at=bill.paid_at
            )
            for bill in bills
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing bills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bills"
        )


@router.get("/{bill_id}", response_model=BillResponse)
async def get_bill(
    bill_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific bill
    
    Args:
        bill_id: UUID of the bill
        current_user: Authenticated user
        db: Database session
        
    Returns:
        BillResponse with bill details
        
    Raises:
        HTTPException 404: Bill not found or doesn't belong to user
    """
    try:
        bill_uuid = UUID(bill_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bill ID format"
        )
    
    bill = db.query(Bill).filter(
        Bill.id == bill_uuid,
        Bill.user_id == current_user.id
    ).first()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )
    
    return BillResponse(
        id=str(bill.id),
        user_id=str(bill.user_id),
        meter_id=str(bill.meter_id),
        verification_id=str(bill.verification_id) if bill.verification_id else None,
        consumption_kwh=bill.consumption_kwh,
        base_charge=bill.base_charge,
        taxes=bill.taxes,
        subsidies=bill.subsidies,
        total_fiat=bill.total_fiat,
        currency=Currency(bill.currency),
        tariff_id=str(bill.tariff_id) if bill.tariff_id else None,
        tariff_snapshot=bill.tariff_snapshot,
        amount_hbar=bill.amount_hbar,
        exchange_rate=bill.exchange_rate,
        exchange_rate_timestamp=bill.exchange_rate_timestamp,
        status=bill.status,
        hedera_tx_id=bill.hedera_tx_id,
        hedera_consensus_timestamp=bill.hedera_consensus_timestamp,
        hcs_topic_id=bill.hcs_topic_id,
        hcs_sequence_number=bill.hcs_sequence_number,
        created_at=bill.created_at,
        paid_at=bill.paid_at
    )


@router.get("/{bill_id}/breakdown", response_model=BillBreakdown)
async def get_bill_breakdown(
    bill_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get itemized breakdown of a bill
    
    Args:
        bill_id: UUID of the bill
        current_user: Authenticated user
        db: Database session
        
    Returns:
        BillBreakdown with itemized charges
        
    Raises:
        HTTPException 404: Bill not found
    """
    try:
        bill_uuid = UUID(bill_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bill ID format"
        )
    
    bill = db.query(Bill).filter(
        Bill.id == bill_uuid,
        Bill.user_id == current_user.id
    ).first()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )
    
    # Extract rate structure from tariff snapshot if available
    rate_structure_type = "flat"  # Default
    rate_details = None
    
    if bill.tariff_snapshot:
        rate_structure_type = bill.tariff_snapshot.get("rate_structure_type", "flat")
        rate_details = bill.tariff_snapshot.get("rate_details")
    
    return BillBreakdown(
        consumption_kwh=bill.consumption_kwh,
        base_charge=bill.base_charge,
        taxes=bill.taxes,
        subsidies=bill.subsidies,
        total_fiat=bill.total_fiat,
        currency=Currency(bill.currency),
        rate_structure_type=rate_structure_type,
        rate_details=rate_details
    )
