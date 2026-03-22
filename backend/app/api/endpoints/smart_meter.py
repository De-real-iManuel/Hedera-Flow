"""
Smart Meter Endpoints
Cryptographic signature generation and verification for smart meter consumption data
"""
from fastapi import APIRouter, Depends, HTTPException, status
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


# Request/Response Schemas
from pydantic import BaseModel, Field


class GenerateKeypairRequest(BaseModel):
    """Request to generate ED25519 keypair for a meter"""
    meter_id: str = Field(..., description="UUID of the meter")


class GenerateKeypairResponse(BaseModel):
    """Response after generating keypair"""
    meter_id: str
    public_key: str
    algorithm: str
    created_at: str


class ConsumeRequest(BaseModel):
    """Request to log consumption with signature"""
    meter_id: str = Field(..., description="UUID of the meter")
    consumption_kwh: float = Field(..., gt=0, description="Consumption amount in kWh")
    timestamp: int = Field(..., description="Unix timestamp of consumption")
    signature: str = Field(..., description="Hex-encoded signature")
    public_key: str = Field(..., description="PEM-encoded public key")
    reading_before: Optional[float] = Field(None, description="Meter reading before consumption")
    reading_after: Optional[float] = Field(None, description="Meter reading after consumption")


class ConsumeResponse(BaseModel):
    """Response after logging consumption"""
    consumption_log_id: str
    meter_id: str
    consumption_kwh: float
    timestamp: int
    signature_valid: bool
    token_deduction: Optional[dict]
    units_deducted: Optional[float]
    units_remaining: Optional[float]
    hcs_topic_id: Optional[str]
    hcs_sequence_number: Optional[int]
    reading_before: Optional[float]
    reading_after: Optional[float]


class VerifySignatureRequest(BaseModel):
    """Request to verify consumption signature"""
    meter_id: str = Field(..., description="UUID of the meter")
    consumption_kwh: float = Field(..., description="Consumption amount in kWh")
    timestamp: int = Field(..., description="Unix timestamp of consumption")
    signature: str = Field(..., description="Hex-encoded signature to verify")
    public_key: Optional[str] = Field(None, description="PEM-encoded public key (optional)")


class VerifySignatureResponse(BaseModel):
    """Response after verifying signature"""
    valid: bool
    meter_id: str
    consumption_kwh: float
    timestamp: int
    message_hash: str
    algorithm: str
    error: Optional[str] = None


class SignConsumptionRequest(BaseModel):
    """Request to sign consumption data with meter's private key"""
    meter_id: str = Field(..., description="UUID of the meter")
    consumption_kwh: float = Field(..., gt=0, description="Consumption amount in kWh")
    timestamp: int = Field(..., description="Unix timestamp of consumption")
    reading_before: Optional[float] = Field(None)
    reading_after: Optional[float] = Field(None)


class SignConsumptionResponse(BaseModel):
    """Signed consumption data ready to submit to /consume"""
    meter_id: str
    consumption_kwh: float
    timestamp: int
    signature: str
    public_key: str
    message_hash: str
    reading_before: Optional[float] = None
    reading_after: Optional[float] = None


