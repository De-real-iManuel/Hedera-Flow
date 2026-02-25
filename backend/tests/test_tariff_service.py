"""
Tests for Tariff Service

Tests tariff fetching logic with database and Redis caching.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.tariff_service import (
    get_tariff,
    invalidate_tariff_cache,
    get_all_tariffs,
    TariffNotFoundError,
    TariffServiceError,
    _fetch_tariff_from_db
)


# Sample tariff data for testing
SAMPLE_TARIFF_ES = {
    'id': '123e4567-e89b-12d3-a456-426614174000',
    'country_code': 'ES',
    'utility_provider': 'Iberdrola',
    'currency': 'EUR',
    'rate_structure': {
        'type': 'time_of_use',
        'periods': [
            {'name': 'peak', 'hours': [10, 11, 12, 13, 14, 18, 19, 20, 21], 'price': 0.40},
            {'name': 'standard', 'hours': [8, 9, 15, 16, 17, 22, 23], 'price': 0.25},
            {'name': 'off_peak', 'hours': [0, 1, 2, 3, 4, 5, 6, 7], 'price': 0.15}
        ]
    },
    'taxes_and_fees': {
        'vat': 0.21,
        'distribution_charge': 0.045
    },
    'subsidies': {},
    'valid_from': date.today() - timedelta(days=30),
    'valid_until': None
}


class TestGetTariff:
    """Test get_tariff function"""
    
    @patch('app.services.tariff_service.redis_client')
    def test_get_tariff_cache_hit(self, mock_redis):
        """Test tariff fetch with cache hit"""
        # Setup
        db = Mock(spec=Session)
        cached_data = {
            'tariff_id': str(SAMPLE_TARIFF_ES['id']),
            'country_code': 'ES',
            'utility_provider': 'Iberdrola',
            'currency': 'EUR',
            'rate_structure': SAMPLE_TARIFF_ES['rate_structure'],
            'taxes_and_fees': SAMPLE_TARIFF_ES['taxes_and_fees'],
            'subsidies': {},
            'valid_from': SAMPLE_TARIFF_ES['valid_from'].isoformat(),
            'valid_until': None
        }
        mock_redis.get_tariff.return_value = cached_data
        
        # Execute
        result = get_tariff(db, 'ES', 'Iberdrola')
        
        # Assert
        assert result == cached_data
        mock_redis.get_tariff.assert_called_once_with('ES', 'Iberdrola')
        # Database should not be queried
        db.execute.assert_not_called()
    
    @patch('app.services.tariff_service.redis_client')
    @patch('app.services.tariff_service._fetch_tariff_from_db')
    def test_get_tariff_cache_miss(self, mock_fetch_db, mock_redis):
        """Test tariff fetch with cache miss"""
        # Setup
        db = Mock(spec=Session)
        mock_redis.get_tariff.return_value = None  # Cache miss
        mock_fetch_db.return_value = SAMPLE_TARIFF_ES
        
        # Execute
        result = get_tariff(db, 'ES', 'Iberdrola')
        
        # Assert
        assert result['country_code'] == 'ES'
        assert result['utility_provider'] == 'Iberdrola'
        assert result['currency'] == 'EUR'
        mock_redis.get_tariff.assert_called_once_with('ES', 'Iberdrola')
        mock_fetch_db.assert_called_once_with(db, 'ES', 'Iberdrola')
        # Should cache the result
        mock_redis.set_tariff.assert_called_once()
    
    @patch('app.services.tariff_service.redis_client')
    @patch('app.services.tariff_service._fetch_tariff_from_db')
    def test_get_tariff_not_found(self, mock_fetch_db, mock_redis):
        """Test tariff fetch when tariff doesn't exist"""
        # Setup
        db = Mock(spec=Session)
        mock_redis.get_tariff.return_value = None
        mock_fetch_db.return_value = None  # No tariff found
        
        # Execute & Assert
        with pytest.raises(TariffNotFoundError) as exc_info:
            get_tariff(db, 'ES', 'NonExistentProvider')
        
        assert 'No active tariff found' in str(exc_info.value)
    
    @patch('app.services.tariff_service.redis_client')
    @patch('app.services.tariff_service._fetch_tariff_from_db')
    def test_get_tariff_without_cache(self, mock_fetch_db, mock_redis):
        """Test tariff fetch with caching disabled"""
        # Setup
        db = Mock(spec=Session)
        mock_fetch_db.return_value = SAMPLE_TARIFF_ES
        
        # Execute
        result = get_tariff(db, 'ES', 'Iberdrola', use_cache=False)
        
        # Assert
        assert result['country_code'] == 'ES'
        # Cache should not be checked or set
        mock_redis.get_tariff.assert_not_called()
        mock_redis.set_tariff.assert_not_called()
    
    @patch('app.services.tariff_service.redis_client')
    @patch('app.services.tariff_service._fetch_tariff_from_db')
    def test_get_tariff_normalizes_country_code(self, mock_fetch_db, mock_redis):
        """Test that country code is normalized to uppercase"""
        # Setup
        db = Mock(spec=Session)
        mock_redis.get_tariff.return_value = None
        mock_fetch_db.return_value = SAMPLE_TARIFF_ES
        
        # Execute with lowercase country code
        result = get_tariff(db, 'es', 'Iberdrola')
        
        # Assert
        mock_redis.get_tariff.assert_called_once_with('ES', 'Iberdrola')
        mock_fetch_db.assert_called_once_with(db, 'ES', 'Iberdrola')


