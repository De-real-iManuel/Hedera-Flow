"""
Fraud Detection Service
Handles fraud detection and validation for meter readings

Task 12.1: Implement FraudDetectionService class

Requirements:
- FR-3.7: System shall validate reading range (100-50000 kWh)
- FR-3.8: System shall compare to historical readings
- FR-3.9: System shall validate image metadata (GPS, timestamp)
- FR-3.10: System shall detect photo manipulation (ELA analysis)
- FR-3.11: System shall calculate fraud score (0.0-1.0)
"""

import numpy as np
from PIL import Image
import io
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from decimal import Decimal

from config import settings

logger = logging.getLogger(__name__)


class FraudDetectionError(Exception):
    """Base exception for fraud detection errors"""
    pass


class FraudDetectionService:
    """Service for detecting fraudulent meter readings and images"""
    
    # Validation thresholds
    MIN_READING = 100.0  # Minimum valid reading (kWh)
    MAX_READING = 100000.0  # Maximum valid reading (kWh)
    
    # Typical household consumption ranges (kWh per month)
    TYPICAL_MIN_CONSUMPTION = 50.0
    TYPICAL_MAX_CONSUMPTION = 2000.0
    
    # Abnormal change thresholds
    ABNORMAL_INCREASE_MULTIPLIER = 2.0  # Flag if consumption > 2x average
    ABNORMAL_DECREASE_THRESHOLD = -50.0  # Flag if reading decreased by more than 50 kWh
    
    # ELA (Error Level Analysis) threshold
    ELA_MANIPULATION_THRESHOLD = 0.15  # Normalized ELA score threshold
    
    # Fraud score weights
    WEIGHT_RANGE = 0.30
    WEIGHT_HISTORICAL = 0.25
    WEIGHT_METADATA = 0.15
    WEIGHT_MANIPULATION = 0.30
    
    def __init__(self):
        """Initialize fraud detection service"""
        self.fraud_threshold = getattr(settings, 'fraud_score_threshold', 0.70)
        self.enabled = getattr(settings, 'fraud_detection_enabled', True)
        
        logger.info(f"FraudDetectionService initialized (enabled={self.enabled}, "
                   f"threshold={self.fraud_threshold})")
    
    def calculate_fraud_score(
        self,
        reading: float,
        previous_readings: Optional[List[float]] = None,
        image_bytes: Optional[bytes] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate comprehensive fraud score based on multiple factors
        
        Args:
            reading: Current meter reading value
            previous_readings: List of historical readings (ordered oldest to newest)
            image_bytes: Image data for manipulation detection
            metadata: Image metadata (GPS, timestamp, device info)
            
        Returns:
            Dictionary containing:
                - fraud_score: Overall fraud score (0.0-1.0)
                - flags: List of detected fraud indicators
                - recommendation: 'PROCEED', 'REVIEW', or 'BLOCK'
                - details: Detailed breakdown of each check
                
        Requirements:
            - FR-3.7: Validate reading range
            - FR-3.8: Compare to historical readings
            - FR-3.9: Validate image metadata
            - FR-3.10: Detect photo manipulation
            - FR-3.11: Calculate fraud score (0.0-1.0)
        """
        if not self.enabled:
            logger.info("Fraud detection disabled, returning clean score")
            return {
                'fraud_score': 0.0,
                'flags': [],
                'recommendation': 'PROCEED',
                'details': {'message': 'Fraud detection disabled'}
            }
        
        flags = []
        details = {}
        total_score = 0.0
        
        # Check 1: Range validation
        range_score, range_flags = self._check_range_validation(reading)
        total_score += range_score * self.WEIGHT_RANGE
        flags.extend(range_flags)
        details['range_validation'] = {
            'score': range_score,
            'flags': range_flags,
            'reading': reading,
            'valid_range': f"{self.MIN_READING}-{self.MAX_READING} kWh"
        }
        
        # Check 2: Historical consistency
        if previous_readings:
            hist_score, hist_flags = self._check_historical_consistency(
                reading, previous_readings
            )
            total_score += hist_score * self.WEIGHT_HISTORICAL
            flags.extend(hist_flags)
            details['historical_consistency'] = {
                'score': hist_score,
                'flags': hist_flags,
                'previous_count': len(previous_readings)
            }
        else:
            details['historical_consistency'] = {
                'score': 0.0,
                'flags': [],
                'message': 'No historical data available'
            }
        
        # Check 3: Image metadata validation
        if metadata:
            meta_score, meta_flags = self._check_metadata_validation(metadata)
            total_score += meta_score * self.WEIGHT_METADATA
            flags.extend(meta_flags)
            details['metadata_validation'] = {
                'score': meta_score,
                'flags': meta_flags,
                'has_gps': bool(metadata.get('gps_coordinates')),
                'has_timestamp': bool(metadata.get('timestamp'))
            }
        else:
            # Missing metadata is suspicious
            meta_score = 0.3
            total_score += meta_score * self.WEIGHT_METADATA
            flags.append('MISSING_METADATA')
            details['metadata_validation'] = {
                'score': meta_score,
                'flags': ['MISSING_METADATA'],
                'message': 'No metadata provided'
            }
        
        # Check 4: Photo manipulation detection (ELA)
        if image_bytes:
            ela_score, ela_flags = self._check_photo_manipulation(image_bytes)
            total_score += ela_score * self.WEIGHT_MANIPULATION
            flags.extend(ela_flags)
            details['manipulation_detection'] = {
                'score': ela_score,
                'flags': ela_flags,
                'method': 'ELA (Error Level Analysis)'
            }
        else:
            details['manipulation_detection'] = {
                'score': 0.0,
                'flags': [],
                'message': 'No image provided for analysis'
            }
        
        # Normalize total score to 0.0-1.0 range
        fraud_score = min(total_score, 1.0)
        
        # Determine recommendation
        if fraud_score >= 0.70:
            recommendation = 'BLOCK'
        elif fraud_score >= 0.40:
            recommendation = 'REVIEW'
        else:
            recommendation = 'PROCEED'
        
        result = {
            'fraud_score': round(fraud_score, 2),
            'flags': list(set(flags)),  # Remove duplicates
            'recommendation': recommendation,
            'details': details
        }
        
        logger.info(f"Fraud detection complete: score={fraud_score:.2f}, "
                   f"recommendation={recommendation}, flags={len(flags)}")
        
        return result
    
    def _check_range_validation(self, reading: float) -> Tuple[float, List[str]]:
        """
        Check if reading is within valid range
        
        Args:
            reading: Meter reading value
            
        Returns:
            Tuple of (score, flags)
            
        Requirements:
            - FR-3.7: Validate reading range (100-50000 kWh)
        """
        flags = []
        score = 0.0
        
        # Check for invalid range
        if reading < 0:
            flags.append('NEGATIVE_READING')
            score = 0.5  # Very suspicious
            
        elif reading < self.MIN_READING:
            flags.append('BELOW_MINIMUM')
            score = 0.3  # Suspicious but possible for new meters
            
        elif reading > self.MAX_READING:
            flags.append('ABOVE_MAXIMUM')
            score = 0.4  # Very suspicious for household meter
            
        # Check for unrealistic values
        if reading == 0:
            flags.append('ZERO_READING')
            score = 0.4
            
        elif reading > 1000000:
            flags.append('EXTREMELY_HIGH')
            score = 0.5
        
        return score, flags
    
    def _check_historical_consistency(
        self,
        reading: float,
        previous_readings: List[float]
    ) -> Tuple[float, List[str]]:
        """
        Check consistency with historical readings
        
        Args:
            reading: Current meter reading
            previous_readings: List of historical readings (ordered oldest to newest)
            
        Returns:
            Tuple of (score, flags)
            
        Requirements:
            - FR-3.8: Compare to historical readings
        """
        flags = []
        score = 0.0
        
        if not previous_readings or len(previous_readings) == 0:
            return score, flags
        
        # Get last reading
        last_reading = previous_readings[-1]
        
        # Calculate consumption (difference from last reading)
        consumption = reading - last_reading
        
        # Check for reading decrease (meter rollback)
        if consumption < self.ABNORMAL_DECREASE_THRESHOLD:
            flags.append('READING_DECREASED')
            score = 0.4  # Very suspicious - meters shouldn't go backwards
            
        elif consumption < 0:
            flags.append('SLIGHT_DECREASE')
            score = 0.2  # Might be meter replacement or error
        
        # Calculate average consumption if we have enough history
        if len(previous_readings) >= 2:
            # Calculate consumption between consecutive readings
            consumptions = []
            for i in range(1, len(previous_readings)):
                cons = previous_readings[i] - previous_readings[i-1]
                if cons > 0:  # Only consider positive consumptions
                    consumptions.append(cons)
            
            if consumptions:
                avg_consumption = np.mean(consumptions)
                std_consumption = np.std(consumptions) if len(consumptions) > 1 else 0
                
                # Check for abnormal increase
                if consumption > avg_consumption * self.ABNORMAL_INCREASE_MULTIPLIER:
                    flags.append('ABNORMAL_INCREASE')
                    
                    # Calculate how many standard deviations away
                    if std_consumption > 0:
                        z_score = (consumption - avg_consumption) / std_consumption
                        if z_score > 3:  # More than 3 standard deviations
                            score = 0.3
                        elif z_score > 2:
                            score = 0.2
                        else:
                            score = 0.1
                    else:
                        score = 0.2
                
                # Check for abnormally low consumption (possible tampering)
                elif consumption < avg_consumption * 0.3 and consumption > 0:
                    flags.append('ABNORMALLY_LOW')
                    score = 0.15
        
        # Check for impossible consumption rates
        # Typical household: 50-2000 kWh per month
        if consumption > self.TYPICAL_MAX_CONSUMPTION * 2:
            flags.append('EXCESSIVE_CONSUMPTION')
            score = max(score, 0.25)
        
        return score, flags
    
    def _check_metadata_validation(self, metadata: Dict) -> Tuple[float, List[str]]:
        """
        Validate image metadata (GPS, timestamp, device info)
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            Tuple of (score, flags)
            
        Requirements:
            - FR-3.9: Validate image metadata (GPS, timestamp)
        """
        flags = []
        score = 0.0
        
        # Check for timestamp
        if not metadata.get('timestamp'):
            flags.append('MISSING_TIMESTAMP')
            score += 0.1
        else:
            # Validate timestamp is recent (within last 24 hours)
            try:
                if isinstance(metadata['timestamp'], str):
                    timestamp = datetime.fromisoformat(metadata['timestamp'].replace('Z', '+00:00'))
                elif isinstance(metadata['timestamp'], datetime):
                    timestamp = metadata['timestamp']
                else:
                    timestamp = datetime.fromtimestamp(float(metadata['timestamp']))
                
                now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
                age = now - timestamp
                
                # Flag if image is too old
                if age > timedelta(days=7):
                    flags.append('OLD_IMAGE')
                    score += 0.15
                
                # Flag if timestamp is in the future
                elif age < timedelta(seconds=0):
                    flags.append('FUTURE_TIMESTAMP')
                    score += 0.2
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid timestamp format: {e}")
                flags.append('INVALID_TIMESTAMP')
                score += 0.1
        
        # Check for GPS coordinates
        if not metadata.get('gps_coordinates'):
            flags.append('MISSING_GPS')
            score += 0.05  # Less critical than timestamp
        else:
            # Validate GPS format
            gps = metadata['gps_coordinates']
            if isinstance(gps, dict):
                lat = gps.get('latitude')
                lon = gps.get('longitude')
                
                # Check for valid coordinates
                if lat is None or lon is None:
                    flags.append('INVALID_GPS')
                    score += 0.05
                elif not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    flags.append('INVALID_GPS_RANGE')
                    score += 0.1
                
                # Check for null island (0, 0) - common fake GPS
                elif abs(lat) < 0.1 and abs(lon) < 0.1:
                    flags.append('SUSPICIOUS_GPS')
                    score += 0.15
        
        # Check for device information
        if not metadata.get('device_id') and not metadata.get('device_model'):
            flags.append('MISSING_DEVICE_INFO')
            score += 0.05
        
        return score, flags
    
    def _check_photo_manipulation(self, image_bytes: bytes) -> Tuple[float, List[str]]:
        """
        Detect photo manipulation using ELA (Error Level Analysis)
        
        ELA works by re-saving the image at a known quality level and comparing
        the difference. Manipulated areas show different error levels.
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            Tuple of (score, flags)
            
        Requirements:
            - FR-3.10: Detect photo manipulation (ELA analysis)
        """
        flags = []
        score = 0.0
        
        if not image_bytes or len(image_bytes) == 0:
            return score, flags
        
        try:
            # Load original image
            original = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if original.mode != 'RGB':
                original = original.convert('RGB')
            
            # Save at a known quality level (90%)
            temp_buffer = io.BytesIO()
            original.save(temp_buffer, 'JPEG', quality=90)
            temp_buffer.seek(0)
            
            # Load the re-saved image
            resaved = Image.open(temp_buffer)
            
            # Convert images to numpy arrays
            original_array = np.array(original, dtype=np.float32)
            resaved_array = np.array(resaved, dtype=np.float32)
            
            # Calculate absolute difference
            diff = np.abs(original_array - resaved_array)
            
            # Calculate ELA score (normalized mean difference)
            ela_score = np.mean(diff) / 255.0
            
            logger.debug(f"ELA score: {ela_score:.4f}")
            
            # High ELA score indicates possible manipulation
            if ela_score > self.ELA_MANIPULATION_THRESHOLD:
                flags.append('POSSIBLE_MANIPULATION')
                
                # Scale score based on how much it exceeds threshold
                excess = (ela_score - self.ELA_MANIPULATION_THRESHOLD) / self.ELA_MANIPULATION_THRESHOLD
                score = min(0.3 + (excess * 0.2), 0.5)  # Cap at 0.5
            
            # Check for uniform ELA (sign of sophisticated manipulation)
            ela_std = np.std(diff)
            if ela_std < 5.0 and ela_score > 0.05:
                flags.append('UNIFORM_MANIPULATION')
                score = max(score, 0.25)
            
            # Check for localized high-error regions
            # Divide image into grid and check for anomalies
            h, w = diff.shape[:2]
            grid_size = 8
            grid_h, grid_w = h // grid_size, w // grid_size
            
            high_error_regions = 0
            for i in range(grid_size):
                for j in range(grid_size):
                    region = diff[i*grid_h:(i+1)*grid_h, j*grid_w:(j+1)*grid_w]
                    region_mean = np.mean(region)
                    
                    if region_mean > ela_score * 2:  # Region has 2x average error
                        high_error_regions += 1
            
            # If more than 10% of regions have high error, flag it
            if high_error_regions > (grid_size * grid_size * 0.1):
                flags.append('LOCALIZED_MANIPULATION')
                score = max(score, 0.2)
            
        except Exception as e:
            logger.error(f"ELA analysis failed: {e}")
            # Don't penalize if analysis fails
            flags.append('ELA_ANALYSIS_FAILED')
            score = 0.0
        
        return score, flags
    
    def is_fraudulent(self, fraud_score: float) -> bool:
        """
        Determine if a fraud score indicates fraudulent activity
        
        Args:
            fraud_score: Fraud score (0.0-1.0)
            
        Returns:
            True if fraudulent, False otherwise
        """
        return fraud_score >= self.fraud_threshold
    
    def get_status_from_score(self, fraud_score: float) -> str:
        """
        Get verification status based on fraud score
        
        Args:
            fraud_score: Fraud score (0.0-1.0)
            
        Returns:
            Status string: 'VERIFIED', 'WARNING', 'DISCREPANCY', or 'FRAUD_DETECTED'
        """
        if fraud_score >= 0.70:
            return 'FRAUD_DETECTED'
        elif fraud_score >= 0.40:
            return 'DISCREPANCY'
        elif fraud_score >= 0.20:
            return 'WARNING'
        else:
            return 'VERIFIED'


# Global fraud detection service instance
_fraud_detection_service: Optional[FraudDetectionService] = None


def get_fraud_detection_service() -> FraudDetectionService:
    """
    Get or create global fraud detection service instance
    
    Returns:
        FraudDetectionService instance
    """
    global _fraud_detection_service
    
    if _fraud_detection_service is None:
        _fraud_detection_service = FraudDetectionService()
    
    return _fraud_detection_service
