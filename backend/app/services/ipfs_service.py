"""
IPFS Service
Handles image storage on IPFS using Pinata
"""
import logging
import requests
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class IPFSService:
    """
    Service for storing images on IPFS via Pinata
    
    Requirements:
        - FR-5.18: Store image hashes on IPFS
        - FR-7.3: Upload evidence to IPFS
    """
    
    def __init__(self):
        self.api_url = settings.ipfs_api_url
        self.api_key = settings.pinata_api_key
        self.secret_key = settings.pinata_secret_key
        
        if not self.api_key or not self.secret_key:
            logger.warning("Pinata API credentials not configured. IPFS uploads will fail.")
    
    def upload_image(self, image_bytes: bytes, filename: str = "meter_image.jpg") -> Dict[str, Any]:
        """
        Upload an image to IPFS via Pinata
        
        Args:
            image_bytes: Image data as bytes
            filename: Optional filename for the image
            
        Returns:
            Dictionary containing:
                - ipfs_hash: The IPFS hash (CID)
                - ipfs_url: Full IPFS URL (ipfs://...)
                - gateway_url: HTTP gateway URL for viewing
                - size: File size in bytes
                
        Raises:
            Exception: If upload fails
        """
        if not self.api_key or not self.secret_key:
            raise Exception("Pinata API credentials not configured")
        
        try:
            logger.info(f"Uploading image to IPFS via Pinata: {filename} ({len(image_bytes)} bytes)")
            
            # Pinata API endpoint for file upload
            url = f"{self.api_url}/pinning/pinFileToIPFS"
            
            # Prepare headers with authentication
            headers = {
                'pinata_api_key': self.api_key,
                'pinata_secret_api_key': self.secret_key
            }
            
            # Prepare file for upload
            files = {
                'file': (filename, image_bytes, 'image/jpeg')
            }
            
            # Optional metadata
            metadata = {
                'name': filename,
                'keyvalues': {
                    'app': 'hedera-flow',
                    'type': 'meter_image'
                }
            }
            
            # Add metadata to request (send as JSON strings)
            import json
            data = {
                'pinataMetadata': json.dumps(metadata),
                'pinataOptions': json.dumps({'cidVersion': 1})
            }
            
            # Make request to Pinata
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
            
            # Check response
            if response.status_code != 200:
                error_msg = f"Pinata upload failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Parse response
            result = response.json()
            ipfs_hash = result.get('IpfsHash')
            
            if not ipfs_hash:
                raise Exception("No IPFS hash returned from Pinata")
            
            logger.info(f"Image uploaded successfully to IPFS: {ipfs_hash}")
            
            return {
                'ipfs_hash': ipfs_hash,
                'ipfs_url': f"ipfs://{ipfs_hash}",
                'gateway_url': f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}",
                'size': result.get('PinSize', len(image_bytes)),
                'timestamp': result.get('Timestamp')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during IPFS upload: {e}")
            raise Exception(f"Failed to upload to IPFS: Network error - {str(e)}")
        except Exception as e:
            logger.error(f"IPFS upload failed: {e}")
            raise
    
    def upload_multiple_images(self, images: list[tuple[bytes, str]]) -> list[Dict[str, Any]]:
        """
        Upload multiple images to IPFS
        
        Args:
            images: List of tuples (image_bytes, filename)
            
        Returns:
            List of upload results
        """
        results = []
        
        for image_bytes, filename in images:
            try:
                result = self.upload_image(image_bytes, filename)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to upload {filename}: {e}")
                results.append({
                    'error': str(e),
                    'filename': filename
                })
        
        return results
    
    def get_image_url(self, ipfs_hash: str, use_gateway: bool = True) -> str:
        """
        Get URL for an IPFS image
        
        Args:
            ipfs_hash: The IPFS hash (CID)
            use_gateway: If True, return HTTP gateway URL; if False, return ipfs:// URL
            
        Returns:
            Image URL
        """
        if use_gateway:
            return f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
        else:
            return f"ipfs://{ipfs_hash}"
    
    def pin_by_hash(self, ipfs_hash: str) -> Dict[str, Any]:
        """
        Pin an existing IPFS hash to Pinata
        
        Args:
            ipfs_hash: The IPFS hash to pin
            
        Returns:
            Pin status
        """
        if not self.api_key or not self.secret_key:
            raise Exception("Pinata API credentials not configured")
        
        try:
            url = f"{self.api_url}/pinning/pinByHash"
            
            headers = {
                'pinata_api_key': self.api_key,
                'pinata_secret_api_key': self.secret_key,
                'Content-Type': 'application/json'
            }
            
            data = {
                'hashToPin': ipfs_hash,
                'pinataMetadata': {
                    'name': f'pinned_{ipfs_hash}',
                    'keyvalues': {
                        'app': 'hedera-flow'
                    }
                }
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Pin failed: {response.status_code} - {response.text}")
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to pin hash {ipfs_hash}: {e}")
            raise


# Singleton instance
_ipfs_service: Optional[IPFSService] = None


def get_ipfs_service() -> IPFSService:
    """Get or create IPFS service instance"""
    global _ipfs_service
    if _ipfs_service is None:
        _ipfs_service = IPFSService()
    return _ipfs_service