class TestFetchTariffFromDb:
    """Test _fetch_tariff_from_db function"""
    
    def test_fetch_tariff_from_db_success(self):
        """Test successful tariff fetch from database"""
        # Setup
        db = Mock(spec=Session)
        mock_result = Mock()
        mock_result.__getitem__ = lambda self, i: [
            SAMPLE_TARIFF_ES['id'],
            'ES',
            'Iberdrola',
            'EUR',
            SAMPLE_TARIFF_ES['rate_structure'],
            SAMPLE_TARIFF_ES['taxes_and_fees'],
            {},
            SAMPLE_TARIFF_ES['valid_from'],
            None
        ][i]
        
        db.execute.return_value.fetchone.return_value = mock_result
        
        # Execute
        result = _fetch_tariff_from_db(db, 'ES', 'Iberdrola')
        
        # Assert
        assert result is not None
        assert result['country_code'] == 'ES'
        assert result['utility_provider'] == 'Iberdrola'
        assert result['currency'] == 'EUR'
        db.execute.assert_called_once()
    
    def test_fetch_tariff_from_db_not_found(self):
        """Test tariff fetch when no matching tariff exists"""
        # Setup
        db = Mock(spec=Session)
        db.execute.return_value.fetchone.return_value = None
        
        # Execute
        result = _fetch_tariff_from_db(db, 'ES', 'NonExistent')
        
        # Assert
        assert result is None


class TestInvalidateTariffCache:
    """Test invalidate_tariff_cache function"""
    
    @patch('app.services.tariff_service.redis_client')
    def test_invalidate_cache_success(self, mock_redis):
        """Test successful cache invalidation"""
        # Setup
        mock_redis.delete_tariff.return_value = True
        
        # Execute
        result = invalidate_tariff_cache('ES', 'Iberdrola')
        
        # Assert
        assert result is True
        mock_redis.delete_tariff.assert_called_once_with('ES', 'Iberdrola')
    
    @patch('app.services.tariff_service.redis_client')
    def test_invalidate_cache_normalizes_country_code(self, mock_redis):
        """Test that country code is normalized to uppercase"""
        # Setup
        mock_redis.delete_tariff.return_value = True
        
        # Execute
        invalidate_tariff_cache('es', 'Iberdrola')
        
        # Assert
        mock_redis.delete_tariff.assert_called_once_with('ES', 'Iberdrola')


class TestGetAllTariffs:
    """Test get_all_tariffs function"""
    
    def test_get_all_tariffs_no_filters(self):
        """Test fetching all tariffs without filters"""
        # Setup
        db = Mock(spec=Session)
        mock_row = Mock()
        mock_row.__getitem__ = lambda self, i: [
            SAMPLE_TARIFF_ES['id'],
            'ES',
            'Iberdrola',
            'EUR',
            SAMPLE_TARIFF_ES['rate_structure'],
            SAMPLE_TARIFF_ES['taxes_and_fees'],
            {},
            SAMPLE_TARIFF_ES['valid_from'],
            None,
            True
        ][i]
        
        db.execute.return_value.fetchall.return_value = [mock_row]
        
        # Execute
        result = get_all_tariffs(db)
        
        # Assert
        assert len(result) == 1
        assert result[0]['country_code'] == 'ES'
        assert result[0]['utility_provider'] == 'Iberdrola'
    
    def test_get_all_tariffs_with_country_filter(self):
        """Test fetching tariffs filtered by country"""
        # Setup
        db = Mock(spec=Session)
        db.execute.return_value.fetchall.return_value = []
        
        # Execute
        result = get_all_tariffs(db, country_code='ES')
        
        # Assert
        assert isinstance(result, list)
        # Verify query was called with country_code parameter
        call_args = db.execute.call_args
        assert 'country_code' in call_args[0][1]
        assert call_args[0][1]['country_code'] == 'ES'
    
    def test_get_all_tariffs_with_provider_filter(self):
        """Test fetching tariffs filtered by utility provider"""
        # Setup
        db = Mock(spec=Session)
        db.execute.return_value.fetchall.return_value = []
        
        # Execute
        result = get_all_tariffs(db, utility_provider='Iberdrola')
        
        # Assert
        assert isinstance(result, list)
        # Verify query was called with utility_provider parameter
        call_args = db.execute.call_args
        assert 'utility_provider' in call_args[0][1]
        assert call_args[0][1]['utility_provider'] == 'Iberdrola'
    
    def test_get_all_tariffs_include_inactive(self):
        """Test fetching all tariffs including inactive ones"""
        # Setup
        db = Mock(spec=Session)
        db.execute.return_value.fetchall.return_value = []
        
        # Execute
        result = get_all_tariffs(db, active_only=False)
        
        # Assert
        assert isinstance(result, list)
        # Verify query doesn't filter by active status
        call_args = db.execute.call_args
        query_text = str(call_args[0][0])
        # When active_only=False, the where clause should be "1=1"
        assert '1=1' in query_text or 'WHERE' not in query_text or 'is_active' not in query_text
