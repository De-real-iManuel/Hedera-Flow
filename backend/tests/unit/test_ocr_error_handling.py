"""
Test for Task 11.7: Handle API errors and fallbacks
Verifies that the OCR service properly handles errors and provides fallbacks
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io
from google.api_core import exceptions as google_exceptions


def create_test_image() -> bytes:
    """Create a simple test image with text"""
    img = Image.new('RGB', (400, 200), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


def test_ocr_service_handles_unavailable_client():
    """Test that OCR service handles unavailable Vision API client gracefully"""
    from app.services.ocr_service import OCRService
    
    # Create service with mocked client initialization that fails
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client:
        mock_client.side_effect = Exception("Failed to initialize")
        
        ocr_service = OCRService()
        
        # Service should be created but marked as unavailable
        assert ocr_service.is_available == False
        
        # Attempting to extract reading should return error
        result = ocr_service.extract_reading(create_test_image())
        
        assert result['reading'] == 0.0
        assert result['confidence'] == 0.0
        assert 'error' in result
        assert result['error_type'] == 'service_unavailable'
        
        print("✓ OCR service handles unavailable client gracefully")


def test_extract_reading_handles_empty_image():
    """Test that extract_reading handles empty image bytes"""
    from app.services.ocr_service import OCRService
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        ocr_service = OCRService()
        
        # Test with empty bytes
        result = ocr_service.extract_reading(b'')
        
        assert result['reading'] == 0.0
        assert result['confidence'] == 0.0
        assert 'error' in result
        assert result['error_type'] == 'invalid_image'
        
        print("✓ extract_reading handles empty image bytes")


def test_extract_reading_handles_invalid_image():
    """Test that extract_reading handles invalid image data"""
    from app.services.ocr_service import OCRService
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock invalid argument error for invalid image
        mock_client.text_detection.side_effect = google_exceptions.InvalidArgument("Invalid image")
        
        ocr_service = OCRService()
        
        # Test with invalid image data
        result = ocr_service.extract_reading(b'not an image')
        
        assert result['reading'] == 0.0
        assert result['confidence'] == 0.0
        assert 'error' in result
        
        print("✓ extract_reading handles invalid image data")


def test_extract_reading_handles_quota_exceeded():
    """Test that extract_reading handles quota exceeded error"""
    from app.services.ocr_service import OCRService
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock quota exceeded error
        mock_client.text_detection.side_effect = google_exceptions.ResourceExhausted("Quota exceeded")
        
        ocr_service = OCRService()
        result = ocr_service.extract_reading(create_test_image())
        
        assert result['reading'] == 0.0
        assert result['error_type'] == 'quota_exceeded'
        assert 'quota' in result['error'].lower()
        
        print("✓ extract_reading handles quota exceeded error")


def test_extract_reading_handles_service_unavailable():
    """Test that extract_reading handles service unavailable error"""
    from app.services.ocr_service import OCRService
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock service unavailable error
        mock_client.text_detection.side_effect = google_exceptions.ServiceUnavailable("Service unavailable")
        
        ocr_service = OCRService()
        result = ocr_service.extract_reading(create_test_image())
        
        assert result['reading'] == 0.0
        assert result['error_type'] == 'service_unavailable'
        assert 'unavailable' in result['error'].lower()
        
        print("✓ extract_reading handles service unavailable error")


def test_extract_reading_handles_authentication_error():
    """Test that extract_reading handles authentication error"""
    from app.services.ocr_service import OCRService
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock authentication error
        mock_client.text_detection.side_effect = google_exceptions.Unauthenticated("Authentication failed")
        
        ocr_service = OCRService()
        result = ocr_service.extract_reading(create_test_image())
        
        assert result['reading'] == 0.0
        assert result['error_type'] == 'authentication_failed'
        assert 'authentication' in result['error'].lower()
        
        print("✓ extract_reading handles authentication error")


def test_extract_reading_handles_permission_denied():
    """Test that extract_reading handles permission denied error"""
    from app.services.ocr_service import OCRService
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock permission denied error
        mock_client.text_detection.side_effect = google_exceptions.PermissionDenied("Permission denied")
        
        ocr_service = OCRService()
        result = ocr_service.extract_reading(create_test_image())
        
        assert result['reading'] == 0.0
        assert result['error_type'] == 'permission_denied'
        assert 'permission' in result['error'].lower()
        
        print("✓ extract_reading handles permission denied error")


def test_extract_reading_handles_invalid_argument():
    """Test that extract_reading handles invalid argument error"""
    from app.services.ocr_service import OCRService
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock invalid argument error
        mock_client.text_detection.side_effect = google_exceptions.InvalidArgument("Invalid image")
        
        ocr_service = OCRService()
        result = ocr_service.extract_reading(create_test_image())
        
        assert result['reading'] == 0.0
        assert result['error_type'] == 'invalid_image'
        
        print("✓ extract_reading handles invalid argument error")


def test_extract_reading_handles_timeout():
    """Test that extract_reading handles timeout error"""
    from app.services.ocr_service import OCRService
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock timeout error
        mock_client.text_detection.side_effect = google_exceptions.DeadlineExceeded("Request timeout")
        
        ocr_service = OCRService()
        result = ocr_service.extract_reading(create_test_image())
        
        assert result['reading'] == 0.0
        assert result['error_type'] == 'timeout'
        assert 'timeout' in result['error'].lower()
        
        print("✓ extract_reading handles timeout error")


def test_extract_reading_handles_no_text_detected():
    """Test that extract_reading handles case when no text is detected"""
    from app.services.ocr_service import OCRService
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock response with no text
        mock_response = Mock()
        mock_response.error.message = ""
        mock_response.text_annotations = []
        mock_client.text_detection.return_value = mock_response
        
        ocr_service = OCRService()
        result = ocr_service.extract_reading(create_test_image())
        
        assert result['reading'] == 0.0
        assert result['error_type'] == 'no_text_detected'
        assert 'no text' in result['error'].lower()
        
        print("✓ extract_reading handles no text detected")


def test_extract_reading_handles_no_number_found():
    """Test that extract_reading handles case when text is detected but no number found"""
    from app.services.ocr_service import OCRService
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock response with text but no numbers
        mock_response = Mock()
        mock_response.error.message = ""
        mock_annotation = Mock()
        mock_annotation.description = "ABC XYZ"  # No numbers
        mock_response.text_annotations = [mock_annotation]
        mock_client.text_detection.return_value = mock_response
        
        ocr_service = OCRService()
        result = ocr_service.extract_reading(create_test_image())
        
        assert result['reading'] == 0.0
        assert result['error_type'] == 'no_number_found'
        assert result['raw_text'] == "ABC XYZ"
        
        print("✓ extract_reading handles no number found")


def test_retry_logic_with_service_unavailable():
    """Test that retry logic works for transient errors"""
    from app.services.ocr_service import OCRService
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock service unavailable on first 2 calls, then success
        mock_response = Mock()
        mock_response.error.message = ""
        mock_annotation = Mock()
        mock_annotation.description = "12345"
        mock_response.text_annotations = [mock_annotation]
        
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise google_exceptions.ServiceUnavailable("Service unavailable")
            return mock_response
        
        mock_client.text_detection.side_effect = side_effect
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            ocr_service = OCRService()
            result = ocr_service.extract_reading(create_test_image())
        
        # Should succeed after retries
        assert result['reading'] > 0
        assert call_count[0] == 3  # Should have retried 3 times
        
        print("✓ Retry logic works for transient errors")


def test_detect_meter_type_handles_errors():
    """Test that detect_meter_type handles errors gracefully"""
    from app.services.ocr_service import OCRService
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock error
        mock_client.label_detection.side_effect = google_exceptions.ServiceUnavailable("Service unavailable")
        
        ocr_service = OCRService()
        meter_type = ocr_service.detect_meter_type(create_test_image())
        
        # Should return 'unknown' instead of raising exception
        assert meter_type == 'unknown'
        
        print("✓ detect_meter_type handles errors gracefully")


def test_process_image_handles_errors():
    """Test that process_image handles errors gracefully"""
    from app.services.ocr_service import OCRService
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock error
        mock_client.text_detection.side_effect = Exception("Unexpected error")
        
        ocr_service = OCRService()
        result = ocr_service.process_image(create_test_image())
        
        # Should return error response instead of raising exception
        assert result['reading'] == 0.0
        assert 'error' in result
        assert result['meter_type'] == 'unknown'
        
        print("✓ process_image handles errors gracefully")


def test_process_image_handles_empty_input():
    """Test that process_image handles empty input"""
    from app.services.ocr_service import OCRService
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        ocr_service = OCRService()
        result = ocr_service.process_image(b'')
        
        assert result['reading'] == 0.0
        assert result['error_type'] == 'invalid_image'
        assert result['meter_type'] == 'unknown'
        
        print("✓ process_image handles empty input")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing Task 11.7: Handle API errors and fallbacks")
    print("="*60 + "\n")
    
    try:
        test_ocr_service_handles_unavailable_client()
        test_extract_reading_handles_empty_image()
        test_extract_reading_handles_invalid_image()
        test_extract_reading_handles_quota_exceeded()
        test_extract_reading_handles_service_unavailable()
        test_extract_reading_handles_authentication_error()
        test_extract_reading_handles_permission_denied()
        test_extract_reading_handles_invalid_argument()
        test_extract_reading_handles_timeout()
        test_extract_reading_handles_no_text_detected()
        test_extract_reading_handles_no_number_found()
        test_retry_logic_with_service_unavailable()
        test_detect_meter_type_handles_errors()
        test_process_image_handles_errors()
        test_process_image_handles_empty_input()
        
        print("\n" + "="*60)
        print("✅ All error handling tests passed!")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        raise
