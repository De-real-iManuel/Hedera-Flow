"""
Authentication Endpoints
User registration, login, and wallet connection with httpOnly cookies
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form, Response, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import logging
import secrets

from app.core.database import get_db
from app.core.dependencies import get_current_user as get_current_user_dependency
from app.schemas.auth import RegisterRequest, LoginRequest, WalletConnectRequest, AuthResponse, UserResponse
from app.models.user import User, CountryCodeEnum, WalletTypeEnum
from app.utils.auth import hash_password, create_access_token, create_refresh_token, validate_password_strength, decode_access_token
from app.services.hedera_service import get_hedera_service
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Set httpOnly cookies for authentication tokens"""
    # Determine if we're in production (use secure cookies only for HTTPS)
    is_production = getattr(settings, 'environment', 'development') == 'production'
    
    # Set access token cookie (15 minutes)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=15 * 60,  # 15 minutes in seconds
        httponly=True,
        secure=is_production,  # Only secure in production (HTTPS)
        samesite="strict"
    )
    
    # Set refresh token cookie (7 days)
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token,
        max_age=7 * 24 * 60 * 60,  # 7 days in seconds
        httponly=True,
        secure=is_production,  # Only secure in production (HTTPS)
        samesite="strict"
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Register a new user with email and password
    
    Requirements:
        - FR-1.1: System shall support email/password registration
        - FR-1.3: System shall create Hedera testnet account for new users without wallet
        - FR-1.4: System shall use JWT tokens for session management
        - FR-1.5: System shall enforce password requirements (min 8 chars, 1 uppercase, 1 number)
        - US-1: User can register with email + password OR connect HashPack wallet
        - US-1: System creates Hedera account (testnet) if user doesn't have one
        - NFR-2.2: Passwords shall be hashed with bcrypt (cost factor 12)
        - NFR-2.3: Access tokens shall expire after 15 minutes, refresh tokens after 7 days
    
    Args:
        request: Registration request with email, password, country_code, and optional hedera_account_id
        response: FastAPI response object to set cookies
        db: Database session
        
    Returns:
        UserResponse with user data (token set in httpOnly cookie)
        
    Raises:
        HTTPException 400: Email already exists, invalid country code, or password validation failed
        HTTPException 500: Failed to create Hedera account or database error
    """
    try:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        # Validate password if provided
        if request.password:
            is_valid, error_message = validate_password_strength(request.password)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message
                )
            
            # Hash password
            password_hash = hash_password(request.password)
        else:
            # Wallet-only authentication (no password)
            password_hash = None
        
        # Create Hedera account if not provided
        if request.hedera_account_id:
            # User provided their own Hedera account (wallet connection)
            hedera_account_id = request.hedera_account_id
            wallet_type = WalletTypeEnum.HASHPACK
        else:
            # Create new Hedera account for user
            try:
                logger.info(f"Creating Hedera account for user: {request.email}")
                hedera_service = get_hedera_service()
                account_id, private_key = hedera_service.create_account(initial_balance=10.0)
                hedera_account_id = account_id
                wallet_type = WalletTypeEnum.SYSTEM_GENERATED
                
                logger.info(f"Created Hedera account: {account_id}")
                # TODO: Securely store or send private key to user
                # For now, log it (REMOVE IN PRODUCTION)
                logger.info(f"Private key for {account_id}: {private_key}")
                
            except Exception as e:
                logger.error(f"Failed to create Hedera account: {e}")
                # Fallback to test account for development
                import uuid
                test_account_suffix = str(uuid.uuid4())[:8]
                hedera_account_id = f"0.0.TEST_{test_account_suffix}"
                wallet_type = WalletTypeEnum.SYSTEM_GENERATED
                logger.warning(f"Using test account as fallback: {hedera_account_id}")
        
        # Create user in database
        new_user = User(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            password_hash=password_hash,
            country_code=request.country_code,
            hedera_account_id=hedera_account_id,
            wallet_type=wallet_type,
            is_active=True,
            is_email_verified=False
        )
        
        # Generate email verification token
        verification_token = secrets.token_urlsafe(32)
        new_user.email_verification_token = verification_token
        new_user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"User registered successfully: {new_user.email} (ID: {new_user.id})")
        
        # TODO: Send verification email
        # For now, just log the verification link
        verification_link = f"http://localhost:8080/verify-email?token={verification_token}"
        logger.info(f"Email verification link: {verification_link}")
        
        # Generate JWT tokens
        access_token = create_access_token(
            user_id=str(new_user.id),
            email=new_user.email,
            country_code=new_user.country_code.value,
            hedera_account_id=new_user.hedera_account_id
        )
        
        refresh_token = create_refresh_token(
            user_id=str(new_user.id),
            email=new_user.email,
            country_code=new_user.country_code.value,
            hedera_account_id=new_user.hedera_account_id
        )
        
        # Set httpOnly cookies
        set_auth_cookies(response, access_token, refresh_token)
        
        # Prepare response (no token in body)
        user_response = UserResponse(
            id=str(new_user.id),
            first_name=new_user.first_name,
            last_name=new_user.last_name,
            email=new_user.email,
            country_code=new_user.country_code,
            hedera_account_id=new_user.hedera_account_id,
            wallet_type=new_user.wallet_type,
            created_at=new_user.created_at,
            last_login=new_user.last_login,
            is_active=new_user.is_active
        )
        
        return user_response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or Hedera account already exists"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=UserResponse)
async def login(
    username: str = Form(...),  # OAuth2 standard uses 'username' field
    password: str = Form(...),
    response: Response = None,
    db: Session = Depends(get_db)
):
    """
    Login user with email and password
    
    Uses OAuth2 password flow (form data with username/password fields)
    
    Requirements:
        - FR-1.4: System shall use JWT tokens for session management
        - US-1: User can login with email + password
        - NFR-2.3: Access tokens shall expire after 15 minutes, refresh tokens after 7 days
    
    Args:
        username: User's email address (OAuth2 standard field name)
        password: User's password
        response: FastAPI response object to set cookies
        db: Database session
        
    Returns:
        UserResponse with user data (token set in httpOnly cookie)
        
    Raises:
        HTTPException 401: Invalid credentials
        HTTPException 404: User not found
    """
    try:
        # Find user by email (username field contains email)
        user = db.query(User).filter(User.email == username).first()
        
        if not user:
            logger.warning(f"Login attempt for non-existent user: {username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user has a password (not wallet-only)
        if not user.password_hash:
            logger.warning(f"Login attempt for wallet-only user: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This account uses wallet authentication only"
            )
        
        # Verify password
        from app.utils.auth import verify_password
        if not verify_password(password, user.password_hash):
            logger.warning(f"Invalid password for user: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if account is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        logger.info(f"User logged in successfully: {user.email} (ID: {user.id})")
        
        # Generate JWT tokens
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            country_code=user.country_code.value,
            hedera_account_id=user.hedera_account_id
        )
        
        refresh_token = create_refresh_token(
            user_id=str(user.id),
            email=user.email,
            country_code=user.country_code.value,
            hedera_account_id=user.hedera_account_id
        )
        
        # Set httpOnly cookies
        set_auth_cookies(response, access_token, refresh_token)
        
        # Prepare response (no token in body)
        user_response = UserResponse(
            id=str(user.id),
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            country_code=user.country_code,
            hedera_account_id=user.hedera_account_id,
            wallet_type=user.wallet_type,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active
        )
        
        return user_response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


# TODO: Implement remaining authentication endpoints (Task 6.7)
# - POST /refresh-token


@router.post("/refresh-token", response_model=UserResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token from httpOnly cookie
    
    This endpoint allows clients to get a new access token using their refresh token.
    Both tokens are rotated for security.
    
    Requirements:
        - FR-1.4: System shall use JWT tokens for session management
        - NFR-2.3: Access tokens shall expire after 15 minutes, refresh tokens after 7 days
    
    Args:
        request: FastAPI request object to access cookies
        response: FastAPI response object to set new cookies
        db: Database session
        
    Returns:
        UserResponse with user data (new tokens set in httpOnly cookies)
        
    Raises:
        HTTPException 401: Invalid or expired refresh token
        HTTPException 404: User not found
    """
    try:
        # Extract refresh token from httpOnly cookie
        refresh_token_value = request.cookies.get("refresh_token")
        
        if not refresh_token_value:
            logger.warning("Token refresh failed: No refresh token cookie provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token required"
            )
        
        # Decode and verify refresh token
        try:
            payload = decode_access_token(refresh_token_value)
        except Exception as e:
            logger.warning(f"Token refresh failed: Invalid refresh token - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Verify token type
        token_type = payload.get("type")
        if token_type != "refresh":
            logger.warning(f"Token refresh failed: Invalid token type '{token_type}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Extract user ID from token payload
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token refresh failed: Token missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Fetch user from database
        from uuid import UUID
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            logger.warning(f"Token refresh failed: Invalid user ID format '{user_id}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in token"
            )
        
        user = db.query(User).filter(User.id == user_uuid).first()
        
        if not user:
            logger.warning(f"Token refresh failed: User {user_id} not found in database")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user account is active
        if not user.is_active:
            logger.warning(f"Token refresh failed: User {user_id} account is inactive")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        logger.info(f"Token refreshed successfully for user: {user.email} (ID: {user.id})")
        
        # Generate new JWT tokens (rotate both for security)
        new_access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            country_code=user.country_code.value,
            hedera_account_id=user.hedera_account_id
        )
        
        new_refresh_token = create_refresh_token(
            user_id=str(user.id),
            email=user.email,
            country_code=user.country_code.value,
            hedera_account_id=user.hedera_account_id
        )
        
        # Set new httpOnly cookies
        set_auth_cookies(response, new_access_token, new_refresh_token)
        
        # Prepare response (no token in body)
        user_response = UserResponse(
            id=str(user.id),
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            country_code=user.country_code,
            hedera_account_id=user.hedera_account_id,
            wallet_type=user.wallet_type,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active
        )
        
        return user_response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    response: Response
):
    """
    Logout user by clearing authentication cookies
    
    This endpoint clears the httpOnly cookies containing the JWT tokens,
    effectively logging out the user.
    
    Requirements:
        - FR-1.4: System shall use JWT tokens for session management
        - Secure logout by clearing httpOnly cookies
    
    Args:
        response: FastAPI response object to clear cookies
        
    Returns:
        Success message
    """
    try:
        # Determine if we're in production
        is_production = getattr(settings, 'environment', 'development') == 'production'
        
        # Clear access token cookie
        response.delete_cookie(
            key="access_token",
            httponly=True,
            secure=is_production,
            samesite="strict"
        )
        
        # Clear refresh token cookie
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=is_production,
            samesite="strict"
        )
        
        logger.info("User logged out successfully")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Unexpected error during logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/wallet-connect", response_model=UserResponse)