@router.post("/sign", response_model=SignConsumptionResponse)
async def sign_consumption(
    request: SignConsumptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sign consumption data with the meter's server-side ED25519 private key.

    The private key never leaves the server (stored AES-256 encrypted).
    Returns the signature so the frontend can immediately call /consume.

    Requirements: FR-9.4, FR-9.5
    """
    try:
        try:
            meter_uuid = UUID(request.meter_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid meter ID format")

        from app.models.meter import Meter
        meter = db.query(Meter).filter(Meter.id == meter_uuid, Meter.user_id == current_user.id).first()
        if not meter:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meter not found")

        smart_meter_service = SmartMeterService(db)

        if not smart_meter_service.keypair_exists(str(meter_uuid)):
            # Auto-generate keypair on first sign
            smart_meter_service.generate_keypair(str(meter_uuid))
            logger.info(f"Auto-generated keypair for meter {meter_uuid}")

        result = smart_meter_service.sign_consumption(
            meter_id=str(meter_uuid),
            consumption_kwh=request.consumption_kwh,
            timestamp=request.timestamp,
            reading_before=request.reading_before,
            reading_after=request.reading_after,
        )

        return SignConsumptionResponse(
            meter_id=result["meter_id"],
            consumption_kwh=result["consumption_kwh"],
            timestamp=result["timestamp"],
            signature=result["signature"],
            public_key=result["public_key"],
            message_hash=result["message_hash"],
            reading_before=result.get("reading_before"),
            reading_after=result.get("reading_after"),
        )

    except SmartMeterError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sign consumption failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/generate-keypair", response_model=GenerateKeypairResponse)
async def generate_keypair(
    request: GenerateKeypairRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate ED25519 keypair for a smart meter
    
    This endpoint:
    1. Validates the meter exists and belongs to the user
    2. Generates a new ED25519 keypair
    3. Encrypts the private key with AES-256
    4. Stores both keys in the database
    5. Returns the public key (private key never exposed)
    
    Requirements:
        - FR-9.1: System shall generate ED25519 keypair for each registered meter
        - FR-9.2: System shall store private key encrypted (AES-256)
        - FR-9.3: System shall store public key in plaintext (for verification)
        - NFR-8.2: Meter private keys shall never be exposed via API
        - Task 2.2: Smart Meter Service - Keypair Generation
    
    Args:
        request: Keypair generation request with meter_id
        current_user: Authenticated user
        db: Database session
        
    Returns:
        GenerateKeypairResponse with public key and metadata
        
    Raises:
        HTTPException 400: Invalid request data or keypair already exists
        HTTPException 404: Meter not found
        HTTPException 500: Keypair generation failed
    """
    try:
        # Validate meter_id format
        try:
            meter_uuid = UUID(request.meter_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meter ID format"
            )
        
        # Import meter model to validate ownership
        from app.models.meter import Meter
        
        # Verify meter exists and belongs to user
        meter = db.query(Meter).filter(
            Meter.id == meter_uuid,
            Meter.user_id == current_user.id
        ).first()
        
        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found or does not belong to you"
            )
        
        # Initialize smart meter service
        smart_meter_service = SmartMeterService(db)
        
        # Check if keypair already exists
        if smart_meter_service.keypair_exists(str(meter_uuid)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Keypair already exists for meter {request.meter_id}. Use the existing public key."
            )
        
        # Generate keypair
        keypair_data = smart_meter_service.generate_keypair(str(meter_uuid))
        
        logger.info(
            f"Generated keypair for meter {request.meter_id} "
            f"(user: {current_user.email})"
        )
        
        return GenerateKeypairResponse(
            meter_id=keypair_data['meter_id'],
            public_key=keypair_data['public_key'],
            algorithm=keypair_data['algorithm'],
            created_at=keypair_data['created_at']
        )
        
    except SmartMeterError as e:
        logger.error(f"Smart meter keypair generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during keypair generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate keypair: {str(e)}"
        )


@router.post("/consume", response_model=ConsumeResponse)
async def log_consumption(
    request: ConsumeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log consumption data with cryptographic signature verification
    
    This endpoint:
    1. Validates the meter exists and belongs to the user
    2. Verifies the cryptographic signature
    3. Rejects invalid signatures (fraud detection)
    4. Deducts units from prepaid tokens (FIFO)
    5. Stores consumption log in database
    6. Logs to HCS with type SMART_METER_CONSUMPTION
    
    Requirements:
        - FR-9.6: System shall verify signature before accepting consumption data
        - FR-9.7: System shall reject invalid signatures and flag as fraud
        - FR-9.8: System shall log consumption to HCS with tag SMART_METER_CONSUMPTION
        - FR-9.9: System shall include signature and verification status in HCS log
        - US-16: Smart meter consumption logging
        - Task 2.5: Consumption Logging & Token Deduction
    
    Args:
        request: Consumption request with meter_id, consumption, signature
        current_user: Authenticated user
        db: Database session
        
    Returns:
        ConsumeResponse with consumption log details and token deduction
        
    Raises:
        HTTPException 400: Invalid request data or signature verification failed
        HTTPException 404: Meter not found
        HTTPException 500: Consumption logging failed
    """
    try:
        # Validate meter_id format
        try:
            meter_uuid = UUID(request.meter_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meter ID format"
            )
        
        # Import meter model to validate ownership
        from app.models.meter import Meter
        
        # Verify meter exists and belongs to user
        meter = db.query(Meter).filter(
            Meter.id == meter_uuid,
            Meter.user_id == current_user.id
        ).first()
        
        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found or does not belong to you"
            )
        
        # Initialize smart meter service
        smart_meter_service = SmartMeterService(db)
        
        # Log consumption (includes signature verification, token deduction, HCS logging)
        consumption_data = smart_meter_service.log_consumption(
            meter_id=str(meter_uuid),
            consumption_kwh=request.consumption_kwh,
            timestamp=request.timestamp,
            signature=request.signature,
            public_key_pem=request.public_key,
            reading_before=request.reading_before,
            reading_after=request.reading_after
        )
        
        logger.info(
            f"Logged consumption for meter {request.meter_id}: "
            f"{request.consumption_kwh} kWh (user: {current_user.email})"
        )
        
        return ConsumeResponse(
            consumption_log_id=consumption_data['consumption_log_id'],
            meter_id=consumption_data['meter_id'],
            consumption_kwh=consumption_data['consumption_kwh'],
            timestamp=consumption_data['timestamp'],
            signature_valid=consumption_data['signature_valid'],
            token_deduction=consumption_data.get('token_deduction'),
            units_deducted=consumption_data.get('units_deducted'),
            units_remaining=consumption_data.get('units_remaining'),
            hcs_topic_id=consumption_data.get('hcs_topic_id'),
            hcs_sequence_number=consumption_data.get('hcs_sequence_number'),
            reading_before=consumption_data.get('reading_before'),
            reading_after=consumption_data.get('reading_after')
        )
        
    except SmartMeterError as e:
        logger.error(f"Smart meter consumption logging failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during consumption logging: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log consumption: {str(e)}"
        )


@router.post("/verify-signature", response_model=VerifySignatureResponse)
async def verify_signature(
    request: VerifySignatureRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify consumption data signature (standalone verification)
    
    This endpoint allows users to verify consumption signatures without
    logging the consumption. Useful for:
    - Manual verification by users
    - Auditing historical consumption data
    - Testing signature generation
    
    Requirements:
        - FR-9.10: System shall provide API endpoint for signature verification
        - US-17: Smart meter signature verification (user)
        - Task 2.4: Smart Meter Service - Signature Verification
    
    Args:
        request: Verification request with meter_id, consumption, signature
        current_user: Authenticated user
        db: Database session
        
    Returns:
        VerifySignatureResponse with verification result
        
    Raises:
        HTTPException 400: Invalid request data
        HTTPException 404: Meter not found
        HTTPException 500: Verification failed
    """
    try:
        # Validate meter_id format
        try:
            meter_uuid = UUID(request.meter_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meter ID format"
            )
        
        # Import meter model to validate ownership
        from app.models.meter import Meter
        
        # Verify meter exists and belongs to user
        meter = db.query(Meter).filter(
            Meter.id == meter_uuid,
            Meter.user_id == current_user.id
        ).first()
        
        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found or does not belong to you"
            )
        
        # Initialize smart meter service
        smart_meter_service = SmartMeterService(db)
        
        # Verify signature
        verification_result = smart_meter_service.verify_signature(
            meter_id=str(meter_uuid),
            consumption_kwh=request.consumption_kwh,
            timestamp=request.timestamp,
            signature=request.signature,
            public_key_pem=request.public_key
        )
        
        logger.info(
            f"Verified signature for meter {request.meter_id}: "
            f"{'VALID' if verification_result['valid'] else 'INVALID'} "
            f"(user: {current_user.email})"
        )
        
        return VerifySignatureResponse(
            valid=verification_result['valid'],
            meter_id=verification_result['meter_id'],
            consumption_kwh=verification_result['consumption_kwh'],
            timestamp=verification_result['timestamp'],
            message_hash=verification_result['message_hash'],
            algorithm=verification_result['algorithm'],
            error=verification_result.get('error')
        )
        
    except SmartMeterError as e:
        logger.error(f"Smart meter signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during signature verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify signature: {str(e)}"
        )


