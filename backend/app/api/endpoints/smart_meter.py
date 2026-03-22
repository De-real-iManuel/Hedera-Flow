"""
Smart Meter Endpoints
Cryptographic signature generation/verification + simulator control
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.smart_meter_service import SmartMeterService, SmartMeterError

logger = logging.getLogger(__name__)
router = APIRouter()

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class GenerateKeypairRequest(BaseModel):
    meter_id: str


class GenerateKeypairResponse(BaseModel):
    meter_id: str
    public_key: str
    algorithm: str
    created_at: str
    kms_key_id: Optional[str] = None


class SignConsumptionRequest(BaseModel):
    meter_id: str
    consumption_kwh: float = Field(..., gt=0)
    timestamp: int
    reading_before: Optional[float] = None
    reading_after: Optional[float] = None


class SignConsumptionResponse(BaseModel):
    meter_id: str
    consumption_kwh: float
    timestamp: int
    signature: str
    public_key: str
    message_hash: str
    reading_before: Optional[float] = None
    reading_after: Optional[float] = None


class ConsumeRequest(BaseModel):
    meter_id: str
    consumption_kwh: float = Field(..., gt=0)
    timestamp: int
    signature: str
    public_key: str
    reading_before: Optional[float] = None
    reading_after: Optional[float] = None


class ConsumeResponse(BaseModel):
    consumption_log_id: str
    meter_id: str
    consumption_kwh: float
    timestamp: int
    signature_valid: bool
    token_deduction: Optional[dict] = None
    units_deducted: Optional[float] = None
    units_remaining: Optional[float] = None
    hcs_topic_id: Optional[str] = None
    hcs_sequence_number: Optional[int] = None
    reading_before: Optional[float] = None
    reading_after: Optional[float] = None


class VerifySignatureRequest(BaseModel):
    meter_id: str
    consumption_kwh: float
    timestamp: int
    signature: str
    public_key: Optional[str] = None


class VerifySignatureResponse(BaseModel):
    valid: bool
    meter_id: str
    consumption_kwh: float
    timestamp: int
    message_hash: str
    algorithm: str
    error: Optional[str] = None


class SimulatorTickRequest(BaseModel):
    meter_id: str
    seconds: float = Field(5.0, gt=0, le=3600)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_meter(meter_id_str: str, current_user: User, db: Session):
    try:
        meter_uuid = UUID(meter_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid meter ID format")
    from app.models.meter import Meter
    meter = db.query(Meter).filter(Meter.id == meter_uuid, Meter.user_id == current_user.id).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found or does not belong to you")
    return meter_uuid


# ---------------------------------------------------------------------------
# Keypair
# ---------------------------------------------------------------------------

@router.post("/generate-keypair", response_model=GenerateKeypairResponse)
async def generate_keypair(
    request: GenerateKeypairRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meter_uuid = _resolve_meter(request.meter_id, current_user, db)
    svc = SmartMeterService(db)
    if svc.keypair_exists(str(meter_uuid)):
        raise HTTPException(status_code=400, detail="Keypair already exists for this meter")
    try:
        data = svc.generate_keypair(str(meter_uuid))
    except SmartMeterError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return GenerateKeypairResponse(**data)


@router.get("/public-key/{meter_id}")
async def get_public_key(
    meter_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meter_uuid = _resolve_meter(meter_id, current_user, db)
    svc = SmartMeterService(db)
    pub = svc.get_public_key(str(meter_uuid))
    if not pub:
        raise HTTPException(status_code=404, detail="No keypair found for this meter")
    return {"meter_id": meter_id, "public_key": pub, "algorithm": "ED25519"}


# ---------------------------------------------------------------------------
# Sign / Consume / Verify
# ---------------------------------------------------------------------------

@router.post("/sign", response_model=SignConsumptionResponse)
async def sign_consumption(
    request: SignConsumptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meter_uuid = _resolve_meter(request.meter_id, current_user, db)
    svc = SmartMeterService(db)
    if not svc.keypair_exists(str(meter_uuid)):
        svc.generate_keypair(str(meter_uuid))
    try:
        result = svc.sign_consumption(
            meter_id=str(meter_uuid),
            consumption_kwh=request.consumption_kwh,
            timestamp=request.timestamp,
            reading_before=request.reading_before,
            reading_after=request.reading_after,
        )
    except SmartMeterError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return SignConsumptionResponse(**result)


@router.post("/consume", response_model=ConsumeResponse)
async def log_consumption(
    request: ConsumeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meter_uuid = _resolve_meter(request.meter_id, current_user, db)
    svc = SmartMeterService(db)
    try:
        data = svc.log_consumption(
            meter_id=str(meter_uuid),
            consumption_kwh=request.consumption_kwh,
            timestamp=request.timestamp,
            signature=request.signature,
            public_key_pem=request.public_key,
            reading_before=request.reading_before,
            reading_after=request.reading_after,
        )
    except SmartMeterError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ConsumeResponse(**data)


@router.post("/verify-signature", response_model=VerifySignatureResponse)
async def verify_signature(
    request: VerifySignatureRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meter_uuid = _resolve_meter(request.meter_id, current_user, db)
    svc = SmartMeterService(db)
    try:
        result = svc.verify_signature(
            meter_id=str(meter_uuid),
            consumption_kwh=request.consumption_kwh,
            timestamp=request.timestamp,
            signature=request.signature,
            public_key_pem=request.public_key,
        )
    except SmartMeterError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return VerifySignatureResponse(**result)


# ---------------------------------------------------------------------------
# Consumption history
# ---------------------------------------------------------------------------

@router.get("/consumption-history/{meter_id}")
async def get_consumption_history(
    meter_id: str,
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meter_uuid = _resolve_meter(meter_id, current_user, db)
    from sqlalchemy import text
    rows = db.execute(text("""
        SELECT cl.id, cl.meter_id, cl.consumption_kwh, cl.timestamp,
               cl.signature_valid, cl.units_deducted, cl.units_remaining,
               cl.hcs_topic_id, cl.hcs_sequence_number,
               cl.reading_before, cl.reading_after, cl.created_at,
               pt.token_id, pt.status
        FROM consumption_logs cl
        LEFT JOIN prepaid_tokens pt ON cl.token_id = pt.id
        WHERE cl.meter_id = :m
        ORDER BY cl.created_at DESC
        LIMIT :limit
    """), {"m": str(meter_uuid), "limit": limit}).fetchall()

    logs = []
    for r in rows:
        token_deduction = None
        if r[12]:
            token_deduction = {
                "token_id": r[12], "token_status": r[13],
                "units_deducted": float(r[5]) if r[5] else 0,
                "units_remaining": float(r[6]) if r[6] else 0,
            }
        logs.append(ConsumeResponse(
            consumption_log_id=str(r[0]),
            meter_id=str(r[1]),
            consumption_kwh=float(r[2]),
            timestamp=r[3],
            signature_valid=r[4],
            units_deducted=float(r[5]) if r[5] else None,
            units_remaining=float(r[6]) if r[6] else None,
            hcs_topic_id=r[7],
            hcs_sequence_number=r[8],
            reading_before=float(r[9]) if r[9] else None,
            reading_after=float(r[10]) if r[10] else None,
            token_deduction=token_deduction,
        ))
    return logs


@router.get("/consumption-logs")
async def get_consumption_logs(
    meter_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meter_uuid = _resolve_meter(meter_id, current_user, db)
    from app.models.consumption_log import ConsumptionLog
    logs = (
        db.query(ConsumptionLog)
        .filter(ConsumptionLog.meter_id == meter_uuid)
        .order_by(ConsumptionLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "logs": [
            {
                "id": str(l.id),
                "meter_id": str(l.meter_id),
                "consumption_kwh": float(l.consumption_kwh),
                "reading_before": float(l.reading_before) if l.reading_before else None,
                "reading_after": float(l.reading_after) if l.reading_after else None,
                "timestamp": l.timestamp,
                "signature": l.signature,
                "public_key": l.public_key,
                "signature_valid": l.signature_valid,
                "units_deducted": float(l.units_deducted) if l.units_deducted else None,
                "units_remaining": float(l.units_remaining) if l.units_remaining else None,
                "token_id": str(l.token_id) if l.token_id else None,
                "hcs_topic_id": l.hcs_topic_id,
                "hcs_sequence_number": l.hcs_sequence_number,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ],
        "total": len(logs),
        "meter_id": meter_id,
    }


# ---------------------------------------------------------------------------
# Simulator endpoints
# ---------------------------------------------------------------------------

@router.post("/simulator/start")
async def simulator_start(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start the in-process simulator for a meter."""
    meter_id = body.get("meter_id", "")
    meter_uuid = _resolve_meter(meter_id, current_user, db)
    svc = SmartMeterService(db)
    # Ensure keypair exists
    if not svc.keypair_exists(str(meter_uuid)):
        svc.generate_keypair(str(meter_uuid))
    state = svc.start_simulator(str(meter_uuid))
    return {"status": "started", **state}


