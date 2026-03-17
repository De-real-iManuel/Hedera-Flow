"""
Test for Task 11.4: extract_reading method
Verifies that the extract_reading method is properly implemented
"""

import pytest
from PIL import Image, ImageDraw, ImageFont
import io


def test_extract_reading_method_exists():
    """Test that extract_reading method exists in OCRService"""
    from app.services.ocr_service import OCRService
    
    # Create OCRService instance
    ocr_service = OCRService()
    
    # Verify method exists
    assert hasattr(ocr_service, 'extract_reading'), "extract_reading method not found"
    assert callable(ocr_service.extract_reading), "extract_reading is not callable"
    
    print("✓ extract_reading method exists")


def test_extract_reading_signature():
    """Test that extract_reading has correct signature"""
    from app.services.ocr_service import OCRService
    import inspect
    
    ocr_service = OCRService()
    
    # Get method signature
    sig = inspect.signature(ocr_service.extract_reading)
    
    # Check parameters
    params = list(sig.parameters.keys())
    assert 'image_bytes' in params, "extract_reading should accept image_bytes parameter"
    
    print("✓ extract_reading has correct signature")


def test_extract_reading_return_type():
    """Test that extract_reading returns a dictionary with required keys"""
    from app.services.ocr_service import OCRService
    from unittest.mock import Mock, patch
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock successful response
        mock_response = Mock()
        mock_response.error.message = ""
        mock_annotation = Mock()
        mock_annotation.description = "12345"
        mock_response.text_annotations = [mock_annotation]
        mock_client.text_detection.return_value = mock_response
        
        ocr_service = OCRService()
        
        # Create a simple test image with text
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw text on image
        try:
            # Try to use a font, fallback to default if not available
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 70), "12345", fill='black', font=font)
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        image_bytes = img_byte_arr.getvalue()
        
        # Call extract_reading
        result = ocr_service.extract_reading(image_bytes)
        
        # Verify return type
        assert isinstance(result, dict), "extract_reading should return a dictionary"
        
        # Verify required keys
        required_keys = ['reading', 'confidence', 'raw_text']
        for key in required_keys:
            assert key in result, f"Result should contain '{key}' key"
        
        # Verify types
        assert isinstance(result['reading'], (int, float)), "reading should be numeric"
        assert isinstance(result['confidence'], (int, float)), "confidence should be numeric"
        assert isinstance(result['raw_text'], str), "raw_text should be string"
        
        # Verify confidence is in valid range
        assert 0.0 <= result['confidence'] <= 1.0, "confidence should be between 0.0 and 1.0"
        
        print(f"✓ extract_reading returns correct format")
        print(f"  - Reading: {result['reading']}")
        print(f"  - Confidence: {result['confidence']:.2f}")
        print(f"  - Raw text: {result['raw_text'][:50]}...")


def test_extract_reading_with_number():
    """Test that extract_reading can extract a number from an image"""
    from app.services.ocr_service import OCRService
    from unittest.mock import Mock, patch
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock successful response with number
        mock_response = Mock()
        mock_response.error.message = ""
        mock_annotation = Mock()
        mock_annotation.description = "54321"
        mock_response.text_annotations = [mock_annotation]
        mock_client.text_detection.return_value = mock_response
        
        ocr_service = OCRService()
        
        # Create test image with a clear number
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 80)
        except:
            font = ImageFont.load_default()
        
        # Draw a clear meter reading
        draw.text((50, 50), "54321", fill='black', font=font)
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        image_bytes = img_byte_arr.getvalue()
        
        # Call extract_reading
        result = ocr_service.extract_reading(image_bytes)
        
        # Verify a number was extracted
        assert result['reading'] > 0, "Should extract a positive number"
        
        # The reading should be close to 54321
        assert result['reading'] >= 1000, "Should extract a reasonable meter reading"
        
        print(f"✓ extract_reading extracted number: {result['reading']}")


def test_extract_reading_error_handling():
    """Test that extract_reading handles errors gracefully"""
    from app.services.ocr_service import OCRService
    from unittest.mock import Mock, patch
    
    with patch('app.services.ocr_service.vision.ImageAnnotatorClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock invalid argument error
        from google.api_core import exceptions as google_exceptions
        mock_client.text_detection.side_effect = google_exceptions.InvalidArgument("Invalid image")
        
        ocr_service = OCRService()
        
        # Test with invalid image bytes
        result = ocr_service.extract_reading(b'invalid image data')
        
        # Should return error in result, not raise exception
        assert 'error' in result or result['reading'] == 0.0, \
            "Should handle invalid image gracefully"
        
        print("✓ extract_reading handles errors gracefully")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing Task 11.4: extract_reading method")
    print("="*60 + "\n")
    
    try:
        test_extract_reading_method_exists()
        test_extract_reading_signature()
        test_extract_reading_return_type()
        test_extract_reading_with_number()
        test_extract_reading_error_handling()
        
        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        raise
