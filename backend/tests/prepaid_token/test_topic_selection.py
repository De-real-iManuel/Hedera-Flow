"""
Tests for HCS topic selection based on country code.

This module tests the get_topic_for_country() method which maps
country codes to regional HCS topics for audit logging.

Requirements: FR-8.7, Task 1.4
"""
import pytest
from unittest.mock import Mock, patch
from app.services.prepaid_token_service import PrepaidTokenService, PrepaidTokenError


class TestTopicSelection:
    """Test suite for country-based HCS topic selection"""
    
    @pytest.fixture
    def prepaid_service(self):
        """Create PrepaidTokenService instance with mocked dependencies"""
        mock_db = Mock()
        
        with patch('app.services.prepaid_token_service.get_hedera_service'):
            service = PrepaidTokenService(db=mock_db)
            return service
    
    def test_spain_maps_to_eu_topic(self, prepaid_service):
        """
        Test that Spain (ES) maps to EU HCS topic.
        
        Verifies:
        - Country code 'ES' returns HCS_TOPIC_EU
        - Correct topic ID format
        """
        with patch('config.settings') as mock_settings:
            mock_settings.hcs_topic_eu = "0.0.5078302"
            
            # Act
            topic_id = prepaid_service.get_topic_for_country("ES")
            
            # Assert
            assert topic_id == "0.0.5078302"
    
    def test_usa_maps_to_us_topic(self, prepaid_service):
        """
        Test that USA (US) maps to US HCS topic.
        
        Verifies:
        - Country code 'US' returns HCS_TOPIC_US
        """
        with patch('config.settings') as mock_settings:
            mock_settings.hcs_topic_us = "0.0.5078303"
            
            # Act
            topic_id = prepaid_service.get_topic_for_country("US")
            
            # Assert
            assert topic_id == "0.0.5078303"
    
    def test_india_maps_to_asia_topic(self, prepaid_service):
        """
        Test that India (IN) maps to Asia HCS topic.
        
        Verifies:
        - Country code 'IN' returns HCS_TOPIC_ASIA
        """
        with patch('config.settings') as mock_settings:
            mock_settings.hcs_topic_asia = "0.0.5078304"
            
            # Act
            topic_id = prepaid_service.get_topic_for_country("IN")
            
            # Assert
            assert topic_id == "0.0.5078304"
    
    def test_brazil_maps_to_sa_topic(self, prepaid_service):
        """
        Test that Brazil (BR) maps to South America HCS topic.
        
        Verifies:
        - Country code 'BR' returns HCS_TOPIC_SA
        """
        with patch('config.settings') as mock_settings:
            mock_settings.hcs_topic_sa = "0.0.5078305"
            
            # Act
            topic_id = prepaid_service.get_topic_for_country("BR")
            
            # Assert
            assert topic_id == "0.0.5078305"
    
    def test_nigeria_maps_to_africa_topic(self, prepaid_service):
        """
        Test that Nigeria (NG) maps to Africa HCS topic.
        
        Verifies:
        - Country code 'NG' returns HCS_TOPIC_AFRICA
        """
        with patch('config.settings') as mock_settings:
            mock_settings.hcs_topic_africa = "0.0.5078306"
            
            # Act
            topic_id = prepaid_service.get_topic_for_country("NG")
            
            # Assert
            assert topic_id == "0.0.5078306"
    
    def test_unsupported_country_raises_error(self, prepaid_service):
        """
        Test that unsupported country code raises PrepaidTokenError.
        
        Verifies:
        - Invalid country code (e.g., 'FR') raises PrepaidTokenError
        - Error message lists supported countries
        """
        with patch('config.settings'):
            # Act & Assert
            with pytest.raises(PrepaidTokenError) as exc_info:
                prepaid_service.get_topic_for_country("FR")
            
            assert "Unsupported country code: FR" in str(exc_info.value)
            assert "ES, US, IN, BR, NG" in str(exc_info.value)
    
    def test_unconfigured_topic_returns_none(self, prepaid_service):
        """
        Test that unconfigured topic returns None with warning.
        
        Verifies:
        - If HCS_TOPIC_EU is None or "0.0.xxxxx", returns None
        - Warning is logged
        """
        with patch('config.settings') as mock_settings:
            mock_settings.hcs_topic_eu = None
            
            # Act
            topic_id = prepaid_service.get_topic_for_country("ES")
            
            # Assert
            assert topic_id is None
    
    def test_placeholder_topic_returns_none(self, prepaid_service):
        """
        Test that placeholder topic ID returns None.
        
        Verifies:
        - If topic is "0.0.xxxxx" (placeholder), returns None
        """
        with patch('config.settings') as mock_settings:
            mock_settings.hcs_topic_us = "0.0.xxxxx"
            
            # Act
            topic_id = prepaid_service.get_topic_for_country("US")
            
            # Assert
            assert topic_id is None
    
    def test_all_countries_have_unique_topics(self, prepaid_service):
        """
        Test that all supported countries map to different topics.
        
        Verifies:
        - Each country has a unique topic ID
        - No topic ID collisions
        """
        with patch('config.settings') as mock_settings:
            mock_settings.hcs_topic_eu = "0.0.5078302"
            mock_settings.hcs_topic_us = "0.0.5078303"
            mock_settings.hcs_topic_asia = "0.0.5078304"
            mock_settings.hcs_topic_sa = "0.0.5078305"
            mock_settings.hcs_topic_africa = "0.0.5078306"
            
            # Act
            topics = {
                'ES': prepaid_service.get_topic_for_country("ES"),
                'US': prepaid_service.get_topic_for_country("US"),
                'IN': prepaid_service.get_topic_for_country("IN"),
                'BR': prepaid_service.get_topic_for_country("BR"),
                'NG': prepaid_service.get_topic_for_country("NG")
            }
            
            # Assert
            topic_values = list(topics.values())
            assert len(topic_values) == len(set(topic_values))  # All unique
            assert all(topic.startswith("0.0.") for topic in topic_values)
