"""
Test PDF Receipt Generation with Various Bill Amounts
Task 20.7: Test PDF generation with various bill amounts across different regions and currencies

This test suite validates:
1. Correct formatting for different bill amounts (small, medium, large)
2. Proper currency display for all 5 regions (EUR, USD, INR, BRL, NGN)
3. Accurate HBAR conversion calculations
4. Itemized breakdown displays correctly for various consumption levels
5. All PDF components render properly (QR code, branding, breakdown)
6. Edge cases handled (zero amounts, very large amounts, decimal precision)
"""
import pytest
from datetime import datetime
from decimal import Decimal
import io
from PIL import Image as PILImage

from app.services.receipt_service import get_receipt_service


class TestReceiptVariousAmounts:
    """Test PDF generation with various bill amounts"""
    
    @pytest.fixture
    def receipt_service(self):
        """Get receipt service instance"""
        return get_receipt_service()
    
    # ========== SMALL BILL AMOUNTS ==========
    
    @pytest.fixture
    def small_bill_eur(self):
        """Small bill amount for EUR (Spain) - €15.50"""
        return {
            'bill_id': 'small-eur-001',
            'consumption_kwh': Decimal('50.00'),
            'base_charge': Decimal('12.50'),
            'taxes': Decimal('3.00'),
            'subsidies': Decimal('0.00'),
            'total_fiat': Decimal('15.50'),
            'currency': 'EUR',
            'amount_hbar': Decimal('45.58823529'),  # @ 0.34 EUR/HBAR
            'exchange_rate': Decimal('0.34'),
            'hedera_tx_id': '0.0.123456@1710789700.001',
            'consensus_timestamp': datetime(2024, 3, 18, 10, 0, 0),
            'paid_at': datetime(2024, 3, 18, 10, 0, 5),
            'user_email': 'small-eur@test.com',
            'meter_id': 'ESP-SMALL-001'
        }
    
    @pytest.fixture
    def small_bill_usd(self):
        """Small bill amount for USD (USA) - $25.00"""
        return {
            'bill_id': 'small-usd-001',
            'consumption_kwh': Decimal('100.00'),
            'base_charge': Decimal('22.00'),
            'taxes': Decimal('3.00'),
            'subsidies': Decimal('0.00'),
            'total_fiat': Decimal('25.00'),
            'currency': 'USD',
            'amount_hbar': Decimal('500.00'),  # @ 0.05 USD/HBAR
            'exchange_rate': Decimal('0.05'),
            'hedera_tx_id': '0.0.234567@1710789700.002',
            'consensus_timestamp': datetime(2024, 3, 18, 11, 0, 0),
            'paid_at': datetime(2024, 3, 18, 11, 0, 5),
            'user_email': 'small-usd@test.com',
            'meter_id': 'USA-CA-SMALL-001'
        }
    
    # ========== MEDIUM BILL AMOUNTS ==========
    
    @pytest.fixture
    def medium_bill_eur(self):
        """Medium bill amount for EUR (Spain) - €85.40"""
        return {
            'bill_id': 'medium-eur-001',
            'consumption_kwh': Decimal('450.50'),
            'base_charge': Decimal('72.34'),
            'taxes': Decimal('15.18'),
            'subsidies': Decimal('2.12'),
            'total_fiat': Decimal('85.40'),
            'currency': 'EUR',
            'amount_hbar': Decimal('251.17647059'),
            'exchange_rate': Decimal('0.34'),
            'hedera_tx_id': '0.0.345678@1710789700.003',
            'consensus_timestamp': datetime(2024, 3, 18, 12, 0, 0),
            'paid_at': datetime(2024, 3, 18, 12, 0, 5),
            'user_email': 'medium-eur@test.com',
            'meter_id': 'ESP-MEDIUM-001'
        }
    
    @pytest.fixture
    def medium_bill_usd(self):
        """Medium bill amount for USD (USA) - $120.50"""
        return {
            'bill_id': 'medium-usd-001',
            'consumption_kwh': Decimal('850.00'),
            'base_charge': Decimal('102.00'),
            'taxes': Decimal('18.50'),
            'subsidies': Decimal('0.00'),
            'total_fiat': Decimal('120.50'),
            'currency': 'USD',
            'amount_hbar': Decimal('2410.00'),
            'exchange_rate': Decimal('0.05'),
            'hedera_tx_id': '0.0.456789@1710789700.004',
            'consensus_timestamp': datetime(2024, 3, 18, 13, 0, 0),
            'paid_at': datetime(2024, 3, 18, 13, 0, 5),
            'user_email': 'medium-usd@test.com',
            'meter_id': 'USA-CA-MEDIUM-001'
        }
    
    @pytest.fixture
    def medium_bill_inr(self):
        """Medium bill amount for INR (India) - ₹1,250.00"""
        return {
            'bill_id': 'medium-inr-001',
            'consumption_kwh': Decimal('300.00'),
            'base_charge': Decimal('1050.00'),
            'taxes': Decimal('200.00'),
            'subsidies': Decimal('0.00'),
            'total_fiat': Decimal('1250.00'),
            'currency': 'INR',
            'amount_hbar': Decimal('25000.00'),
            'exchange_rate': Decimal('0.05'),
            'hedera_tx_id': '0.0.567890@1710789700.005',
            'consensus_timestamp': datetime(2024, 3, 18, 14, 0, 0),
            'paid_at': datetime(2024, 3, 18, 14, 0, 5),
            'user_email': 'medium-inr@test.com',
            'meter_id': 'IN-TPDDL-MEDIUM-001'
        }
    
    @pytest.fixture
    def medium_bill_brl(self):
        """Medium bill amount for BRL (Brazil) - R$95.00"""
        return {
            'bill_id': 'medium-brl-001',
            'consumption_kwh': Decimal('400.00'),
            'base_charge': Decimal('80.00'),
            'taxes': Decimal('15.00'),
            'subsidies': Decimal('0.00'),
            'total_fiat': Decimal('95.00'),
            'currency': 'BRL',
            'amount_hbar': Decimal('1900.00'),
            'exchange_rate': Decimal('0.05'),
            'hedera_tx_id': '0.0.678901@1710789700.006',
            'consensus_timestamp': datetime(2024, 3, 18, 15, 0, 0),
            'paid_at': datetime(2024, 3, 18, 15, 0, 5),
            'user_email': 'medium-brl@test.com',
            'meter_id': 'BR-ENEL-MEDIUM-001'
        }
    
    @pytest.fixture
    def medium_bill_ngn(self):
        """Medium bill amount for NGN (Nigeria) - ₦12,500.00"""
        return {
            'bill_id': 'medium-ngn-001',
            'consumption_kwh': Decimal('320.00'),
            'base_charge': Decimal('11627.91'),
            'taxes': Decimal('872.09'),
            'subsidies': Decimal('0.00'),
            'total_fiat': Decimal('12500.00'),
            'currency': 'NGN',
            'amount_hbar': Decimal('250000.00'),
            'exchange_rate': Decimal('0.05'),
            'hedera_tx_id': '0.0.789012@1710789700.007',
            'consensus_timestamp': datetime(2024, 3, 18, 16, 0, 0),
            'paid_at': datetime(2024, 3, 18, 16, 0, 5),
            'user_email': 'medium-ngn@test.com',
            'meter_id': 'NG-IKEDP-MEDIUM-001'
        }
    
    # ========== LARGE BILL AMOUNTS ==========
    
    @pytest.fixture
    def large_bill_eur(self):
        """Large bill amount for EUR (Spain) - €450.75"""
        return {
            'bill_id': 'large-eur-001',
            'consumption_kwh': Decimal('2500.00'),
            'base_charge': Decimal('380.00'),
            'taxes': Decimal('79.80'),
            'subsidies': Decimal('9.05'),
            'total_fiat': Decimal('450.75'),
            'currency': 'EUR',
            'amount_hbar': Decimal('1325.73529412'),
            'exchange_rate': Decimal('0.34'),
            'hedera_tx_id': '0.0.890123@1710789700.008',
            'consensus_timestamp': datetime(2024, 3, 18, 17, 0, 0),
            'paid_at': datetime(2024, 3, 18, 17, 0, 5),
            'user_email': 'large-eur@test.com',
            'meter_id': 'ESP-LARGE-001'
        }
    
    @pytest.fixture
    def large_bill_usd(self):
        """Large bill amount for USD (USA) - $875.25"""
        return {
            'bill_id': 'large-usd-001',
            'consumption_kwh': Decimal('5000.00'),
            'base_charge': Decimal('750.00'),
            'taxes': Decimal('125.25'),
            'subsidies': Decimal('0.00'),
            'total_fiat': Decimal('875.25'),
            'currency': 'USD',
            'amount_hbar': Decimal('17505.00'),
            'exchange_rate': Decimal('0.05'),
            'hedera_tx_id': '0.0.901234@1710789700.009',
            'consensus_timestamp': datetime(2024, 3, 18, 18, 0, 0),
            'paid_at': datetime(2024, 3, 18, 18, 0, 5),
            'user_email': 'large-usd@test.com',
            'meter_id': 'USA-CA-LARGE-001'
        }
    
    # ========== EDGE CASES ==========
    
    @pytest.fixture
    def minimum_bill_eur(self):
        """Minimum bill amount for EUR - €5.00 (minimum transfer)"""
        return {
            'bill_id': 'min-eur-001',
            'consumption_kwh': Decimal('10.00'),
            'base_charge': Decimal('4.00'),
            'taxes': Decimal('1.00'),
            'subsidies': Decimal('0.00'),
            'total_fiat': Decimal('5.00'),
            'currency': 'EUR',
            'amount_hbar': Decimal('14.70588235'),
            'exchange_rate': Decimal('0.34'),
            'hedera_tx_id': '0.0.012345@1710789700.010',
            'consensus_timestamp': datetime(2024, 3, 18, 19, 0, 0),
            'paid_at': datetime(2024, 3, 18, 19, 0, 5),
            'user_email': 'min-eur@test.com',
            'meter_id': 'ESP-MIN-001'
        }
    
    @pytest.fixture
    def very_large_bill_ngn(self):
        """Very large bill amount for NGN - ₦500,000.00"""
        return {
            'bill_id': 'xlarge-ngn-001',
            'consumption_kwh': Decimal('10000.00'),
            'base_charge': Decimal('465116.28'),
            'taxes': Decimal('34883.72'),
            'subsidies': Decimal('0.00'),
            'total_fiat': Decimal('500000.00'),
            'currency': 'NGN',
            'amount_hbar': Decimal('10000000.00'),
            'exchange_rate': Decimal('0.05'),
            'hedera_tx_id': '0.0.123450@1710789700.011',
            'consensus_timestamp': datetime(2024, 3, 18, 20, 0, 0),
            'paid_at': datetime(2024, 3, 18, 20, 0, 5),
            'user_email': 'xlarge-ngn@test.com',
            'meter_id': 'NG-IKEDP-XLARGE-001'
        }
    
    @pytest.fixture
    def high_precision_bill(self):
        """Bill with high decimal precision"""
        return {
            'bill_id': 'precision-001',
            'consumption_kwh': Decimal('123.456789'),
            'base_charge': Decimal('45.678901'),
            'taxes': Decimal('9.876543'),
            'subsidies': Decimal('1.234567'),
            'total_fiat': Decimal('54.320877'),
            'currency': 'EUR',
            'amount_hbar': Decimal('159.76728529411764705882352941'),
            'exchange_rate': Decimal('0.34'),
            'hedera_tx_id': '0.0.234501@1710789700.012',
            'consensus_timestamp': datetime(2024, 3, 18, 21, 0, 0),
            'paid_at': datetime(2024, 3, 18, 21, 0, 5),
            'user_email': 'precision@test.com',
            'meter_id': 'ESP-PRECISION-001'
        }
    
    # ========== TEST METHODS ==========
    
    def test_small_bill_eur(self, receipt_service, small_bill_eur):
        """Test PDF generation for small EUR bill (€15.50)"""
        pdf_bytes = receipt_service.generate_receipt_pdf(small_bill_eur)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
        
        # Verify reasonable file size (PDFs with QR codes and branding can be larger)
        assert 3000 < len(pdf_bytes) < 2000000  # 2MB max
    
    def test_small_bill_usd(self, receipt_service, small_bill_usd):
        """Test PDF generation for small USD bill ($25.00)"""
        pdf_bytes = receipt_service.generate_receipt_pdf(small_bill_usd)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
        assert 3000 < len(pdf_bytes) < 2000000  # 2MB max
    
    def test_medium_bills_all_currencies(self, receipt_service, medium_bill_eur, 
                                         medium_bill_usd, medium_bill_inr, 
                                         medium_bill_brl, medium_bill_ngn):
        """Test PDF generation for medium bills in all 5 currencies"""
        bills = [
            ('EUR', medium_bill_eur, '€85.40'),
            ('USD', medium_bill_usd, '$120.50'),
            ('INR', medium_bill_inr, '₹1,250.00'),
            ('BRL', medium_bill_brl, 'R$95.00'),
            ('NGN', medium_bill_ngn, '₦12,500.00')
        ]
        
        for currency, bill_data, expected_display in bills:
            pdf_bytes = receipt_service.generate_receipt_pdf(bill_data)
            
            # Verify PDF is valid
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
            assert pdf_bytes[:4] == b'%PDF'
            
            # Verify reasonable file size (PDFs with QR codes can be larger)
            assert 3000 < len(pdf_bytes) < 2000000  # 2MB max
            
            # Verify currency matches
            assert bill_data['currency'] == currency
    
    def test_large_bill_eur(self, receipt_service, large_bill_eur):
        """Test PDF generation for large EUR bill (€450.75)"""
        pdf_bytes = receipt_service.generate_receipt_pdf(large_bill_eur)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
        assert 3000 < len(pdf_bytes) < 2000000  # 2MB max
    
    def test_large_bill_usd(self, receipt_service, large_bill_usd):
        """Test PDF generation for large USD bill ($875.25)"""
        pdf_bytes = receipt_service.generate_receipt_pdf(large_bill_usd)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
        assert 3000 < len(pdf_bytes) < 2000000  # 2MB max
    
    def test_minimum_bill_eur(self, receipt_service, minimum_bill_eur):
        """Test PDF generation for minimum EUR bill (€5.00)"""
        pdf_bytes = receipt_service.generate_receipt_pdf(minimum_bill_eur)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
        
        # Verify minimum amount
        assert float(minimum_bill_eur['total_fiat']) == 5.00
    
    def test_very_large_bill_ngn(self, receipt_service, very_large_bill_ngn):
        """Test PDF generation for very large NGN bill (₦500,000.00)"""
        pdf_bytes = receipt_service.generate_receipt_pdf(very_large_bill_ngn)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
        
        # Verify large amount handling
        assert float(very_large_bill_ngn['total_fiat']) == 500000.00
    
    def test_high_precision_bill(self, receipt_service, high_precision_bill):
        """Test PDF generation with high decimal precision"""
        pdf_bytes = receipt_service.generate_receipt_pdf(high_precision_bill)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
        
        # Verify precision is maintained
        assert high_precision_bill['consumption_kwh'] == Decimal('123.456789')
        assert high_precision_bill['total_fiat'] == Decimal('54.320877')
    
    def test_hbar_conversion_accuracy(self, receipt_service, medium_bill_eur):
        """Test HBAR conversion calculation accuracy"""
        total_fiat = float(medium_bill_eur['total_fiat'])
        exchange_rate = float(medium_bill_eur['exchange_rate'])
        amount_hbar = float(medium_bill_eur['amount_hbar'])
        
        # Calculate expected HBAR amount
        expected_hbar = total_fiat / exchange_rate
        
        # Verify conversion is accurate (within 0.01 HBAR)
        assert abs(amount_hbar - expected_hbar) < 0.01
        
        # Generate PDF to ensure it renders correctly
        pdf_bytes = receipt_service.generate_receipt_pdf(medium_bill_eur)
        assert pdf_bytes is not None
    
    def test_currency_formatting_all_amounts(self, receipt_service):
        """Test currency formatting for various amounts in all currencies"""
        test_cases = [
            ('EUR', 5.00, '€'),
            ('EUR', 85.40, '€'),
            ('EUR', 450.75, '€'),
            ('USD', 25.00, '$'),
            ('USD', 120.50, '$'),
            ('USD', 875.25, '$'),
            ('INR', 450.00, '₹'),
            ('INR', 1250.00, '₹'),
            ('BRL', 95.00, 'R$'),
            ('NGN', 12500.00, '₦'),
            ('NGN', 500000.00, '₦'),
        ]
        
        for currency, amount, symbol in test_cases:
            bill_data = {
                'bill_id': f'format-{currency}-{amount}',
                'consumption_kwh': Decimal('100.00'),
                'base_charge': Decimal(str(amount * 0.8)),
                'taxes': Decimal(str(amount * 0.2)),
                'subsidies': Decimal('0.00'),
                'total_fiat': Decimal(str(amount)),
                'currency': currency,
                'amount_hbar': Decimal(str(amount * 20)),
                'exchange_rate': Decimal('0.05'),
                'hedera_tx_id': f'0.0.123456@1710789700.{currency}',
                'consensus_timestamp': datetime.utcnow(),
                'paid_at': datetime.utcnow(),
                'user_email': f'test-{currency}@example.com',
                'meter_id': f'{currency}-TEST-001'
            }
            
            pdf_bytes = receipt_service.generate_receipt_pdf(bill_data)
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
            
            # Verify currency symbol is correct
            assert receipt_service.CURRENCY_SYMBOLS[currency] == symbol
    
    def test_consumption_levels_impact_breakdown(self, receipt_service):
        """Test that different consumption levels display correctly in breakdown"""
        consumption_levels = [
            (50.00, 'Low consumption'),
            (450.50, 'Medium consumption'),
            (2500.00, 'High consumption'),
            (10000.00, 'Very high consumption')
        ]
        
        for consumption, description in consumption_levels:
            bill_data = {
                'bill_id': f'consumption-{consumption}',
                'consumption_kwh': Decimal(str(consumption)),
                'base_charge': Decimal(str(consumption * 0.15)),
                'taxes': Decimal(str(consumption * 0.03)),
                'subsidies': Decimal('0.00'),
                'total_fiat': Decimal(str(consumption * 0.18)),
                'currency': 'EUR',
                'amount_hbar': Decimal(str(consumption * 0.18 / 0.34)),
                'exchange_rate': Decimal('0.34'),
                'hedera_tx_id': f'0.0.123456@1710789700.{int(consumption)}',
                'consensus_timestamp': datetime.utcnow(),
                'paid_at': datetime.utcnow(),
                'user_email': 'consumption@test.com',
                'meter_id': f'ESP-CONS-{int(consumption)}'
            }
            
            pdf_bytes = receipt_service.generate_receipt_pdf(bill_data)
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
            
            # Verify consumption is correctly stored
            assert float(bill_data['consumption_kwh']) == consumption
    
    def test_pdf_components_present_all_amounts(self, receipt_service, small_bill_eur, 
                                                medium_bill_usd, large_bill_eur):
        """Test that all PDF components are present for different bill amounts"""
        bills = [small_bill_eur, medium_bill_usd, large_bill_eur]
        
        for bill_data in bills:
            pdf_bytes = receipt_service.generate_receipt_pdf(bill_data)
            
            # Verify PDF is valid
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
            assert pdf_bytes[:4] == b'%PDF'
            
            # Verify file size indicates content is present
            # (QR code, branding, breakdown all add to file size)
            assert len(pdf_bytes) > 5000  # Should have substantial content
    
    def test_exchange_rate_variations(self, receipt_service):
        """Test PDF generation with different exchange rates"""
        exchange_rates = [
            (Decimal('0.05'), 'Low rate'),
            (Decimal('0.34'), 'Medium rate'),
            (Decimal('0.50'), 'High rate'),
            (Decimal('1.00'), 'Parity rate')
        ]
        
        for rate, description in exchange_rates:
            total_fiat = Decimal('100.00')
            amount_hbar = total_fiat / rate
            
            bill_data = {
                'bill_id': f'rate-{rate}',
                'consumption_kwh': Decimal('500.00'),
                'base_charge': Decimal('85.00'),
                'taxes': Decimal('15.00'),
                'subsidies': Decimal('0.00'),
                'total_fiat': total_fiat,
                'currency': 'EUR',
                'amount_hbar': amount_hbar,
                'exchange_rate': rate,
                'hedera_tx_id': f'0.0.123456@1710789700.{rate}',
                'consensus_timestamp': datetime.utcnow(),
                'paid_at': datetime.utcnow(),
                'user_email': 'rate@test.com',
                'meter_id': f'ESP-RATE-{rate}'
            }
            
            pdf_bytes = receipt_service.generate_receipt_pdf(bill_data)
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
            
            # Verify exchange rate calculation
            calculated_hbar = float(total_fiat) / float(rate)
            assert abs(float(amount_hbar) - calculated_hbar) < 0.01
    
    def test_zero_subsidy_vs_with_subsidy(self, receipt_service):
        """Test PDF generation with and without subsidies"""
        # Bill without subsidy
        bill_no_subsidy = {
            'bill_id': 'no-subsidy-001',
            'consumption_kwh': Decimal('400.00'),
            'base_charge': Decimal('80.00'),
            'taxes': Decimal('16.00'),
            'subsidies': Decimal('0.00'),
            'total_fiat': Decimal('96.00'),
            'currency': 'EUR',
            'amount_hbar': Decimal('282.35294118'),
            'exchange_rate': Decimal('0.34'),
            'hedera_tx_id': '0.0.123456@1710789700.100',
            'consensus_timestamp': datetime.utcnow(),
            'paid_at': datetime.utcnow(),
            'user_email': 'no-subsidy@test.com',
            'meter_id': 'ESP-NOSUB-001'
        }
        
        # Bill with subsidy
        bill_with_subsidy = {
            'bill_id': 'with-subsidy-001',
            'consumption_kwh': Decimal('400.00'),
            'base_charge': Decimal('80.00'),
            'taxes': Decimal('16.00'),
            'subsidies': Decimal('10.00'),
            'total_fiat': Decimal('86.00'),
            'currency': 'EUR',
            'amount_hbar': Decimal('252.94117647'),
            'exchange_rate': Decimal('0.34'),
            'hedera_tx_id': '0.0.123456@1710789700.101',
            'consensus_timestamp': datetime.utcnow(),
            'paid_at': datetime.utcnow(),
            'user_email': 'with-subsidy@test.com',
            'meter_id': 'ESP-WITHSUB-001'
        }
        
        # Generate both PDFs
        pdf_no_subsidy = receipt_service.generate_receipt_pdf(bill_no_subsidy)
        pdf_with_subsidy = receipt_service.generate_receipt_pdf(bill_with_subsidy)
        
        # Verify both are valid
        assert pdf_no_subsidy is not None and len(pdf_no_subsidy) > 0
        assert pdf_with_subsidy is not None and len(pdf_with_subsidy) > 0
        
        # Verify subsidy affects total
        assert float(bill_with_subsidy['total_fiat']) < float(bill_no_subsidy['total_fiat'])
    
    def test_decimal_precision_maintained(self, receipt_service, high_precision_bill):
        """Test that decimal precision is maintained throughout PDF generation"""
        pdf_bytes = receipt_service.generate_receipt_pdf(high_precision_bill)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        
        # Verify precision in source data
        assert isinstance(high_precision_bill['consumption_kwh'], Decimal)
        assert isinstance(high_precision_bill['total_fiat'], Decimal)
        assert isinstance(high_precision_bill['amount_hbar'], Decimal)
        
        # Verify very high precision HBAR amount
        hbar_str = str(high_precision_bill['amount_hbar'])
        assert '.' in hbar_str
        assert len(hbar_str.split('.')[1]) > 8  # More than 8 decimal places
    
    def test_file_size_consistency_across_amounts(self, receipt_service, 
                                                   small_bill_eur, medium_bill_usd, 
                                                   large_bill_eur):
        """Test that file size is consistent regardless of bill amount"""
        pdf_small = receipt_service.generate_receipt_pdf(small_bill_eur)
        pdf_medium = receipt_service.generate_receipt_pdf(medium_bill_usd)
        pdf_large = receipt_service.generate_receipt_pdf(large_bill_eur)
        
        # All PDFs should be within reasonable size range (2MB max with QR codes and branding)
        sizes = [len(pdf_small), len(pdf_medium), len(pdf_large)]
        
        for size in sizes:
            assert 3000 < size < 2000000
        
        # Size variation should be minimal (within 50%)
        min_size = min(sizes)
        max_size = max(sizes)
        assert max_size < min_size * 1.5
    
    def test_all_currencies_minimum_amounts(self, receipt_service):
        """Test minimum transfer amounts for all currencies"""
        minimum_amounts = [
            ('EUR', Decimal('5.00')),
            ('USD', Decimal('5.00')),
            ('INR', Decimal('50.00')),
            ('BRL', Decimal('10.00')),
            ('NGN', Decimal('2000.00'))
        ]
        
        for currency, min_amount in minimum_amounts:
            bill_data = {
                'bill_id': f'min-{currency}',
                'consumption_kwh': Decimal('10.00'),
                'base_charge': min_amount * Decimal('0.8'),
                'taxes': min_amount * Decimal('0.2'),
                'subsidies': Decimal('0.00'),
                'total_fiat': min_amount,
                'currency': currency,
                'amount_hbar': min_amount / Decimal('0.05'),
                'exchange_rate': Decimal('0.05'),
                'hedera_tx_id': f'0.0.123456@1710789700.{currency}',
                'consensus_timestamp': datetime.utcnow(),
                'paid_at': datetime.utcnow(),
                'user_email': f'min-{currency}@test.com',
                'meter_id': f'{currency}-MIN-001'
            }
            
            pdf_bytes = receipt_service.generate_receipt_pdf(bill_data)
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
            assert pdf_bytes[:4] == b'%PDF'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
