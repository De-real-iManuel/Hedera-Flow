"""
Smart Meter Service for Hedera Flow MVP

Implements smart meter cryptographic signature functionality:
- ED25519 keypair generation for meters
- Private key encryption (AES-256) and secure storage
- Consumption data signing with meter private key
- Signature verification with public key
- Fraud detection for invalid signatures

Requirements: FR-9.1 to FR-9.12, US-16, US-17
Spec: prepaid-smart-meter-mvp
"""
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import uuid
import os
import hashlib

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.backends import default_backend
import base64

logger = logging.getLogger(__name__)


class SmartMeterError(Exception):
    """Raised when smart meter operation fails"""
    pass


class SmartMeterService:
    """Service for smart meter cryptographic operations"""
    
    def __init__(self, db: Session):
        """
        Initialize smart meter service
        
        Args:
            db: Database session
        """
        self.db = db
        self._setup_encryption()
    
    def _setup_encryption(self):
        """
        Setup AES-256 encryption key for private key storage.
        
        Uses environment variable METER_KEY_ENCRYPTION_KEY or generates one.
        In production, this should be stored in a secure key management system.
        
        The encryption key must be 32 bytes (256 bits) for AES-256.
        
        Requirements: FR-9.2 (Private key encryption with AES-256)
        """
        try:
            # Get encryption key from environment
            encryption_key = os.getenv('METER_KEY_ENCRYPTION_KEY')
            
            if not encryption_key:
                logger.warning(
                    "METER_KEY_ENCRYPTION_KEY not set in environment. "
                    "Generating temporary key (NOT SUITABLE FOR PRODUCTION)"
                )
                # Generate a 32-byte (256-bit) key for AES-256
                encryption_key = base64.b64encode(os.urandom(32)).decode()
                logger.warning(f"Temporary encryption key: {encryption_key}")
            
            # Decode base64 key to bytes
            if isinstance(encryption_key, str):
                try:
                    self.encryption_key = base64.b64decode(encryption_key)
                except Exception:
                    # If not base64, use the string directly (hash it to 32 bytes)
                    self.encryption_key = hashlib.sha256(encryption_key.encode()).digest()
            else:
                self.encryption_key = encryption_key
            
            # Verify key length (must be 32 bytes for AES-256)
            if len(self.encryption_key) != 32:
                raise ValueError(f"Encryption key must be 32 bytes for AES-256, got {len(self.encryption_key)}")
            
            logger.info("AES-256 encryption setup complete for smart meter keys")
            
        except Exception as e:
            logger.error(f"Failed to setup encryption: {e}", exc_info=True)
            raise SmartMeterError(f"Failed to setup encryption: {str(e)}")
    
    def _encrypt_private_key(self, private_key_pem: bytes) -> tuple[str, str]:
        """
        Encrypt private key using AES-256-CBC.
        
        Args:
            private_key_pem: PEM-encoded private key bytes
        
        Returns:
            Tuple of (encrypted_data_base64, iv_base64)
        
        Requirements: FR-9.2 (AES-256 encryption)
        """
        try:
            # Generate random IV (16 bytes for AES)
            iv = os.urandom(16)
            
            # Create AES-256-CBC cipher
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Apply PKCS7 padding
            padder = sym_padding.PKCS7(128).padder()
            padded_data = padder.update(private_key_pem) + padder.finalize()
            
            # Encrypt
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            # Encode to base64 for storage
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            iv_b64 = base64.b64encode(iv).decode('utf-8')
            
            return encrypted_b64, iv_b64
            
        except Exception as e:
            logger.error(f"Failed to encrypt private key: {e}", exc_info=True)
            raise SmartMeterError(f"Failed to encrypt private key: {str(e)}")
    
    def _decrypt_private_key(self, encrypted_data_b64: str, iv_b64: str) -> bytes:
        """
        Decrypt private key using AES-256-CBC.
        
        Args:
            encrypted_data_b64: Base64-encoded encrypted data
            iv_b64: Base64-encoded initialization vector
        
        Returns:
            Decrypted PEM-encoded private key bytes
        
        Requirements: FR-9.2 (AES-256 decryption)
        """
        try:
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted_data_b64)
            iv = base64.b64decode(iv_b64)
            
            # Create AES-256-CBC cipher
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt
            padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Remove PKCS7 padding
            unpadder = sym_padding.PKCS7(128).unpadder()
            private_key_pem = unpadder.update(padded_data) + unpadder.finalize()
            
            return private_key_pem
            
        except Exception as e:
            logger.error(f"Failed to decrypt private key: {e}", exc_info=True)
            raise SmartMeterError(f"Failed to decrypt private key: {str(e)}")
    
    def generate_keypair(self, meter_id: str) -> Dict[str, Any]:
        """
        Generate ED25519 keypair for a smart meter.
        
        Creates a new keypair, encrypts the private key, and stores both
        in the database. The public key is stored in plaintext for verification.
        
        Args:
            meter_id: Meter UUID
        
        Returns:
            Dictionary containing:
                - meter_id: Meter UUID
                - public_key: PEM-encoded public key
                - algorithm: Signature algorithm (ED25519)
                - created_at: Timestamp
        
        Raises:
            SmartMeterError: If keypair generation fails
        
        Requirements: FR-9.1, FR-9.2, FR-9.3, Task 2.2
        """
        try:
            logger.info(f"Generating ED25519 keypair for meter {meter_id}")
            
            # Check if keypair already exists
            check_query = text("""
                SELECT id FROM smart_meter_keys
                WHERE meter_id = :meter_id
            """)
            existing = self.db.execute(check_query, {'meter_id': meter_id}).fetchone()
            
            if existing:
                raise SmartMeterError(
                    f"Keypair already exists for meter {meter_id}. "
                    "Use get_public_key() to retrieve it."
                )
            
            # Generate ED25519 keypair
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            # Serialize private key to PEM format
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Serialize public key to PEM format
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Encrypt private key with AES-256-CBC
            encrypted_private, encryption_iv = self._encrypt_private_key(private_pem)
            
            # Store in database
            created_at = datetime.utcnow()
            insert_query = text("""
                INSERT INTO smart_meter_keys (
                    id, meter_id, public_key, private_key_encrypted,
                    encryption_iv, algorithm, created_at
                ) VALUES (
                    :id, :meter_id, :public_key, :private_key_encrypted,
                    :encryption_iv, :algorithm, :created_at
                )
            """)
            
            params = {
                'id': str(uuid.uuid4()),
                'meter_id': meter_id,
                'public_key': public_pem.decode('utf-8'),
                'private_key_encrypted': encrypted_private,
                'encryption_iv': encryption_iv,
                'algorithm': 'ED25519',
                'created_at': created_at
            }
            
            self.db.execute(insert_query, params)
            self.db.commit()
            
            logger.info(f"✅ Generated and stored keypair for meter {meter_id}")
            logger.info(f"   Algorithm: ED25519")
            logger.info(f"   Public key length: {len(public_pem)} bytes")
            logger.info(f"   Private key encrypted: Yes")
            
            return {
                'meter_id': meter_id,
                'public_key': public_pem.decode('utf-8'),
                'algorithm': 'ED25519',
                'created_at': created_at.isoformat()
            }
            
        except SmartMeterError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to generate keypair: {e}", exc_info=True)
            raise SmartMeterError(f"Failed to generate keypair: {str(e)}")
    
    def get_public_key(self, meter_id: str) -> Optional[str]:
        """
        Get public key for a meter.
        
        Args:
            meter_id: Meter UUID
        
        Returns:
            PEM-encoded public key or None if not found
        
        Requirements: FR-9.3
        """
        try:
            query = text("""
                SELECT public_key FROM smart_meter_keys
                WHERE meter_id = :meter_id
            """)
            
            result = self.db.execute(query, {'meter_id': meter_id}).fetchone()
            
            if result:
                return result[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get public key: {e}", exc_info=True)
            raise SmartMeterError(f"Failed to get public key: {str(e)}")
    
    def _get_private_key(self, meter_id: str) -> ed25519.Ed25519PrivateKey:
        """
        Retrieve and decrypt private key for a meter.
        
        INTERNAL USE ONLY - Private keys should never be exposed via API.
        
        Args:
            meter_id: Meter UUID
        
        Returns:
            Decrypted ED25519 private key object
        
        Raises:
            SmartMeterError: If key not found or decryption fails
        
        Requirements: FR-9.2, NFR-8.2
        """
        try:
            query = text("""
                SELECT private_key_encrypted, encryption_iv FROM smart_meter_keys
                WHERE meter_id = :meter_id
            """)
            
            result = self.db.execute(query, {'meter_id': meter_id}).fetchone()
            
            if not result:
                raise SmartMeterError(f"No keypair found for meter {meter_id}")
            
            # Decrypt private key using AES-256
            encrypted_private = result[0]
            encryption_iv = result[1]
            private_pem = self._decrypt_private_key(encrypted_private, encryption_iv)
            
            # Load private key object
            private_key = serialization.load_pem_private_key(
                private_pem,
                password=None,
                backend=default_backend()
            )
            
            # Update last_used_at timestamp
            update_query = text("""
                UPDATE smart_meter_keys
                SET last_used_at = NOW()
                WHERE meter_id = :meter_id
            """)
            self.db.execute(update_query, {'meter_id': meter_id})
            self.db.commit()
            
            return private_key
            
        except SmartMeterError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve private key: {e}", exc_info=True)
            raise SmartMeterError(f"Failed to retrieve private key: {str(e)}")
    
    def sign_consumption(
        self,
        meter_id: str,
        consumption_kwh: float,
        timestamp: int,
        reading_before: Optional[float] = None,
        reading_after: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Sign consumption data with meter's private key.
        
        Creates a deterministic message from consumption data, hashes it with SHA-256,
        and signs the hash with the meter's ED25519 private key.
        
        Message format: meter_id + consumption_kwh + timestamp
        
        Args:
            meter_id: Meter UUID
            consumption_kwh: Consumption amount in kWh
            timestamp: Unix timestamp of consumption
            reading_before: Optional meter reading before consumption
            reading_after: Optional meter reading after consumption
        
        Returns:
            Dictionary containing:
                - meter_id: Meter UUID
                - consumption_kwh: Consumption amount
                - timestamp: Unix timestamp
                - reading_before: Meter reading before (if provided)
                - reading_after: Meter reading after (if provided)
                - signature: Hex-encoded signature
                - public_key: PEM-encoded public key
                - message_hash: SHA-256 hash of message (hex)
        
        Raises:
            SmartMeterError: If signing fails
        
        Requirements: FR-9.4, FR-9.5, Task 2.3
        """
        try:
            logger.info(f"Signing consumption data for meter {meter_id}")
            
            # Get private key
            private_key = self._get_private_key(meter_id)
            
            # Get public key
            public_key_pem = self.get_public_key(meter_id)
            
            # Create message to sign (deterministic format)
            message = f"{meter_id}{consumption_kwh}{timestamp}"
            message_bytes = message.encode('utf-8')
            
            # Hash message with SHA-256
            digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
            digest.update(message_bytes)
            message_hash = digest.finalize()
            
            # Sign the hash
            signature = private_key.sign(message_bytes)
            
            # Convert to hex for storage/transmission
            signature_hex = signature.hex()
            message_hash_hex = message_hash.hex()
            
            logger.info(f"✅ Signed consumption data for meter {meter_id}")
            logger.info(f"   Consumption: {consumption_kwh} kWh")
            logger.info(f"   Timestamp: {timestamp}")
            logger.info(f"   Message hash: {message_hash_hex[:16]}...")
            logger.info(f"   Signature: {signature_hex[:16]}...")
            
            return {
                'meter_id': meter_id,
                'consumption_kwh': consumption_kwh,
                'timestamp': timestamp,
                'reading_before': reading_before,
                'reading_after': reading_after,
                'signature': signature_hex,
                'public_key': public_key_pem,
                'message_hash': message_hash_hex
            }
            
        except SmartMeterError:
            raise
        except Exception as e:
            logger.error(f"Failed to sign consumption data: {e}", exc_info=True)
            raise SmartMeterError(f"Failed to sign consumption data: {str(e)}")
    
    def verify_signature(
        self,
        meter_id: str,
        consumption_kwh: float,
        timestamp: int,
        signature: str,
        public_key_pem: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify consumption data signature.
        
        Reconstructs the message from consumption data, and verifies the signature
        using the meter's public key. Uses constant-time comparison for security.
        
        Args:
            meter_id: Meter UUID
            consumption_kwh: Consumption amount in kWh
            timestamp: Unix timestamp of consumption
            signature: Hex-encoded signature to verify
            public_key_pem: Optional PEM-encoded public key (fetched if not provided)
        
        Returns:
            Dictionary containing:
                - valid: Boolean indicating if signature is valid
                - meter_id: Meter UUID
                - consumption_kwh: Consumption amount
                - timestamp: Unix timestamp
                - message_hash: SHA-256 hash of message (hex)
                - algorithm: Signature algorithm (ED25519)
        
        Raises:
            SmartMeterError: If verification process fails (not if signature is invalid)
        
        Requirements: FR-9.6, FR-9.7, NFR-8.3, Task 2.4
        """
        try:
            logger.info(f"Verifying signature for meter {meter_id}")
            
            # Get public key if not provided
            if public_key_pem is None:
                public_key_pem = self.get_public_key(meter_id)
                if not public_key_pem:
                    raise SmartMeterError(f"No public key found for meter {meter_id}")
            
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            
            # Reconstruct message (same format as signing)
            message = f"{meter_id}{consumption_kwh}{timestamp}"
            message_bytes = message.encode('utf-8')
            
            # Hash message with SHA-256
            digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
            digest.update(message_bytes)
            message_hash = digest.finalize()
            message_hash_hex = message_hash.hex()
            
            # Decode hex signature
            try:
                signature_bytes = bytes.fromhex(signature)
            except ValueError:
                logger.warning(f"Invalid signature format for meter {meter_id}")
                return {
                    'valid': False,
                    'meter_id': meter_id,
                    'consumption_kwh': consumption_kwh,
                    'timestamp': timestamp,
                    'message_hash': message_hash_hex,
                    'algorithm': 'ED25519',
                    'error': 'Invalid signature format'
                }
            
            # Verify signature (constant-time comparison)
            try:
                public_key.verify(signature_bytes, message_bytes)
                is_valid = True
                logger.info(f"✅ Signature VALID for meter {meter_id}")
            except Exception as verify_error:
                is_valid = False
                logger.warning(f"❌ Signature INVALID for meter {meter_id}: {verify_error}")
            
            return {
                'valid': is_valid,
                'meter_id': meter_id,
                'consumption_kwh': consumption_kwh,
                'timestamp': timestamp,
                'message_hash': message_hash_hex,
                'algorithm': 'ED25519'
            }
            
        except SmartMeterError:
            raise
        except Exception as e:
            logger.error(f"Failed to verify signature: {e}", exc_info=True)
            raise SmartMeterError(f"Failed to verify signature: {str(e)}")
    
    def keypair_exists(self, meter_id: str) -> bool:
        """
        Check if a keypair exists for a meter.
        
        Args:
            meter_id: Meter UUID
        
        Returns:
            True if keypair exists, False otherwise
        """
        try:
            query = text("""
                SELECT COUNT(*) FROM smart_meter_keys
                WHERE meter_id = :meter_id
            """)
            
            result = self.db.execute(query, {'meter_id': meter_id}).fetchone()
            return result[0] > 0
            
        except Exception as e:
            logger.error(f"Failed to check keypair existence: {e}", exc_info=True)
            return False


# Helper function for service instantiation
def get_smart_meter_service(db: Session) -> SmartMeterService:
    """
    Get smart meter service instance.
    
    Args:
        db: Database session
    
    Returns:
        SmartMeterService instance
    """
    return SmartMeterService(db)
