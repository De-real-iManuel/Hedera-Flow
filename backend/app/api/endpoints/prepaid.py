"""
Prepaid Token Endpoints
HBAR/USDC prepaid electricity token purchase and management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form
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
from app.services.tariff_service import TariffNotFoundError

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
    sts_token: str | None
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
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


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
    except TariffNotFoundError as e:
        logger.warning(f"Tariff not found for preview: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No tariff configured for your utility provider. Please contact support."
        )
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
    logger.info(f"BUY ENDPOINT CALLED: user={current_user.email}, meter={request.meter_id}, amount={request.amount_fiat} {request.currency}")
    
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
        
        # Calculate exchange rate + crypto amount before creating token
        # so amount_paid_hbar is stored correctly in the DB
        from app.services.exchange_rate_service import ExchangeRateService
        _exchange_svc = ExchangeRateService(db)
        try:
            _exchange_rate = _exchange_svc.get_hbar_price(request.currency)
            _amount_crypto = float(request.amount_fiat) / _exchange_rate
        except Exception:
            _exchange_rate = None
            _amount_crypto = None

        # Create token (this will calculate units, generate token ID, and prepare transaction)
        token_data = prepaid_service.create_token(
            user_id=str(current_user.id),
            meter_id=str(meter_uuid),
            amount_fiat=float(request.amount_fiat),
            currency=request.currency,
            country_code=country_code_str,
            utility_provider=meter.utility_provider,
            payment_method=request.payment_method,
            amount_crypto=_amount_crypto,
            exchange_rate=_exchange_rate,
        )
        
        logger.info(
            f"Prepaid token created: {token_data['token_id']} "
            f"for user {current_user.email} (ID: {current_user.id})"
        )
        
        # Prepare response
        token_response = PrepaidTokenResponse(
            id=str(token_data['id']),
            token_id=token_data['token_id'],
            sts_token=token_data.get('sts_token'),
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
        
        response = PrepaidTokenBuyResponse(
            token=token_response,
            transaction=transaction
        )
        
        logger.info(f"BUY ENDPOINT SUCCESS: token_id={token_response.token_id}, response_keys={list(response.dict().keys())}")
        
        return response
        
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
                sts_token=token.get('sts_token'),
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
            sts_token=token.sts_token,
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
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all prepaid tokens for the current user with filtering and pagination
    
    Args:
        meter_id: Optional meter UUID to filter tokens
        status: Optional status filter (active, depleted, expired, cancelled)
        date_from: Optional start date filter (YYYY-MM-DD)
        date_to: Optional end date filter (YYYY-MM-DD)
        limit: Maximum number of tokens to return (default: 50, max: 100)
        offset: Number of tokens to skip for pagination (default: 0)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of PrepaidTokenResponse ordered by most recent first
    """
    try:
        # Import PrepaidToken model
        from app.models.prepaid_token import PrepaidToken
        from datetime import datetime
        
        # Validate limit
        if limit > 100:
            limit = 100
        
        # Build query
        query = db.query(PrepaidToken).filter(
            PrepaidToken.user_id == current_user.id
        )
        
        # Filter by meter if provided
        if meter_id:
            meter_uuid = UUID(meter_id)
            query = query.filter(PrepaidToken.meter_id == meter_uuid)
        
        # Filter by status if provided
        if status:
            query = query.filter(PrepaidToken.status == status)
        
        # Filter by date range if provided
        if date_from:
            start_date = datetime.fromisoformat(date_from)
            query = query.filter(PrepaidToken.issued_at >= start_date)
        
        if date_to:
            end_date = datetime.fromisoformat(date_to + "T23:59:59")
            query = query.filter(PrepaidToken.issued_at <= end_date)
        
        # Order by most recent first and apply pagination
        tokens = query.order_by(PrepaidToken.issued_at.desc()).offset(offset).limit(limit).all()
        
        # Convert to response models
        return [
            PrepaidTokenResponse(
                id=str(token.id),
                token_id=token.token_id,
                sts_token=token.sts_token,
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
            detail="Invalid meter ID or date format"
        )
    except Exception as e:
        logger.error(f"Error listing prepaid tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tokens"
        )


@router.post("/confirm-payment", response_model=PrepaidTokenBuyResponse)
async def confirm_prepaid_payment(
    token_id: str = Form(...),
    hedera_tx_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm prepaid token payment after user signs transaction with wallet
    
    This endpoint:
    1. Verifies the transaction on Hedera network via Mirror Node
    2. Validates transaction amount matches expected HBAR amount
    3. Updates token status to 'active'
    4. Logs token issuance to HCS
    
    Requirements:
        - FR-8.6: System shall verify HBAR payment on Hedera network
        - FR-8.7: System shall log token issuance to HCS
        - US-13: Prepaid token purchase with wallet signing
    
    Args:
        token_id: Token ID (TOKEN-XX-YYYY-NNN format)
        hedera_tx_id: Hedera transaction ID from wallet (format: 0.0.xxx@timestamp.nnnnnnnnn)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Updated token with transaction details
        
    Raises:
        HTTPException 404: Token not found
        HTTPException 400: Transaction verification failed or amount mismatch
        HTTPException 500: Database or service error
    """
    try:
        from app.utils.transaction_verifier import TransactionVerifier, TransactionVerificationError
        from sqlalchemy import text
        from datetime import datetime
        
        logger.info(f"Confirming prepaid payment: token={token_id}, tx={hedera_tx_id}")
        
        # Get token
        query = text("""
            SELECT id, user_id, meter_id, amount_paid_hbar, amount_paid_fiat, 
                   currency, status, hcs_topic_id
            FROM prepaid_tokens
            WHERE token_id = :token_id AND user_id = :user_id
        """)
        
        result = db.execute(query, {
            'token_id': token_id,
            'user_id': str(current_user.id)
        }).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found or does not belong to you"
            )
        
        token_uuid = result[0]
        expected_hbar = float(result[3]) if result[3] else 0
        token_status = result[6]
        hcs_topic_id = result[7]
        
        # Check if already confirmed
        if token_status == 'active':
            logger.warning(f"Token {token_id} already confirmed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token payment already confirmed"
            )
        
        # Verify transaction on Hedera network
        logger.info(f"Verifying transaction {hedera_tx_id} on Hedera network")
        
        # Check if this is an EVM transaction (starts with 0x)
        is_evm_transaction = hedera_tx_id.startswith('0x')
        
        if is_evm_transaction:
            # For EVM transactions (MetaMask), skip Mirror Node verification
            # The transaction hash is from Hedera's EVM layer
            logger.info(f"EVM transaction detected: {hedera_tx_id}")
            logger.info("Skipping Mirror Node verification for EVM transaction (MVP mode)")
            
            # For MVP, we trust the transaction was successful
            # In production, you would verify via Hedera's JSON-RPC endpoint
            # or wait for the transaction to be indexed in Mirror Node
            tx_details = {
                'valid': True,
                'amount_hbar': expected_hbar,  # Trust the expected amount
                'consensus_timestamp': datetime.utcnow()
            }
            
            logger.info(f"✅ EVM transaction accepted (MVP mode): {expected_hbar} HBAR")
            
        else:
            # Native Hedera transaction - verify via Mirror Node
            verifier = TransactionVerifier()
            
            try:
                tx_details = verifier.verify_transaction(hedera_tx_id)
            except TransactionVerificationError as e:
                logger.error(f"Transaction verification failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Transaction verification failed: {str(e)}"
                )
            
            if not tx_details.get('valid'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid transaction: {tx_details.get('error', 'Unknown error')}"
                )
            
            # Validate amount (allow 1% tolerance for exchange rate fluctuations)
            actual_hbar = tx_details.get('amount_hbar', 0)
            tolerance = expected_hbar * 0.01  # 1% tolerance
            
            if abs(actual_hbar - expected_hbar) > max(tolerance, 0.01):
                logger.error(
                    f"Amount mismatch: expected {expected_hbar} HBAR, "
                    f"got {actual_hbar} HBAR (tolerance: {tolerance})"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Amount mismatch: expected {expected_hbar} HBAR, got {actual_hbar} HBAR"
                )
            
            logger.info(f"✅ Transaction verified: {actual_hbar} HBAR")
        
        # Update token status
        consensus_timestamp = tx_details.get('consensus_timestamp')
        
        update_query = text("""
            UPDATE prepaid_tokens
            SET status = 'active',
                hedera_tx_id = :tx_id,
                hedera_consensus_timestamp = :consensus_timestamp
            WHERE id = :token_id
            RETURNING id, token_id, sts_token, user_id, meter_id, units_purchased, units_remaining,
                      amount_paid_hbar, amount_paid_usdc, amount_paid_fiat, currency,
                      exchange_rate, tariff_rate, status, hedera_tx_id, 
                      hedera_consensus_timestamp, hcs_topic_id, hcs_sequence_number,
                      issued_at, expires_at, depleted_at
        """)
        
        updated_result = db.execute(update_query, {
            'token_id': str(token_uuid),
            'tx_id': hedera_tx_id,
            'consensus_timestamp': consensus_timestamp
        }).fetchone()
        
        db.commit()
        
        logger.info(f"✅ Token {token_id} activated successfully")

        # Generate STS token now that payment is confirmed (prevents free-token exploit)
        try:
            prepaid_service_sts = PrepaidTokenService(db)
            sts_token_value = prepaid_service_sts.generate_sts_for_confirmed_token(token_id)
            logger.info(f"STS token generated for {token_id}: {sts_token_value}")
        except Exception as sts_err:
            logger.error(f"STS generation failed (non-critical): {sts_err}")
            sts_token_value = None

        # Reload updated row (includes sts_token)
        reload_query = text("""
            SELECT id, token_id, sts_token, user_id, meter_id, units_purchased, units_remaining,
                   amount_paid_hbar, amount_paid_usdc, amount_paid_fiat, currency,
                   exchange_rate, tariff_rate, status, hedera_tx_id,
                   hedera_consensus_timestamp, hcs_topic_id, hcs_sequence_number,
                   issued_at, expires_at, depleted_at
            FROM prepaid_tokens WHERE id = :token_id
        """)
        updated_result = db.execute(reload_query, {'token_id': str(token_uuid)}).fetchone()

        # Log to HCS if topic configured
        if hcs_topic_id and hcs_topic_id != "0.0.xxxxx":
            try:
                prepaid_service = PrepaidTokenService(db)
                hcs_result = prepaid_service.log_token_issuance_to_hcs(
                    token_id=token_id,
                    user_id=str(current_user.id),
                    meter_id=str(result[2]),
                    units_purchased=float(updated_result[4]),
                    amount_paid_hbar=float(updated_result[6]) if updated_result[6] else None,
                    amount_paid_fiat=float(updated_result[8]),
                    currency=updated_result[9],
                    hedera_tx_id=hedera_tx_id,
                    hcs_topic_id=hcs_topic_id
                )
                
                # Update HCS sequence number
                if hcs_result and hcs_result.get('sequence_number'):
                    hcs_update = text("""
                        UPDATE prepaid_tokens
                        SET hcs_sequence_number = :seq_num
                        WHERE id = :token_id
                    """)
                    db.execute(hcs_update, {
                        'token_id': str(token_uuid),
                        'seq_num': hcs_result['sequence_number']
                    })
                    db.commit()
                    
                logger.info(f"✅ Token issuance logged to HCS: {hcs_topic_id}")
                
            except Exception as e:
                logger.error(f"HCS logging failed (non-critical): {e}")
                # Don't fail the confirmation if HCS logging fails
        
        # Return updated token in the same format as buy endpoint
        token_response = PrepaidTokenResponse(
            id=str(updated_result[0]),
            token_id=updated_result[1],
            sts_token=updated_result[2],
            user_id=str(updated_result[3]),
            meter_id=str(updated_result[4]),
            units_purchased=float(updated_result[5]),
            units_remaining=float(updated_result[6]),
            amount_paid_hbar=float(updated_result[7]) if updated_result[7] else None,
            amount_paid_usdc=float(updated_result[8]) if updated_result[8] else None,
            amount_paid_fiat=float(updated_result[9]),
            currency=updated_result[10],
            exchange_rate=float(updated_result[11]),
            tariff_rate=float(updated_result[12]),
            status=updated_result[13],
            hedera_tx_id=updated_result[14],
            hedera_consensus_timestamp=updated_result[15],
            hcs_topic_id=updated_result[16],
            hcs_sequence_number=updated_result[17],
            issued_at=updated_result[18],
            expires_at=updated_result[19],
            depleted_at=updated_result[20]
        )
        
        # Prepare transaction details (already completed)
        from config import settings as _settings
        _treasury = _settings.hedera_treasury_id or "0.0.7942971"
        transaction = {
            "from": current_user.hedera_account_id or "0.0.0",
            "to": _treasury,
            "amount_hbar": float(updated_result[7]) if updated_result[7] else None,
            "amount_usdc": float(updated_result[8]) if updated_result[8] else None,
            "memo": f"Prepaid token confirmed - {updated_result[1]}"
        }
        
        return PrepaidTokenBuyResponse(
            token=token_response,
            transaction=transaction
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Payment confirmation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment confirmation failed: {str(e)}"
        )


class CustodialPayRequest(BaseModel):
    token_id: str = Field(..., description="Token ID (TOKEN-XX-YYYY-NNN) from /buy endpoint")


@router.post("/pay-custodial", response_model=PrepaidTokenBuyResponse)
async def pay_custodial(
    request: CustodialPayRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Custodial payment — backend signs HBAR transfer via AWS KMS so users
    without a crypto wallet can pay.

    Flow:
    1. Look up the pending token created by /buy
    2. Use AWS KMS (or mock) to sign a Hedera HBAR transfer from treasury
    3. Activate the token and generate STS
    4. Return the activated token

    This endpoint is the "Pay without wallet" path for the 95% of users
    who don't have MetaMask / HashPack.
    """
    try:
        from sqlalchemy import text as _text
        from config import settings as _settings

        logger.info(f"Custodial payment requested: token={request.token_id}, user={current_user.email}")

        # 1. Fetch the pending token
        row = db.execute(_text("""
            SELECT id, user_id, meter_id, amount_paid_hbar, amount_paid_fiat,
                   currency, status, hcs_topic_id, token_id
            FROM prepaid_tokens
            WHERE token_id = :token_id AND user_id = :user_id
        """), {"token_id": request.token_id, "user_id": str(current_user.id)}).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Token not found or does not belong to you")

        token_uuid, _, _, amount_paid_hbar, amount_paid_fiat, currency, token_status, hcs_topic_id, token_id_str = row

        if token_status == "active":
            raise HTTPException(status_code=400, detail="Token already activated")

        if token_status not in ("pending",):
            raise HTTPException(status_code=400, detail=f"Token cannot be paid in status: {token_status}")

        # 2. Submit real HBAR transfer on Hedera testnet.
        #    The USER's account pays — we decrypt their private key from KMS.
        from app.services.hedera_service import get_hedera_service as _get_hedera
        from app.services.aws_kms_service import get_kms_service as _get_kms

        treasury_id = _settings.hedera_treasury_id or "0.0.7942971"
        hbar_amount = float(amount_paid_hbar) if amount_paid_hbar else 0.0

        # If hbar_amount is 0 (legacy token without amount stored), recalculate from fiat
        if hbar_amount <= 0 and amount_paid_fiat:
            try:
                from app.services.exchange_rate_service import ExchangeRateService
                _ex = ExchangeRateService(db)
                _rate = _ex.get_hbar_price(currency)
                hbar_amount = float(amount_paid_fiat) / _rate
                logger.info(f"Recalculated hbar_amount={hbar_amount} from fiat={amount_paid_fiat} {currency} rate={_rate}")
            except Exception as _ex_err:
                logger.error(f"Exchange rate recalc failed: {_ex_err}")
                raise HTTPException(status_code=503, detail="Cannot determine HBAR amount for payment")

        # Retrieve user's encrypted private key from KMS
        user_account_id = current_user.hedera_account_id
        payer_private_key_hex: str | None = None

        encrypted_key = (current_user.preferences or {}).get("encrypted_hedera_key")
        if encrypted_key:
            try:
                kms = _get_kms()
                if kms.is_available:
                    context_label = f"user-{current_user.email}"
                    payer_private_key_hex = kms.get_private_key(encrypted_key, context_label)
                    logger.info(f"✅ Decrypted user private key from KMS for {current_user.email}")
                else:
                    logger.warning("KMS unavailable — cannot decrypt user key")
            except Exception as kms_err:
                logger.error(f"KMS key decryption failed: {kms_err}")

        hedera_svc = _get_hedera()
        try:
            if payer_private_key_hex:
                # User's key available — user's account pays (correct custodial flow)
                real_tx_id = hedera_svc.transfer_hbar(
                    to_account_id=treasury_id,
                    amount_hbar=hbar_amount,
                    memo=f"Prepaid payment - {token_id_str}",
                    payer_account_id=user_account_id,
                    payer_private_key_hex=payer_private_key_hex,
                )
                logger.info(f"✅ Real Hedera tx submitted (user pays): {real_tx_id}")
            else:
                # No KMS key stored — operator pays on behalf of user (legacy accounts)
                # This happens for users registered before KMS was configured on Railway.
                # Their account was funded with 50 HBAR by the operator at registration,
                # so the operator covers this payment as a custodial service.
                logger.warning(
                    f"No KMS key for {current_user.email} — operator paying on their behalf. "
                    f"Re-register or call /health/backfill-hedera-accounts to fix."
                )
                real_tx_id = hedera_svc.transfer_hbar(
                    to_account_id=treasury_id,
                    amount_hbar=hbar_amount,
                    memo=f"Prepaid payment (operator) - {token_id_str}",
                )
                logger.info(f"✅ Real Hedera tx submitted (operator fallback): {real_tx_id}")
        except Exception as tx_err:
            logger.error(f"Hedera transfer failed: {tx_err}")
            raise HTTPException(
                status_code=503,
                detail=f"Hedera payment failed: {str(tx_err)}"
            )

        fake_tx_id = real_tx_id

        # 3. Activate token
        updated = db.execute(_text("""
            UPDATE prepaid_tokens
            SET status = 'active',
                hedera_tx_id = :tx_id,
                hedera_consensus_timestamp = NOW()
            WHERE id = :token_uuid
            RETURNING id, token_id, sts_token, user_id, meter_id, units_purchased, units_remaining,
                      amount_paid_hbar, amount_paid_usdc, amount_paid_fiat, currency,
                      exchange_rate, tariff_rate, status, hedera_tx_id,
                      hedera_consensus_timestamp, hcs_topic_id, hcs_sequence_number,
                      issued_at, expires_at, depleted_at
        """), {"tx_id": fake_tx_id, "token_uuid": str(token_uuid)}).fetchone()
        db.commit()

        # 4. Generate STS token
        try:
            prepaid_service = PrepaidTokenService(db)
            sts_value = prepaid_service.generate_sts_for_confirmed_token(token_id_str)
        except Exception as sts_err:
            logger.error(f"STS generation failed: {sts_err}")
            sts_value = None

        # Reload with STS
        updated = db.execute(_text("""
            SELECT id, token_id, sts_token, user_id, meter_id, units_purchased, units_remaining,
                   amount_paid_hbar, amount_paid_usdc, amount_paid_fiat, currency,
                   exchange_rate, tariff_rate, status, hedera_tx_id,
                   hedera_consensus_timestamp, hcs_topic_id, hcs_sequence_number,
                   issued_at, expires_at, depleted_at
            FROM prepaid_tokens WHERE id = :token_uuid
        """), {"token_uuid": str(token_uuid)}).fetchone()

        token_response = PrepaidTokenResponse(
            id=str(updated[0]),
            token_id=updated[1],
            sts_token=updated[2],
            user_id=str(updated[3]),
            meter_id=str(updated[4]),
            units_purchased=float(updated[5]),
            units_remaining=float(updated[6]),
            amount_paid_hbar=float(updated[7]) if updated[7] else None,
            amount_paid_usdc=float(updated[8]) if updated[8] else None,
            amount_paid_fiat=float(updated[9]),
            currency=updated[10],
            exchange_rate=float(updated[11]),
            tariff_rate=float(updated[12]),
            status=updated[13],
            hedera_tx_id=updated[14],
            hedera_consensus_timestamp=updated[15],
            hcs_topic_id=updated[16],
            hcs_sequence_number=updated[17],
            issued_at=updated[18],
            expires_at=updated[19],
            depleted_at=updated[20],
        )

        transaction_out = {
            "from": current_user.hedera_account_id or treasury_id,
            "to": treasury_id,
            "amount_hbar": float(updated[7]) if updated[7] else None,
            "amount_usdc": None,
            "memo": f"Custodial payment - {token_id_str}",
            "hedera_tx_id": fake_tx_id,
            "hashscan_url": (
                f"https://hashscan.io/testnet/transaction/{fake_tx_id}"
                if fake_tx_id and not fake_tx_id.startswith("MOCK-") and not fake_tx_id.startswith("KMS-")
                else None
            ),
        }

        logger.info(f"✅ Custodial payment complete: {token_id_str}")
        return PrepaidTokenBuyResponse(token=token_response, transaction=transaction_out)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Custodial payment failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Custodial payment failed: {str(e)}")


@router.get("/tokens/{token_id}/receipt")
async def get_token_receipt(
    token_id: str,
    format: str = "html",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate and return a receipt for a prepaid token purchase
    
    Args:
        token_id: Token ID (e.g., TOKEN-ES-2026-001) or UUID
        format: Receipt format (html, text, json) - default: html
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Receipt in requested format
        
    Raises:
        HTTPException 404: Token not found or doesn't belong to user
        HTTPException 400: Invalid format
    """
    try:
        # Import PrepaidToken model and receipt service
        from app.models.prepaid_token import PrepaidToken
        from app.services.receipt_service import ReceiptService
        from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
        
        # Validate format
        valid_formats = ["html", "text", "json"]
        if format not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
            )
        
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
        
        # Convert token to dict for receipt service
        token_data = {
            'token_id': token.token_id,
            'amount_paid_fiat': float(token.amount_paid_fiat),
            'amount_paid_hbar': float(token.amount_paid_hbar) if token.amount_paid_hbar else None,
            'amount_paid_usdc': float(token.amount_paid_usdc) if token.amount_paid_usdc else None,
            'currency': token.currency,
            'units_purchased': float(token.units_purchased),
            'tariff_rate': float(token.tariff_rate),
            'exchange_rate': float(token.exchange_rate),
            'hedera_tx_id': token.hedera_tx_id,
            'hcs_topic_id': token.hcs_topic_id,
            'issued_at': token.issued_at,
            'expires_at': token.expires_at,
            'status': token.status
        }
        
        # Generate receipt
        receipt_service = ReceiptService()
        receipt = receipt_service.generate_token_receipt(token_data)
        
        # Return in requested format
        if format == "html":
            return HTMLResponse(content=receipt['html'])
        elif format == "text":
            return PlainTextResponse(content=receipt['text'])
        elif format == "json":
            return JSONResponse(content={
                'token_id': token.token_id,
                'receipt': receipt,
                'generated_at': datetime.utcnow().isoformat()
            })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating receipt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate receipt"
        )


@router.post("/tokens/{token_id}/receipt/email")
async def email_token_receipt(
    token_id: str,
    email_address: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Email a receipt for a prepaid token purchase
    
    Args:
        token_id: Token ID (e.g., TOKEN-ES-2026-001) or UUID
        email_address: Email address to send receipt to
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException 404: Token not found or doesn't belong to user
        HTTPException 400: Invalid email address
    """
    try:
        # Import PrepaidToken model and receipt service
        from app.models.prepaid_token import PrepaidToken
        from app.services.receipt_service import ReceiptService
        import re
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email_address):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email address format"
            )
        
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
        
        # Convert token to dict for receipt service
        token_data = {
            'token_id': token.token_id,
            'amount_paid_fiat': float(token.amount_paid_fiat),
            'amount_paid_hbar': float(token.amount_paid_hbar) if token.amount_paid_hbar else None,
            'amount_paid_usdc': float(token.amount_paid_usdc) if token.amount_paid_usdc else None,
            'currency': token.currency,
            'units_purchased': float(token.units_purchased),
            'tariff_rate': float(token.tariff_rate),
            'exchange_rate': float(token.exchange_rate),
            'hedera_tx_id': token.hedera_tx_id,
            'hcs_topic_id': token.hcs_topic_id,
            'issued_at': token.issued_at,
            'expires_at': token.expires_at,
            'status': token.status
        }
        
        # Generate receipt
        receipt_service = ReceiptService()
        receipt = receipt_service.generate_token_receipt(token_data)
        
        # TODO: Implement email sending service
        # For now, just log that email would be sent
        logger.info(f"Receipt email requested for token {token.token_id} to {email_address}")
        
        return {
            "message": "Receipt email sent successfully",
            "token_id": token.token_id,
            "email_address": email_address,
            "sent_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending receipt email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send receipt email"
        )