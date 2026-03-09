"""
Prepaid Token Endpoints
HBAR/USDC prepaid electricity token purchase and management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from decimal import Decimal
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.prepaid_token_service import PrepaidTokenService, PrepaidTokenError

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Schemas
from pydantic import BaseModel, Field


class PrepaidTokenPreviewRequest(BaseModel):
    """Request to preview prepaid token purchase calculation"""
    meter_id: str = Field(..., description="UUID of the meter")
    amount_fiat: float = Field(..., gt=0, description="Amount in local currency")
    currency: str = Field(..., pattern=r"^[A-Z]{3}$", description="3-letter currency code (EUR, USD, etc.)")
    payment_method: str = Field(default="HBAR", pattern=r"^(HBAR|USDC)$", description="Payment method: HBAR or USDC")


class PrepaidTokenPreviewResponse(BaseModel):
    """Preview of prepaid token purchase calculation"""
    amount_fiat: float
    currency: str
    amount_hbar: float | None
    amount_usdc: float | None
    units_kwh: float
    exchange_rate: float
    tariff_rate: float


class PrepaidTokenBuyRequest(BaseModel):
    """Request to buy prepaid electricity tokens"""
    meter_id: str = Field(..., description="UUID of the meter")
    amount_fiat: float = Field(..., gt=0, description="Amount in local currency")
    currency: str = Field(..., pattern=r"^[A-Z]{3}$", description="3-letter currency code (EUR, USD, etc.)")
    payment_method: str = Field(default="HBAR", pattern=r"^(HBAR|USDC)$", description="Payment method: HBAR or USDC")

    class PrepaidTokenPreviewRequest(BaseModel):
        """Request to preview prepaid token purchase calculation"""
        meter_id: str = Field(..., description="UUID of the meter")
        amount_fiat: float = Field(..., gt=0, description="Amount in local currency")
        currency: str = Field(..., pattern=r"^[A-Z]{3}$", description="3-letter currency code (EUR, USD, etc.)")
        payment_method: str = Field(default="HBAR", pattern=r"^(HBAR|USDC)$", description="Payment method: HBAR or USDC")


    class PrepaidTokenPreviewResponse(BaseModel):
        """Preview of prepaid token purchase calculation"""
        amount_fiat: float
        currency: str
        amount_hbar: float | None
        amount_usdc: float | None
        units_kwh: float
        exchange_rate: float
        tariff_rate: float


    class PrepaidTokenBuyRequest(BaseModel):
        """Request to buy prepaid electricity tokens"""
        meter_id: str = Field(..., description="UUID of the meter")
        amount_fiat: float = Field(..., gt=0, description="Amount in local currency")
        currency: str = Field(..., pattern=r"^[A-Z]{3}$", description="3-letter currency code (EUR, USD, etc.)")
        payment_method: str = Field(default="HBAR", pattern=r"^(HBAR|USDC)$", description="Payment method: HBAR or USDC")


class PrepaidTokenResponse(BaseModel):
    """Prepaid token details"""
    id: str
    token_id: str
    user_id: str
    meter_id: str
    units_purchased: float
    units_remaining: float
    amount_paid_hbar: float | None
    amount_paid_usdc: float | None
    amount_paid_fiat: float
    currency: str
    exchange_rate: float
    tariff_rate: float
    status: str
    hedera_tx_id: str | None
    hedera_consensus_timestamp: datetime | None
    hcs_topic_id: str | None
    hcs_sequence_number: int | None
    issued_at: datetime
    expires_at: datetime
    depleted_at: datetime | None


class PrepaidTokenBuyResponse(BaseModel):
    """Response after initiating token purchase"""
    token: PrepaidTokenResponse
    transaction: dict = Field(..., description="Transaction details for user to sign")


class PrepaidBalanceResponse(BaseModel):
    """User's prepaid token balance"""
    tokens: List[PrepaidTokenResponse]
    total_units_remaining: float