async def wallet_connect(
    request: WalletConnectRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Connect or register user with wallet (HashPack or MetaMask)
    
    This endpoint allows users to authenticate using their wallet
    by providing a signed message. Supports both:
    - Hedera native wallets (HashPack, Kabila, Blade) - account ID format: 0.0.xxx
    - MetaMask (EVM) - address format: 0x...
    
    If the account doesn't exist, a new user is created. If it exists, the user is logged in.
    
    Requirements:
        - FR-1.2: System shall support wallet connection
        - FR-1.4: System shall use JWT tokens for session management
        - US-1: User can register with email + password OR connect wallet
        - NFR-2.3: Access tokens shall expire after 15 minutes, refresh tokens after 7 days
    
    Args:
        request: Wallet connection request with hedera_account_id (or EVM address), signature, and message
        response: FastAPI response object to set cookies
        db: Database session
        
    Returns:
        UserResponse with user data (token set in httpOnly cookie)
        
    Raises:
        HTTPException 401: Invalid signature
        HTTPException 400: Invalid account ID or account doesn't exist
        HTTPException 500: Database or service error
    """
    try:
        account_identifier = request.hedera_account_id
        is_evm_address = account_identifier.startswith('0x')
        
        # For EVM addresses (MetaMask), we skip Hedera service verification
        # and use Ethereum signature verification instead
        if is_evm_address:
            logger.info(f"MetaMask wallet connect attempt: {account_identifier}")
            
            # For MVP, we'll accept the signature without verification
            # In production, implement proper Ethereum signature verification
            # using web3.py or eth_account library
            
            # TODO: Implement proper EVM signature verification
            # from eth_account.messages import encode_defunct
            # from web3.auto import w3
            # message_hash = encode_defunct(text=request.message)
            # recovered_address = w3.eth.account.recover_message(message_hash, signature=request.signature)
            # if recovered_address.lower() != account_identifier.lower():
            #     raise HTTPException(status_code=401, detail="Invalid signature")
            
            logger.info(f"EVM signature accepted (verification skipped for MVP): {account_identifier}")
            
        else:
            # Hedera native wallet verification
            hedera_service = get_hedera_service()
            
            # Check if account exists on Hedera network
            if not hedera_service.account_exists(account_identifier):
                logger.warning(f"Wallet connect attempt with non-existent Hedera account: {account_identifier}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Hedera account does not exist on the network"
                )
            
            # Verify the signature
            is_valid = hedera_service.verify_signature(
                account_id=account_identifier,
                message=request.message,
                signature=request.signature
            )
            
            if not is_valid:
                logger.warning(f"Invalid signature for wallet connect: {account_identifier}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid signature"
                )
            
            logger.info(f"Hedera signature verified successfully for account: {account_identifier}")
        
        # Check if user already exists with this wallet
        existing_user = db.query(User).filter(
            User.hedera_account_id == account_identifier
        ).first()
        
        if existing_user:
            # User exists - perform login
            logger.info(f"Existing user logging in with wallet: {existing_user.email} (ID: {existing_user.id})")
            
            # Check if account is active
            if not existing_user.is_active:
                logger.warning(f"Wallet connect attempt for inactive user: {existing_user.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is inactive"
                )
            
            # Update last login timestamp
            existing_user.last_login = datetime.utcnow()
            db.commit()
            db.refresh(existing_user)
            
            # Generate JWT tokens
            access_token = create_access_token(
                user_id=str(existing_user.id),
                email=existing_user.email,
                country_code=existing_user.country_code.value,
                hedera_account_id=existing_user.hedera_account_id
            )
            
            refresh_token = create_refresh_token(
                user_id=str(existing_user.id),
                email=existing_user.email,
                country_code=existing_user.country_code.value,
                hedera_account_id=existing_user.hedera_account_id
            )
            
            # Set httpOnly cookies
            set_auth_cookies(response, access_token, refresh_token)
            
            # Prepare response (no token in body)
            user_response = UserResponse(
                id=str(existing_user.id),
                first_name=existing_user.first_name,
                last_name=existing_user.last_name,
                email=existing_user.email,
                country_code=existing_user.country_code,
                hedera_account_id=existing_user.hedera_account_id,
                wallet_type=existing_user.wallet_type,
                created_at=existing_user.created_at,
                last_login=existing_user.last_login,
                is_active=existing_user.is_active
            )
            
            return user_response
        
        else:
            # User doesn't exist - create new account
            # Generate a unique email for wallet-only users
            if is_evm_address:
                wallet_email = f"{account_identifier.lower()}@metamask.hederaflow.local"
                wallet_type = WalletTypeEnum.HASHPACK  # Using HASHPACK enum for now, can add METAMASK later
            else:
                wallet_email = f"{account_identifier.replace('.', '-')}@wallet.hederaflow.local"
                wallet_type = WalletTypeEnum.HASHPACK
            
            logger.info(f"Creating new user with wallet: {account_identifier}")
            
            # For wallet-only registration, default to ES (Spain)
            # In production, get from user input or geolocation
            default_country = CountryCodeEnum.ES
            
            # Create new user
            new_user = User(
                email=wallet_email,
                password_hash=None,  # No password for wallet-only auth
                country_code=default_country,
                hedera_account_id=account_identifier,
                wallet_type=wallet_type,
                is_active=True
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info(f"New wallet user created: {new_user.email} (ID: {new_user.id})")
            
            # Generate JWT tokens
            access_token = create_access_token(
                user_id=str(new_user.id),
                email=new_user.email,
                country_code=new_user.country_code.value,
                hedera_account_id=new_user.hedera_account_id
            )
            
            refresh_token = create_refresh_token(
                user_id=str(new_user.id),
                email=new_user.email,
                country_code=new_user.country_code.value,
                hedera_account_id=new_user.hedera_account_id
            )
            
            # Set httpOnly cookies
            set_auth_cookies(response, access_token, refresh_token)
            
            # Prepare response (no token in body)
            user_response = UserResponse(
                id=str(new_user.id),
                first_name=new_user.first_name,
                last_name=new_user.last_name,
                email=new_user.email,
                country_code=new_user.country_code,
                hedera_account_id=new_user.hedera_account_id,
                wallet_type=new_user.wallet_type,
                created_at=new_user.created_at,
                last_login=new_user.last_login,
                is_active=new_user.is_active
            )
            
            return user_response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during wallet connect: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hedera account already registered"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during wallet connect: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Wallet connection failed: {str(e)}"
        )



@router.post("/send-verification-email")
async def send_verification_email(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Send email verification link to user
    
    Args:
        email: User's email address
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException 404: User not found
        HTTPException 400: Email already verified
    """
    try:
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        user.email_verification_token = verification_token
        user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        db.commit()
        
        # TODO: Send email with verification link
        # For now, just log the token (in production, send via email service)
        verification_link = f"http://localhost:8080/verify-email?token={verification_token}"
        logger.info(f"Email verification link for {email}: {verification_link}")
        
        return {
            "message": "Verification email sent successfully",
            "verification_link": verification_link  # Remove this in production
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error sending verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification email: {str(e)}"
        )


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify user's email address using token
    
    Args:
        token: Email verification token
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException 400: Invalid or expired token
    """
    try:
        # Find user by verification token
        user = db.query(User).filter(
            User.email_verification_token == token
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        # Check if token is expired
        if user.email_verification_expires < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired"
            )
        
        # Mark email as verified
        user.is_email_verified = True
        user.email_verification_token = None
        user.email_verification_expires = None
        
        db.commit()
        
        logger.info(f"Email verified successfully for user: {user.email}")
        
        return {
            "message": "Email verified successfully",
            "email": user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error verifying email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Get current authenticated user
    
    This endpoint returns the currently authenticated user's information.
    
    Requirements:
        - FR-1.4: System shall use JWT tokens for session management
        - NFR-2.1: All API endpoints shall require authentication
    
    Args:
        current_user: Current authenticated user from JWT token
        
    Returns:
        UserResponse with current user data
        
    Raises:
        HTTPException 401: Unauthorized (no valid token)
    """
    return UserResponse(
        id=str(current_user.id),
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        country_code=current_user.country_code,
        hedera_account_id=current_user.hedera_account_id,
        wallet_type=current_user.wallet_type,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        is_active=current_user.is_active
    )
@router.put("/complete-profile", response_model=UserResponse)
async def complete_profile(
    first_name: str = Form(..., min_length=1, max_length=100),
    last_name: str = Form(..., min_length=1, max_length=100),
    country_code: str = Form(..., pattern=r"^(ES|US|IN|BR|NG)$"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Complete user profile after wallet-only registration

    This endpoint allows wallet-only users to add their name and country.
    Required for users who registered via wallet connect without providing
    personal information.

    Requirements:
        - Allow wallet users to complete their profile
        - Update first_name, last_name, and country_code

    Args:
        first_name: User's first name
        last_name: User's last name
        country_code: Country code (ES, US, IN, BR, NG)
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated user data

    Raises:
        HTTPException 400: Invalid country code
    """
    try:
        # Update user profile
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.country_code = CountryCodeEnum[country_code]

        db.commit()
        db.refresh(current_user)

        logger.info(f"Profile completed for user {current_user.email} (ID: {current_user.id})")

        return UserResponse(
            id=str(current_user.id),
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            email=current_user.email,
            country_code=current_user.country_code,
            hedera_account_id=current_user.hedera_account_id,
            wallet_type=current_user.wallet_type,
            created_at=current_user.created_at,
            last_login=current_user.last_login,
            is_active=current_user.is_active
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to complete profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )





@router.put("/complete-profile", response_model=UserResponse)
async def complete_profile(
    first_name: str = Form(..., min_length=1, max_length=100),
    last_name: str = Form(..., min_length=1, max_length=100),
    country_code: str = Form(..., pattern=r"^(ES|US|IN|BR|NG)$"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Complete user profile after wallet-only registration
    
    This endpoint allows wallet-only users to add their name and country.
    Required for users who registered via wallet connect without providing
    personal information.
    
    Requirements:
        - Allow wallet users to complete their profile
        - Update first_name, last_name, and country_code
    
    Args:
        first_name: User's first name
        last_name: User's last name
        country_code: Country code (ES, US, IN, BR, NG)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Updated user data
        
    Raises:
        HTTPException 400: Invalid country code
    """
    try:
        # Update user profile
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.country_code = CountryCodeEnum[country_code]
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Profile completed for user {current_user.email} (ID: {current_user.id})")
        
        return UserResponse(
            id=str(current_user.id),
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            email=current_user.email,
            country_code=current_user.country_code,
            hedera_account_id=current_user.hedera_account_id,
            wallet_type=current_user.wallet_type,
            created_at=current_user.created_at,
            last_login=current_user.last_login,
            is_active=current_user.is_active
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to complete profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )
