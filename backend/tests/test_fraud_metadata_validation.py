"""
Unit tests for fraud detection metadata validation

Tests the _check_metadata_validation method of FraudDetectionService

Requirements:
- FR-3.9: Validate image metadata (GPS, timestamp)
- Task 12.4: Add image metadata validation
"""

import pytest
from datetime import datetime, timedelta
from app.services.fraud_detection_service import FraudDetectionService


class TestMetadataValidation:
    """Test suite for metadata validation in fraud detection"""
    
    @pytest.fixture
    def service(self):
        """Create a FraudDetectionService instance"""
        return FraudDetectionService()
    
    # ========== Timestamp Tests ==========
    
    def test_valid_recent_timestamp(self, service):
        """Test with valid recent timestamp"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'latitude': 40.4168, 'longitude': -3.7038},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score == 0.0
        assert len(flags) == 0
    
    def test_missing_timestamp(self, service):
        """Test with missing timestamp"""
        metadata = {
            'gps_coordinates': {'latitude': 40.4168, 'longitude': -3.7038},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.1
        assert 'MISSING_TIMESTAMP' in flags
    
    def test_old_timestamp(self, service):
        """Test with timestamp older than 7 days"""
        old_time = datetime.now() - timedelta(days=10)
        metadata = {
            'timestamp': old_time.isoformat(),
            'gps_coordinates': {'latitude': 40.4168, 'longitude': -3.7038},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.15
        assert 'OLD_IMAGE' in flags
    
    def test_future_timestamp(self, service):
        """Test with timestamp in the future"""
        future_time = datetime.now() + timedelta(days=1)
        metadata = {
            'timestamp': future_time.isoformat(),
            'gps_coordinates': {'latitude': 40.4168, 'longitude': -3.7038},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.2
        assert 'FUTURE_TIMESTAMP' in flags
    
    def test_invalid_timestamp_format(self, service):
        """Test with invalid timestamp format"""
        metadata = {
            'timestamp': 'invalid-timestamp',
            'gps_coordinates': {'latitude': 40.4168, 'longitude': -3.7038},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.1
        assert 'INVALID_TIMESTAMP' in flags
    
    def test_timestamp_as_datetime_object(self, service):
        """Test with timestamp as datetime object"""
        metadata = {
            'timestamp': datetime.now(),
            'gps_coordinates': {'latitude': 40.4168, 'longitude': -3.7038},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score == 0.0
        assert len(flags) == 0
    
    def test_timestamp_as_unix_timestamp(self, service):
        """Test with timestamp as Unix timestamp (float)"""
        metadata = {
            'timestamp': datetime.now().timestamp(),
            'gps_coordinates': {'latitude': 40.4168, 'longitude': -3.7038},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score == 0.0
        assert len(flags) == 0
    
    # ========== GPS Coordinate Tests ==========
    
    def test_valid_gps_coordinates(self, service):
        """Test with valid GPS coordinates"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'latitude': 40.4168, 'longitude': -3.7038},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score == 0.0
        assert len(flags) == 0
    
    def test_missing_gps_coordinates(self, service):
        """Test with missing GPS coordinates"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.05
        assert 'MISSING_GPS' in flags
    
    def test_invalid_gps_format_missing_latitude(self, service):
        """Test with GPS missing latitude"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'longitude': -3.7038},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.05
        assert 'INVALID_GPS' in flags
    
    def test_invalid_gps_format_missing_longitude(self, service):
        """Test with GPS missing longitude"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'latitude': 40.4168},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.05
        assert 'INVALID_GPS' in flags
    
    def test_invalid_gps_latitude_out_of_range_high(self, service):
        """Test with latitude > 90"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'latitude': 95.0, 'longitude': -3.7038},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.1
        assert 'INVALID_GPS_RANGE' in flags
    
    def test_invalid_gps_latitude_out_of_range_low(self, service):
        """Test with latitude < -90"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'latitude': -95.0, 'longitude': -3.7038},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.1
        assert 'INVALID_GPS_RANGE' in flags
    
    def test_invalid_gps_longitude_out_of_range_high(self, service):
        """Test with longitude > 180"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'latitude': 40.4168, 'longitude': 185.0},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.1
        assert 'INVALID_GPS_RANGE' in flags
    
    def test_invalid_gps_longitude_out_of_range_low(self, service):
        """Test with longitude < -180"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'latitude': 40.4168, 'longitude': -185.0},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.1
        assert 'INVALID_GPS_RANGE' in flags
    
    def test_suspicious_gps_null_island(self, service):
        """Test with GPS at null island (0, 0)"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'latitude': 0.0, 'longitude': 0.0},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.15
        assert 'SUSPICIOUS_GPS' in flags
    
    def test_suspicious_gps_near_null_island(self, service):
        """Test with GPS near null island (0.05, 0.05)"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'latitude': 0.05, 'longitude': 0.05},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.15
        assert 'SUSPICIOUS_GPS' in flags
    
    def test_valid_gps_edge_cases(self, service):
        """Test with valid GPS at edge of ranges"""
        # North pole
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'latitude': 90.0, 'longitude': 0.0},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        assert 'INVALID_GPS_RANGE' not in flags
        
        # South pole
        metadata['gps_coordinates'] = {'latitude': -90.0, 'longitude': 0.0}
        score, flags = service._check_metadata_validation(metadata)
        assert 'INVALID_GPS_RANGE' not in flags
        
        # International date line
        metadata['gps_coordinates'] = {'latitude': 0.0, 'longitude': 180.0}
        score, flags = service._check_metadata_validation(metadata)
        assert 'INVALID_GPS_RANGE' not in flags
        
        metadata['gps_coordinates'] = {'latitude': 0.0, 'longitude': -180.0}
        score, flags = service._check_metadata_validation(metadata)
        assert 'INVALID_GPS_RANGE' not in flags
    
    # ========== Device Information Tests ==========
    
    def test_valid_device_info_with_id(self, service):
        """Test with valid device ID"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'latitude': 40.4168, 'longitude': -3.7038},
            'device_id': 'test-device-123'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score == 0.0
        assert 'MISSING_DEVICE_INFO' not in flags
    
    def test_valid_device_info_with_model(self, service):
        """Test with valid device model"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'latitude': 40.4168, 'longitude': -3.7038},
            'device_model': 'iPhone 13'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score == 0.0
        assert 'MISSING_DEVICE_INFO' not in flags
    
    def test_valid_device_info_with_both(self, service):
        """Test with both device ID and model"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'latitude': 40.4168, 'longitude': -3.7038},
            'device_id': 'test-device-123',
            'device_model': 'iPhone 13'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score == 0.0
        assert 'MISSING_DEVICE_INFO' not in flags
    
    def test_missing_device_info(self, service):
        """Test with missing device information"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {'latitude': 40.4168, 'longitude': -3.7038}
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.05
        assert 'MISSING_DEVICE_INFO' in flags
    
    # ========== Combined Scenarios ==========
    
    def test_empty_metadata(self, service):
        """Test with completely empty metadata"""
        metadata = {}
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.2  # Should accumulate multiple penalties
        assert 'MISSING_TIMESTAMP' in flags
        assert 'MISSING_GPS' in flags
        assert 'MISSING_DEVICE_INFO' in flags
    
    def test_multiple_issues(self, service):
        """Test with multiple metadata issues"""
        old_time = datetime.now() - timedelta(days=10)
        metadata = {
            'timestamp': old_time.isoformat(),
            'gps_coordinates': {'latitude': 0.0, 'longitude': 0.0}
            # Missing device info
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score >= 0.25  # Multiple penalties
        assert 'OLD_IMAGE' in flags
        assert 'SUSPICIOUS_GPS' in flags
        assert 'MISSING_DEVICE_INFO' in flags
    
    def test_perfect_metadata(self, service):
        """Test with perfect metadata (all fields valid)"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'gps_coordinates': {
                'latitude': 40.4168,  # Madrid, Spain
                'longitude': -3.7038
            },
            'device_id': 'ABC123XYZ',
            'device_model': 'iPhone 13 Pro'
        }
        score, flags = service._check_metadata_validation(metadata)
        
        assert score == 0.0
        assert len(flags) == 0
    
    # ========== Real-world Location Tests ==========
    
    def test_real_world_locations(self, service):
        """Test with real-world GPS coordinates from different regions"""
        locations = [
            {'latitude': 40.4168, 'longitude': -3.7038},   # Madrid, Spain
            {'latitude': 37.7749, 'longitude': -122.4194},  # San Francisco, USA
            {'latitude': 28.6139, 'longitude': 77.2090},    # New Delhi, India
            {'latitude': -23.5505, 'longitude': -46.6333},  # São Paulo, Brazil
            {'latitude': 6.5244, 'longitude': 3.3792},      # Lagos, Nigeria
        ]
        
        for coords in locations:
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'gps_coordinates': coords,
                'device_id': 'test-device'
            }
            score, flags = service._check_metadata_validation(metadata)
            
            assert 'INVALID_GPS_RANGE' not in flags
            assert 'SUSPICIOUS_GPS' not in flags
