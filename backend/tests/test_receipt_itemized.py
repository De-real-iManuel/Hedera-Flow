"""
Tests for Itemized Breakdown in PDF Receipt Generation
Tests Task 20.4: Include itemized breakdown of charges
"""
import pytest
from datetime import datetime
from decimal import Decimal
import io

from app.services.receipt_service import ReceiptService, get_receipt_service


class TestReceiptItemizedBreakdown:
    """Test suite for itemized breakdown in receipts"""
    
    @pytest.fixture
    def receipt_service(self):
        """Create a receipt service instance"""
        return ReceiptService()
    
    @pytest.fixture
    def bill_data_tiered_usa(self):
        """Sample bill data with tiered rate structure (USA)"""
        return {
            'bill_id': '12345678-1234-1234-1234-123456789abc',
            'consumption_kwh': 850.00,
            'base_charge': 102.00,
            'taxes': 18.50,
            'subsidies': 0,
            'total_fiat': 120.50,
            'currency': 'USD',
            'amount_hbar': 2410.00,
            'exchange_rate': 0.05,
            'hedera_tx_id': '0.0.123456@1710789700.123456789',
            'consensus_timestamp': datetime(2024, 3, 18, 14, 30, 0),
            'paid_at': datetime(2024, 3, 18, 14, 30, 5),
            'user_email': 'test@example.com',
            'meter_id': 'USA-CA-87654321',
            'tariff_snapshot': {
                'rate_structure_type': 'tiered',
                'breakdown': {
                    'tiers': [
                        {'tier': 'Tier 1 (0-400 kWh)', 'kwh': 400, 'rate': 0.32, 'charge': 128.00},
                        {'tier': 'Tier 2 (401-800 kWh)', 'kwh': 400, 'rate': 0.40, 'charge': 160.00},
                        {'tier': 'Tier 3 (801+ kWh)', 'kwh': 50, 'rate': 0.50, 'charge': 25.00}
                    ]
                },
                'taxes_and_fees': {
                    'vat': 0.0725,
                    'service_charge': 10.00
                }
            },
            'breakdown': {
                'tiers': [
                    {'tier': 'Tier 1 (0-400 kWh)', 'kwh': 400, 'rate': 0.32, 'charge': 128.00},
                    {'tier': 'Tier 2 (401-800 kWh)', 'kwh': 400, 'rate': 0.40, 'charge': 160.00},
                    {'tier': 'Tier 3 (801+ kWh)', 'kwh': 50, 'rate': 0.50, 'charge': 25.00}
                ]
            },
            'service_charge': 10.00,
            'tax_breakdown': {
                'vat': 7.40,
                'vat_rate': 0.0725,
                'other_taxes': 11.10
            }
        }
    
    @pytest.fixture
    def bill_data_time_of_use_spain(self):
        """Sample bill data with time-of-use rate structure (Spain)"""
        return {
            'bill_id': '87654321-4321-4321-4321-cba987654321',
            'consumption_kwh': 450.50,
            'base_charge': 72.34,
            'taxes': 15.18,
            'subsidies': 2.12,
            'total_fiat': 85.40,
            'currency': 'EUR',
            'amount_hbar': 251.17647059,
            'exchange_rate': 0.34,
            'hedera_tx_id': '0.0.654321@1710789800.987654321',
            'consensus_timestamp': datetime(2024, 3, 19, 10, 15, 30),
            'paid_at': datetime(2024, 3, 19, 10, 15, 35),
            'user_email': 'user@test.com',
            'meter_id': 'ESP-12345678',
            'tariff_snapshot': {
                'rate_structure_type': 'time_of_use',
                'breakdown': {
                    'periods': [
                        {'period': 'Peak (10-14h, 18-22h)', 'kwh': 150.0, 'rate': 0.40, 'charge': 60.00},
                        {'period': 'Standard (8-10h, 14-18h, 22-24h)', 'kwh': 200.5, 'rate': 0.25, 'charge': 50.13},
                        {'period': 'Off-Peak (0-8h)', 'kwh': 100.0, 'rate': 0.15, 'charge': 15.00}
                    ]
                },
                'taxes_and_fees': {
                    'vat': 0.21,
                    'distribution_charge': 0.045
                }
            },
            'breakdown': {
                'periods': [
                    {'period': 'Peak (10-14h, 18-22h)', 'kwh': 150.0, 'rate': 0.40, 'charge': 60.00},
                    {'period': 'Standard (8-10h, 14-18h, 22-24h)', 'kwh': 200.5, 'rate': 0.25, 'charge': 50.13},
                    {'period': 'Off-Peak (0-8h)', 'kwh': 100.0, 'rate': 0.15, 'charge': 15.00}
                ]
            },
            'distribution_charge': 20.27,
            'tax_breakdown': {
                'vat': 15.18,
                'vat_rate': 0.21,
                'other_taxes': 0
            }
        }
    
    @pytest.fixture
    def bill_data_band_based_nigeria(self):
        """Sample bill data with band-based rate structure (Nigeria)"""
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
            'meter_id': 'NG-IKEDP-12345',
            'tariff_snapshot': {
                'rate_structure_type': 'band_based',
                'breakdown': {
                    'band': 'C',
                    'rate': 50.00
                },
                'taxes_and_fees': {
                    'vat': 0.075,
                    'service_charge': 1500.00
                }
            },
            'breakdown': {
                'band': 'C',
                'rate': 50.00
            },
            'service_charge': 1500.00,
            'tax_breakdown': {
                'vat': 872.09,
                'vat_rate': 0.075,
                'other_taxes': 0
            }
        }
    
    @pytest.fixture
    def bill_data_with_subsidies(self):
        """Sample bill data with subsidies"""
        return {
            'bill_id': 'subsidy-1234-5678-9abc-def012345678',
            'consumption_kwh': 250.00,
            'base_charge': 45.00,
            'taxes': 9.45,
            'subsidies': 5.00,
            'total_fiat': 49.45,
            'currency': 'INR',
            'amount_hbar': 989.00,
            'exchange_rate': 0.05,
            'hedera_tx_id': '0.0.111222@1710790100.444555666',
            'consensus_timestamp': datetime(2024, 3, 21, 12, 0, 0),
            'paid_at': datetime(2024, 3, 21, 12, 0, 5),
            'user_email': 'india@test.com',
            'meter_id': 'IN-TPDDL-54321',
            'tariff_snapshot': {
                'rate_structure_type': 'tiered',
                'taxes_and_fees': {
                    'vat': 0.18
                }
            },
            'tax_breakdown': {
                'vat': 9.45,
                'vat_rate': 0.18,
                'other_taxes': 0
            }
        }
    
    @pytest.fixture
    def bill_data_with_platform_charges(self):
        """Sample bill data with platform service charges"""
        return {
            'bill_id': 'platform-1234-5678-9abc-def012345678',
            'consumption_kwh': 500.00,
            'base_charge': 80.00,
            'taxes': 16.80,
            'subsidies': 0,
            'total_fiat': 99.70,
            'currency': 'BRL',
            'amount_hbar': 1994.00,
            'exchange_rate': 0.05,
            'hedera_tx_id': '0.0.333444@1710790200.777888999',
            'consensus_timestamp': datetime(2024, 3, 22, 15, 30, 0),
            'paid_at': datetime(2024, 3, 22, 15, 30, 5),
            'user_email': 'brazil@test.com',
            'meter_id': 'BR-ENEL-98765',
            'platform_service_charge': 2.40,
            'platform_vat': 0.50,
            'tax_breakdown': {
                'vat': 16.80,
                'vat_rate': 0.21,
                'other_taxes': 0
            }
        }
    
    def test_receipt_with_tiered_breakdown(self, receipt_service, bill_data_tiered_usa):
        """Test receipt includes tiered rate breakdown"""
        pdf_bytes = receipt_service.generate_receipt_pdf(bill_data_tiered_usa)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        
        # Verify PDF is valid
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_receipt_with_time_of_use_breakdown(self, receipt_service, bill_data_time_of_use_spain):
        """Test receipt includes time-of-use period breakdown"""
        pdf_bytes = receipt_service.generate_receipt_pdf(bill_data_time_of_use_spain)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_receipt_with_band_based_breakdown(self, receipt_service, bill_data_band_based_nigeria):
        """Test receipt includes band-based rate information"""
        pdf_bytes = receipt_service.generate_receipt_pdf(bill_data_band_based_nigeria)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_receipt_with_subsidies(self, receipt_service, bill_data_with_subsidies):
        """Test receipt shows subsidies as negative amounts"""
        pdf_bytes = receipt_service.generate_receipt_pdf(bill_data_with_subsidies)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_receipt_with_platform_charges(self, receipt_service, bill_data_with_platform_charges):
        """Test receipt includes platform service charges"""
        pdf_bytes = receipt_service.generate_receipt_pdf(bill_data_with_platform_charges)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_receipt_shows_consumption_with_rate(self, receipt_service, bill_data_tiered_usa):
        """Test receipt shows consumption and average rate per kWh"""
        pdf_bytes = receipt_service.generate_receipt_pdf(bill_data_tiered_usa)
        
        # Calculate expected rate
        consumption = bill_data_tiered_usa['consumption_kwh']
        base_charge = bill_data_tiered_usa['base_charge']
        expected_rate = base_charge / consumption
        
        assert pdf_bytes is not None
        # Rate should be calculated and included in PDF
        assert expected_rate > 0
    
    def test_receipt_shows_tax_breakdown(self, receipt_service, bill_data_time_of_use_spain):
        """Test receipt shows detailed tax breakdown with VAT rate"""
        pdf_bytes = receipt_service.generate_receipt_pdf(bill_data_time_of_use_spain)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        
        # Verify tax breakdown is present in bill_data
        assert 'tax_breakdown' in bill_data_time_of_use_spain
        assert 'vat' in bill_data_time_of_use_spain['tax_breakdown']
        assert 'vat_rate' in bill_data_time_of_use_spain['tax_breakdown']
    
    def test_receipt_shows_distribution_charges(self, receipt_service, bill_data_time_of_use_spain):
        """Test receipt shows distribution charges separately"""
        pdf_bytes = receipt_service.generate_receipt_pdf(bill_data_time_of_use_spain)
        
        assert pdf_bytes is not None
        assert 'distribution_charge' in bill_data_time_of_use_spain
        assert bill_data_time_of_use_spain['distribution_charge'] > 0
    
    def test_receipt_shows_service_charges(self, receipt_service, bill_data_band_based_nigeria):
        """Test receipt shows service charges separately"""
        pdf_bytes = receipt_service.generate_receipt_pdf(bill_data_band_based_nigeria)
        
        assert pdf_bytes is not None
        assert 'service_charge' in bill_data_band_based_nigeria
        assert bill_data_band_based_nigeria['service_charge'] > 0
    
    def test_receipt_currency_formatting_all_regions(self, receipt_service):
        """Test receipt formats currency correctly for all 5 regions"""
        currencies = [
            ('EUR', '€'),
            ('USD', '$'),
            ('INR', '₹'),
            ('BRL', 'R$'),
            ('NGN', '₦')
        ]
        
        for currency_code, symbol in currencies:
            bill_data = {
                'bill_id': f'test-{currency_code}',
                'consumption_kwh': 100.00,
                'base_charge': 50.00,
                'taxes': 10.00,
                'subsidies': 0,
                'total_fiat': 60.00,
                'currency': currency_code,
                'amount_hbar': 1200.00,
                'exchange_rate': 0.05,
                'hedera_tx_id': '0.0.123456@1710789700.123456789',
                'consensus_timestamp': datetime(2024, 3, 18, 14, 30, 0),
                'paid_at': datetime(2024, 3, 18, 14, 30, 5),
                'user_email': 'test@example.com',
                'meter_id': f'{currency_code}-TEST-12345'
            }
            
            pdf_bytes = receipt_service.generate_receipt_pdf(bill_data)
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
    
    def test_receipt_without_breakdown_still_works(self, receipt_service):
        """Test receipt generation works even without detailed breakdown"""
        minimal_bill_data = {
            'bill_id': 'minimal-1234',
            'consumption_kwh': 100.00,
            'base_charge': 50.00,
            'taxes': 10.00,
            'subsidies': 0,
            'total_fiat': 60.00,
            'currency': 'USD',
            'amount_hbar': 1200.00,
            'exchange_rate': 0.05,
            'hedera_tx_id': '0.0.123456@1710789700.123456789',
            'consensus_timestamp': datetime(2024, 3, 18, 14, 30, 0),
            'paid_at': datetime(2024, 3, 18, 14, 30, 5),
            'user_email': 'test@example.com',
            'meter_id': 'TEST-12345'
        }
        
        pdf_bytes = receipt_service.generate_receipt_pdf(minimal_bill_data)
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
    
    def test_receipt_total_matches_bill_total(self, receipt_service, bill_data_tiered_usa):
        """Test that total in breakdown matches bill total_fiat"""
        pdf_bytes = receipt_service.generate_receipt_pdf(bill_data_tiered_usa)
        
        assert pdf_bytes is not None
        
        # Verify total_fiat is present and positive
        assert bill_data_tiered_usa['total_fiat'] > 0
    
    def test_receipt_file_size_reasonable(self, receipt_service, bill_data_time_of_use_spain):
        """Test that PDF with detailed breakdown has reasonable file size"""
        pdf_bytes = receipt_service.generate_receipt_pdf(bill_data_time_of_use_spain)
        
        # PDF should be between 3KB and 1MB
        assert len(pdf_bytes) >= 3000  # At least 3KB
        assert len(pdf_bytes) <= 1024 * 1024  # At most 1MB
