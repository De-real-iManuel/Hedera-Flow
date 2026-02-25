"""
Meter Management Endpoints
Register and manage electricity meters
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import logging
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.meters import MeterCreateRequest, MeterResponse, MeterListResponse
from app.models.user import User
from app.models.meter import Meter
from app.models.utility_provider import UtilityProvider
from app.utils.meter_validation import validate_meter_id, normalize_meter_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=MeterResponse, status_code=status.HTTP_201_CREATED)
async def create_meter(
    request: MeterCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register a new electricity meter for the authenticated user
    
    This endpoint allows users to register their electricity meters with the system.
    The meter is associated with a utility provider based on the country, state/province,
    and utility provider hierarchy.
    
    Requirements:
        - FR-2.1: System shall allow users to register multiple meters
        - FR-2.2: System shall validate meter ID format per region
        - FR-2.3: System shall store meter metadata (ID, type, utility, registration date)
        - US-2: User can register meter with state/utility dropdowns
        - US-2: For Nigeria, user selects band classification (A, B, C, D, E)
    
    Args:
        request: Meter creation request with meter details
        current_user: Authenticated user (from JWT token)
        db: Database session
        
    Returns:
        MeterResponse with created meter data
        
    Raises:
        HTTPException 400: Invalid meter data or meter already registered
        HTTPException 404: Utility provider not found
        HTTPException 500: Database error
    """
    try:
        # Normalize meter ID
        normalized_meter_id = normalize_meter_id(request.meter_id, current_user.country_code.value)
        
        # Validate meter ID format per region (FR-2.2)
        is_valid, error_message = validate_meter_id(normalized_meter_id, current_user.country_code.value)
        if not is_valid:
            logger.warning(
                f"Invalid meter ID format: {request.meter_id} for country {current_user.country_code.value}. "
                f"Error: {error_message}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Validate utility provider exists
        try:
            utility_provider_uuid = UUID(request.utility_provider_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid utility provider ID format"
            )
        
        utility_provider = db.query(UtilityProvider).filter(
            UtilityProvider.id == utility_provider_uuid,
            UtilityProvider.is_active == True
        ).first()
        
        if not utility_provider:
            logger.warning(f"Utility provider not found: {request.utility_provider_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utility provider not found or inactive"
            )
        
        # Validate that utility provider matches the user's country
        if utility_provider.country_code != current_user.country_code.value:
            logger.warning(
                f"Country mismatch: User country {current_user.country_code.value}, "
                f"Provider country {utility_provider.country_code}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Utility provider must be from your country ({current_user.country_code.value})"
            )
        
        # Validate state/province matches utility provider
        if request.state_province != utility_provider.state_province:
            logger.warning(
                f"State mismatch: Request state {request.state_province}, "
                f"Provider state {utility_provider.state_province}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Utility provider does not serve {request.state_province}"
            )
        
        # Check if meter already registered by this user
        existing_meter = db.query(Meter).filter(
            Meter.user_id == current_user.id,
            Meter.meter_id == normalized_meter_id
        ).first()
        
        if existing_meter:
            logger.warning(
                f"Meter already registered: {normalized_meter_id} for user {current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Meter already registered"
            )
        
        # Validate band classification for Nigeria
        if current_user.country_code.value == 'NG' and not request.band_classification:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Band classification is required for Nigeria meters"
            )
        
        # If this is set as primary, unset other primary meters
        if request.is_primary:
            db.query(Meter).filter(
                Meter.user_id == current_user.id,
                Meter.is_primary == True
            ).update({"is_primary": False})
        
        # Create new meter
        new_meter = Meter(
            user_id=current_user.id,
            meter_id=normalized_meter_id,  # Use normalized meter ID
            utility_provider_id=utility_provider.id,
            state_province=request.state_province,
            utility_provider=request.utility_provider,  # Denormalized for quick access
            meter_type=request.meter_type,
            band_classification=request.band_classification,
            address=request.address,
            is_primary=request.is_primary
        )
        
        db.add(new_meter)
        db.commit()
        db.refresh(new_meter)
        
        logger.info(
            f"Meter registered successfully: {new_meter.meter_id} "
            f"for user {current_user.email} (ID: {current_user.id})"
        )
        
        # Prepare response
        return MeterResponse(
            id=str(new_meter.id),
            user_id=str(new_meter.user_id),
            meter_id=new_meter.meter_id,
            utility_provider_id=str(new_meter.utility_provider_id),
            state_province=new_meter.state_province,
            utility_provider=new_meter.utility_provider,
            meter_type=new_meter.meter_type,
            band_classification=new_meter.band_classification,
            address=new_meter.address,
            is_primary=new_meter.is_primary,
            created_at=new_meter.created_at,
            updated_at=new_meter.updated_at
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during meter creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meter already registered or invalid data"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during meter creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register meter: {str(e)}"
        )