@router.get("/public-key/{meter_id}")
async def get_public_key(
    meter_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get public key for a meter
    
    Args:
        meter_id: Meter UUID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Dictionary with public key and metadata
        
    Raises:
        HTTPException 404: Meter not found or no keypair exists
    """
    try:
        # Validate meter_id format
        try:
            meter_uuid = UUID(meter_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meter ID format"
            )
        
        # Import meter model to validate ownership
        from app.models.meter import Meter
        
        # Verify meter exists and belongs to user
        meter = db.query(Meter).filter(
            Meter.id == meter_uuid,
            Meter.user_id == current_user.id
        ).first()
        
        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found or does not belong to you"
            )
        
        # Initialize smart meter service
        smart_meter_service = SmartMeterService(db)
        
        # Get public key
        public_key = smart_meter_service.get_public_key(str(meter_uuid))
        
        if not public_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No keypair found for this meter. Generate one first."
            )
        
        return {
            "meter_id": meter_id,
            "public_key": public_key,
            "algorithm": "ED25519"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving public key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve public key"
        )


@router.get("/consumption-logs")
async def get_consumption_logs(
    meter_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get consumption logs for a meter
    
    Args:
        meter_id: Meter UUID
        limit: Maximum number of logs to return (default 50)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of consumption logs with signature verification status
        
    Raises:
        HTTPException 404: Meter not found
    """
    try:
        # Validate meter_id format
        try:
            meter_uuid = UUID(meter_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meter ID format"
            )
        
        # Import meter model to validate ownership
        from app.models.meter import Meter
        from app.models.consumption_log import ConsumptionLog
        
        # Verify meter exists and belongs to user
        meter = db.query(Meter).filter(
            Meter.id == meter_uuid,
            Meter.user_id == current_user.id
        ).first()
        
        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found or does not belong to you"
            )
        
        # Fetch consumption logs
        logs = db.query(ConsumptionLog).filter(
            ConsumptionLog.meter_id == meter_uuid
        ).order_by(
            ConsumptionLog.created_at.desc()
        ).limit(limit).all()
        
        # Format response
        logs_data = []
        for log in logs:
            logs_data.append({
                "id": str(log.id),
                "meter_id": str(log.meter_id),
                "consumption_kwh": float(log.consumption_kwh),
                "reading_before": float(log.reading_before) if log.reading_before else None,
                "reading_after": float(log.reading_after) if log.reading_after else None,
                "timestamp": log.timestamp,
                "signature": log.signature,
                "public_key": log.public_key,
                "signature_valid": log.signature_valid,
                "units_deducted": float(log.units_deducted) if log.units_deducted else None,
                "units_remaining": float(log.units_remaining) if log.units_remaining else None,
                "token_id": str(log.token_id) if log.token_id else None,
                "hcs_topic_id": log.hcs_topic_id,
                "hcs_sequence_number": log.hcs_sequence_number,
                "created_at": log.created_at.isoformat()
            })
        
        return {
            "logs": logs_data,
            "total": len(logs_data),
            "meter_id": meter_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving consumption logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve consumption logs"
        )
