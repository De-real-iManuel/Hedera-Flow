"""
OCR Service
Handles server-side OCR using Google Cloud Vision API

Task 11.3: Implement OCRService class
Task 11.7: Handle API errors and fallbacks

Requirements:
- FR-3.2: System shall fallback to Google Vision API if confidence < 90%
- FR-3.3: System shall detect meter type (analog/digital/smart)
- FR-3.4: System shall extract reading value and unit
- FR-3.5: System shall calculate confidence score (0-100%)
"""

from google.cloud import vision
from google.api_core import exceptions as google_exceptions
from typing import Dict, Optional, Tuple
import re
import logging
import io
from decimal import Decimal
import time

from config import settings

logger = logging.getLogger(__name__)


class OCRServiceError(Exception):
    """Base exception for OCR service errors"""
    pass


class VisionAPIError(OCRServiceError):
    """Exception for Google Vision API errors"""
    pass


class VisionAPIQuotaExceeded(OCRServiceError):
    """Exception for quota exceeded errors"""
    pass


class VisionAPIUnavailable(OCRServiceError):
    """Exception for service unavailable errors"""
    pass


class OCRService:
    """Service for server-side OCR using Google Cloud Vision API"""
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    RETRY_BACKOFF = 2  # exponential backoff multiplier
    
    def __init__(self):
        """Initialize Google Cloud Vision API client"""
        self.client = None
        self.is_available = False
        self._setup_client()
    
    def _setup_client(self):
        """Setup Vision API client with credentials"""
        try:
            # Initialize Vision API client
            # Credentials are loaded from GOOGLE_APPLICATION_CREDENTIALS env var
            self.client = vision.ImageAnnotatorClient()
            self.is_available = True
            
            logger.info("Google Cloud Vision API client initialized")
            
            if settings.google_application_credentials:
                logger.info(f"Using credentials from: {settings.google_application_credentials}")
            else:
                logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set - using default credentials")
                
        except Exception as e:
            logger.error(f"Failed to initialize Vision API client: {e}")
            self.is_available = False
            # Don't raise - allow service to continue with degraded functionality
            logger.warning("OCR service will operate in degraded mode without Vision API")
    
    def _handle_vision_api_error(self, error: Exception) -> Dict:
        """
        Handle Vision API errors and return appropriate error response
        
        Args:
            error: Exception from Vision API
            
        Returns:
            Error response dictionary
        """
        error_response = {
            'reading': 0.0,
            'confidence': 0.0,
            'raw_text': '',
            'error': None,
            'error_type': None
        }
        
        # Handle specific Google API exceptions
        if isinstance(error, google_exceptions.ResourceExhausted):
            error_response['error'] = 'Vision API quota exceeded. Please try again later.'
            error_response['error_type'] = 'quota_exceeded'
            logger.error("Vision API quota exceeded")
            
        elif isinstance(error, google_exceptions.ServiceUnavailable):
            error_response['error'] = 'Vision API temporarily unavailable. Please try again.'
            error_response['error_type'] = 'service_unavailable'
            logger.error("Vision API service unavailable")
            
        elif isinstance(error, google_exceptions.Unauthenticated):
            error_response['error'] = 'Vision API authentication failed. Please check credentials.'
            error_response['error_type'] = 'authentication_failed'
            logger.error("Vision API authentication failed")
            
        elif isinstance(error, google_exceptions.PermissionDenied):
            error_response['error'] = 'Vision API permission denied. Please check API access.'
            error_response['error_type'] = 'permission_denied'
            logger.error("Vision API permission denied")
            
        elif isinstance(error, google_exceptions.InvalidArgument):
            error_response['error'] = 'Invalid image format or corrupted image data.'
            error_response['error_type'] = 'invalid_image'
            logger.error(f"Vision API invalid argument: {error}")
            
        elif isinstance(error, google_exceptions.DeadlineExceeded):
            error_response['error'] = 'Vision API request timeout. Please try again.'
            error_response['error_type'] = 'timeout'
            logger.error("Vision API request timeout")
            
        else:
            error_response['error'] = f'Vision API error: {str(error)}'
            error_response['error_type'] = 'unknown'
            logger.error(f"Vision API unknown error: {error}")
        
        return error_response
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Retry a function with exponential backoff
        
        Args:
            func: Function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or raises exception after max retries
        """
        last_exception = None
        delay = self.RETRY_DELAY
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except (google_exceptions.ServiceUnavailable, 
                    google_exceptions.DeadlineExceeded) as e:
                last_exception = e
                
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"Retry attempt {attempt + 1}/{self.MAX_RETRIES} "
                                 f"after {delay}s delay due to: {type(e).__name__}")
                    time.sleep(delay)
                    delay *= self.RETRY_BACKOFF
                else:
                    logger.error(f"All {self.MAX_RETRIES} retry attempts failed")
                    raise
            except Exception as e:
                # Don't retry for other exceptions
                raise
        
        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
    
    def extract_reading(self, image_bytes: bytes) -> Dict:
        """
        Extract meter reading using Google Vision API
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            Dictionary containing:
                - reading: Extracted meter reading value (float)
                - confidence: Confidence score (0.0-1.0)
                - raw_text: Full text detected by OCR
                - error: Error message if extraction failed (optional)
                - error_type: Type of error (optional)
                
        Requirements:
            - FR-3.2: Fallback to Google Vision API if confidence < 90%
            - FR-3.4: Extract reading value and unit
            - FR-3.5: Calculate confidence score (0-100%)
        """
        # Check if Vision API is available
        if not self.is_available or self.client is None:
            logger.error("Vision API client not available")
            return {
                'reading': 0.0,
                'confidence': 0.0,
                'raw_text': '',
                'error': 'Vision API not initialized. Please check configuration.',
                'error_type': 'service_unavailable'
            }
        
        # Validate input
        if not image_bytes or len(image_bytes) == 0:
            logger.error("Empty image bytes provided")
            return {
                'reading': 0.0,
                'confidence': 0.0,
                'raw_text': '',
                'error': 'Empty or invalid image data',
                'error_type': 'invalid_image'
            }
        
        try:
            # Create Vision API image object
            image = vision.Image(content=image_bytes)
            
            # Perform text detection with retry logic
            def _detect_text():
                return self.client.text_detection(image=image)
            
            response = self._retry_with_backoff(_detect_text)
            
            # Check for API errors in response
            if response.error.message:
                error_msg = f"Vision API error: {response.error.message}"
                logger.error(error_msg)
                return {
                    'reading': 0.0,
                    'confidence': 0.0,
                    'raw_text': '',
                    'error': error_msg,
                    'error_type': 'api_error'
                }
            
            # Get text annotations
            texts = response.text_annotations
            
            if not texts:
                logger.warning("No text detected in image")
                return {
                    'reading': 0.0,
                    'confidence': 0.0,
                    'raw_text': '',
                    'error': 'No text detected in image',
                    'error_type': 'no_text_detected'
                }
            
            # First annotation contains all detected text
            full_text = texts[0].description
            
            # Calculate confidence from bounding box confidence (if available)
            confidence = self._estimate_confidence(texts)
            
            logger.info(f"Vision API detected text: {full_text[:100]}...")
            logger.info(f"Estimated confidence: {confidence:.2f}")
            
            # Extract numeric reading from text
            reading = self._extract_number_from_text(full_text)
            
            if reading == 0.0:
                logger.warning("Could not extract valid number from detected text")
                return {
                    'reading': 0.0,
                    'confidence': confidence,
                    'raw_text': full_text,
                    'error': 'No valid meter reading found in text',
                    'error_type': 'no_number_found'
                }
            
            return {
                'reading': reading,
                'confidence': confidence,
                'raw_text': full_text
            }
            
        except google_exceptions.GoogleAPIError as e:
            # Handle Google API specific errors
            return self._handle_vision_api_error(e)
            
        except Exception as e:
            logger.error(f"Vision API extraction failed: {e}")
            return {
                'reading': 0.0,
                'confidence': 0.0,
                'raw_text': '',
                'error': f'OCR extraction failed: {str(e)}',
                'error_type': 'unknown'
            }
    
    def detect_meter_type(self, image_bytes: bytes) -> str:
        """
        Detect meter type (analog/digital/smart) using label detection
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            Meter type: 'digital', 'analog', or 'unknown'
            
        Requirements:
            - FR-3.3: System shall detect meter type (analog/digital/smart)
        """
        # Check if Vision API is available
        if not self.is_available or self.client is None:
            logger.error("Vision API client not available for meter type detection")
            return 'unknown'
        
        # Validate input
        if not image_bytes or len(image_bytes) == 0:
            logger.error("Empty image bytes provided for meter type detection")
            return 'unknown'
        
        try:
            # Create Vision API image object
            image = vision.Image(content=image_bytes)
            
            # Perform label detection with retry logic
            def _detect_labels():
                return self.client.label_detection(image=image)
            
            response = self._retry_with_backoff(_detect_labels)
            
            # Check for API errors
            if response.error.message:
                logger.error(f"Vision API label detection error: {response.error.message}")
                return 'unknown'
            
            # Get labels
            labels = response.label_annotations
            
            if not labels:
                logger.warning("No labels detected in image")
                return 'unknown'
            
            # Extract label names (lowercase for comparison)
            label_names = [label.description.lower() for label in labels]
            
            logger.info(f"Detected labels: {', '.join(label_names[:10])}")
            
            # Check for digital meter indicators
            digital_keywords = ['digital', 'lcd', 'display', 'screen', 'electronic', 'led']
            if any(keyword in label_names for keyword in digital_keywords):
                logger.info("Detected meter type: digital")
                return 'digital'
            
            # Check for analog meter indicators
            analog_keywords = ['analog', 'dial', 'gauge', 'mechanical', 'needle', 'pointer']
            if any(keyword in label_names for keyword in analog_keywords):
                logger.info("Detected meter type: analog")
                return 'analog'
            
            # Check for smart meter indicators
            smart_keywords = ['smart', 'digital display', 'touchscreen']
            if any(keyword in label_names for keyword in smart_keywords):
                logger.info("Detected meter type: smart (digital)")
                return 'digital'  # Smart meters are digital
            
            logger.info("Could not determine meter type from labels")
            return 'unknown'
            
        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Vision API meter type detection failed: {type(e).__name__}: {e}")
            return 'unknown'
            
        except Exception as e:
            logger.error(f"Meter type detection failed: {e}")
            return 'unknown'
    
    def _extract_number_from_text(self, text: str) -> float:
        """
        Extract numeric reading from OCR text
        
        Args:
            text: Raw OCR text
            
        Returns:
            Extracted number as float, or 0.0 if no valid number found
        """
        # Remove whitespace and newlines
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Find all numbers (including decimals)
        # Pattern matches: 12345, 12345.67, 1,234.56, etc.
        patterns = [
            r'\d+\.\d+',  # Decimal numbers (e.g., 12345.67)
            r'\d{4,}',    # 4+ digit numbers (e.g., 12345)
            r'\d+,\d+\.\d+',  # Numbers with comma separators (e.g., 1,234.56)
        ]
        
        all_matches = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            all_matches.extend(matches)
        
        if not all_matches:
            # Try simpler pattern - any sequence of digits
            matches = re.findall(r'\d+', text)
            if matches:
                # Take the longest sequence
                longest = max(matches, key=len)
                if len(longest) >= 3:  # At least 3 digits for a valid reading
                    return float(longest)
            return 0.0
        
        # Convert matches to floats
        numbers = []
        for match in all_matches:
            try:
                # Remove commas if present
                clean_match = match.replace(',', '')
                num = float(clean_match)
                
                # Filter out unrealistic readings
                # Typical household meter: 100 - 100,000 kWh
                if 10 <= num <= 1000000:
                    numbers.append(num)
            except ValueError:
                continue
        
        if not numbers:
            return 0.0
        
        # Return the most likely reading
        # Prefer numbers with 4-6 digits (typical meter reading range)
        preferred = [n for n in numbers if 1000 <= n <= 999999]
        if preferred:
            return preferred[0]
        
        # Otherwise return the first valid number
        return numbers[0]
    
    def _estimate_confidence(self, text_annotations) -> float:
        """
        Estimate confidence score from Vision API text annotations
        
        Vision API doesn't provide per-text confidence scores in the same way
        as Tesseract, so we estimate based on detection quality.
        
        Args:
            text_annotations: List of text annotations from Vision API
            
        Returns:
            Confidence score (0.0-1.0)
        """
        if not text_annotations:
            return 0.0
        
        # Base confidence on number of detected text elements
        # More detected elements usually means clearer image
        num_elements = len(text_annotations)
        
        # Vision API is generally very accurate, so we start with high confidence
        base_confidence = 0.85
        
        # Adjust based on number of detected elements
        if num_elements >= 10:
            # Many elements detected - likely clear image
            confidence = 0.95
        elif num_elements >= 5:
            # Moderate number of elements
            confidence = 0.90
        elif num_elements >= 2:
            # Few elements but some text detected
            confidence = 0.85
        else:
            # Very few elements - might be unclear
            confidence = 0.70
        
        return confidence
    
    def process_image(self, image_bytes: bytes) -> Dict:
        """
        Complete OCR processing: extract reading and detect meter type
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            Dictionary containing:
                - reading: Extracted meter reading
                - confidence: Confidence score
                - raw_text: Full OCR text
                - meter_type: Detected meter type
                - error: Error message if any
                - error_type: Type of error if any
        """
        # Validate input
        if not image_bytes or len(image_bytes) == 0:
            logger.error("Empty image bytes provided for processing")
            return {
                'reading': 0.0,
                'confidence': 0.0,
                'raw_text': '',
                'meter_type': 'unknown',
                'error': 'Empty or invalid image data',
                'error_type': 'invalid_image'
            }
        
        try:
            # Extract reading
            ocr_result = self.extract_reading(image_bytes)
            
            # Detect meter type (only if reading extraction succeeded or partially succeeded)
            meter_type = 'unknown'
            if not ocr_result.get('error') or ocr_result.get('raw_text'):
                try:
                    meter_type = self.detect_meter_type(image_bytes)
                except Exception as e:
                    logger.warning(f"Meter type detection failed, continuing with 'unknown': {e}")
                    meter_type = 'unknown'
            
            # Combine results
            result = {
                **ocr_result,
                'meter_type': meter_type
            }
            
            if result.get('error'):
                logger.warning(f"OCR processing completed with errors: {result['error']}")
            else:
                logger.info(f"OCR processing complete: reading={result['reading']}, "
                           f"confidence={result['confidence']:.2f}, type={meter_type}")
            
            return result
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return {
                'reading': 0.0,
                'confidence': 0.0,
                'raw_text': '',
                'meter_type': 'unknown',
                'error': f'OCR processing failed: {str(e)}',
                'error_type': 'unknown'
            }


# Global OCR service instance
_ocr_service: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """
    Get or create global OCR service instance
    
    Returns:
        OCRService instance
    """
    global _ocr_service
    
    if _ocr_service is None:
        _ocr_service = OCRService()
    
    return _ocr_service
