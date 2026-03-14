"""
Unit tests for PrepaidTokenService.get_user_tokens method

Tests the token retrieval functionality.
"""
import pytest
from unittest.mock import Mock
from datetime import datetime

from app.services.prepaid_token_service import PrepaidTokenService, PrepaidTokenError


class TestGetUserTokens:
    """Test get_user_tokens method"""
    
    def test_get_all_user_tokens(self):
        """Test retrieving all tokens for a user"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - 3 tokens
        result_mock = Mock()
        result_mock.fetchall.return_value = [
            (
                'token-uuid-1', 'TOKEN-ES-2026-001', 'meter-uuid-1',
                100.0, 75.0,  # units_purchased, units_remaining
                147.0, None,  # amount_paid_hbar, amount_paid_usdc
                50.0, 'EUR',  # amount_paid_fiat, currency
                0.34, 0.40,  # exchange_rate, tariff_rate
                'active', '0.0.123456@1234567890.123',  # status, hedera_tx_id
                datetime(2026, 3, 3, 10, 0, 0),  # issued_at
                datetime(2027, 3, 3, 10, 0, 0),  # expires_at
                None  # depleted_at
            ),
            (
                'token-uuid-2', 'TOKEN-ES-2026-002', 'meter-uuid-1',
                50.0, 0.0,  # fully depleted
                73.5, None,
                25.0, 'EUR',
                0.34, 0.40,
                'depleted', '0.0.123456@1234567891.123',
                datetime(2026, 3, 2, 10, 0, 0),
                datetime(2027, 3, 2, 10, 0, 0),
                datetime(2026, 3, 10, 15, 30, 0)  # depleted_at
            ),
            (
                'token-uuid-3', 'TOKEN-ES-2026-003', 'meter-uuid-2',
                200.0, 200.0,  # unused token
                None, 50.0,  # USDC payment
                50.0, 'USD',
                1.0, 0.25,
                'active', '0.0.123456@1234567892.123',
                datetime(2026, 3, 4, 10, 0, 0),
                datetime(2027, 3, 4, 10, 0, 0),
                None
            )
        ]
        
        db_mock.execute.return_value = result_mock
        
        # Execute
        result = service.get_user_tokens(user_id='user-uuid')
        
        # Verify
        assert len(result) == 3
        
        # First token
        assert result[0]['token_id'] == 'TOKEN-ES-2026-001'
        assert result[0]['units_purchased'] == 100.0
        assert result[0]['units_remaining'] == 75.0
        assert result[0]['units_consumed'] == 25.0
        assert result[0]['amount_paid_hbar'] == 147.0
        assert result[0]['amount_paid_usdc'] is None
        assert result[0]['status'] == 'active'
        assert result[0]['depleted_at'] is None
        
        # Second token (depleted)
        assert result[1]['token_id'] == 'TOKEN-ES-2026-002'
        assert result[1]['units_remaining'] == 0.0
        assert result[1]['units_consumed'] == 50.0
        assert result[1]['status'] == 'depleted'
        assert result[1]['depleted_at'] is not None
        
        # Third token (USDC payment)
        assert result[2]['token_id'] == 'TOKEN-ES-2026-003'
        assert result[2]['amount_paid_usdc'] == 50.0
        assert result[2]['amount_paid_hbar'] is None
    
    def test_get_user_tokens_filter_by_status(self):
        """Test filtering tokens by status"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - only active tokens
        result_mock = Mock()
        result_mock.fetchall.return_value = [
            (
                'token-uuid-1', 'TOKEN-ES-2026-001', 'meter-uuid-1',
                100.0, 75.0,
                147.0, None,
                50.0, 'EUR',
                0.34, 0.40,
                'active', '0.0.123456@1234567890.123',
                datetime(2026, 3, 3, 10, 0, 0),
                datetime(2027, 3, 3, 10, 0, 0),
                None
            )
        ]
        
        db_mock.execute.return_value = result_mock
        
        # Execute
        result = service.get_user_tokens(user_id='user-uuid', status='active')
        
        # Verify
        assert len(result) == 1
        assert result[0]['status'] == 'active'
        
        # Verify query includes status filter
        call_args = db_mock.execute.call_args
        query_text = str(call_args[0][0])
        assert 'status = :status' in query_text
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args.kwargs
        assert params['status'] == 'active'
    
    def test_get_user_tokens_filter_by_meter(self):
        """Test filtering tokens by meter_id"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - tokens for specific meter
        result_mock = Mock()
        result_mock.fetchall.return_value = [
            (
                'token-uuid-1', 'TOKEN-ES-2026-001', 'meter-uuid-1',
                100.0, 75.0,
                147.0, None,
                50.0, 'EUR',
                0.34, 0.40,
                'active', '0.0.123456@1234567890.123',
                datetime(2026, 3, 3, 10, 0, 0),
                datetime(2027, 3, 3, 10, 0, 0),
                None
            )
        ]
        
        db_mock.execute.return_value = result_mock
        
        # Execute
        result = service.get_user_tokens(
            user_id='user-uuid',
            meter_id='meter-uuid-1'
        )
        
        # Verify
        assert len(result) == 1
        assert result[0]['meter_id'] == 'meter-uuid-1'
        
        # Verify query includes meter_id filter
        call_args = db_mock.execute.call_args
        query_text = str(call_args[0][0])
        assert 'meter_id = :meter_id' in query_text
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args.kwargs
        assert params['meter_id'] == 'meter-uuid-1'
    
    def test_get_user_tokens_filter_by_status_and_meter(self):
        """Test filtering tokens by both status and meter_id"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result
        result_mock = Mock()
        result_mock.fetchall.return_value = [
            (
                'token-uuid-1', 'TOKEN-ES-2026-001', 'meter-uuid-1',
                100.0, 75.0,
                147.0, None,
                50.0, 'EUR',
                0.34, 0.40,
                'active', '0.0.123456@1234567890.123',
                datetime(2026, 3, 3, 10, 0, 0),
                datetime(2027, 3, 3, 10, 0, 0),
                None
            )
        ]
        
        db_mock.execute.return_value = result_mock
        
        # Execute
        result = service.get_user_tokens(
            user_id='user-uuid',
            status='active',
            meter_id='meter-uuid-1'
        )
        
        # Verify
        assert len(result) == 1
        assert result[0]['status'] == 'active'
        assert result[0]['meter_id'] == 'meter-uuid-1'
        
        # Verify query includes both filters
        call_args = db_mock.execute.call_args
        query_text = str(call_args[0][0])
        assert 'status = :status' in query_text
        assert 'meter_id = :meter_id' in query_text
    
    def test_get_user_tokens_empty_result(self):
        """Test when user has no tokens"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock empty result
        result_mock = Mock()
        result_mock.fetchall.return_value = []
        
        db_mock.execute.return_value = result_mock
        
        # Execute
        result = service.get_user_tokens(user_id='user-uuid')
        
        # Verify
        assert len(result) == 0
        assert result == []
    
    def test_get_user_tokens_ordered_by_issued_at_desc(self):
        """Test that tokens are ordered by issued_at DESC (newest first)"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - tokens in descending order
        result_mock = Mock()
        result_mock.fetchall.return_value = [
            (
                'token-uuid-3', 'TOKEN-ES-2026-003', 'meter-uuid-1',
                100.0, 100.0,
                147.0, None,
                50.0, 'EUR',
                0.34, 0.40,
                'active', '0.0.123456@1234567892.123',
                datetime(2026, 3, 5, 10, 0, 0),  # Newest
                datetime(2027, 3, 5, 10, 0, 0),
                None
            ),
            (
                'token-uuid-2', 'TOKEN-ES-2026-002', 'meter-uuid-1',
                100.0, 50.0,
                147.0, None,
                50.0, 'EUR',
                0.34, 0.40,
                'active', '0.0.123456@1234567891.123',
                datetime(2026, 3, 4, 10, 0, 0),  # Middle
                datetime(2027, 3, 4, 10, 0, 0),
                None
            ),
            (
                'token-uuid-1', 'TOKEN-ES-2026-001', 'meter-uuid-1',
                100.0, 0.0,
                147.0, None,
                50.0, 'EUR',
                0.34, 0.40,
                'depleted', '0.0.123456@1234567890.123',
                datetime(2026, 3, 3, 10, 0, 0),  # Oldest
                datetime(2027, 3, 3, 10, 0, 0),
                datetime(2026, 3, 10, 15, 30, 0)
            )
        ]
        
        db_mock.execute.return_value = result_mock
        
        # Execute
        result = service.get_user_tokens(user_id='user-uuid')
        
        # Verify order (newest first)
        assert result[0]['token_id'] == 'TOKEN-ES-2026-003'
        assert result[1]['token_id'] == 'TOKEN-ES-2026-002'
        assert result[2]['token_id'] == 'TOKEN-ES-2026-001'
        
        # Verify query includes ORDER BY
        call_args = db_mock.execute.call_args
        query_text = str(call_args[0][0])
        assert 'ORDER BY issued_at DESC' in query_text
    
    def test_get_user_tokens_units_consumed_calculation(self):
        """Test that units_consumed is calculated correctly"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result
        result_mock = Mock()
        result_mock.fetchall.return_value = [
            (
                'token-uuid-1', 'TOKEN-ES-2026-001', 'meter-uuid-1',
                100.0, 35.5,  # purchased 100, remaining 35.5
                147.0, None,
                50.0, 'EUR',
                0.34, 0.40,
                'active', '0.0.123456@1234567890.123',
                datetime(2026, 3, 3, 10, 0, 0),
                datetime(2027, 3, 3, 10, 0, 0),
                None
            )
        ]
        
        db_mock.execute.return_value = result_mock
        
        # Execute
        result = service.get_user_tokens(user_id='user-uuid')
        
        # Verify units_consumed = units_purchased - units_remaining
        assert result[0]['units_consumed'] == 64.5  # 100 - 35.5
    
    def test_get_user_tokens_includes_all_fields(self):
        """Test that all token fields are included in response"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result
        result_mock = Mock()
        result_mock.fetchall.return_value = [
            (
                'token-uuid-1', 'TOKEN-ES-2026-001', 'meter-uuid-1',
                100.0, 75.0,
                147.0, None,
                50.0, 'EUR',
                0.34, 0.40,
                'active', '0.0.123456@1234567890.123',
                datetime(2026, 3, 3, 10, 0, 0),
                datetime(2027, 3, 3, 10, 0, 0),
                None
            )
        ]
        
        db_mock.execute.return_value = result_mock
        
        # Execute
        result = service.get_user_tokens(user_id='user-uuid')
        
        # Verify all expected fields are present
        token = result[0]
        expected_fields = [
            'id', 'token_id', 'meter_id',
            'units_purchased', 'units_remaining', 'units_consumed',
            'amount_paid_hbar', 'amount_paid_usdc', 'amount_paid_fiat',
            'currency', 'exchange_rate', 'tariff_rate',
            'status', 'hedera_tx_id',
            'issued_at', 'expires_at', 'depleted_at'
        ]
        
        for field in expected_fields:
            assert field in token, f"Field '{field}' missing from token"
    
    def test_get_user_tokens_datetime_serialization(self):
        """Test that datetime fields are serialized to ISO format"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result
        result_mock = Mock()
        result_mock.fetchall.return_value = [
            (
                'token-uuid-1', 'TOKEN-ES-2026-001', 'meter-uuid-1',
                100.0, 75.0,
                147.0, None,
                50.0, 'EUR',
                0.34, 0.40,
                'active', '0.0.123456@1234567890.123',
                datetime(2026, 3, 3, 10, 0, 0),
                datetime(2027, 3, 3, 10, 0, 0),
                None
            )
        ]
        
        db_mock.execute.return_value = result_mock
        
        # Execute
        result = service.get_user_tokens(user_id='user-uuid')
        
        # Verify datetime fields are ISO strings
        assert isinstance(result[0]['issued_at'], str)
        assert isinstance(result[0]['expires_at'], str)
        assert result[0]['issued_at'] == '2026-03-03T10:00:00'
        assert result[0]['expires_at'] == '2027-03-03T10:00:00'
        assert result[0]['depleted_at'] is None
    
    def test_get_user_tokens_database_error(self):
        """Test that PrepaidTokenError is raised on database error"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock database error
        db_mock.execute.side_effect = Exception("Database connection failed")
        
        # Execute & Verify
        with pytest.raises(PrepaidTokenError, match="Failed to get tokens"):
            service.get_user_tokens(user_id='user-uuid')
    
    def test_get_user_tokens_different_statuses(self):
        """Test retrieving tokens with different statuses"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Test each status
        statuses = ['active', 'depleted', 'expired', 'cancelled']
        
        for status in statuses:
            # Mock query result
            result_mock = Mock()
            result_mock.fetchall.return_value = [
                (
                    'token-uuid-1', f'TOKEN-ES-2026-001', 'meter-uuid-1',
                    100.0, 0.0 if status == 'depleted' else 75.0,
                    147.0, None,
                    50.0, 'EUR',
                    0.34, 0.40,
                    status, '0.0.123456@1234567890.123',
                    datetime(2026, 3, 3, 10, 0, 0),
                    datetime(2027, 3, 3, 10, 0, 0),
                    datetime(2026, 3, 10, 15, 30, 0) if status == 'depleted' else None
                )
            ]
            
            db_mock.execute.return_value = result_mock
            
            # Execute
            result = service.get_user_tokens(user_id='user-uuid', status=status)
            
            # Verify
            assert len(result) == 1
            assert result[0]['status'] == status
    
    def test_get_user_tokens_multiple_meters(self):
        """Test retrieving tokens across multiple meters"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - tokens for different meters
        result_mock = Mock()
        result_mock.fetchall.return_value = [
            (
                'token-uuid-1', 'TOKEN-ES-2026-001', 'meter-uuid-1',
                100.0, 75.0,
                147.0, None,
                50.0, 'EUR',
                0.34, 0.40,
                'active', '0.0.123456@1234567890.123',
                datetime(2026, 3, 3, 10, 0, 0),
                datetime(2027, 3, 3, 10, 0, 0),
                None
            ),
            (
                'token-uuid-2', 'TOKEN-ES-2026-002', 'meter-uuid-2',
                50.0, 25.0,
                73.5, None,
                25.0, 'EUR',
                0.34, 0.40,
                'active', '0.0.123456@1234567891.123',
                datetime(2026, 3, 2, 10, 0, 0),
                datetime(2027, 3, 2, 10, 0, 0),
                None
            )
        ]
        
        db_mock.execute.return_value = result_mock
        
        # Execute
        result = service.get_user_tokens(user_id='user-uuid')
        
        # Verify
        assert len(result) == 2
        assert result[0]['meter_id'] == 'meter-uuid-1'
        assert result[1]['meter_id'] == 'meter-uuid-2'
    
    def test_get_user_tokens_numeric_precision(self):
        """Test that numeric fields maintain precision"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result with precise decimals
        result_mock = Mock()
        result_mock.fetchall.return_value = [
            (
                'token-uuid-1', 'TOKEN-ES-2026-001', 'meter-uuid-1',
                123.456, 78.901,  # Precise decimals
                147.123456, None,
                50.12, 'EUR',
                0.340000, 0.400000,
                'active', '0.0.123456@1234567890.123',
                datetime(2026, 3, 3, 10, 0, 0),
                datetime(2027, 3, 3, 10, 0, 0),
                None
            )
        ]
        
        db_mock.execute.return_value = result_mock
        
        # Execute
        result = service.get_user_tokens(user_id='user-uuid')
        
        # Verify precision is maintained
        assert result[0]['units_purchased'] == 123.456
        assert result[0]['units_remaining'] == 78.901
        assert result[0]['amount_paid_hbar'] == 147.123456
        assert result[0]['amount_paid_fiat'] == 50.12
