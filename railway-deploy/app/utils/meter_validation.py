"""
Meter ID Validation Utilities

This module provides meter ID format validation for different regions.
Each region has specific meter ID formats that must be validated before
meter registration.

Requirements:
    - FR-2.2: System shall validate meter ID format per region
    - US-2: Meter registration with validation
"""
import re
from typing import Dict, Tuple


class MeterIDValidator:
    """
    Validates meter IDs based on regional formats
    
    Regional Formats:
    - Spain (ES): 2-3 letter prefix + 8-12 digits (e.g., ES-12345678, ESP-123456789012)
    - USA (US): 8-15 alphanumeric characters (e.g., PGE12345678, 123456789012345)
    - India (IN): 10-15 digits (e.g., 1234567890, 123456789012345)
    - Brazil (BR): 10-14 digits (e.g., 1234567890, 12345678901234)
    - Nigeria (NG): 11-13 digits (e.g., 12345678901, 1234567890123)
    """
    
    # Regional patterns
    PATTERNS: Dict[str, Dict[str, any]] = {
        'ES': {
            'pattern': r'^[A-Z]{2,3}-?\d{8,12}$',
            'description': '2-3 letter prefix + 8-12 digits (e.g., ES-12345678, ESP-123456789012)',
            'examples': ['ES-12345678', 'ESP-123456789012', 'MAD12345678'],
            'min_length': 10,
            'max_length': 16
        },
        'US': {
            'pattern': r'^[A-Z0-9]{8,15}$',
            'description': '8-15 alphanumeric characters (e.g., PGE12345678, 123456789012345)',
            'examples': ['PGE12345678', '123456789012345', 'SCE1234567890'],
            'min_length': 8,
            'max_length': 15
        },
        'IN': {
            'pattern': r'^\d{10,15}$',
            'description': '10-15 digits (e.g., 1234567890, 123456789012345)',
            'examples': ['1234567890', '123456789012345', '12345678901'],
            'min_length': 10,
            'max_length': 15
        },
        'BR': {
            'pattern': r'^\d{10,14}$',
            'description': '10-14 digits (e.g., 1234567890, 12345678901234)',
            'examples': ['1234567890', '12345678901234', '123456789012'],
            'min_length': 10,
            'max_length': 14
        },
        'NG': {
            'pattern': r'^\d{11,13}$',
            'description': '11-13 digits (e.g., 12345678901, 1234567890123)',
            'examples': ['12345678901', '1234567890123', '123456789012'],
            'min_length': 11,
            'max_length': 13
        }
    }
    
    @classmethod
    def validate(cls, meter_id: str, country_code: str) -> Tuple[bool, str]:
        """
        Validate meter ID format for a specific country
        
        Args:
            meter_id: The meter ID to validate
            country_code: ISO 3166-1 alpha-2 country code (ES, US, IN, BR, NG)
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if meter ID is valid, False otherwise
            - error_message: Empty string if valid, error description if invalid
            
        Examples:
            >>> MeterIDValidator.validate('ES-12345678', 'ES')
            (True, '')
            
            >>> MeterIDValidator.validate('123', 'ES')
            (False, 'Invalid meter ID format for Spain...')
        """
        # Check if country code is supported
        if country_code not in cls.PATTERNS:
            return False, f"Unsupported country code: {country_code}"
        
        # Get pattern for country
        pattern_info = cls.PATTERNS[country_code]
        pattern = pattern_info['pattern']
        
        # Basic validation
        if not meter_id or not isinstance(meter_id, str):
            return False, "Meter ID must be a non-empty string"
        
        # Remove whitespace
        meter_id = meter_id.strip()
        
        # Check length
        if len(meter_id) < pattern_info['min_length']:
            return False, (
                f"Meter ID too short for {cls._get_country_name(country_code)}. "
                f"Expected at least {pattern_info['min_length']} characters. "
                f"Format: {pattern_info['description']}"
            )
        
        if len(meter_id) > pattern_info['max_length']:
            return False, (
                f"Meter ID too long for {cls._get_country_name(country_code)}. "
                f"Expected at most {pattern_info['max_length']} characters. "
                f"Format: {pattern_info['description']}"
            )
        
        # Check pattern
        if not re.match(pattern, meter_id, re.IGNORECASE):
            return False, (
                f"Invalid meter ID format for {cls._get_country_name(country_code)}. "
                f"Expected format: {pattern_info['description']}. "
                f"Examples: {', '.join(pattern_info['examples'])}"
            )
        
        return True, ""
    
    @classmethod
    def normalize(cls, meter_id: str, country_code: str) -> str:
        """
        Normalize meter ID to standard format
        
        - Removes whitespace
        - Converts to uppercase (for alphanumeric IDs)
        - Standardizes separators
        
        Args:
            meter_id: The meter ID to normalize
            country_code: ISO 3166-1 alpha-2 country code
            
        Returns:
            Normalized meter ID
            
        Examples:
            >>> MeterIDValidator.normalize('es-12345678', 'ES')
            'ES-12345678'
            
            >>> MeterIDValidator.normalize(' pge 12345678 ', 'US')
            'PGE12345678'
        """
        if not meter_id:
            return meter_id
        
        # Remove whitespace
        meter_id = meter_id.strip()
        
        # Convert to uppercase for alphanumeric IDs
        if country_code in ['ES', 'US']:
            meter_id = meter_id.upper()
        
        # Standardize Spain format (ensure hyphen)
        if country_code == 'ES':
            # If it has letters at the start but no hyphen, add one
            match = re.match(r'^([A-Z]{2,3})(\d{8,12})$', meter_id, re.IGNORECASE)
            if match:
                meter_id = f"{match.group(1)}-{match.group(2)}"
        
        return meter_id
    
    @classmethod
    def get_format_info(cls, country_code: str) -> Dict[str, any]:
        """
        Get format information for a country
        
        Args:
            country_code: ISO 3166-1 alpha-2 country code
            
        Returns:
            Dictionary with format information or None if country not supported
        """
        return cls.PATTERNS.get(country_code)
    
    @classmethod
    def _get_country_name(cls, country_code: str) -> str:
        """Get full country name from code"""
        country_names = {
            'ES': 'Spain',
            'US': 'USA',
            'IN': 'India',
            'BR': 'Brazil',
            'NG': 'Nigeria'
        }
        return country_names.get(country_code, country_code)


def validate_meter_id(meter_id: str, country_code: str) -> Tuple[bool, str]:
    """
    Convenience function for meter ID validation
    
    Args:
        meter_id: The meter ID to validate
        country_code: ISO 3166-1 alpha-2 country code
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    return MeterIDValidator.validate(meter_id, country_code)


def normalize_meter_id(meter_id: str, country_code: str) -> str:
    """
    Convenience function for meter ID normalization
    
    Args:
        meter_id: The meter ID to normalize
        country_code: ISO 3166-1 alpha-2 country code
        
    Returns:
        Normalized meter ID
    """
    return MeterIDValidator.normalize(meter_id, country_code)
