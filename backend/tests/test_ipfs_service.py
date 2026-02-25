"""
Tests for IPFS Service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.ipfs_service import IPFSService, get_ipfs_service


@pytest.fixture
def mock_settings():
    """Mock settings with Pinata credentials"""
    with patch('app.services.ipfs_service.settings') as mock:
        mock.ipfs_api_url = "https://api.pinata.cloud"
        mock.pinata_api_key = "test_api_key"
        mock.pinata_secret_key = "test_secret_key"
        yield mock


@pytest.fixture
def ipfs_service(mock_settings):
    """Create IPFS service instance with mocked settings"""
    return IPFSService()


@pytest.fixture
def sample_image_bytes():
    """Sample image data"""
    # Create a minimal valid JPEG header
    return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00' + b'\x00' * 100


class TestIPFSService:
    """Test IPFS service functionality"""
    
    def test_initialization_with_credentials(self, mock_settings):
        """Test service initializes correctly with credentials"""
        service = IPFSService()
        
        assert service.api_url == "https://api.pinata.cloud"
        assert service.api_key == "test_api_key"
        assert service.secret_key == "test_secret_key"
    
    def test_initialization_without_credentials(self):
        """Test service warns when credentials are missing"""
        with patch('app.services.ipfs_service.settings') as mock_settings:
            mock_settings.ipfs_api_url = "https://api.pinata.cloud"
            mock_settings.pinata_api_key = None
            mock_settings.pinata_secret_key = None
            
            with patch('app.services.ipfs_service.logger') as mock_logger:
                service = IPFSService()
                mock_logger.warning.assert_called_once()
    
    @patch('app.services.ipfs_service.requests.post')
    def test_upload_image_success(self, mock_post, ipfs_service, sample_image_bytes):
        """Test successful image upload to IPFS"""
        # Mock successful Pinata response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'IpfsHash': 'QmTest123456789',
            'PinSize': 1024,
            'Timestamp': '2024-02-18T12:00:00.000Z'
        }
        mock_post.return_value = mock_response
        
        # Upload image
        result = ipfs_service.upload_image(sample_image_bytes, "test_meter.jpg")
        
        # Verify result
        assert result['ipfs_hash'] == 'QmTest123456789'
        assert result['ipfs_url'] == 'ipfs://QmTest123456789'
        assert result['gateway_url'] == 'https://gateway.pinata.cloud/ipfs/QmTest123456789'
        assert result['size'] == 1024
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://api.pinata.cloud/pinning/pinFileToIPFS'
        assert call_args[1]['headers']['pinata_api_key'] == 'test_api_key'
        assert call_args[1]['headers']['pinata_secret_api_key'] == 'test_secret_key'
    
    @patch('app.services.ipfs_service.requests.post')
    def test_upload_image_api_error(self, mock_post, ipfs_service, sample_image_bytes):
        """Test handling of Pinata API errors"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_post.return_value = mock_response
        
        # Upload should raise exception
        with pytest.raises(Exception) as exc_info:
            ipfs_service.upload_image(sample_image_bytes, "test_meter.jpg")
        
        assert "Pinata upload failed: 401" in str(exc_info.value)
    
    @patch('app.services.ipfs_service.requests.post')
    def test_upload_image_no_hash_returned(self, mock_post, ipfs_service, sample_image_bytes):
        """Test handling when no IPFS hash is returned"""
        # Mock response without hash
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response
        
        # Upload should raise exception
        with pytest.raises(Exception) as exc_info:
            ipfs_service.upload_image(sample_image_bytes, "test_meter.jpg")
        
        assert "No IPFS hash returned" in str(exc_info.value)
    
    @patch('app.services.ipfs_service.requests.post')
    def test_upload_image_network_error(self, mock_post, ipfs_service, sample_image_bytes):
        """Test handling of network errors"""
        # Mock network error
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")
        
        # Upload should raise exception
        with pytest.raises(Exception) as exc_info:
            ipfs_service.upload_image(sample_image_bytes, "test_meter.jpg")
        
        assert "Network error" in str(exc_info.value)
    
    def test_upload_image_without_credentials(self, sample_image_bytes):
        """Test upload fails without credentials"""
        with patch('app.services.ipfs_service.settings') as mock_settings:
            mock_settings.ipfs_api_url = "https://api.pinata.cloud"
            mock_settings.pinata_api_key = None
            mock_settings.pinata_secret_key = None
            
            service = IPFSService()
            
            with pytest.raises(Exception) as exc_info:
                service.upload_image(sample_image_bytes, "test.jpg")
            
            assert "not configured" in str(exc_info.value)
    
    @patch('app.services.ipfs_service.requests.post')
    def test_upload_multiple_images(self, mock_post, ipfs_service, sample_image_bytes):
        """Test uploading multiple images"""
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            {'IpfsHash': 'QmHash1', 'PinSize': 1024},
            {'IpfsHash': 'QmHash2', 'PinSize': 2048}
        ]
        mock_post.return_value = mock_response
        
        # Upload multiple images
        images = [
            (sample_image_bytes, "image1.jpg"),
            (sample_image_bytes, "image2.jpg")
        ]
        results = ipfs_service.upload_multiple_images(images)
        
        # Verify results
        assert len(results) == 2
        assert results[0]['ipfs_hash'] == 'QmHash1'
        assert results[1]['ipfs_hash'] == 'QmHash2'
        assert mock_post.call_count == 2
    
    @patch('app.services.ipfs_service.requests.post')
    def test_upload_multiple_images_with_failures(self, mock_post, ipfs_service, sample_image_bytes):
        """Test uploading multiple images with some failures"""
        # Mock mixed responses
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {'IpfsHash': 'QmHash1', 'PinSize': 1024}
        
        mock_response2 = Mock()
        mock_response2.status_code = 500
        mock_response2.text = 'Server error'
        
        mock_post.side_effect = [mock_response1, mock_response2]
        
        # Upload multiple images
        images = [
            (sample_image_bytes, "image1.jpg"),
            (sample_image_bytes, "image2.jpg")
        ]
        results = ipfs_service.upload_multiple_images(images)
        
        # Verify results
        assert len(results) == 2
        assert results[0]['ipfs_hash'] == 'QmHash1'
        assert 'error' in results[1]
        assert results[1]['filename'] == 'image2.jpg'
    
    def test_get_image_url_with_gateway(self, ipfs_service):
        """Test getting gateway URL for IPFS hash"""
        url = ipfs_service.get_image_url('QmTest123', use_gateway=True)
        assert url == 'https://gateway.pinata.cloud/ipfs/QmTest123'
    
    def test_get_image_url_without_gateway(self, ipfs_service):
        """Test getting IPFS URL for hash"""
        url = ipfs_service.get_image_url('QmTest123', use_gateway=False)
        assert url == 'ipfs://QmTest123'
    
    @patch('app.services.ipfs_service.requests.post')
    def test_pin_by_hash_success(self, mock_post, ipfs_service):
        """Test pinning existing IPFS hash"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'pin_id',
            'ipfsHash': 'QmTest123',
            'status': 'pinned'
        }
        mock_post.return_value = mock_response
        
        # Pin hash
        result = ipfs_service.pin_by_hash('QmTest123')
        
        # Verify result
        assert result['ipfsHash'] == 'QmTest123'
        assert result['status'] == 'pinned'
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://api.pinata.cloud/pinning/pinByHash'
    
    @patch('app.services.ipfs_service.requests.post')
    def test_pin_by_hash_error(self, mock_post, ipfs_service):
        """Test error handling when pinning fails"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = 'Hash not found'
        mock_post.return_value = mock_response
        
        # Pin should raise exception
        with pytest.raises(Exception) as exc_info:
            ipfs_service.pin_by_hash('QmInvalidHash')
        
        assert "Pin failed: 404" in str(exc_info.value)
    
    def test_get_ipfs_service_singleton(self, mock_settings):
        """Test that get_ipfs_service returns singleton instance"""
        # Reset singleton
        import app.services.ipfs_service
        app.services.ipfs_service._ipfs_service = None
        
        # Get service twice
        service1 = get_ipfs_service()
        service2 = get_ipfs_service()
        
        # Should be same instance
        assert service1 is service2


class TestIPFSServiceIntegration:
    """Integration tests for IPFS service (require actual Pinata credentials)"""
    
    @pytest.mark.skip(reason="Requires actual Pinata API credentials")
    def test_real_upload(self, sample_image_bytes):
        """Test actual upload to Pinata (skipped by default)"""
        # This test requires real credentials in environment
        service = IPFSService()
        result = service.upload_image(sample_image_bytes, "test_integration.jpg")
        
        assert result['ipfs_hash'].startswith('Qm')
        assert 'gateway.pinata.cloud' in result['gateway_url']
