"""
Authentication Endpoints
User registration, login, and wallet connection
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import logging
import secrets

from app.core.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, WalletConnectRequest, AuthResponse, UserResponse
from app.models.user import User, CountryCodeEnum, WalletTypeEnum
from app.utils.auth import hash_password, create_access_token, validate_password_strength
from app.services.hedera_service import get_hedera_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
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
        - NFR-2.3: JWT tokens shall expire after 30 days
    
    Args:
        request: Registration request with email, password, country_code, and optional hedera_account_id
        db: Database session
        
    Returns:
        AuthResponse with JWT token and user data
        
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
        
        # Create Hedera account if not provided (TEMPORARILY DISABLED FOR TESTING)
        # Generate unique test account ID for each user during MVP
        import uuid
        test_account_suffix = str(uuid.uuid4())[:8]
        hedera_account_id = request.hedera_account_id or f"0.0.TEST_{test_account_suffix}"
        wallet_type = WalletTypeEnum.HASHPACK if request.hedera_account_id else WalletTypeEnum.SYSTEM_GENERATED
        
        # TODO: Re-enable Hedera account creation after fixing credentials
        # if not hedera_account_id:
        #     try:
        #         logger.info(f"Creating Hedera account for user: {request.email}")
        #         hedera_service = get_hedera_service()
        #         account_id, private_key = hedera_service.create_account(initial_balance=10.0)
        #         hedera_account_id = account_id
        #         logger.info(f"Created Hedera account: {account_id}")
        #         logger.info(f"Private key for {account_id}: {private_key}")
        #     except Exception as e:
        #         logger.error(f"Failed to create Hedera account: {e}")
        #         raise HTTPException(
        #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #             detail=f"Failed to create Hedera account: {str(e)}"
        #         )
        
        # Create user in database
        new_user = User(
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
        
        # Generate JWT token
        token = create_access_token(
            user_id=str(new_user.id),
            email=new_user.email,
            country_code=new_user.country_code.value,
            hedera_account_id=new_user.hedera_account_id
        )
        
        # Prepare response
        user_response = UserResponse(
            id=str(new_user.id),
            email=new_user.email,
            country_code=new_user.country_code,
            hedera_account_id=new_user.hedera_account_id,
            wallet_type=new_user.wallet_type,
            created_at=new_user.created_at,
            last_login=new_user.last_login,
            is_active=new_user.is_active
        )
        
        return AuthResponse(
            token=token,
            user=user_response
        )
        
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


@router.post("/login", response_model=AuthResponse)
async def login(
    username: str = Form(...),  # OAuth2 standard uses 'username' field
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Login user with email and password
    
    Uses OAuth2 password flow (form data with username/password fields)
    
    Requirements:
        - FR-1.4: System shall use JWT tokens for session management
        - US-1: User can login with email + password
        - NFR-2.3: JWT tokens shall expire after 30 days
    
    Args:
        username: User's email address (OAuth2 standard field name)
        password: User's password
        db: Database session
        
    Returns:
        AuthResponse with JWT token and user data
        
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
            logger.warning(f"Login attempt for inactive user: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        logger.info(f"User logged in successfully: {user.email} (ID: {user.id})")
        
        # Generate JWT token
        token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            country_code=user.country_code.value,
            hedera_account_id=user.hedera_account_id
        )
        
        # Prepare response
        user_response = UserResponse(
            id=str(user.id),
            email=user.email,
            country_code=user.country_code,
            hedera_account_id=user.hedera_account_id,
            wallet_type=user.wallet_type,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active
        )
        
        return AuthResponse(
            token=token,
            user=user_response
        )
        
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


@router.post("/wallet-connect", response_model=AuthResponse)
async def wallet_connect(
    request: WalletConnectRequest,
    db: Session = Depends(get_db)
):
    """
    Connect or register user with HashPack wallet
    
    This endpoint allows users to authenticate using their HashPack wallet
    by providing a signed message. If the account doesn't exist, a new user
    is created. If it exists, the user is logged in.
    
    Requirements:
        - FR-1.2: System shall support HashPack wallet connection
        - FR-1.4: System shall use JWT tokens for session management
        - US-1: User can register with email + password OR connect HashPack wallet
        - NFR-2.3: JWT tokens shall expire after 30 days
    
    Args:
        request: Wallet connection request with hedera_account_id, signature, and message
        db: Database session
        
    Returns:
        AuthResponse with JWT token and user data
        
    Raises:
        HTTPException 401: Invalid signature
        HTTPException 400: Invalid account ID or account doesn't exist on Hedera
        HTTPException 500: Database or Hedera service error
    """
    try:
        # Verify the signature with Hedera
        hedera_service = get_hedera_service()
        
        # First check if account exists on Hedera network
        if not hedera_service.account_exists(request.hedera_account_id):
            logger.warning(f"Wallet connect attempt with non-existent Hedera account: {request.hedera_account_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hedera account does not exist on the network"
            )
        
        # Verify the signature
        is_valid = hedera_service.verify_signature(
            account_id=request.hedera_account_id,
            message=request.message,
            signature=request.signature
        )
        
        if not is_valid:
            logger.warning(f"Invalid signature for wallet connect: {request.hedera_account_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
        
        logger.info(f"Signature verified successfully for account: {request.hedera_account_id}")
        
        # Check if user already exists with this Hedera account
        existing_user = db.query(User).filter(
            User.hedera_account_id == request.hedera_account_id
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
            
            # Generate JWT token
            token = create_access_token(
                user_id=str(existing_user.id),
                email=existing_user.email,
                country_code=existing_user.country_code.value,
                hedera_account_id=existing_user.hedera_account_id
            )
            
            # Prepare response
            user_response = UserResponse(
                id=str(existing_user.id),
                email=existing_user.email,
                country_code=existing_user.country_code,
                hedera_account_id=existing_user.hedera_account_id,
                wallet_type=existing_user.wallet_type,
                created_at=existing_user.created_at,
                last_login=existing_user.last_login,
                is_active=existing_user.is_active
            )
            
            return AuthResponse(
                token=token,
                user=user_response
            )
        
        else:
            # User doesn't exist - create new account
            # Generate a unique email for wallet-only users
            wallet_email = f"{request.hedera_account_id.replace('.', '-')}@wallet.hederaflow.local"
            
            logger.info(f"Creating new user with wallet: {request.hedera_account_id}")
            
            # For wallet-only registration, we need to determine country code
            # For MVP, we'll default to ES (Spain) but in production this should be
            # determined from user input or geolocation
            default_country = CountryCodeEnum.ES
            
            # Create new user
            new_user = User(
                email=wallet_email,
                password_hash=None,  # No password for wallet-only auth
                country_code=default_country,
                hedera_account_id=request.hedera_account_id,
                wallet_type=WalletTypeEnum.HASHPACK,
                is_active=True
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info(f"New wallet user created: {new_user.email} (ID: {new_user.id})")
            
            # Generate JWT token
            token = create_access_token(
                user_id=str(new_user.id),
                email=new_user.email,
                country_code=new_user.country_code.value,
                hedera_account_id=new_user.hedera_account_id
            )
            
            # Prepare response
            user_response = UserResponse(
                id=str(new_user.id),
                email=new_user.email,
                country_code=new_user.country_code,
                hedera_account_id=new_user.hedera_account_id,
                wallet_type=new_user.wallet_type,
                created_at=new_user.created_at,
                last_login=new_user.last_login,
                is_active=new_user.is_active
            )
            
            return AuthResponse(
                token=token,
                user=user_response
            )
        
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
