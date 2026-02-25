"""
Unit Tests for Meter ID Validation

Tests the meter ID validation logic for all 5 regions.

Requirements:
    - FR-2.2: System shall validate meter ID format per region
    - US-2: Meter registration with validation
"""
import pytest
from app.utils.meter_validation import (
    MeterIDValidator,
    validate_meter_id,
    normalize_meter_id
)


class TestSpainMeterValidation:
    """Test meter ID validation for Spain (ES)"""
    
    def test_valid_spain_meter_ids(self):
        """Test valid Spain meter ID formats"""
        valid_ids = [
            'ES-12345678',
            'ESP-123456789012',
            'MAD-12345678',
            'BCN-123456789',
            'ES12345678',  # Without hyphen
            'ESP123456789012'
        ]
        
        for meter_id in valid_ids:
            is_valid, error = validate_meter_id(meter_id, 'ES')
            assert is_valid, f"Expected {meter_id} to be valid, but got error: {error}"
            assert error == ""
    
    def test_invalid_spain_meter_ids(self):
        """Test invalid Spain meter ID formats"""
        invalid_ids = [
            '12345678',  # No prefix
            'E-12345678',  # Prefix too short
            'ESPA-12345678',  # Prefix too long
            'ES-1234567',  # Too few digits
            'ES-12345678901234',  # Too many digits
            'ES-ABC12345',  # Letters in number part
            '',  # Empty
            'ES-',  # No digits
        ]
        
        for meter_id in invalid_ids:
            is_valid, error = validate_meter_id(meter_id, 'ES')
            assert not is_valid, f"Expected {meter_id} to be invalid"
            assert error != ""
    
    def test_spain_meter_id_normalization(self):
        """Test Spain meter ID normalization"""
        assert normalize_meter_id('es-12345678', 'ES') == 'ES-12345678'
        assert normalize_meter_id('ES12345678', 'ES') == 'ES-12345678'
        assert normalize_meter_id(' ESP-123456789 ', 'ES') == 'ESP-123456789'
        assert normalize_meter_id('mad12345678', 'ES') == 'MAD-12345678'


class TestUSAMeterValidation:
    """Test meter ID validation for USA (US)"""
    
    def test_valid_usa_meter_ids(self):
        """Test valid USA meter ID formats"""
        valid_ids = [
            'PGE12345678',
            '123456789012345',
            'SCE1234567890',
            'SDGE12345',
            'A1B2C3D4E5',
            '12345678'
        ]
        
        for meter_id in valid_ids:
            is_valid, error = validate_meter_id(meter_id, 'US')
            assert is_valid, f"Expected {meter_id} to be valid, but got error: {error}"
            assert error == ""
    
    def test_invalid_usa_meter_ids(self):
        """Test invalid USA meter ID formats"""
        invalid_ids = [
            '1234567',  # Too short
            '1234567890123456',  # Too long
            'PGE-12345678',  # Contains hyphen
            'PGE 12345678',  # Contains space
            'PGE@12345',  # Special characters
            '',  # Empty
        ]
        
        for meter_id in invalid_ids:
            is_valid, error = validate_meter_id(meter_id, 'US')
            assert not is_valid, f"Expected {meter_id} to be invalid"
            assert error != ""
    
    def test_usa_meter_id_normalization(self):
        """Test USA meter ID normalization"""
        assert normalize_meter_id('pge12345678', 'US') == 'PGE12345678'
        assert normalize_meter_id(' 123456789012345 ', 'US') == '123456789012345'
        assert normalize_meter_id('sce1234567890', 'US') == 'SCE1234567890'


class TestIndiaMeterValidation:
    """Test meter ID validation for India (IN)"""
    
    def test_valid_india_meter_ids(self):
        """Test valid India meter ID formats"""
        valid_ids = [
            '1234567890',  # 10 digits
            '123456789012345',  # 15 digits
            '12345678901',  # 11 digits
            '1234567890123'  # 13 digits
        ]
        
        for meter_id in valid_ids:
            is_valid, error = validate_meter_id(meter_id, 'IN')
            assert is_valid, f"Expected {meter_id} to be valid, but got error: {error}"
            assert error == ""
    
    def test_invalid_india_meter_ids(self):
        """Test invalid India meter ID formats"""
        invalid_ids = [
            '123456789',  # Too short (9 digits)
            '1234567890123456',  # Too long (16 digits)
            'ABC1234567890',  # Contains letters
            '12345-67890',  # Contains hyphen
            '',  # Empty
        ]
        
        for meter_id in invalid_ids:
            is_valid, error = validate_meter_id(meter_id, 'IN')
            assert not is_valid, f"Expected {meter_id} to be invalid"
            assert error != ""
    
    def test_india_meter_id_normalization(self):
        """Test India meter ID normalization"""
        assert normalize_meter_id(' 1234567890 ', 'IN') == '1234567890'
        assert normalize_meter_id('123456789012345', 'IN') == '123456789012345'


class TestBrazilMeterValidation:
    """Test meter ID validation for Brazil (BR)"""
    
    def test_valid_brazil_meter_ids(self):
        """Test valid Brazil meter ID formats"""
        valid_ids = [
            '1234567890',  # 10 digits
            '12345678901234',  # 14 digits
            '123456789012',  # 12 digits
            '12345678901'  # 11 digits
        ]
        
        for meter_id in valid_ids:
            is_valid, error = validate_meter_id(meter_id, 'BR')
            assert is_valid, f"Expected {meter_id} to be valid, but got error: {error}"
            assert error == ""
    
    def test_invalid_brazil_meter_ids(self):
        """Test invalid Brazil meter ID formats"""
        invalid_ids = [
            '123456789',  # Too short (9 digits)
            '123456789012345',  # Too long (15 digits)
            'BR1234567890',  # Contains letters
            '12345-67890',  # Contains hyphen
            '',  # Empty
        ]
        
        for meter_id in invalid_ids:
            is_valid, error = validate_meter_id(meter_id, 'BR')
            assert not is_valid, f"Expected {meter_id} to be invalid"
            assert error != ""
    
    def test_brazil_meter_id_normalization(self):
        """Test Brazil meter ID normalization"""
        assert normalize_meter_id(' 1234567890 ', 'BR') == '1234567890'
        assert normalize_meter_id('12345678901234', 'BR') == '12345678901234'


class TestNigeriaMeterValidation:
    """Test meter ID validation for Nigeria (NG)"""
    
    def test_valid_nigeria_meter_ids(self):
        """Test valid Nigeria meter ID formats"""
        valid_ids = [
            '12345678901',  # 11 digits
            '1234567890123',  # 13 digits
            '123456789012'  # 12 digits
        ]
        
        for meter_id in valid_ids:
            is_valid, error = validate_meter_id(meter_id, 'NG')
            assert is_valid, f"Expected {meter_id} to be valid, but got error: {error}"
            assert error == ""
    
    def test_invalid_nigeria_meter_ids(self):
        """Test invalid Nigeria meter ID formats"""
        invalid_ids = [
            '1234567890',  # Too short (10 digits)
            '12345678901234',  # Too long (14 digits)
            'NG12345678901',  # Contains letters
            '12345-678901',  # Contains hyphen
            '',  # Empty
        ]
        
        for meter_id in invalid_ids:
            is_valid, error = validate_meter_id(meter_id, 'NG')
            assert not is_valid, f"Expected {meter_id} to be invalid"
            assert error != ""
    
    def test_nigeria_meter_id_normalization(self):
        """Test Nigeria meter ID normalization"""
        assert normalize_meter_id(' 12345678901 ', 'NG') == '12345678901'
        assert normalize_meter_id('1234567890123', 'NG') == '1234567890123'


class TestMeterValidatorUtility:
    """Test MeterIDValidator utility class methods"""
    
    def test_unsupported_country_code(self):
        """Test validation with unsupported country code"""
        is_valid, error = validate_meter_id('12345678', 'FR')
        assert not is_valid
        assert 'Unsupported country code' in error
    
    def test_empty_meter_id(self):
        """Test validation with empty meter ID"""
        is_valid, error = validate_meter_id('', 'ES')
        assert not is_valid
        assert 'non-empty string' in error
    
    def test_none_meter_id(self):
        """Test validation with None meter ID"""
        is_valid, error = validate_meter_id(None, 'ES')
        assert not is_valid
        assert 'non-empty string' in error
    
    def test_get_format_info(self):
        """Test getting format information for a country"""
        info = MeterIDValidator.get_format_info('ES')
        assert info is not None
        assert 'pattern' in info
        assert 'description' in info
        assert 'examples' in info
        assert 'min_length' in info
        assert 'max_length' in info
    
    def test_get_format_info_unsupported(self):
        """Test getting format info for unsupported country"""
        info = MeterIDValidator.get_format_info('FR')
        assert info is None
    
    def test_all_supported_countries(self):
        """Test that all 5 countries are supported"""
        supported_countries = ['ES', 'US', 'IN', 'BR', 'NG']
        for country in supported_countries:
            info = MeterIDValidator.get_format_info(country)
            assert info is not None, f"Country {country} should be supported"


class TestMeterValidationErrorMessages:
    """Test that error messages are helpful and descriptive"""
    
    def test_error_message_includes_format_description(self):
        """Test that error messages include format description"""
        is_valid, error = validate_meter_id('123', 'ES')
        assert not is_valid
        assert 'Spain' in error
        assert 'letter prefix' in error.lower() or 'digit' in error.lower()
    
    def test_error_message_includes_examples(self):
        """Test that error messages include examples"""
        is_valid, error = validate_meter_id('ABC', 'ES')
        assert not is_valid
        assert 'ES-' in error or 'ESP-' in error
    
    def test_length_error_messages(self):
        """Test that length errors provide clear feedback"""
        # Too short
        is_valid, error = validate_meter_id('ES-123', 'ES')
        assert not is_valid
        assert 'short' in error.lower() or 'at least' in error.lower()
        
        # Too long
        is_valid, error = validate_meter_id('ES-' + '1' * 20, 'ES')
        assert not is_valid
        assert 'long' in error.lower() or 'at most' in error.lower()


class TestMeterValidationIntegration:
    """Integration tests for meter validation"""
    
    def test_validate_and_normalize_workflow(self):
        """Test typical workflow: normalize then validate"""
        # Spain
        meter_id = ' es-12345678 '
        normalized = normalize_meter_id(meter_id, 'ES')
        is_valid, error = validate_meter_id(normalized, 'ES')
        assert is_valid
        assert normalized == 'ES-12345678'
        
        # USA
        meter_id = ' pge12345678 '
        normalized = normalize_meter_id(meter_id, 'US')
        is_valid, error = validate_meter_id(normalized, 'US')
        assert is_valid
        assert normalized == 'PGE12345678'
    
    def test_cross_country_validation(self):
        """Test that meter IDs are validated against correct country"""
        # Spain meter ID should not be valid for USA
        spain_meter = 'ES-12345678'
        is_valid, _ = validate_meter_id(spain_meter, 'US')
        assert not is_valid
        
        # USA meter ID should not be valid for India
        usa_meter = 'PGE12345678'
        is_valid, _ = validate_meter_id(usa_meter, 'IN')
        assert not is_valid
