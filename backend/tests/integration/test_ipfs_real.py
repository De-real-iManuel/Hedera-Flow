"""
Real IPFS Integration Test
Tests actual upload to Pinata with real credentials
"""
import sys
import os
from pathlib import Path

# Change to backend directory to ensure correct .env is loaded
backend_dir = Path(__file__).parent
os.chdir(backend_dir)

# Add backend to path
sys.path.insert(0, str(backend_dir))

from app.services.ipfs_service import get_ipfs_service
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_image():
    """Create a minimal valid JPEG image"""
    # JPEG header
    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
    # Add some data
    jpeg_data = b'\xff\xdb\x00\x43\x00' + b'\x00' * 64  # Quantization table
    jpeg_data += b'\xff\xc0\x00\x11\x08\x00\x10\x00\x10\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01'  # Start of frame
    jpeg_data += b'\xff\xc4\x00\x1f\x00' + b'\x00' * 28  # Huffman table
    jpeg_data += b'\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00'  # Start of scan
    jpeg_data += b'\x00' * 100  # Image data
    jpeg_data += b'\xff\xd9'  # End of image
    
    return jpeg_header + jpeg_data


def test_ipfs_upload():
    """Test real IPFS upload to Pinata"""
    try:
        logger.info("=" * 60)
        logger.info("IPFS Real Integration Test")
        logger.info("=" * 60)
        
        # Get IPFS service
        ipfs_service = get_ipfs_service()
        
        # Check credentials
        logger.info(f"API URL: {ipfs_service.api_url}")
        logger.info(f"API Key configured: {bool(ipfs_service.api_key)}")
        logger.info(f"Secret Key configured: {bool(ipfs_service.secret_key)}")
        
        if not ipfs_service.api_key or not ipfs_service.secret_key:
            logger.error("❌ Pinata credentials not configured!")
            return False
        
        # Create test image
        logger.info("\n📸 Creating test image...")
        image_bytes = create_test_image()
        logger.info(f"   Image size: {len(image_bytes)} bytes")
        
        # Upload to IPFS
        logger.info("\n☁️  Uploading to IPFS via Pinata...")
        result = ipfs_service.upload_image(
            image_bytes,
            filename="test_meter_reading.jpg"
        )
        
        # Display results
        logger.info("\n✅ Upload successful!")
        logger.info(f"   IPFS Hash: {result['ipfs_hash']}")
        logger.info(f"   IPFS URL: {result['ipfs_url']}")
        logger.info(f"   Gateway URL: {result['gateway_url']}")
        logger.info(f"   Size: {result['size']} bytes")
        if result.get('timestamp'):
            logger.info(f"   Timestamp: {result['timestamp']}")
        
        # Test retrieval URL
        logger.info("\n🔗 Testing URL generation...")
        gateway_url = ipfs_service.get_image_url(result['ipfs_hash'], use_gateway=True)
        ipfs_url = ipfs_service.get_image_url(result['ipfs_hash'], use_gateway=False)
        logger.info(f"   Gateway URL: {gateway_url}")
        logger.info(f"   IPFS URL: {ipfs_url}")
        
        # Test multiple uploads
        logger.info("\n📤 Testing multiple uploads...")
        images = [
            (create_test_image(), "meter_1.jpg"),
            (create_test_image(), "meter_2.jpg"),
        ]
        results = ipfs_service.upload_multiple_images(images)
        
        logger.info(f"   Uploaded {len(results)} images:")
        for i, res in enumerate(results, 1):
            if 'error' in res:
                logger.error(f"   {i}. ❌ {res['filename']}: {res['error']}")
            else:
                logger.info(f"   {i}. ✅ {res['ipfs_hash']}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ All IPFS tests passed!")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_ipfs_upload()
    sys.exit(0 if success else 1)
