"""
Tests for storing HCS sequence number in database.

This module tests that HCS topic ID and sequence number are correctly
stored in the prepaid_tokens table when creating a token.

Requirements:
    - Task 1.4: Store HCS sequence number in database
    - FR-8.7: System shall log token issuance to HCS
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from sqlalchemy import text

from app.services.prepaid_token_service import PrepaidTokenService


class TestStoreHCSSequence:
    """Test suite for storing HCS sequence numbers"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = Mock()
        
        # Mock execute to return a result with id, token_id, issued_at, expires_at
        mock_result = Mock()
        mock_result.fetchone.return_value = (
            "550e8400-e29b-41d4-a716-446655440000",  # id
            "TOKEN-ES-2026-001",  # token_id
            datetime(2026, 3, 3, 10, 0, 0),  # issued_at
            datetime(2027, 3, 3, 10, 0, 0)   # expires_at
        )
        db.execute.return_value = mock_result
        db.commit = Mock()
        
        return db
    
    @pytest.fixture
    def prepaid_service(self, mock_db):
        """Create PrepaidTokenService with mocked database"""
        with patch('app.services.prepaid_token_service.get_tariff') as mock_tariff:
            # Mock tariff service to return valid tariff data
            mock_tariff.return_value = {
                'country_code': 'ES',
                'utility_provider': 'Iberdrola',
                'rate_per_kwh': 0.40,
                'currency': 'EUR',
                'rate_structure': {'type': 'flat', 'rate': 0.40}
            }
            service = PrepaidTokenService(mock_db)
            return service
    
    def test_create_token_with_hcs_info(self, prepaid_service, mock_db):
        """
        Test that create_token stores HCS topic ID and sequence number.
        
        Verifies:
        - HCS topic ID is included in INSERT query
        - HCS sequence number is included in INSERT query
        - HCS info is returned in response
        - HCS sequence is logged
        """
        # Arrange
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        meter_id = "660e8400-e29b-41d4-a716-446655440000"
        amount_fiat = 50.0
        currency = "EUR"
        country_code = "ES"
        utility_provider = "Iberdrola"
        payment_method = "HBAR"
        amount_crypto = 147.0
        exchange_rate = 0.34
        hedera_tx_id = "0.0.123456@1234567890.123"
        hcs_topic_id = "0.0.5078302"
        hcs_sequence_number = 12345
        
        with patch('app.services.prepaid_token_service.get_tariff') as mock_tariff:
            mock_tariff.return_value = {
                'country_code': 'ES',
                'utility_provider': 'Iberdrola',
                'rate_per_kwh': 0.40,
                'currency': 'EUR',
                'rate_structure': {'type': 'flat', 'rate': 0.40}
            }
            
            # Act
            result = prepaid_service.create_token(
                user_id=user_id,
                meter_id=meter_id,
                amount_fiat=amount_fiat,
                currency=currency,
                country_code=country_code,
                utility_provider=utility_provider,
                payment_method=payment_method,
                amount_crypto=amount_crypto,
                exchange_rate=exchange_rate,
                hedera_tx_id=hedera_tx_id,
                hcs_topic_id=hcs_topic_id,
                hcs_sequence_number=hcs_sequence_number
            )
        
        # Assert - Verify INSERT query was called
        assert mock_db.execute.called
        call_args = mock_db.execute.call_args
        
        # Verify SQL includes HCS fields
        sql_query = str(call_args[0][0])
        assert "hcs_topic_id" in sql_query
        assert "hcs_sequence_number" in sql_query
        
        # Verify params include HCS values
        params = call_args[0][1]
        assert params['hcs_topic_id'] == hcs_topic_id
        assert params['hcs_sequence_number'] == hcs_sequence_number
        
        # Verify commit was called
        assert mock_db.commit.called
        
        # Verify response includes HCS info
        assert result['hcs_topic_id'] == hcs_topic_id
        assert result['hcs_sequence_number'] == hcs_sequence_number
    
    def test_create_token_without_hcs_info(self, prepaid_service, mock_db):
        """
        Test that create_token works when HCS info is not provided.
        
        Verifies:
        - Token can be created without HCS info (optional)
        - HCS fields are set to None in database
        """
        # Arrange
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        meter_id = "660e8400-e29b-41d4-a716-446655440000"
        amount_fiat = 50.0
        currency = "EUR"
        country_code = "ES"
        utility_provider = "Iberdrola"
        
        with patch('app.services.prepaid_token_service.get_tariff') as mock_tariff:
            mock_tariff.return_value = {
                'country_code': 'ES',
                'utility_provider': 'Iberdrola',
                'rate_per_kwh': 0.40,
                'currency': 'EUR',
                'rate_structure': {'type': 'flat',
            }
            
            # Act
            result = prepaid_service.create_token(
                user_id=user_id,
                meter_id=meter_id,
                amount_fiat=amount_fiat,
                currency=currency,
                country_code=country_code,
                utility_provider=utility_provider
                # No HCS info provided
            )
        
        # Assert - Verify params include None for HCS fields
        call_args = mock_db.execute.call_args
        params = call_args[0][1]
        assert params['hcs_topic_id'] is None
        assert params['hcs_sequence_number'] is None
        
        # Verify response includes None for HCS info
        assert result['hcs_topic_id'] is None
        assert result['hcs_sequence_number'] is None
    
    def test_create_token_with_partial_hcs_info(self, prepaid_service, mock_db):
        """
        Test that create_token handles partial HCS info correctly.
        
        Verifies:
        - Can provide topic ID without sequence number
        - Can provide sequence number without topic ID
        """
        # Arrange
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        meter_id = "660e8400-e29b-41d4-a716-446655440000"
        amount_fiat = 50.0
        currency = "EUR"
        country_code = "ES"
        utility_provider = "Iberdrola"
        hcs_topic_id = "0.0.5078302"
        
        with patch('app.services.prepaid_token_service.get_tariff') as mock_tariff:
            mock_tariff.return_value = {
                'country_code': 'ES',
                'utility_provider': 'Iberdrola',
                'rate_per_kwh': 0.40,
                'currency': 'EUR',
                'rate_structure': {'type': 'flat', 'rate': 0.40}
            }
            
            # Act - Only topic ID provided
            result = prepaid_service.create_token(
                user_id=user_id,
                meter_id=meter_id,
                amount_fiat=amount_fiat,
                currency=currency,
                country_code=country_code,
                utility_provider=utility_provider,
                hcs_topic_id=hcs_topic_id
                # No sequence number
            )
        
        # Assert
        call_args = mock_db.execute.call_args
        params = call_args[0][1]
        assert params['hcs_topic_id'] == hcs_topic_id
        assert params['hcs_sequence_number'] is None
        
        assert result['hcs_topic_id'] == hcs_topic_id
        assert result['hcs_sequence_number'] is None