@router.get("/consumption-history/{meter_id}")
async def get_consumption_history(
    meter_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get consumption history for a meter with HCS verification data

    Returns recent consumption logs including:
    - Consumption amount and timestamp
    - Signature verification status
    - HCS topic and sequence number for blockchain audit
    - Token deduction details
    - Meter readings before/after

    This endpoint provides real cryptographic verification data instead of mock data.

    Requirements:
        - FR-9.8: Display HCS logging data for consumption
        - FR-9.9: Show signature verification status
        - US-16: Smart meter consumption history

    Args:
        meter_id: Meter UUID
        limit: Number of records to return (default: 10, max: 100)
        current_user: Authenticated user
        db: Database session

    Returns:
        List of consumption logs with HCS data

    Raises:
        HTTPException 404: Meter not found
        HTTPException 400: Invalid meter ID format
    """
    try:
        from sqlalchemy import text

        # Validate meter_id format
        try:
            meter_uuid = UUID(meter_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meter ID format"
            )

        # Validate limit
        if limit > 100:
            limit = 100

        # Validate meter ownership
        from app.models.meter import Meter

        meter = db.query(Meter).filter(
            Meter.id == meter_uuid,
            Meter.user_id == current_user.id
        ).first()

        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found or does not belong to you"
            )

        # Fetch consumption logs with HCS data
        query = text("""
            SELECT
                cl.id, cl.meter_id, cl.consumption_kwh, cl.timestamp,
                cl.signature_valid, cl.units_deducted, cl.units_remaining,
                cl.hcs_topic_id, cl.hcs_sequence_number,
                cl.reading_before, cl.reading_after, cl.created_at,
                pt.token_id, pt.status as token_status
            FROM consumption_logs cl
            LEFT JOIN prepaid_tokens pt ON cl.token_id = pt.id
            WHERE cl.meter_id = :meter_id
            ORDER BY cl.created_at DESC
            LIMIT :limit
        """)

        results = db.execute(query, {
            'meter_id': str(meter_uuid),
            'limit': limit
        }).fetchall()

        logs = []
        for row in results:
            token_deduction = None
            if row[12]:  # token_id exists
                token_deduction = {
                    'token_id': row[12],
                    'token_status': row[13],
                    'units_deducted': float(row[5]) if row[5] else 0,
                    'units_remaining': float(row[6]) if row[6] else 0
                }

            logs.append(ConsumeResponse(
                consumption_log_id=str(row[0]),
                meter_id=str(row[1]),
                consumption_kwh=float(row[2]),
                timestamp=row[3],
                signature_valid=row[4],
                units_deducted=float(row[5]) if row[5] else None,
                units_remaining=float(row[6]) if row[6] else None,
                hcs_topic_id=row[7],
                hcs_sequence_number=row[8],
                reading_before=float(row[9]) if row[9] else None,
                reading_after=float(row[10]) if row[10] else None,
                token_deduction=token_deduction
            ))

        logger.info(f"Retrieved {len(logs)} consumption logs for meter {meter_id}")
        return logs

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch consumption history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch consumption history: {str(e)}"
        )





@router.get("/consumption-logs")
async def get_consumption_logs(
    meter_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get consumption logs for a meter

    Args:
        meter_id: Meter UUID
        limit: Maximum number of logs to return (default 50)
        current_user: Authenticated user
        db: Database session

    Returns:
        List of consumption logs with signature verification status

    Raises:
        HTTPException 404: Meter not found
    """
    try:
        # Validate meter_id format
        try:
            meter_uuid = UUID(meter_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meter ID format"
            )

        # Import meter model to validate ownership
        from app.models.meter import Meter
        from app.models.consumption_log import ConsumptionLog

        # Verify meter exists and belongs to user
        meter = db.query(Meter).filter(
            Meter.id == meter_uuid,
            Meter.user_id == current_user.id
        ).first()

        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found or does not belong to you"
            )

        # Fetch consumption logs
        logs = db.query(ConsumptionLog).filter(
            ConsumptionLog.meter_id == meter_uuid
        ).order_by(
            ConsumptionLog.created_at.desc()
        ).limit(limit).all()

        # Format response
        logs_data = []
        for log in logs:
            logs_data.append({
                "id": str(log.id),
                "meter_id": str(log.meter_id),
                "consumption_kwh": float(log.consumption_kwh),
                "reading_before": float(log.reading_before) if log.reading_before else None,
                "reading_after": float(log.reading_after) if log.reading_after else None,
                "timestamp": log.timestamp,
                "signature": log.signature,
                "public_key": log.public_key,
                "signature_valid": log.signature_valid,
                "units_deducted": float(log.units_deducted) if log.units_deducted else None,
                "units_remaining": float(log.units_remaining) if log.units_remaining else None,
                "token_id": str(log.token_id) if log.token_id else None,
                "hcs_topic_id": log.hcs_topic_id,
                "hcs_sequence_number": log.hcs_sequence_number,
                "created_at": log.created_at.isoformat()
            })

        return {
            "logs": logs_data,
            "total": len(logs_data),
            "meter_id": meter_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving consumption logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve consumption logs"
        )



