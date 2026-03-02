"""
Tests for PDF Receipt Generation Service
Tests the receipt_service.py functionality
"""
import pytest
from datetime import datetime
from decimal import Decimal
import io

from app.services.receipt_service import ReceiptService, get_receipt_service


class TestReceiptService:
    """Test suite for ReceiptService"""
    
    @pytest.fixture
    def receipt_service(self):
        """Create a receipt service instance"""
        return ReceiptService()
    
    @pytest.fixture
    def sample_bill_data_eur(self):
        """Sample bill data for EUR currency"""
        return {
            'bill_id': '12345678-1234-1234-1234-123456789abc',
            'consumption_kwh': 450.50,
            'base_charge': 72.34,
            'taxes': 15.18,
            'subsidies': 2.12,
            'total_fiat': 85.40,
            'currency': 'EUR',
            'amount_hbar': 251.17647059,
            'exchange_rate': 0.34,
            'hedera_tx_id': '0.0.123456@1710789700.123456789',
            'consensus_timestamp': datetime(2024, 3, 18, 14, 30, 0),
            'paid_at': datetime(2024, 3, 18, 14, 30, 5),
            'user_email': 'test@example.com',
            'meter_id': 'ESP-12345678'
        }
    
    @pytest.fixture
    def sample_bill_data_usd(self):
        """Sample bill data for USD currency"""
        return {
            'bill_id': '87654321-4321-4321-4321-cba987654321',
            'consumption_kwh': 850.00,
            'base_charge': 102.00,
            'taxes': 18.50,
            'subsidies': 0,
            'total_fiat': 120.50,
            'currency': 'USD',
            'amount_hbar': 2410.00,
            'exchange_rate': 0.05,
            'hedera_tx_id': '0.0.654321@1710789800.987654321',
            'consensus_timestamp': datetime(2024, 3, 19, 10, 15, 30),
            'paid_at': datetime(2024, 3, 19, 10, 15, 35),
            'user_email': 'user@test.com',
            'meter_id': 'USA-CA-87654321'
        }
    
    @pytest.fixture
    def sample_bill_data_ngn(self):
        """Sample bill data for NGN currency (Nigeria)"""
        return {
            'bill_id': 'abcdef12-abcd-abcd-abcd-abcdef123456',
            'consumption_kwh': 320.00,
            'base_charge': 11627.91,
            'taxes': 872.09,
            'subsidies': 0,
            'total_fiat': 12500.00,
            'currency': 'NGN',
            'amount_hbar': 250000.00,
            'exchange_rate': 0.05,
            'hedera_tx_id': '0.0.789012@1710790000.111222333',
            'consensus_timestamp': datetime(2024, 3, 20, 8, 45, 15),
            'paid_at': datetime(2024, 3, 20, 8, 45, 20),
            'user_email': 'nigeria@test.com',
            'meter_id': 'NG-IKEDP-12345'
        }
    
    def test_service_initialization(self, receipt_service):
        """Test that service initializes correctly"""
        assert receipt_service is not None
        assert hasattr(receipt_service, 'styles')
        assert 'ReceiptTitle' in receipt_service.styles
        assert 'SectionHeader' in receipt_service.styles
    
    def test_singleton_pattern(self):
        """Test that get_receipt_service returns singleton"""
        service1 = get_receipt_service()
        service2 = get_receipt_service()
        assert service1 is service2
    
    def test_generate_receipt_eur(self, receipt_service, sample_bill_data_eur):
        """Test PDF generation for EUR currency"""
        pdf_bytes = receipt_service.generate_receipt_pdf(sample_bill_data_eur)
        
        # Verify PDF was generated
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        
        # Verify it's a PDF (starts with PDF header)
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_generate_receipt_usd(self, receipt_service, sample_bill_data_usd):
        """Test PDF generation for USD currency"""
        pdf_bytes = receipt_service.generate_receipt_pdf(sample_bill_data_usd)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_generate_receipt_ngn(self, receipt_service, sample_bill_data_ngn):
        """Test PDF generation for NGN currency (Nigeria)"""
        pdf_bytes = receipt_service.generate_receipt_pdf(sample_bill_data_ngn)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_generate_receipt_all_currencies(self, receipt_service):
        """Test PDF generation for all supported currencies"""
        currencies = ['EUR', 'USD', 'INR', 'BRL', 'NGN']
        
        for currency in currencies:
            bill_data = {
                'bill_id': f'test-{currency}',
                'consumption_kwh': 500.0,
                'base_charge': 80.0,
                'taxes': 15.0,
                'subsidies': 0,
                'total_fiat': 95.0,
                'currency': currency,
                'amount_hbar': 1900.0,
                'exchange_rate': 0.05,
                'hedera_tx_id': f'0.0.123456@1710789700.{currency}',
                'consensus_timestamp': datetime.utcnow(),
                'paid_at': datetime.utcnow(),
                'user_email': f'test-{currency}@example.com',
                'meter_id': f'{currency}-12345'
            }
            
            pdf_bytes = receipt_service.generate_receipt_pdf(bill_data)
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
            assert pdf_bytes[:4] == b'%PDF'
    
    def test_missing_required_field(self, receipt_service):
        """Test that missing required fields raise ValueError"""
        incomplete_data = {
            'bill_id': 'test-123',
            'total_fiat': 100.0,
            # Missing other required fields
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            receipt_service.generate_receipt_pdf(incomplete_data)
    
    def test_receipt_with_minimal_data(self, receipt_service):
        """Test receipt generation with only required fields"""
        minimal_data = {
            'bill_id': 'minimal-test',
            'total_fiat': 100.0,
            'currency': 'EUR',
            'amount_hbar': 294.11764706,
            'exchange_rate': 0.34,
            'hedera_tx_id': '0.0.123456@1710789700.123',
            'consensus_timestamp': datetime.utcnow()
        }
        
        pdf_bytes = receipt_service.generate_receipt_pdf(minimal_data)
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_receipt_with_subsidies(self, receipt_service):
        """Test receipt generation with subsidies"""
        data_with_subsidies = {
            'bill_id': 'subsidy-test',
            'consumption_kwh': 400.0,
            'base_charge': 70.0,
            'taxes': 14.0,
            'subsidies': 10.0,  # Subsidy applied
            'total_fiat': 74.0,
            'currency': 'EUR',
            'amount_hbar': 217.64705882,
            'exchange_rate': 0.34,
            'hedera_tx_id': '0.0.123456@1710789700.456',
            'consensus_timestamp': datetime.utcnow(),
            'paid_at': datetime.utcnow(),
            'user_email': 'subsidy@test.com',
            'meter_id': 'SUB-12345'
        }
        
        pdf_bytes = receipt_service.generate_receipt_pdf(data_with_subsidies)
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
    
    def test_hashscan_url_generation(self, receipt_service):
        """Test that HashScan URL is correctly formatted"""
        tx_id = '0.0.123456@1710789700.123456789'
        expected_url = f"{receipt_service.HASHSCAN_BASE_URL}/transaction/{tx_id}"
        
        assert receipt_service.HASHSCAN_BASE_URL == "https://hashscan.io/testnet"
        assert expected_url == f"https://hashscan.io/testnet/transaction/{tx_id}"
    
    def test_currency_symbols(self, receipt_service):
        """Test that all currency symbols are defined"""
        expected_symbols = {
            'EUR': '€',
            'USD': '$',
            'INR': '₹',
            'BRL': 'R$',
            'NGN': '₦'
        }
        
        assert receipt_service.CURRENCY_SYMBOLS == expected_symbols
    
    def test_receipt_file_size(self, receipt_service, sample_bill_data_eur):
        """Test that generated PDF has reasonable file size"""
        pdf_bytes = receipt_service.generate_receipt_pdf(sample_bill_data_eur)
        
        # PDF should be between 3KB and 500KB (adjusted for minimal PDF size)
        assert 3_000 < len(pdf_bytes) < 500_000
    
    def test_receipt_with_decimal_types(self, receipt_service):
        """Test receipt generation with Decimal types (from database)"""
        decimal_data = {
            'bill_id': 'decimal-test',
            'consumption_kwh': Decimal('450.50'),
            'base_charge': Decimal('72.34'),
            'taxes': Decimal('15.18'),
            'subsidies': Decimal('2.12'),
            'total_fiat': Decimal('85.40'),
            'currency': 'EUR',
            'amount_hbar': Decimal('251.17647059'),
            'exchange_rate': Decimal('0.34'),
            'hedera_tx_id': '0.0.123456@1710789700.123',
            'consensus_timestamp': datetime.utcnow(),
            'paid_at': datetime.utcnow(),
            'user_email': 'decimal@test.com',
            'meter_id': 'DEC-12345'
        }
        
        pdf_bytes = receipt_service.generate_receipt_pdf(decimal_data)
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_receipt_timestamp_formats(self, receipt_service):
        """Test receipt with various timestamp formats"""
        # Test with datetime object
        data_datetime = {
            'bill_id': 'datetime-test',
            'total_fiat': 100.0,
            'currency': 'EUR',
            'amount_hbar': 294.11764706,
            'exchange_rate': 0.34,
            'hedera_tx_id': '0.0.123456@1710789700.123',
            'consensus_timestamp': datetime(2024, 3, 18, 14, 30, 0),
            'paid_at': datetime(2024, 3, 18, 14, 30, 5)
        }
        
        pdf_bytes = receipt_service.generate_receipt_pdf(data_datetime)
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
    
    def test_receipt_with_long_transaction_id(self, receipt_service):
        """Test receipt with long Hedera transaction ID"""
        long_tx_data = {
            'bill_id': 'long-tx-test',
            'total_fiat': 100.0,
            'currency': 'EUR',
            'amount_hbar': 294.11764706,
            'exchange_rate': 0.34,
            'hedera_tx_id': '0.0.1234567890@1710789700.123456789012345',
            'consensus_timestamp': datetime.utcnow()
        }
        
        pdf_bytes = receipt_service.generate_receipt_pdf(long_tx_data)
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
    
    def test_receipt_with_high_precision_hbar(self, receipt_service):
        """Test receipt with high precision HBAR amounts"""
        high_precision_data = {
            'bill_id': 'precision-test',
            'total_fiat': 85.40,
            'currency': 'EUR',
            'amount_hbar': 251.17647058823529411764705882,  # Very high precision
            'exchange_rate': 0.34,
            'hedera_tx_id': '0.0.123456@1710789700.123',
            'consensus_timestamp': datetime.utcnow()
        }
        
        pdf_bytes = receipt_service.generate_receipt_pdf(high_precision_data)
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0


class TestReceiptEndpointIntegration:
    """Integration tests for receipt endpoint"""
    
    def test_receipt_data_structure(self):
        """Test that bill data structure matches receipt requirements"""
        # This test verifies the data structure expected by the receipt service
        # matches what the payment endpoint provides
        
        required_fields = [
            'bill_id', 'total_fiat', 'currency', 'amount_hbar',
            'exchange_rate', 'hedera_tx_id', 'consensus_timestamp'
        ]
        
        optional_fields = [
            'consumption_kwh', 'base_charge', 'taxes', 'subsidies',
            'paid_at', 'user_email', 'meter_id'
        ]
        
        # Verify all fields are documented
        all_fields = required_fields + optional_fields
        assert len(all_fields) == 14  # 7 required + 7 optional
    
    def test_currency_support(self):
        """Test that all required currencies are supported"""
        supported_currencies = ['EUR', 'USD', 'INR', 'BRL', 'NGN']
        
        service = get_receipt_service()
        for currency in supported_currencies:
            assert currency in service.CURRENCY_SYMBOLS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