@router.post("/simulator/stop")
async def simulator_stop(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stop the simulator for a meter."""
    meter_id = body.get("meter_id", "")
    meter_uuid = _resolve_meter(meter_id, current_user, db)
    svc = SmartMeterService(db)
    try:
        state = svc.stop_simulator(str(meter_uuid))
    except SmartMeterError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "stopped", **state}


@router.get("/simulator/status/{meter_id}")
async def simulator_status(
    meter_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current simulator state for a meter."""
    meter_uuid = _resolve_meter(meter_id, current_user, db)
    svc = SmartMeterService(db)
    return svc.get_simulator_status(str(meter_uuid))


@router.post("/simulator/tick")
async def simulator_tick(
    request: SimulatorTickRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Advance simulator clock by `seconds` and optionally auto-log if threshold crossed.
    Returns updated state. Frontend polls this to drive the UI.
    """
    meter_uuid = _resolve_meter(request.meter_id, current_user, db)
    svc = SmartMeterService(db)
    try:
        state = svc.tick_simulator(str(meter_uuid), request.seconds)
    except SmartMeterError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Auto-log when delta >= 0.1 kWh
    auto_logged = None
    delta = state["current_reading"] - state["last_logged_reading"]
    if delta >= 0.1:
        try:
            signed = svc.sign_consumption(
                meter_id=str(meter_uuid),
                consumption_kwh=round(delta, 6),
                timestamp=int(datetime.utcnow().timestamp()),
                reading_before=state["last_logged_reading"],
                reading_after=state["current_reading"],
            )
            log = svc.log_consumption(
                meter_id=str(meter_uuid),
                consumption_kwh=round(delta, 6),
                timestamp=signed["timestamp"],
                signature=signed["signature"],
                public_key_pem=signed["public_key"],
                reading_before=state["last_logged_reading"],
                reading_after=state["current_reading"],
            )
            state["last_logged_reading"] = state["current_reading"]
            state["logs_count"] = state.get("logs_count", 0) + 1
            state["last_log_at"] = datetime.utcnow().isoformat()
            auto_logged = {
                "consumption_log_id": log["consumption_log_id"],
                "consumption_kwh": log["consumption_kwh"],
                "hcs_sequence_number": log.get("hcs_sequence_number"),
            }
        except Exception as e:
            logger.warning(f"Auto-log failed during tick: {e}")

    return {"state": state, "auto_logged": auto_logged}
