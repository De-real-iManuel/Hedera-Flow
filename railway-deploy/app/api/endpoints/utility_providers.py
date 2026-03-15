"""
Utility Providers API Endpoints
Provides access to utility provider data for meter registration
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.dependencies import get_db
from app.models.utility_provider import UtilityProvider
from app.schemas.utility_providers import UtilityProviderResponse

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("", response_model=List[UtilityProviderResponse])
async def list_utility_providers(
    country_code: Optional[str] = Query(None, description="Filter by country code (ES, US, IN, BR, NG)"),
    state_province: Optional[str] = Query(None, description="Filter by state/province"),
    db: Session = Depends(get_db)
):
    """
    List utility providers with optional filtering
    
    This endpoint returns utility providers that can be used for meter registration.
    Supports filtering by country and state/province for cascading dropdowns.
    
    Requirements:
        - US-2: User can select utility provider from dropdown
        - FR-2.1: System shall allow users to register multiple meters
    
    Query Parameters:
        - country_code: ISO 3166-1 alpha-2 country code (ES, US, IN, BR, NG)
        - state_province: State or province name
    
    Returns:
        List of utility providers matching the filters
    
    Example:
        GET /utility-providers?country_code=ES
        GET /utility-providers?country_code=NG&state_province=Lagos
    """
    try:
        # Build query
        query = db.query(UtilityProvider).filter(
            UtilityProvider.is_active == True
        )
        
        # Apply filters
        if country_code:
            query = query.filter(UtilityProvider.country_code == country_code.upper())
        
        if state_province:
            query = query.filter(UtilityProvider.state_province == state_province)
        
        # Execute query
        providers = query.order_by(
            UtilityProvider.state_province,
            UtilityProvider.provider_name
        ).all()
        
        logger.info(
            f"Retrieved {len(providers)} utility providers "
            f"(country={country_code}, state={state_province})"
        )
        
        # Convert to response format
        return [
            UtilityProviderResponse(
                id=str(provider.id),
                country_code=provider.country_code,
                state_province=provider.state_province,
                provider_name=provider.provider_name,
                provider_code=provider.provider_code,
                service_areas=provider.service_areas or [],
                is_active=provider.is_active
            )
            for provider in providers
        ]
        
    except Exception as e:
        logger.error(f"Error retrieving utility providers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve utility providers"
        )


@router.get("/states", response_model=List[str])
async def list_states(
    country_code: str = Query(..., description="Country code (ES, US, IN, BR, NG)"),
    db: Session = Depends(get_db)
):
    """
    List unique states/provinces for a country
    
    This endpoint returns a list of unique state/province names for a given country.
    Used to populate the state dropdown in the meter registration form.
    
    Requirements:
        - US-2: User selects state/province from dropdown
    
    Query Parameters:
        - country_code: ISO 3166-1 alpha-2 country code (required)
    
    Returns:
        List of unique state/province names
    
    Example:
        GET /utility-providers/states?country_code=ES
        Returns: ["Madrid", "Valencia", "Catalonia", ...]
    """
    try:
        # Query distinct states for the country
        states = db.query(UtilityProvider.state_province).filter(
            UtilityProvider.country_code == country_code.upper(),
            UtilityProvider.is_active == True
        ).distinct().order_by(UtilityProvider.state_province).all()
        
        # Extract state names from tuples
        state_list = [state[0] for state in states]
        
        logger.info(f"Retrieved {len(state_list)} states for country {country_code}")
        
        return state_list
        
    except Exception as e:
        logger.error(f"Error retrieving states: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve states"
        )


@router.get("/{provider_id}", response_model=UtilityProviderResponse)
async def get_utility_provider(
    provider_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific utility provider by ID
    
    Requirements:
        - FR-2.1: System shall store meter metadata including utility provider
    
    Path Parameters:
        - provider_id: UUID of the utility provider
    
    Returns:
        Utility provider details
    
    Raises:
        HTTPException 404: Provider not found
    """
    try:
        from uuid import UUID
        provider_uuid = UUID(provider_id)
        
        provider = db.query(UtilityProvider).filter(
            UtilityProvider.id == provider_uuid
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utility provider not found"
            )
        
        return UtilityProviderResponse(
            id=str(provider.id),
            country_code=provider.country_code,
            state_province=provider.state_province,
            provider_name=provider.provider_name,
            provider_code=provider.provider_code,
            service_areas=provider.service_areas or [],
            is_active=provider.is_active
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving utility provider: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve utility provider"
        )
