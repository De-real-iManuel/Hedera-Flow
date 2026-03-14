"""
Unit tests for PrepaidTokenService.generate_token_id method

Tests the token ID generation functionality.
"""
import pytest
from unittest.mock import Mock
from datetime import datetime

from app.services.prepaid_token_service import PrepaidTokenService, PrepaidTokenError


class TestGenerateTokenId:
    """Test generate_token_id method"""
    
    def test_token_id_format(self):
        """Test that token ID follows correct format: TOKEN-{COUNTRY}-{YEAR}-{SEQ}"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock database query to return sequence 1
        result_mock = Mock()
        result_mock.fetchone.return_value = (1,)
        db_mock.execute.return_value = result_mock
        
        # Execute
        token_id = service.generate_token_id(country_code='ES', year=2026)
        
        # Verify
        assert token_id == 'TOKEN-ES-2026-001'
        assert token_id.startswith('TOKEN-')
        assert 'ES' in token_id
        assert '2026' in token_id
    
    def test_token_id_sequence_increment(self):
        """Test that sequence number increments correctly"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock database query to return sequence 5
        result_mock = Mock()
        result_mock.fetchone.return_value = (5,)
        db_mock.execute.return_value = result_mock
        
        # Execute
        token_id = service.generate_token_id(country_code='US', year=2026)
        
        # Verify
        assert token_id == 'TOKEN-US-2026-005'
    
    def test_token_id_default_year(self):
        """Test that current year is used when year is not provided"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock database query
        result_mock = Mock()
        result_mock.fetchone.return_value = (1,)
        db_mock.execute.return_value = result_mock
        
        # Execute
        current_year = datetime.now().year
        token_id = service.generate_token_id(country_code='IN')
        
        # Verify
        assert f'TOKEN-IN-{current_year}-001' == token_id
    
    def test_token_id_different_countries(self):
        """Test token ID generation for different countries"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock database query
        result_mock = Mock()
        result_mock.fetchone.return_value = (1,)
        db_mock.execute.return_value = result_mock
        
        # Test different country codes
        countries = ['ES', 'US', 'IN', 'BR', 'NG']
        for country in countries:
            token_id = service.generate_token_id(country_code=country, year=2026)
            assert token_id == f'TOKEN-{country}-2026-001'
    
    def test_token_id_sequence_padding(self):
        """Test that sequence number is zero-padded to 3 digits"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Test different sequence numbers
        test_cases = [
            (1, '001'),
            (10, '010'),
            (99, '099'),
            (100, '100'),
            (999, '999'),
            (1000, '1000')  # Should handle numbers > 999
        ]
        
        for seq, expected_str in test_cases:
            result_mock = Mock()
            result_mock.fetchone.return_value = (seq,)
            db_mock.execute.return_value = result_mock
            
            token_id = service.generate_token_id(country_code='ES', year=2026)
            assert token_id == f'TOKEN-ES-2026-{expected_str}'
    
    def test_token_id_query_pattern(self):
        """Test that database query uses correct pattern for counting"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock database query
        result_mock = Mock()
        result_mock.fetchone.return_value = (1,)
        db_mock.execute.return_value = result_mock
        
        # Execute
        service.generate_token_id(country_code='ES', year=2026)
        
        # Verify query was called with correct pattern
        call_args = db_mock.execute.call_args
        assert 'TOKEN-ES-2026-%' in str(call_args)
    
    def test_token_id_database_error(self):
        """Test that PrepaidTokenError is raised on database error"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock database error
        db_mock.execute.side_effect = Exception("Database connection failed")
        
        # Execute & Verify
        with pytest.raises(PrepaidTokenError, match="Failed to generate token ID"):
            service.generate_token_id(country_code='ES', year=2026)
    
    def test_token_id_empty_result(self):
        """Test that sequence starts at 1 when no existing tokens"""
        # Setup
        db_mock = Mock()
        service = PrepaidTokenService(db_mock)
        
        # Mock empty result (no existing tokens)
        result_mock = Mock()
        result_mock.fetchone.return_value = None
        db_mock.execute.return_value = result_mock
        
        # Execute
        token_id = service.generate_token_id(country_code='ES', year=2026)
        
        # Verify - should default to sequence 1
        assert token_id == 'TOKEN-ES-2026-001'
