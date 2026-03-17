"""
Unit Tests for Hedera Account Creation Flow (Task 6.6)

Tests the integration of Hedera account creation with user registration.

Requirements:
    - FR-1.3: System shall create Hedera testnet account for new users without wallet
    - US-1: System creates Hedera account (testnet) if user doesn't have one

Test Coverage:
    1. Successful account creation during registration
    2. Account ID and private key storage
    3. Error handling for Hedera testnet failures
    4. Wallet-only registration (no account creation)
    5. Registration with existing Hedera account
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.api.endpoints.auth import register
from app.schemas.auth import RegisterRequest
from app.models.user import User, CountryCodeEnum, WalletTypeEnum


class TestHederaAccountCreation:
    """Test suite for Hedera account creation during registration"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        return db
    
    @pytest.fixture
    def mock_hedera_service(self):
        """Mock Hedera service"""
        with patch('app.api.endpoints.auth.get_hedera_service') as mock:
            service = Mock()
            service.create_account.return_value = ("0.0.123456", "302e020100300506032b657004220420...")
            mock.return_value = service
            yield service
    
    @pytest.fixture
    def registration_request(self):
        """Standard registration request without Hedera account"""
        return RegisterRequest(
            email="test@example.com",
            password="TestPass123",
            country_code=CountryCodeEnum.ES
        )
    
    @pytest.mark.asyncio
    async def test_account_creation_on_registration(self, mock_db, mock_hedera_service, registration_request):
        """
        Test that Hedera account is created when user registers without wallet
        
        Requirements: FR-1.3, US-1
        """
        # Mock user creation
        created_user = User(
            id="test-user-id",
            email=registration_request.email,
            password_hash="hashed_password",
            country_code=registration_request.country_code,
            hedera_account_id="0.0.123456",
            wallet_type=WalletTypeEnum.SYSTEM_GENERATED,
            is_active=True
        )
        
        def mock_refresh(user):
            user.id = created_user.id
            user.hedera_account_id = created_user.hedera_account_id
            user.wallet_type = created_user.wallet_type
        
        mock_db.refresh.side_effect = mock_refresh
        
        # Execute registration
        with patch('app.api.endpoints.auth.hash_password', return_value="hashed_password"):
            with patch('app.api.endpoints.auth.validate_password_strength', return_value=(True, None)):
                with patch('app.api.endpoints.auth.create_access_token', return_value="jwt_token"):
                    response = await register(registration_request, mock_db)
        
        # Verify Hedera account was created
        mock_hedera_service.create_account.assert_called_once_with(initial_balance=10.0)
        
        # Verify user was created with Hedera account ID
        assert mock_db.add.called
        added_user = mock_db.add.call_args[0][0]
        assert added_user.hedera_account_id == "0.0.123456"
        assert added_user.wallet_type == WalletTypeEnum.SYSTEM_GENERATED
        
        # Verify response contains Hedera account
        assert response.user.hedera_account_id == "0.0.123456"
        assert response.user.wallet_type == WalletTypeEnum.SYSTEM_GENERATED
    
    @pytest.mark.asyncio
    async def test_account_creation_stores_account_id(self, mock_db, mock_hedera_service, registration_request):
        """
        Test that account ID is properly stored in database
        
        Requirements: FR-1.3
        """
        created_user = User(
            id="test-user-id",
            email=registration_request.email,
            password_hash="hashed_password",
            country_code=registration_request.country_code,
            hedera_account_id="0.0.123456",
            wallet_type=WalletTypeEnum.SYSTEM_GENERATED,
            is_active=True
        )
        
        def mock_refresh(user):
            user.id = created_user.id
            user.hedera_account_id = created_user.hedera_account_id
        
        mock_db.refresh.side_effect = mock_refresh
        
        with patch('app.api.endpoints.auth.hash_password', return_value="hashed_password"):
            with patch('app.api.endpoints.auth.validate_password_strength', return_value=(True, None)):
                with patch('app.api.endpoints.auth.create_access_token', return_value="jwt_token"):
                    response = await register(registration_request, mock_db)
        
        # Verify account ID was stored
        added_user = mock_db.add.call_args[0][0]
        assert added_user.hedera_account_id == "0.0.123456"
        assert added_user.hedera_account_id is not None
        assert len(added_user.hedera_account_id) > 0
    
    @pytest.mark.asyncio
    async def test_hedera_account_creation_failure(self, mock_db, registration_request):
        """
        Test error handling when Hedera account creation fails
        
        Requirements: FR-1.3 (error handling)
        """
        # Mock Hedera service to raise exception
        with patch('app.api.endpoints.auth.get_hedera_service') as mock_service:
            service = Mock()
            service.create_account.side_effect = Exception("Hedera testnet unavailable")
            mock_service.return_value = service
            
            with patch('app.api.endpoints.auth.hash_password', return_value="hashed_password"):
                with patch('app.api.endpoints.auth.validate_password_strength', return_value=(True, None)):
                    # Should raise HTTPException with 500 status
                    with pytest.raises(HTTPException) as exc_info:
                        await register(registration_request, mock_db)
                    
                    assert exc_info.value.status_code == 500
                    assert "Failed to create Hedera account" in exc_info.value.detail
                    assert "Hedera testnet unavailable" in exc_info.value.detail
        
        # Verify user was NOT created in database
        assert not mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_registration_with_existing_wallet(self, mock_db):
        """
        Test registration with existing HashPack wallet (no account creation)
        
        Requirements: US-1 (wallet connection)
        """
        # Registration request with existing Hedera account
        request = RegisterRequest(
            email="wallet@example.com",
            password="TestPass123",
            country_code=CountryCodeEnum.ES,
            hedera_account_id="0.0.999999"  # Existing wallet
        )
        
        created_user = User(
            id="test-user-id",
            email=request.email,
            password_hash="hashed_password",
            country_code=request.country_code,
            hedera_account_id="0.0.999999",
            wallet_type=WalletTypeEnum.HASHPACK,
            is_active=True
        )
        
        def mock_refresh(user):
            user.id = created_user.id
            user.hedera_account_id = created_user.hedera_account_id
            user.wallet_type = created_user.wallet_type
        
        mock_db.refresh.side_effect = mock_refresh
        
        with patch('app.api.endpoints.auth.get_hedera_service') as mock_service:
            with patch('app.api.endpoints.auth.hash_password', return_value="hashed_password"):
                with patch('app.api.endpoints.auth.validate_password_strength', return_value=(True, None)):
                    with patch('app.api.endpoints.auth.create_access_token', return_value="jwt_token"):
                        response = await register(request, mock_db)
            
            # Verify Hedera account was NOT created
            mock_service.return_value.create_account.assert_not_called()
        
        # Verify user was created with provided account ID
        added_user = mock_db.add.call_args[0][0]
        assert added_user.hedera_account_id == "0.0.999999"
        assert added_user.wallet_type == WalletTypeEnum.HASHPACK
        
        # Verify response
        assert response.user.hedera_account_id == "0.0.999999"
        assert response.user.wallet_type == WalletTypeEnum.HASHPACK
    
    @pytest.mark.asyncio
    async def test_wallet_type_system_generated(self, mock_db, mock_hedera_service, registration_request):
        """
        Test that wallet_type is set to SYSTEM_GENERATED for created accounts
        
        Requirements: FR-1.3
        """
        created_user = User(
            id="test-user-id",
            email=registration_request.email,
            password_hash="hashed_password",
            country_code=registration_request.country_code,
            hedera_account_id="0.0.123456",
            wallet_type=WalletTypeEnum.SYSTEM_GENERATED,
            is_active=True
        )
        
        def mock_refresh(user):
            user.wallet_type = created_user.wallet_type
        
        mock_db.refresh.side_effect = mock_refresh
        
        with patch('app.api.endpoints.auth.hash_password', return_value="hashed_password"):
            with patch('app.api.endpoints.auth.validate_password_strength', return_value=(True, None)):
                with patch('app.api.endpoints.auth.create_access_token', return_value="jwt_token"):
                    response = await register(registration_request, mock_db)
        
        # Verify wallet type
        added_user = mock_db.add.call_args[0][0]
        assert added_user.wallet_type == WalletTypeEnum.SYSTEM_GENERATED
    
    @pytest.mark.asyncio
    async def test_wallet_type_hashpack(self, mock_db):
        """
        Test that wallet_type is set to HASHPACK for existing wallets
        
        Requirements: US-1
        """
        request = RegisterRequest(
            email="wallet@example.com",
            password="TestPass123",
            country_code=CountryCodeEnum.ES,
            hedera_account_id="0.0.999999"
        )
        
        created_user = User(
            id="test-user-id",
            email=request.email,
            password_hash="hashed_password",
            country_code=request.country_code,
            hedera_account_id="0.0.999999",
            wallet_type=WalletTypeEnum.HASHPACK,
            is_active=True
        )
        
        def mock_refresh(user):
            user.wallet_type = created_user.wallet_type
        
        mock_db.refresh.side_effect = mock_refresh
        
        with patch('app.api.endpoints.auth.get_hedera_service'):
            with patch('app.api.endpoints.auth.hash_password', return_value="hashed_password"):
                with patch('app.api.endpoints.auth.validate_password_strength', return_value=(True, None)):
                    with patch('app.api.endpoints.auth.create_access_token', return_value="jwt_token"):
                        response = await register(request, mock_db)
        
        # Verify wallet type
        added_user = mock_db.add.call_args[0][0]
        assert added_user.wallet_type == WalletTypeEnum.HASHPACK
    
    @pytest.mark.asyncio
    async def test_initial_balance_10_hbar(self, mock_db, mock_hedera_service, registration_request):
        """
        Test that new accounts are created with 10 HBAR initial balance
        
        Requirements: FR-1.3
        """
        created_user = User(
            id="test-user-id",
            email=registration_request.email,
            password_hash="hashed_password",
            country_code=registration_request.country_code,
            hedera_account_id="0.0.123456",
            wallet_type=WalletTypeEnum.SYSTEM_GENERATED,
            is_active=True
        )
        
        mock_db.refresh.side_effect = lambda user: setattr(user, 'id', created_user.id)
        
        with patch('app.api.endpoints.auth.hash_password', return_value="hashed_password"):
            with patch('app.api.endpoints.auth.validate_password_strength', return_value=(True, None)):
                with patch('app.api.endpoints.auth.create_access_token', return_value="jwt_token"):
                    await register(registration_request, mock_db)
        
        # Verify initial balance parameter
        mock_hedera_service.create_account.assert_called_once_with(initial_balance=10.0)
    
    @pytest.mark.asyncio
    async def test_private_key_logged(self, mock_db, mock_hedera_service, registration_request, caplog):
        """
        Test that private key is logged for user retrieval (MVP only)
        
        Requirements: FR-1.3
        Note: In production, private key should be securely stored or given to user
        """
        created_user = User(
            id="test-user-id",
            email=registration_request.email,
            password_hash="hashed_password",
            country_code=registration_request.country_code,
            hedera_account_id="0.0.123456",
            wallet_type=WalletTypeEnum.SYSTEM_GENERATED,
            is_active=True
        )
        
        mock_db.refresh.side_effect = lambda user: setattr(user, 'id', created_user.id)
        
        with patch('app.api.endpoints.auth.hash_password', return_value="hashed_password"):
            with patch('app.api.endpoints.auth.validate_password_strength', return_value=(True, None)):
                with patch('app.api.endpoints.auth.create_access_token', return_value="jwt_token"):
                    await register(registration_request, mock_db)
        
        # Verify private key was logged
        assert "Private key for 0.0.123456" in caplog.text
        assert "302e020100300506032b657004220420" in caplog.text


