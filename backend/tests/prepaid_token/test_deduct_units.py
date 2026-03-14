"""
Unit tests for PrepaidTokenService.deduct_units method

Tests the FIFO unit deduction functionality.
"""
import pytest
from unittest.mock import Mock, patch

from app.services.prepaid_token_service import PrepaidTokenService, PrepaidTokenError


class TestDeductUnits:
    """Test deduct_units method"""
    
    def test_deduct_from_single_token_partial(self):
        """Test deducting units from a single token (partial deduction)"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - single token with 100 kWh
        tokens_result = Mock()
        tokens_result.fetchall.return_value = [
            ('token-uuid-1', 'TOKEN-ES-2026-001', 100.0)
        ]
        
        # Mock update result
        update_result = Mock()
        
        # Setup execute to return different mocks for query and update
        db_mock.execute.side_effect = [tokens_result, update_result]
        
        # Execute - deduct 30 kWh
        result = service.deduct_units(
            meter_id='meter-uuid',
            consumption_kwh=30.0
        )
        
        # Verify
        assert result['total_deducted'] == 30.0
        assert result['remaining_consumption'] == 0.0
        assert len(result['tokens_deducted']) == 1
        assert result['tokens_deducted'][0]['token_id'] == 'TOKEN-ES-2026-001'
        assert result['tokens_deducted'][0]['deducted'] == 30.0
        assert result['tokens_deducted'][0]['remaining'] == 70.0
        assert result['tokens_deducted'][0]['depleted'] is False
        
        # Verify commit was called
        db_mock.commit.assert_called_once()
    
    def test_deduct_from_single_token_full(self):
        """Test deducting all units from a single token (full depletion)"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - single token with 50 kWh
        tokens_result = Mock()
        tokens_result.fetchall.return_value = [
            ('token-uuid-1', 'TOKEN-ES-2026-001', 50.0)
        ]
        
        # Mock update result
        update_result = Mock()
        
        # Setup execute to return different mocks
        db_mock.execute.side_effect = [tokens_result, update_result]
        
        # Execute - deduct exactly 50 kWh
        result = service.deduct_units(
            meter_id='meter-uuid',
            consumption_kwh=50.0
        )
        
        # Verify
        assert result['total_deducted'] == 50.0
        assert result['remaining_consumption'] == 0.0
        assert len(result['tokens_deducted']) == 1
        assert result['tokens_deducted'][0]['token_id'] == 'TOKEN-ES-2026-001'
        assert result['tokens_deducted'][0]['deducted'] == 50.0
        assert result['tokens_deducted'][0]['remaining'] == 0.0
        assert result['tokens_deducted'][0]['depleted'] is True
        
        # Verify commit was called
        db_mock.commit.assert_called_once()
    
    def test_deduct_from_multiple_tokens_fifo(self):
        """Test FIFO deduction from multiple tokens (oldest first)"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - 3 tokens in FIFO order
        tokens_result = Mock()
        tokens_result.fetchall.return_value = [
            ('token-uuid-1', 'TOKEN-ES-2026-001', 30.0),  # Oldest
            ('token-uuid-2', 'TOKEN-ES-2026-002', 50.0),
            ('token-uuid-3', 'TOKEN-ES-2026-003', 100.0)  # Newest
        ]
        
        # Mock update results
        update_result_1 = Mock()
        update_result_2 = Mock()
        
        # Setup execute to return different mocks
        db_mock.execute.side_effect = [tokens_result, update_result_1, update_result_2]
        
        # Execute - deduct 70 kWh (should use first 2 tokens)
        result = service.deduct_units(
            meter_id='meter-uuid',
            consumption_kwh=70.0
        )
        
        # Verify
        assert result['total_deducted'] == 70.0
        assert result['remaining_consumption'] == 0.0
        assert len(result['tokens_deducted']) == 2
        
        # First token (oldest) should be fully depleted
        assert result['tokens_deducted'][0]['token_id'] == 'TOKEN-ES-2026-001'
        assert result['tokens_deducted'][0]['deducted'] == 30.0
        assert result['tokens_deducted'][0]['remaining'] == 0.0
        assert result['tokens_deducted'][0]['depleted'] is True
        
        # Second token should have 10 kWh remaining
        assert result['tokens_deducted'][1]['token_id'] == 'TOKEN-ES-2026-002'
        assert result['tokens_deducted'][1]['deducted'] == 40.0
        assert result['tokens_deducted'][1]['remaining'] == 10.0
        assert result['tokens_deducted'][1]['depleted'] is False
        
        # Verify commit was called
        db_mock.commit.assert_called_once()
    
    def test_deduct_insufficient_balance(self):
        """Test deduction when tokens don't have enough balance"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - single token with only 20 kWh
        tokens_result = Mock()
        tokens_result.fetchall.return_value = [
            ('token-uuid-1', 'TOKEN-ES-2026-001', 20.0)
        ]
        
        # Mock update result
        update_result = Mock()
        
        # Setup execute to return different mocks
        db_mock.execute.side_effect = [tokens_result, update_result]
        
        # Execute - try to deduct 50 kWh (more than available)
        result = service.deduct_units(
            meter_id='meter-uuid',
            consumption_kwh=50.0
        )
        
        # Verify
        assert result['total_deducted'] == 20.0
        assert result['remaining_consumption'] == 30.0  # 30 kWh not covered
        assert len(result['tokens_deducted']) == 1
        assert result['tokens_deducted'][0]['token_id'] == 'TOKEN-ES-2026-001'
        assert result['tokens_deducted'][0]['deducted'] == 20.0
        assert result['tokens_deducted'][0]['remaining'] == 0.0
        assert result['tokens_deducted'][0]['depleted'] is True
        
        # Verify commit was called
        db_mock.commit.assert_called_once()
    
    def test_deduct_no_active_tokens(self):
        """Test deduction when no active tokens exist"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - no tokens
        tokens_result = Mock()
        tokens_result.fetchall.return_value = []
        
        # Setup execute to return empty result
        db_mock.execute.return_value = tokens_result
        
        # Execute
        result = service.deduct_units(
            meter_id='meter-uuid',
            consumption_kwh=50.0
        )
        
        # Verify
        assert result['total_deducted'] == 0.0
        assert result['remaining_consumption'] == 50.0
        assert len(result['tokens_deducted']) == 0
        
        # Verify commit was NOT called (no changes)
        db_mock.commit.assert_not_called()
    
    def test_deduct_low_balance_alert(self):
        """Test that low balance alert is triggered when balance < 10 kWh"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - token with 15 kWh
        tokens_result = Mock()
        tokens_result.fetchall.return_value = [
            ('token-uuid-1', 'TOKEN-ES-2026-001', 15.0)
        ]
        
        # Mock update result
        update_result = Mock()
        
        # Setup execute to return different mocks
        db_mock.execute.side_effect = [tokens_result, update_result]
        
        # Execute - deduct 10 kWh (leaving 5 kWh, which is < 10)
        with patch('app.services.prepaid_token_service.logger') as mock_logger:
            result = service.deduct_units(
                meter_id='meter-uuid',
                consumption_kwh=10.0
            )
            
            # Verify low balance warning was logged
            mock_logger.warning.assert_called()
            warning_call = mock_logger.warning.call_args[0][0]
            assert 'Low balance alert' in warning_call
            assert 'TOKEN-ES-2026-001' in warning_call
        
        # Verify result
        assert result['tokens_deducted'][0]['remaining'] == 5.0
        assert result['tokens_deducted'][0]['depleted'] is False
    
    def test_deduct_no_low_balance_alert_when_above_threshold(self):
        """Test that no low balance alert when balance >= 10 kWh"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - token with 50 kWh
        tokens_result = Mock()
        tokens_result.fetchall.return_value = [
            ('token-uuid-1', 'TOKEN-ES-2026-001', 50.0)
        ]
        
        # Mock update result
        update_result = Mock()
        
        # Setup execute to return different mocks
        db_mock.execute.side_effect = [tokens_result, update_result]
        
        # Execute - deduct 30 kWh (leaving 20 kWh, which is >= 10)
        with patch('app.services.prepaid_token_service.logger') as mock_logger:
            result = service.deduct_units(
                meter_id='meter-uuid',
                consumption_kwh=30.0
            )
            
            # Verify no low balance warning was logged
            mock_logger.warning.assert_not_called()
        
        # Verify result
        assert result['tokens_deducted'][0]['remaining'] == 20.0
    
    def test_deduct_no_low_balance_alert_when_depleted(self):
        """Test that no low balance alert when token is fully depleted"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - token with 10 kWh
        tokens_result = Mock()
        tokens_result.fetchall.return_value = [
            ('token-uuid-1', 'TOKEN-ES-2026-001', 10.0)
        ]
        
        # Mock update result
        update_result = Mock()
        
        # Setup execute to return different mocks
        db_mock.execute.side_effect = [tokens_result, update_result]
        
        # Execute - deduct exactly 10 kWh (leaving 0 kWh)
        with patch('app.services.prepaid_token_service.logger') as mock_logger:
            result = service.deduct_units(
                meter_id='meter-uuid',
                consumption_kwh=10.0
            )
            
            # Verify no low balance warning (because balance is 0, not between 0 and 10)
            mock_logger.warning.assert_not_called()
        
        # Verify result
        assert result['tokens_deducted'][0]['remaining'] == 0.0
        assert result['tokens_deducted'][0]['depleted'] is True
    
    def test_deduct_zero_consumption(self):
        """Test deduction with zero consumption"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - token with 100 kWh
        tokens_result = Mock()
        tokens_result.fetchall.return_value = [
            ('token-uuid-1', 'TOKEN-ES-2026-001', 100.0)
        ]
        
        # Setup execute to return result
        db_mock.execute.return_value = tokens_result
        
        # Execute - deduct 0 kWh
        result = service.deduct_units(
            meter_id='meter-uuid',
            consumption_kwh=0.0
        )
        
        # Verify - no tokens should be deducted
        assert result['total_deducted'] == 0.0
        assert result['remaining_consumption'] == 0.0
        assert len(result['tokens_deducted']) == 0
        
        # Verify commit was called (even though no changes)
        db_mock.commit.assert_called_once()
    
    def test_deduct_decimal_precision(self):
        """Test that decimal precision is handled correctly"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - token with 33.33 kWh
        tokens_result = Mock()
        tokens_result.fetchall.return_value = [
            ('token-uuid-1', 'TOKEN-ES-2026-001', 33.33)
        ]
        
        # Mock update result
        update_result = Mock()
        
        # Setup execute to return different mocks
        db_mock.execute.side_effect = [tokens_result, update_result]
        
        # Execute - deduct 11.11 kWh
        result = service.deduct_units(
            meter_id='meter-uuid',
            consumption_kwh=11.11
        )
        
        # Verify
        assert result['total_deducted'] == 11.11
        assert result['remaining_consumption'] == 0.0
        assert result['tokens_deducted'][0]['deducted'] == 11.11
        # Remaining should be 22.22 (33.33 - 11.11)
        assert abs(result['tokens_deducted'][0]['remaining'] - 22.22) < 0.01
    
    def test_deduct_database_error_rollback(self):
        """Test that database error triggers rollback"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock database error
        db_mock.execute.side_effect = Exception("Database connection failed")
        
        # Execute & Verify
        with pytest.raises(PrepaidTokenError, match="Failed to deduct units"):
            service.deduct_units(
                meter_id='meter-uuid',
                consumption_kwh=50.0
            )
        
        # Verify rollback was called
        db_mock.rollback.assert_called_once()
    
    def test_deduct_for_update_lock(self):
        """Test that query uses FOR UPDATE to lock rows"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result
        tokens_result = Mock()
        tokens_result.fetchall.return_value = []
        
        # Setup execute to return result
        db_mock.execute.return_value = tokens_result
        
        # Execute
        service.deduct_units(
            meter_id='meter-uuid',
            consumption_kwh=50.0
        )
        
        # Verify query contains FOR UPDATE
        call_args = db_mock.execute.call_args
        query_text = str(call_args[0][0])
        assert 'FOR UPDATE' in query_text
    
    def test_deduct_query_filters_active_tokens(self):
        """Test that query only selects active tokens with units_remaining > 0"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result
        tokens_result = Mock()
        tokens_result.fetchall.return_value = []
        
        # Setup execute to return result
        db_mock.execute.return_value = tokens_result
        
        # Execute
        service.deduct_units(
            meter_id='meter-uuid',
            consumption_kwh=50.0
        )
        
        # Verify query filters by status and units_remaining
        call_args = db_mock.execute.call_args
        query_text = str(call_args[0][0])
        assert "status = 'active'" in query_text
        assert 'units_remaining > 0' in query_text
    
    def test_deduct_query_orders_by_issued_at_asc(self):
        """Test that query orders tokens by issued_at ASC (FIFO)"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result
        tokens_result = Mock()
        tokens_result.fetchall.return_value = []
        
        # Setup execute to return result
        db_mock.execute.return_value = tokens_result
        
        # Execute
        service.deduct_units(
            meter_id='meter-uuid',
            consumption_kwh=50.0
        )
        
        # Verify query orders by issued_at ASC
        call_args = db_mock.execute.call_args
        query_text = str(call_args[0][0])
        assert 'ORDER BY issued_at ASC' in query_text
    
    def test_deduct_updates_depleted_at_timestamp(self):
        """Test that depleted_at timestamp is set when token is depleted"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - token with 20 kWh
        tokens_result = Mock()
        tokens_result.fetchall.return_value = [
            ('token-uuid-1', 'TOKEN-ES-2026-001', 20.0)
        ]
        
        # Mock update result
        update_result = Mock()
        
        # Setup execute to return different mocks
        db_mock.execute.side_effect = [tokens_result, update_result]
        
        # Execute - deduct exactly 20 kWh (full depletion)
        service.deduct_units(
            meter_id='meter-uuid',
            consumption_kwh=20.0
        )
        
        # Verify update query sets depleted_at
        update_call = db_mock.execute.call_args_list[1]
        query_text = str(update_call[0][0])
        assert 'depleted_at' in query_text
        assert 'NOW()' in query_text
    
    def test_deduct_from_all_tokens_when_needed(self):
        """Test deduction that requires all available tokens"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock query result - 3 tokens
        tokens_result = Mock()
        tokens_result.fetchall.return_value = [
            ('token-uuid-1', 'TOKEN-ES-2026-001', 20.0),
            ('token-uuid-2', 'TOKEN-ES-2026-002', 30.0),
            ('token-uuid-3', 'TOKEN-ES-2026-003', 50.0)
        ]
        
        # Mock update results
        update_result_1 = Mock()
        update_result_2 = Mock()
        update_result_3 = Mock()
        
        # Setup execute to return different mocks
        db_mock.execute.side_effect = [
            tokens_result, 
            update_result_1, 
            update_result_2, 
            update_result_3
        ]
        
        # Execute - deduct 100 kWh (exactly all tokens)
        result = service.deduct_units(
            meter_id='meter-uuid',
            consumption_kwh=100.0
        )
        
        # Verify
        assert result['total_deducted'] == 100.0
        assert result['remaining_consumption'] == 0.0
        assert len(result['tokens_deducted']) == 3
        
        # All tokens should be depleted
        assert all(token['depleted'] for token in result['tokens_deducted'])
        assert result['tokens_deducted'][0]['deducted'] == 20.0
        assert result['tokens_deducted'][1]['deducted'] == 30.0
        assert result['tokens_deducted'][2]['deducted'] == 50.0