@router.post("/preview", response_model=PrepaidTokenPreviewResponse)
async def preview_prepaid_token(
    request: PrepaidTokenPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Preview prepaid token purchase calculation without creating a token
    
    This endpoint calculates:
    1. HBAR/USDC amount needed based on current exchange rate
    2. kWh units that will be issued based on tariff
    3. Exchange rate and tariff rate used
    
    This is used for real-time calculation in the UI as the user types.
    
    Requirements:
        - FR-8.3: System shall calculate kWh units based on current tariff rate
        - US-13: Real-time HBAR equivalent calculation
    
    Args:
        request: Preview request with meter_id, amount, currency, payment_method
        current_user: Authenticated user
        db: Database session
        
    Returns:
        PrepaidTokenPreviewResponse with calculated amounts
        
    Raises:
        HTTPException 400: Invalid request data
        HTTPException 404: Meter not found
        HTTPException 503: Exchange rate service unavailable
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
        
        # Initialize prepaid token service
        prepaid_service = PrepaidTokenService(db)
        
        # Get exchange rate
        from app.services.exchange_rate_service import ExchangeRateService
        exchange_service = ExchangeRateService(db)
        
        if request.payment_method == "HBAR":
            exchange_rate = exchange_service.get_hbar_price(request.currency)
            amount_crypto = float(Decimal(str(request.amount_fiat)) / Decimal(str(exchange_rate)))
            amount_hbar = amount_crypto
            amount_usdc = None
        else:  # USDC
            # For USDC, assume 1:1 with USD for now
            # TODO: Implement proper USDC exchange rate
            if request.currency == "USD":
                amount_usdc = request.amount_fiat
                exchange_rate = 1.0
            else:
                # Convert local currency to USD equivalent
                hbar_price_usd = exchange_service.get_hbar_price("USD")
                hbar_price_local = exchange_service.get_hbar_price(request.currency)
                usd_to_local_rate = hbar_price_local / hbar_price_usd
                amount_usdc = float(Decimal(str(request.amount_fiat)) / Decimal(str(usd_to_local_rate)))
                exchange_rate = usd_to_local_rate
            amount_hbar = None
        
        # Get tariff rate for the meter's country
        # Calculate units using the service method
        country_code_str = current_user.country_code.value if hasattr(current_user.country_code, 'value') else str(current_user.country_code)
        
        calculation = prepaid_service.calculate_units_from_fiat(
            amount_fiat=request.amount_fiat,
            country_code=country_code_str,
            utility_provider=meter.utility_provider
        )
        
        units_kwh = calculation['units_kwh']
        tariff_rate = calculation['tariff_rate']
        
        return PrepaidTokenPreviewResponse(
            amount_fiat=request.amount_fiat,
            currency=request.currency,
            amount_hbar=amount_hbar,
            amount_usdc=amount_usdc,
            units_kwh=units_kwh,
            exchange_rate=exchange_rate,
            tariff_rate=tariff_rate
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating preview: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to calculate preview: {str(e)}"
        )


@router.post("/buy", response_model=PrepaidTokenBuyResponse)
async def buy_prepaid_token(
    request: PrepaidTokenBuyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Purchase prepaid electricity tokens with HBAR or USDC
    
    This endpoint:
    1. Validates the meter exists and belongs to the user
    2. Fetches current HBAR exchange rate
    3. Calculates kWh units based on tariff
    4. Generates unique token ID
    5. Creates token record in database
    6. Returns transaction details for user to sign
    
    Requirements:
        - FR-8.1: System shall support HBAR payment for prepaid tokens
        - FR-8.2: System shall optionally support USDC payment
        - FR-8.3: System shall calculate kWh units based on current tariff rate
        - FR-8.4: System shall generate unique token ID
        - US-13: Prepaid token purchase flow
    
    Args:
        request: Token purchase request with meter_id, amount, currency, payment_method
        current_user: Authenticated user
        db: Database session
        
    Returns:
        PrepaidTokenBuyResponse with token details and transaction to sign
        
    Raises:
        HTTPException 400: Invalid request data
        HTTPException 404: Meter not found
        HTTPException 503: Exchange rate service unavailable
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
        
        # Initialize prepaid token service
        prepaid_service = PrepaidTokenService(db)
        
        # Get country code and utility provider from meter
        country_code_str = current_user.country_code.value if hasattr(current_user.country_code, 'value') else str(current_user.country_code)
        
        # Create token (this will calculate units, generate token ID, and prepare transaction)
        token_data = prepaid_service.create_token(
            user_id=str(current_user.id),
            meter_id=str(meter_uuid),
            amount_fiat=float(request.amount_fiat),
            currency=request.currency,
            country_code=country_code_str,
            utility_provider=meter.utility_provider,
            payment_method=request.payment_method
        )
        
        logger.info(
            f"Prepaid token created: {token_data['token_id']} "
            f"for user {current_user.email} (ID: {current_user.id})"
        )
        
        # Prepare response
        token_response = PrepaidTokenResponse(
            id=str(token_data['id']),
            token_id=token_data['token_id'],
            user_id=str(token_data['user_id']),
            meter_id=str(token_data['meter_id']),
            units_purchased=float(token_data['units_purchased']),
            units_remaining=float(token_data['units_remaining']),
            amount_paid_hbar=float(token_data['amount_paid_hbar']) if token_data.get('amount_paid_hbar') else None,
            amount_paid_usdc=float(token_data['amount_paid_usdc']) if token_data.get('amount_paid_usdc') else None,
            amount_paid_fiat=float(token_data['amount_paid_fiat']),
            currency=token_data['currency'],
            exchange_rate=float(token_data['exchange_rate']),
            tariff_rate=float(token_data['tariff_rate']),
            status=token_data['status'],
            hedera_tx_id=token_data.get('hedera_tx_id'),
            hedera_consensus_timestamp=token_data.get('hedera_consensus_timestamp'),
            hcs_topic_id=token_data.get('hcs_topic_id'),
            hcs_sequence_number=token_data.get('hcs_sequence_number'),
            issued_at=token_data['issued_at'],
            expires_at=token_data['expires_at'],
            depleted_at=token_data.get('depleted_at')
        )
        
        # Prepare transaction details for user to sign
        transaction = {
            "from": current_user.hedera_account_id or "0.0.0",
            "to": token_data['transaction']['to'],
            "amount_hbar": float(token_data['transaction']['amount_hbar']) if request.payment_method == "HBAR" else None,
            "amount_usdc": float(token_data['transaction']['amount_usdc']) if request.payment_method == "USDC" else None,
            "memo": token_data['transaction']['memo']
        }
        
        return PrepaidTokenBuyResponse(
            token=token_response,
            transaction=transaction
        )
        
    except PrepaidTokenError as e:
        logger.error(f"Prepaid token creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during prepaid token purchase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prepaid token: {str(e)}"
        )


@router.get("/balance", response_model=PrepaidBalanceResponse)
async def get_prepaid_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's prepaid token balance
    
    Returns all active, depleted, and expired tokens for the user,
    along with total remaining units across all active tokens.
    
    Requirements:
        - US-15: View prepaid token balance
        - FR-8.8: System shall support multiple active tokens per user/meter
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        PrepaidBalanceResponse with list of tokens and total balance
    """
    try:
        # Initialize prepaid token service
        prepaid_service = PrepaidTokenService(db)
        
        # Get all tokens for user
        tokens_data = prepaid_service.get_user_tokens(current_user.id)
        
        # Convert to response format
        tokens = [
            PrepaidTokenResponse(
                id=str(token['id']),
                token_id=token['token_id'],
                user_id=str(token['user_id']),
                meter_id=str(token['meter_id']),
                units_purchased=float(token['units_purchased']),
                units_remaining=float(token['units_remaining']),
                amount_paid_hbar=float(token['amount_paid_hbar']) if token.get('amount_paid_hbar') else None,
                amount_paid_usdc=float(token['amount_paid_usdc']) if token.get('amount_paid_usdc') else None,
                amount_paid_fiat=float(token['amount_paid_fiat']),
                currency=token['currency'],
                exchange_rate=float(token['exchange_rate']),
                tariff_rate=float(token['tariff_rate']),
                status=token['status'],
                hedera_tx_id=token.get('hedera_tx_id'),
                hedera_consensus_timestamp=token.get('hedera_consensus_timestamp'),
                hcs_topic_id=token.get('hcs_topic_id'),
                hcs_sequence_number=token.get('hcs_sequence_number'),
                issued_at=token['issued_at'],
                expires_at=token['expires_at'],
                depleted_at=token.get('depleted_at')
            )
            for token in tokens_data
        ]
        
        # Calculate total remaining units (only active tokens)
        total_units_remaining = sum(
            float(token['units_remaining'])
            for token in tokens_data
            if token['status'] == 'active'
        )
        
        return PrepaidBalanceResponse(
            tokens=tokens,
            total_units_remaining=total_units_remaining
        )
        
    except Exception as e:
        logger.error(f"Error retrieving prepaid balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prepaid balance"
        )


@router.get("/tokens/{token_id}", response_model=PrepaidTokenResponse)
async def get_prepaid_token(
    token_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific prepaid token
    
    Args:
        token_id: Token ID (e.g., TOKEN-ES-2026-001) or UUID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        PrepaidTokenResponse with token details
        
    Raises:
        HTTPException 404: Token not found or doesn't belong to user
    """
    try:
        # Import PrepaidToken model
        from app.models.prepaid_token import PrepaidToken
        
        # Try to parse as UUID first, otherwise treat as token_id string
        try:
            token_uuid = UUID(token_id)
            token = db.query(PrepaidToken).filter(
                PrepaidToken.id == token_uuid,
                PrepaidToken.user_id == current_user.id
            ).first()
        except ValueError:
            # Not a UUID, search by token_id string
            token = db.query(PrepaidToken).filter(
                PrepaidToken.token_id == token_id,
                PrepaidToken.user_id == current_user.id
            ).first()
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found"
            )
        
        return PrepaidTokenResponse(
            id=str(token.id),
            token_id=token.token_id,
            user_id=str(token.user_id),
            meter_id=str(token.meter_id),
            units_purchased=float(token.units_purchased),
            units_remaining=float(token.units_remaining),
            amount_paid_hbar=float(token.amount_paid_hbar) if token.amount_paid_hbar else None,
            amount_paid_usdc=float(token.amount_paid_usdc) if token.amount_paid_usdc else None,
            amount_paid_fiat=float(token.amount_paid_fiat),
            currency=token.currency,
            exchange_rate=float(token.exchange_rate),
            tariff_rate=float(token.tariff_rate),
            status=token.status,
            hedera_tx_id=token.hedera_tx_id,
            hedera_consensus_timestamp=token.hedera_consensus_timestamp,
            hcs_topic_id=token.hcs_topic_id,
            hcs_sequence_number=token.hcs_sequence_number,
            issued_at=token.issued_at,
            expires_at=token.expires_at,
            depleted_at=token.depleted_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving prepaid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve token"
        )



@router.get("/balance/{meter_id}", response_model=PrepaidBalanceResponse)
async def get_meter_prepaid_balance(
    meter_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get prepaid balance for a specific meter
    
    Args:
        meter_id: Meter UUID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        PrepaidBalanceResponse with balance details
        
    Raises:
        HTTPException 404: Meter not found or doesn't belong to user
    """
    try:
        # Import Meter model
        from app.models.meter import Meter
        
        # Verify meter belongs to user
        meter_uuid = UUID(meter_id)
        meter = db.query(Meter).filter(
            Meter.id == meter_uuid,
            Meter.user_id == current_user.id
        ).first()
        
        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found"
            )
        
        # Get prepaid service
        prepaid_service = PrepaidTokenService(db)
        
        # Get balance
        balance_data = prepaid_service.get_prepaid_balance(
            user_id=current_user.id,
            meter_id=meter_id
        )
        
        return PrepaidBalanceResponse(**balance_data)
        
    except HTTPException:
        raise
    except PrepaidTokenError as e:
        logger.error(f"Prepaid token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving meter prepaid balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prepaid balance"
        )


@router.get("/tokens", response_model=List[PrepaidTokenResponse])
async def list_prepaid_tokens(
    meter_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all prepaid tokens for the current user, optionally filtered by meter
    
    Args:
        meter_id: Optional meter UUID to filter tokens
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of PrepaidTokenResponse
    """
    try:
        # Import PrepaidToken model
        from app.models.prepaid_token import PrepaidToken
        
        # Build query
        query = db.query(PrepaidToken).filter(
            PrepaidToken.user_id == current_user.id
        )
        
        # Filter by meter if provided
        if meter_id:
            meter_uuid = UUID(meter_id)
            query = query.filter(PrepaidToken.meter_id == meter_uuid)
        
        # Order by most recent first
        tokens = query.order_by(PrepaidToken.issued_at.desc()).all()
        
        # Convert to response models
        return [
            PrepaidTokenResponse(
                id=str(token.id),
                token_id=token.token_id,
                user_id=str(token.user_id),
                meter_id=str(token.meter_id),
                units_purchased=float(token.units_purchased),
                units_remaining=float(token.units_remaining),
                amount_paid_hbar=float(token.amount_paid_hbar) if token.amount_paid_hbar else None,
                amount_paid_usdc=float(token.amount_paid_usdc) if token.amount_paid_usdc else None,
                amount_paid_fiat=float(token.amount_paid_fiat),
                currency=token.currency,
                exchange_rate=float(token.exchange_rate),
                tariff_rate=float(token.tariff_rate),
                status=token.status,
                hedera_tx_id=token.hedera_tx_id,
                hedera_consensus_timestamp=token.hedera_consensus_timestamp,
                hcs_topic_id=token.hcs_topic_id,
                hcs_sequence_number=token.hcs_sequence_number,
                issued_at=token.issued_at,
                expires_at=token.expires_at,
                depleted_at=token.depleted_at
            )
            for token in tokens
        ]
        
    except ValueError as e:
        logger.error(f"Invalid UUID format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid meter ID format"
        )
    except Exception as e:
        logger.error(f"Error listing prepaid tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tokens"
        )