class TestHederaServiceIntegration:
    """Integration tests for HederaService"""
    
    def test_hedera_service_create_account_returns_tuple(self):
        """
        Test that create_account returns (account_id, private_key) tuple
        
        Requirements: FR-1.3
        """
        with patch('app.services.hedera_service.Client') as mock_client:
            with patch('app.services.hedera_service.PrivateKey') as mock_private_key:
                with patch('app.services.hedera_service.AccountCreateTransaction') as mock_transaction:
                    # Mock the transaction flow
                    mock_key = Mock()
                    mock_key.getPublicKey.return_value = Mock()
                    mock_private_key.generate.return_value = mock_key
                    mock_private_key.fromString.return_value = mock_key
                    
                    mock_receipt = Mock()
                    mock_receipt.accountId = "0.0.123456"
                    
                    mock_response = Mock()
                    mock_response.getReceipt.return_value = mock_receipt
                    
                    mock_tx = Mock()
                    mock_tx.setKey.return_value = mock_tx
                    mock_tx.setInitialBalance.return_value = mock_tx
                    mock_tx.setMaxTransactionFee.return_value = mock_tx
                    mock_tx.execute.return_value = mock_response
                    
                    mock_transaction.return_value = mock_tx
                    
                    # Import and test
                    from app.services.hedera_service import HederaService
                    
                    service = HederaService()
                    result = service.create_account(initial_balance=10.0)
                    
                    # Verify result is a tuple
                    assert isinstance(result, tuple)
                    assert len(result) == 2
                    
                    account_id, private_key = result
                    assert isinstance(account_id, str)
                    assert isinstance(private_key, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
