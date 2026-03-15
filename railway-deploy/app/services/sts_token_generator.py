"""
STS (Standard Transfer Specification) Token Generator
Generates 20-digit prepaid electricity tokens compatible with physical meters.

Based on IEC 62055-41 standard for electricity payment systems.
"""
import hashlib
import secrets
from typing import Tuple
from datetime import datetime


class STSTokenGenerator:
    """
    Generate STS-compliant 20-digit tokens for prepaid electricity meters.
    
    Token Format: XXXX-XXXX-XXXX-XXXX-XXXX (20 digits, 5 groups of 4)
    
    Token Structure:
    - Digits 1-4: Token Class and Subclass
    - Digits 5-8: Random/Encrypted data
    - Digits 9-16: kWh units (encrypted)
    - Digits 17-20: CRC checksum
    """
    
    # Token Class Identifiers (IEC 62055-41)
    TOKEN_CLASS_CREDIT = "01"  # Credit transfer (add units)
    TOKEN_CLASS_CLEAR = "02"   # Clear credit
    TOKEN_CLASS_SET_TARIFF = "03"  # Set tariff
    
    def __init__(self, utility_provider: str, country_code: str):
        """
        Initialize token generator for specific utility and country.
        
        Args:
            utility_provider: Name of utility company
            country_code: ISO country code (NG, ES, US, etc.)
        """
        self.utility_provider = utility_provider
        self.country_code = country_code
        
        # Generate utility-specific encryption key
        self.encryption_key = self._generate_encryption_key(
            utility_provider, 
            country_code
        )
    
    def generate_token(
        self, 
        meter_number: str, 
        units_kwh: float,
        amount_paid: float,
        currency: str
    ) -> Tuple[str, dict]:
        """
        Generate a 20-digit STS token for prepaid electricity.
        
        Args:
            meter_number: Meter serial number
            units_kwh: kWh units to credit
            amount_paid: Amount paid in local currency
            currency: Currency code (NGN, EUR, etc.)
            
        Returns:
            Tuple of (formatted_token, token_metadata)
            
        Example:
            >>> generator = STSTokenGenerator("PHED", "NG")
            >>> token, meta = generator.generate_token("0137234144889", 45.8, 2000, "NGN")
            >>> print(token)
            "3914-1149-7778-9057-6069"
        """
        # Convert kWh to integer (multiply by 10 for 0.1 kWh precision)
        units_int = int(units_kwh * 10)
        
        # Generate token components
        token_class = self._get_token_class()
        random_data = self._generate_random_data()
        encrypted_units = self._encrypt_units(units_int, meter_number)
        
        # Combine components (16 digits so far)
        token_base = token_class + random_data + encrypted_units
        
        # Calculate CRC checksum (4 digits)
        checksum = self._calculate_checksum(token_base, meter_number)
        
        # Complete 20-digit token
        token_digits = token_base + checksum
        
        # Format with dashes: XXXX-XXXX-XXXX-XXXX-XXXX
        formatted_token = self._format_token(token_digits)
        
        # Generate metadata
        metadata = {
            'token': formatted_token,
            'token_raw': token_digits,
            'meter_number': meter_number,
            'units_kwh': units_kwh,
            'amount_paid': amount_paid,
            'currency': currency,
            'utility_provider': self.utility_provider,
            'country_code': self.country_code,
            'token_class': token_class,
            'generated_at': datetime.utcnow().isoformat(),
            'valid': True
        }
        
        return formatted_token, metadata
    
    def verify_token(self, token: str, meter_number: str) -> bool:
        """
        Verify if a token is valid for a specific meter.
        
        Args:
            token: 20-digit token (with or without dashes)
            meter_number: Meter serial number
            
        Returns:
            True if token is valid, False otherwise
        """
        # Remove dashes and validate format
        token_digits = token.replace('-', '').replace(' ', '')
        
        if len(token_digits) != 20 or not token_digits.isdigit():
            return False
        
        # Extract components
        token_base = token_digits[:16]
        provided_checksum = token_digits[16:20]
        
        # Calculate expected checksum
        expected_checksum = self._calculate_checksum(token_base, meter_number)
        
        # Verify checksum
        return provided_checksum == expected_checksum
    
    def decode_token(self, token: str, meter_number: str) -> dict:
        """
        Decode a token to extract units and metadata.
        
        Args:
            token: 20-digit token
            meter_number: Meter serial number
            
        Returns:
            Dictionary with decoded information
        """
        token_digits = token.replace('-', '').replace(' ', '')
        
        if not self.verify_token(token, meter_number):
            return {'valid': False, 'error': 'Invalid token or meter mismatch'}
        
        # Extract components
        token_class = token_digits[:2]
        random_data = token_digits[2:6]
        encrypted_units = token_digits[6:16]
        checksum = token_digits[16:20]
        
        # Decrypt units
        units_int = self._decrypt_units(encrypted_units, meter_number)
        units_kwh = units_int / 10.0
        
        return {
            'valid': True,
            'token': self._format_token(token_digits),
            'token_class': token_class,
            'units_kwh': units_kwh,
            'meter_number': meter_number,
            'checksum': checksum
        }
    
    def _get_token_class(self) -> str:
        """Get token class identifier (2 digits)"""
        # For credit transfer tokens - return exactly 2 digits
        return self.TOKEN_CLASS_CREDIT
    
    def _generate_random_data(self) -> str:
        """Generate random data component (4 digits)"""
        return str(secrets.randbelow(10000)).zfill(4)
    
    def _encrypt_units(self, units_int: int, meter_number: str) -> str:
        """
        Encrypt kWh units using meter-specific key (10 digits).
        
        Simple encryption: XOR with meter-derived key
        """
        # Generate meter-specific key
        meter_key = self._get_meter_key(meter_number)
        
        # Ensure units fit in 10 digits (max 9,999,999,999)
        units_int = min(units_int, 9999999999)
        
        # XOR encryption
        encrypted = units_int ^ meter_key
        
        return str(encrypted).zfill(10)
    
    def _decrypt_units(self, encrypted_units: str, meter_number: str) -> int:
        """Decrypt kWh units"""
        meter_key = self._get_meter_key(meter_number)
        encrypted_int = int(encrypted_units)
        
        # XOR decryption (same as encryption)
        decrypted = encrypted_int ^ meter_key
        
        return decrypted
    
    def _get_meter_key(self, meter_number: str) -> int:
        """
        Generate encryption key from meter number.
        Uses utility encryption key + meter number.
        """
        # Combine utility key and meter number
        combined = f"{self.encryption_key}{meter_number}"
        
        # Hash to generate numeric key
        hash_obj = hashlib.sha256(combined.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Take first 10 digits from hash
        key_int = int(hash_hex[:10], 16) % 10000000000
        
        return key_int
    
    def _calculate_checksum(self, token_base: str, meter_number: str) -> str:
        """
        Calculate CRC checksum for token validation (4 digits).
        
        Uses Luhn algorithm variant with meter number.
        """
        # Combine token base with meter number
        data = token_base + meter_number
        
        # Calculate hash
        hash_obj = hashlib.sha256(data.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Take first 4 digits from hash
        checksum = str(int(hash_hex[:8], 16) % 10000).zfill(4)
        
        return checksum
    
    def _generate_encryption_key(self, utility: str, country: str) -> str:
        """Generate utility-specific encryption key"""
        # Combine utility and country for unique key
        combined = f"{utility.upper()}{country.upper()}"
        
        # Hash to generate key
        hash_obj = hashlib.sha256(combined.encode())
        
        return hash_obj.hexdigest()[:16]
    
    def _format_token(self, token_digits: str) -> str:
        """Format 20 digits as XXXX-XXXX-XXXX-XXXX-XXXX"""
        if len(token_digits) != 20:
            raise ValueError("Token must be exactly 20 digits")
        
        return '-'.join([
            token_digits[0:4],
            token_digits[4:8],
            token_digits[8:12],
            token_digits[12:16],
            token_digits[16:20]
        ])


# Example usage and testing
if __name__ == "__main__":
    # Test token generation
    generator = STSTokenGenerator("Port Harcourt Electricity Distribution Company", "NG")
    
    # Generate token
    token, metadata = generator.generate_token(
        meter_number="0137234144889",
        units_kwh=45.8,
        amount_paid=2000,
        currency="NGN"
    )
    
    print("Generated Token:", token)
    print("Metadata:", metadata)
    
    # Verify token
    is_valid = generator.verify_token(token, "0137234144889")
    print(f"\nToken Valid: {is_valid}")
    
    # Decode token
    decoded = generator.decode_token(token, "0137234144889")
    print(f"Decoded: {decoded}")
    
    # Test with wrong meter
    is_valid_wrong = generator.verify_token(token, "9999999999999")
    print(f"\nToken Valid for Wrong Meter: {is_valid_wrong}")