@router.get("", response_model=List[MeterResponse])
async def list_meters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all meters registered by the authenticated user
    
    Returns:
        List of MeterResponse objects
    """
    try:
        meters = db.query(Meter).filter(
            Meter.user_id == current_user.id
        ).order_by(Meter.is_primary.desc(), Meter.created_at.desc()).all()
        
        return [
            MeterResponse(
                id=str(meter.id),
                user_id=str(meter.user_id),
                meter_id=meter.meter_id,
                utility_provider_id=str(meter.utility_provider_id),
                state_province=meter.state_province,
                utility_provider=meter.utility_provider,
                meter_type=meter.meter_type,
                band_classification=meter.band_classification,
                address=meter.address,
                is_primary=meter.is_primary,
                created_at=meter.created_at,
                updated_at=meter.updated_at
            )
            for meter in meters
        ]
    except Exception as e:
        logger.error(f"Error listing meters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve meters"
        )


@router.get("/{meter_id}", response_model=MeterResponse)
async def get_meter(
    meter_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific meter
    
    Args:
        meter_id: UUID of the meter
        current_user: Authenticated user
        db: Database session
        
    Returns:
        MeterResponse with meter details
        
    Raises:
        HTTPException 404: Meter not found or doesn't belong to user
    """
    try:
        meter_uuid = UUID(meter_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid meter ID format"
        )
    
    meter = db.query(Meter).filter(
        Meter.id == meter_uuid,
        Meter.user_id == current_user.id
    ).first()
    
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter not found"
        )
    
    return MeterResponse(
        id=str(meter.id),
        user_id=str(meter.user_id),
        meter_id=meter.meter_id,
        utility_provider_id=str(meter.utility_provider_id),
        state_province=meter.state_province,
        utility_provider=meter.utility_provider,
        meter_type=meter.meter_type,
        band_classification=meter.band_classification,
        address=meter.address,
        is_primary=meter.is_primary,
        created_at=meter.created_at,
        updated_at=meter.updated_at
    )


@router.put("/{meter_id}", response_model=MeterResponse)
async def update_meter(
    meter_id: str,
    request: MeterCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing meter
    
    Args:
        meter_id: UUID of the meter to update
        request: Updated meter data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        MeterResponse with updated meter data
        
    Raises:
        HTTPException 404: Meter not found
        HTTPException 400: Invalid data
    """
    try:
        meter_uuid = UUID(meter_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid meter ID format"
        )
    
    meter = db.query(Meter).filter(
        Meter.id == meter_uuid,
        Meter.user_id == current_user.id
    ).first()
    
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter not found"
        )
    
    try:
        # Validate utility provider if changed
        utility_provider_uuid = UUID(request.utility_provider_id)
        utility_provider = db.query(UtilityProvider).filter(
            UtilityProvider.id == utility_provider_uuid,
            UtilityProvider.is_active == True
        ).first()
        
        if not utility_provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utility provider not found or inactive"
            )
        
        # If setting as primary, unset other primary meters
        if request.is_primary and not meter.is_primary:
            db.query(Meter).filter(
                Meter.user_id == current_user.id,
                Meter.id != meter_uuid,
                Meter.is_primary == True
            ).update({"is_primary": False})
        
        # Update meter fields
        meter.meter_id = request.meter_id
        meter.utility_provider_id = utility_provider.id
        meter.state_province = request.state_province
        meter.utility_provider = request.utility_provider
        meter.meter_type = request.meter_type
        meter.band_classification = request.band_classification
        meter.address = request.address
        meter.is_primary = request.is_primary
        
        db.commit()
        db.refresh(meter)
        
        logger.info(f"Meter updated: {meter.meter_id} for user {current_user.id}")
        
        return MeterResponse(
            id=str(meter.id),
            user_id=str(meter.user_id),
            meter_id=meter.meter_id,
            utility_provider_id=str(meter.utility_provider_id),
            state_province=meter.state_province,
            utility_provider=meter.utility_provider,
            meter_type=meter.meter_type,
            band_classification=meter.band_classification,
            address=meter.address,
            is_primary=meter.is_primary,
            created_at=meter.created_at,
            updated_at=meter.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating meter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update meter"
        )


@router.delete("/{meter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meter(
    meter_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a meter
    
    Args:
        meter_id: UUID of the meter to delete
        current_user: Authenticated user
        db: Database session
        
    Raises:
        HTTPException 404: Meter not found
        HTTPException 400: Cannot delete meter with associated bills
    """
    try:
        meter_uuid = UUID(meter_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid meter ID format"
        )
    
    meter = db.query(Meter).filter(
        Meter.id == meter_uuid,
        Meter.user_id == current_user.id
    ).first()
    
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meter not found"
        )
    
    # TODO: Check if meter has associated bills before deleting
    # For now, we'll allow deletion
    
    try:
        db.delete(meter)
        db.commit()
        logger.info(f"Meter deleted: {meter.meter_id} for user {current_user.id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting meter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete meter"
        )