@router.get("/consumption-history/{meter_id}")
async def get_consumption_history(
    meter_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get consumption history for a meter with HCS verification data
    
    Returns recent consumption logs including:
    - Consumption amount and timestamp
    - Signature verification status
    - HCS topic and sequence number for blockchain audit
    - Token deduction details
    - Meter readings before/after
    
    This endpoint provides real cryptographic verification data instead of mock data.
    
    Requirements:
        - FR-9.8: Display HCS logging data for consumption
        - FR-9.9: Show signature verification status
        - US-16: Smart meter consumption history
    
    Args:
        meter_id: Meter UUID
        limit: Number of records to return (default: 10, max: 100)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of consumption logs with HCS data
        
    Raises:
        HTTPException 404: Meter not found
        HTTPException 400: Invalid meter ID format
    """
    try:
        from sqlalchemy import text
        
        # Validate meter_id format
        try:
            meter_uuid = UUID(meter_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meter ID format"
            )
        
        # Validate limit
        if limit > 100:
            limit = 100
        
        # Validate meter ownership
        from app.models.meter import Meter
        
        meter = db.query(Meter).filter(
            Meter.id == meter_uuid,
            Meter.user_id == current_user.id
        ).first()
        
        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found or does not belong to you"
            )
        
        # Fetch consumption logs with HCS data
        query = text("""
            SELECT 
                cl.id, cl.meter_id, cl.consumption_kwh, cl.timestamp,
                cl.signature_valid, cl.units_deducted, cl.units_remaining,
                cl.hcs_topic_id, cl.hcs_sequence_number,
                cl.reading_before, cl.reading_after, cl.created_at,
                pt.token_id, pt.status as token_status
            FROM consumption_logs cl
            LEFT JOIN prepaid_tokens pt ON cl.token_id = pt.id
            WHERE cl.meter_id = :meter_id
            ORDER BY cl.created_at DESC
            LIMIT :limit
        """)
        
        results = db.execute(query, {
            'meter_id': str(meter_uuid),
            'limit': limit
        }).fetchall()
        
        logs = []
        for row in results:
            token_deduction = None
            if row[12]:  # token_id exists
                token_deduction = {
                    'token_id': row[12],
                    'token_status': row[13],
                    'units_deducted': float(row[5]) if row[5] else 0,
                    'units_remaining': float(row[6]) if row[6] else 0
                }
            
            logs.append(ConsumeResponse(
                consumption_log_id=str(row[0]),
                meter_id=str(row[1]),
                consumption_kwh=float(row[2]),
                timestamp=row[3],
                signature_valid=row[4],
                units_deducted=float(row[5]) if row[5] else None,
                units_remaining=float(row[6]) if row[6] else None,
                hcs_topic_id=row[7],
                hcs_sequence_number=row[8],
                reading_before=float(row[9]) if row[9] else None,
                reading_after=float(row[10]) if row[10] else None,
                token_deduction=token_deduction
            ))
        
        logger.info(f"Retrieved {len(logs)} consumption logs for meter {meter_id}")
        return logs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch consumption history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch consumption history: {str(e)}"
        )
