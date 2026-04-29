"""
Dispute Management Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging
import os

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.bill import Bill
from app.models.dispute import Dispute
from app.schemas.disputes import (
    DisputeCreateRequest,
    DisputeResolveRequest,
    DisputeResponse,
    DisputeResolveResponse,
    DisputeStatus,
    DisputeReason,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_response(d: Dispute) -> DisputeResponse:
    return DisputeResponse(
        id=str(d.id),
        dispute_id=d.dispute_id,
        user_id=str(d.user_id),
        bill_id=str(d.bill_id),
        reason=DisputeReason(d.reason),
        description=d.description,
        evidence_ipfs_hashes=d.evidence_ipfs_hashes or [],
        escrow_amount_hbar=d.escrow_amount_hbar or 0,
        escrow_amount_fiat=d.escrow_amount_fiat or 0,
        escrow_currency=d.escrow_currency or "USD",
        escrow_tx_id=d.escrow_tx_id or "",
        status=DisputeStatus(d.status),
        resolution_notes=d.resolution_notes,
        resolved_by=str(d.resolved_by) if d.resolved_by else None,
        resolved_at=d.resolved_at,
        hcs_topic_id=d.hcs_topic_id or "",
        hcs_sequence_number=d.hcs_sequence_number or 0,
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


def _generate_dispute_id(db: Session, currency: str) -> str:
    from datetime import datetime
    year = datetime.utcnow().year
    count = db.query(Dispute).count() + 1
    return f"DISP-{currency}-{year}-{count:04d}"


@router.post("", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
async def create_dispute(
    request: DisputeCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Open a dispute for a bill.
    - Marks the bill as 'disputed'
    - Creates a dispute record
    - Logs to HCS
    """
    try:
        bill_uuid = UUID(request.bill_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bill ID format")

    bill = db.query(Bill).filter(
        Bill.id == bill_uuid,
        Bill.user_id == current_user.id,
    ).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    if bill.status == "disputed":
        raise HTTPException(status_code=400, detail="Bill already has an open dispute")

    if bill.status == "paid":
        raise HTTPException(status_code=400, detail="Cannot dispute a paid bill")

    # Generate dispute ID
    dispute_id = _generate_dispute_id(db, bill.currency)

    # Escrow = bill amount (held until resolved)
    dispute = Dispute(
        dispute_id=dispute_id,
        user_id=current_user.id,
        bill_id=bill.id,
        reason=request.reason.value,
        description=request.description,
        evidence_ipfs_hashes=[],
        escrow_amount_fiat=bill.total_fiat,
        escrow_amount_hbar=bill.amount_hbar,
        escrow_currency=bill.currency,
        escrow_tx_id="",
        status="pending",
    )

    # Mark bill as disputed
    bill.status = "disputed"

    db.add(dispute)

    # Log to HCS
    try:
        from app.services.hedera_service import get_hedera_service
        hcs_topic = os.getenv("HEDERA_TOPIC_EU", "0.0.5078302")
        hedera_svc = get_hedera_service()
        hcs_result = hedera_svc.log_to_hcs(
            topic_id=hcs_topic,
            payload={
                "event": "dispute_created",
                "dispute_id": dispute_id,
                "bill_id": str(bill.id),
                "reason": request.reason.value,
                "user_id": str(current_user.id),
            },
        )
        dispute.hcs_topic_id = hcs_result.get("topic_id", hcs_topic)
        dispute.hcs_sequence_number = hcs_result.get("sequence_number")
    except Exception as e:
        logger.warning(f"HCS logging failed for dispute (non-fatal): {e}")

    db.commit()
    db.refresh(dispute)

    logger.info(f"Dispute created: {dispute_id} for bill {bill.id} by {current_user.email}")
    return _to_response(dispute)


@router.get("", response_model=List[DisputeResponse])
async def list_disputes(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all disputes for the authenticated user."""
    query = db.query(Dispute).filter(Dispute.user_id == current_user.id)

    if status_filter:
        valid = [s.value for s in DisputeStatus]
        if status_filter not in valid:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid}")
        query = query.filter(Dispute.status == status_filter)

    disputes = query.order_by(Dispute.created_at.desc()).offset(offset).limit(limit).all()
    return [_to_response(d) for d in disputes]


@router.get("/{dispute_id}", response_model=DisputeResponse)
async def get_dispute(
    dispute_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific dispute by ID (DISP-XX-YYYY-NNN or UUID)."""
    try:
        uuid_val = UUID(dispute_id)
        dispute = db.query(Dispute).filter(
            Dispute.id == uuid_val,
            Dispute.user_id == current_user.id,
        ).first()
    except ValueError:
        dispute = db.query(Dispute).filter(
            Dispute.dispute_id == dispute_id,
            Dispute.user_id == current_user.id,
        ).first()

    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    return _to_response(dispute)


@router.post("/{dispute_id}/cancel", response_model=DisputeResponse)
async def cancel_dispute(
    dispute_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel an open dispute (user can cancel their own pending disputes)."""
    try:
        uuid_val = UUID(dispute_id)
        dispute = db.query(Dispute).filter(
            Dispute.id == uuid_val,
            Dispute.user_id == current_user.id,
        ).first()
    except ValueError:
        dispute = db.query(Dispute).filter(
            Dispute.dispute_id == dispute_id,
            Dispute.user_id == current_user.id,
        ).first()

    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    if dispute.status not in ("pending", "under_review"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel dispute in status: {dispute.status}")

    dispute.status = "cancelled"

    # Revert bill back to pending
    bill = db.query(Bill).filter(Bill.id == dispute.bill_id).first()
    if bill and bill.status == "disputed":
        bill.status = "pending"

    db.commit()
    db.refresh(dispute)
    return _to_response(dispute)


@router.post("/{dispute_id}/resolve", response_model=DisputeResolveResponse)
async def resolve_dispute(
    dispute_id: str,
    request: DisputeResolveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Resolve a dispute (admin only).
    winner: 'user' → bill refunded, 'utility' → bill marked paid.
    """
    # Admin check — compare against ADMIN_EMAIL env var
    admin_email = os.getenv("ADMIN_EMAIL", "")
    if not admin_email or current_user.email != admin_email:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        uuid_val = UUID(dispute_id)
        dispute = db.query(Dispute).filter(Dispute.id == uuid_val).first()
    except ValueError:
        dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()

    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    if dispute.status in ("resolved_user", "resolved_utility", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Dispute already closed: {dispute.status}")

    from datetime import datetime

    winner = request.winner
    new_status = "resolved_user" if winner == "user" else "resolved_utility"

    dispute.status = new_status
    dispute.resolution_notes = request.resolution_notes
    dispute.resolved_by = current_user.id
    dispute.resolved_at = datetime.utcnow()

    # Update bill status based on winner
    bill = db.query(Bill).filter(Bill.id == dispute.bill_id).first()
    if bill:
        bill.status = "refunded" if winner == "user" else "paid"

    db.commit()
    db.refresh(dispute)

    logger.info(f"Dispute {dispute.dispute_id} resolved: winner={winner} by admin {current_user.email}")

    return DisputeResolveResponse(
        dispute=_to_response(dispute),
        message="Dispute resolved successfully",
        escrow_released_to=winner,
        release_tx_id=dispute.escrow_tx_id or "N/A",
    )
