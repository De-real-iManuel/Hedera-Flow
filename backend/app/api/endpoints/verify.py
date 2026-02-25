"""
Verification Endpoints
Meter reading verification and OCR processing
"""
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from decimal import Decimal
import logging
import json
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.verifications import (
    VerificationResponse,
    VerificationStatus,
    OCREngine
)
from app.services.ocr_service import get_ocr_service
from app.services.fraud_detection_service import get_fraud_detection_service
from app.services.ipfs_service import get_ipfs_service
from app.utils.hedera_client import hedera_client
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


# HCS Topic mapping by country
HCS_TOPICS = {
    'ES': settings.hcs_topic_eu,
    'US': settings.hcs_topic_us,
    'IN': settings.hcs_topic_asia,
    'BR': settings.hcs_topic_sa,
    'NG': settings.hcs_topic_africa
}


def get_topic_for_country(country_code: str) -> Optional[str]:
    """Get HCS topic ID for a country"""
    return HCS_TOPICS.get(country_code)


@router.post("/verify", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
@router.post("/verify/scan", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
async def create_verification(
    meter_id: str = Form(...),
    ocr_reading: Optional[float] = Form(None),
    ocr_confidence: Optional[float] = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new meter reading verification
    
    This endpoint handles the complete verification flow:
    1. Validates meter ownership
    2. Processes image with OCR (server-side if client-side failed)
    3. Runs fraud detection
    4. Stores verification in database
    5. Logs to HCS blockchain
    6. Returns verification result
    
    Requirements:
        - FR-3.1 through FR-3.11: OCR processing and fraud detection
        - FR-5.13: Log verifications to HCS
        - US-3: Meter reading capture
        - US-4: AI verification
        - US-6: Verification result display
        - US-8: HCS audit logging
    
    Args:
        meter_id: UUID of the meter to verify
        ocr_reading: Optional client-side OCR reading
        ocr_confidence: Optional client-side OCR confidence (0-1)
        image: Meter photo (JPEG/PNG)
        db: Database session
        current_user: Authenticated user
        
    Returns:
        VerificationResponse with reading, confidence, fraud score, and status
        
    Raises:
        404: Meter not found or not owned by user
        400: Invalid image format or OCR failed
        500: Internal server error
    """
    try:
        logger.info(f"Starting verification for meter {meter_id} by user {current_user['user_id']}")
        
        # Step 1: Validate meter exists and belongs to user
        meter_query = text("""
            SELECT id, user_id, meter_id, utility_provider, meter_type, band_classification
            FROM meters
            WHERE id = :meter_id AND user_id = :user_id
        """)
        
        meter_result = db.execute(
            meter_query,
            {"meter_id": meter_id, "user_id": current_user['user_id']}
        ).fetchone()
        
        if not meter_result:
            logger.warning(f"Meter {meter_id} not found for user {current_user['user_id']}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found or not owned by user"
            )
        
        meter_data = {
            'id': str(meter_result[0]),
            'user_id': str(meter_result[1]),
            'meter_id': meter_result[2],
            'utility_provider': meter_result[3],
            'meter_type': meter_result[4],
            'band_classification': meter_result[5]
        }
        
        logger.info(f"Meter validated: {meter_data['meter_id']} ({meter_data['utility_provider']})")
        
        # Step 2: Read image bytes
        image_bytes = await image.read()
        
        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image file"
            )
        
        logger.info(f"Image received: {len(image_bytes)} bytes")
        
        # Step 3: OCR Processing
        ocr_engine = OCREngine.TESSERACT
        reading_value = None
        confidence = None
        raw_ocr_text = None
        
        # Check if client-side OCR succeeded (confidence > 0.90)
        if ocr_reading is not None and ocr_confidence is not None and ocr_confidence >= 0.90:
            logger.info(f"Using client-side OCR result: {ocr_reading} (confidence: {ocr_confidence})")
            reading_value = Decimal(str(ocr_reading))
            confidence = Decimal(str(ocr_confidence))
            raw_ocr_text = f"Client-side OCR: {ocr_reading}"
            ocr_engine = OCREngine.TESSERACT
        else:
            # Run server-side OCR (Google Vision API)
            logger.info("Running server-side OCR (Google Vision API)")
            ocr_service = get_ocr_service()
            
            try:
                ocr_result = ocr_service.extract_reading(image_bytes)
                
                if ocr_result.get('error'):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"OCR failed: {ocr_result['error']}"
                    )
                
                reading_value = Decimal(str(ocr_result['reading']))
                confidence = Decimal(str(ocr_result['confidence']))
                raw_ocr_text = ocr_result.get('raw_text', '')
                ocr_engine = OCREngine.GOOGLE_VISION
                
                logger.info(f"Server-side OCR result: {reading_value} (confidence: {confidence})")
                
            except Exception as e:
                logger.error(f"OCR processing failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"OCR processing failed: {str(e)}"
                )
        
        # Step 4: Get previous reading for consumption calculation
        previous_reading_query = text("""
            SELECT reading_value
            FROM verifications
            WHERE meter_id = :meter_id AND user_id = :user_id
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        previous_result = db.execute(
            previous_reading_query,
            {"meter_id": meter_id, "user_id": current_user['user_id']}
        ).fetchone()
        
        previous_reading = Decimal(str(previous_result[0])) if previous_result else None
        consumption_kwh = None
        
        if previous_reading:
            consumption_kwh = reading_value - previous_reading
            logger.info(f"Consumption calculated: {consumption_kwh} kWh (current: {reading_value}, previous: {previous_reading})")
        
        # Step 5: Fraud Detection
        logger.info("Running fraud detection")
        fraud_service = get_fraud_detection_service()
        
        # Get historical readings for fraud detection
        historical_query = text("""
            SELECT reading_value
            FROM verifications
            WHERE meter_id = :meter_id AND user_id = :user_id
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        historical_results = db.execute(
            historical_query,
            {"meter_id": meter_id, "user_id": current_user['user_id']}
        ).fetchall()
        
        previous_readings = [float(row[0]) for row in historical_results]
        
        # Extract image metadata (simplified for MVP)
        metadata = {
            'timestamp': datetime.now(datetime.UTC).isoformat(),
            'filename': image.filename,
            'content_type': image.content_type,
            'size': len(image_bytes)
        }
        
        fraud_result = fraud_service.calculate_fraud_score(
            reading=float(reading_value),
            previous_readings=previous_readings,
            image_bytes=image_bytes,
            metadata=metadata
        )
        
        fraud_score = Decimal(str(fraud_result['fraud_score']))
        fraud_flags = fraud_result.get('flags', [])
        
        logger.info(f"Fraud detection complete: score={fraud_score}, flags={fraud_flags}")
        
        # Step 6: Determine verification status
        if fraud_score >= Decimal('0.70'):
            verification_status = VerificationStatus.FRAUD_DETECTED
        elif fraud_score >= Decimal('0.40'):
            verification_status = VerificationStatus.WARNING
        elif confidence < Decimal('0.85'):
            verification_status = VerificationStatus.WARNING
        else:
            verification_status = VerificationStatus.VERIFIED
        
        logger.info(f"Verification status: {verification_status}")
        
        # Step 7: Store image on IPFS (Pinata)
        image_ipfs_hash = None
        ipfs_gateway_url = None
        
        try:
            logger.info("Uploading image to IPFS via Pinata")
            ipfs_service = get_ipfs_service()
            
            # Upload image to IPFS
            ipfs_result = ipfs_service.upload_image(
                image_bytes=image_bytes,
                filename=f"meter_{meter_data['meter_id']}_{datetime.now(datetime.UTC).strftime('%Y%m%d_%H%M%S')}.jpg"
            )
            
            image_ipfs_hash = ipfs_result['ipfs_url']  # ipfs://hash format
            ipfs_gateway_url = ipfs_result['gateway_url']
            
            logger.info(f"Image uploaded to IPFS: {image_ipfs_hash}")
            logger.info(f"Gateway URL: {ipfs_gateway_url}")
            
        except Exception as e:
            # Log error but don't fail verification if IPFS upload fails
            logger.error(f"IPFS upload failed (non-critical): {e}")
            # Use placeholder if IPFS fails
            image_ipfs_hash = f"ipfs://placeholder_{uuid.uuid4().hex[:16]}"
            logger.warning(f"Using placeholder IPFS hash: {image_ipfs_hash}")
        
        # Step 8: Get HCS topic for user's country
        user_country_query = text("""
            SELECT country_code FROM users WHERE id = :user_id
        """)
        
        user_country_result = db.execute(
            user_country_query,
            {"user_id": current_user['user_id']}
        ).fetchone()
        
        country_code = user_country_result[0] if user_country_result else 'ES'
        hcs_topic_id = get_topic_for_country(country_code)
        
        # Step 9: Log to HCS (if topic configured)
        hcs_sequence_number = None
        hcs_timestamp = None
        
        if hcs_topic_id and hcs_topic_id != "0.0.xxxxx":
            try:
                logger.info(f"Logging verification to HCS topic {hcs_topic_id}")
                
                hcs_message = {
                    'type': 'VERIFICATION',
                    'timestamp': int(datetime.now(datetime.UTC).timestamp()),
                    'user_id': str(current_user['user_id'])[:8] + '...',  # Anonymized
                    'meter_id': meter_data['meter_id'],
                    'reading': float(reading_value),
                    'utility_reading': None,  # Not available in MVP
                    'confidence': float(confidence),
                    'fraud_score': float(fraud_score),
                    'status': verification_status.value,
                    'image_hash': image_ipfs_hash
                }
                
                hcs_result = await hedera_client.submit_hcs_message(
                    topic_id=hcs_topic_id,
                    message=hcs_message
                )
                
                hcs_sequence_number = hcs_result['sequence_number']
                hcs_timestamp = datetime.now(datetime.UTC)
                
                logger.info(f"HCS logging successful: sequence={hcs_sequence_number}")
                
            except Exception as e:
                logger.error(f"HCS logging failed (non-critical): {e}")
                # Don't fail the verification if HCS logging fails
        else:
            logger.warning(f"HCS topic not configured for country {country_code}, skipping blockchain logging")
        
        # Step 10: Save verification to database
        verification_id = uuid.uuid4()
        
        insert_query = text("""
            INSERT INTO verifications (
                id, user_id, meter_id, reading_value, previous_reading, consumption_kwh,
                image_ipfs_hash, ocr_engine, confidence, raw_ocr_text,
                fraud_score, fraud_flags, utility_reading, utility_api_response,
                status, hcs_topic_id, hcs_sequence_number, hcs_timestamp, created_at
            ) VALUES (
                :id, :user_id, :meter_id, :reading_value, :previous_reading, :consumption_kwh,
                :image_ipfs_hash, :ocr_engine, :confidence, :raw_ocr_text,
                :fraud_score, :fraud_flags, :utility_reading, :utility_api_response,
                :status, :hcs_topic_id, :hcs_sequence_number, :hcs_timestamp, :created_at
            )
            RETURNING id, user_id, meter_id, reading_value, previous_reading, consumption_kwh,
                      image_ipfs_hash, ocr_engine, confidence, raw_ocr_text,
                      fraud_score, fraud_flags, utility_reading, utility_api_response,
                      status, hcs_topic_id, hcs_sequence_number, hcs_timestamp, created_at
        """)
        
        result = db.execute(
            insert_query,
            {
                'id': verification_id,
                'user_id': uuid.UUID(current_user['user_id']),
                'meter_id': uuid.UUID(meter_id),
                'reading_value': reading_value,
                'previous_reading': previous_reading,
                'consumption_kwh': consumption_kwh,
                'image_ipfs_hash': image_ipfs_hash,
                'ocr_engine': ocr_engine.value,
                'confidence': confidence,
                'raw_ocr_text': raw_ocr_text,
                'fraud_score': fraud_score,
                'fraud_flags': json.dumps(fraud_flags),
                'utility_reading': None,
                'utility_api_response': None,
                'status': verification_status.value,
                'hcs_topic_id': hcs_topic_id,
                'hcs_sequence_number': hcs_sequence_number,
                'hcs_timestamp': hcs_timestamp,
                'created_at': datetime.now(datetime.UTC)
            }
        )
        
        db.commit()
        
        verification_row = result.fetchone()
        
        logger.info(f"Verification saved to database: {verification_id}")
        
        # Step 11: Build response
        response = VerificationResponse(
            id=str(verification_row[0]),
            user_id=str(verification_row[1]),
            meter_id=str(verification_row[2]),
            reading_value=verification_row[3],
            previous_reading=verification_row[4],
            consumption_kwh=verification_row[5],
            image_ipfs_hash=verification_row[6],
            ocr_engine=OCREngine(verification_row[7]),
            confidence=verification_row[8],
            raw_ocr_text=verification_row[9],
            fraud_score=verification_row[10],
            fraud_flags=json.loads(verification_row[11]) if verification_row[11] else {},
            utility_reading=verification_row[12],
            utility_api_response=verification_row[13],
            status=VerificationStatus(verification_row[14]),
            hcs_topic_id=verification_row[15] or "",
            hcs_sequence_number=verification_row[16] or 0,
            hcs_timestamp=verification_row[17],
            created_at=verification_row[18]
        )
        
        logger.info(f"Verification complete: {verification_id} - Status: {verification_status}")
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )

