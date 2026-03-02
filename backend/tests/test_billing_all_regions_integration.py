"""
Integration tests for billing calculations across all 5 regions with sample data

Tests billing calculations for:
- Spain (ES): Time-of-use rates with peak/standard/off-peak
- USA (US): Tiered rates with baseline/tier2/tier3
- India (IN): Tiered rates with 3 tiers
- Brazil (BR): Tiered rates with ICMS tax
- Nigeria (NG): Band-based rates with A-E classifications

Requirements: US-5 (Bill Calculation user story)
Task: 15.10 - Test billing calculations for all 5 regions with sample data
"""
import pytest
from decimal import Decimal
from app.services.billing_service import calculate_bill, BillingCalculationError


class TestSpainIntegration:
    """Integration tests for Spain billing with realistic sample data"""
    
    def test_spain_low_consumption_household(self):
        """Test Spain billing for low consumption household (150 kWh)"""
        # Scenario: Small apartment, single person, mostly off-peak usage
        tariff_data = {
            'currency': 'EUR',
            'rate_structure': {
                'type': 'time_of_use',
                'periods': [
                    {'name': 'peak', 'hours': [10,11,12,13,18,19,20,21], 'price': 0.40},
                    {'name': 'standard', 'hours': [8,9,14,15,16,17,22,23], 'price': 0.25},
                    {'name': 'off_peak', 'hours': [0,1,2,3,4,5,6,7], 'price': 0.15}
                ]
            },
            'taxes_and_fees': {
                'vat': 0.21,
                'distribution_charge': 0.045
            },
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=150,
            country_code='ES',
            utility_provider='Iberdrola',
            tariff_data=tariff_data
        )
        
        # Verify calculation
        assert result['consumption_kwh'] == Decimal('150')
        assert result['currency'] == 'EUR'
        assert result['country_code'] == 'ES'
        
        # Base charge should be around €37.50 (estimated distribution)
        # Peak (30%): 45 kWh × €0.40 = €18.00
        # Standard (40%): 60 kWh × €0.25 = €15.00
        # Off-peak (30%): 45 kWh × €0.15 = €6.75
        # Total base: €39.75
        assert 35 < float(result['base_charge']) < 45
        
        # Utility taxes: VAT (21%) + distribution (€0.045/kWh)
        # Distribution: 150 × €0.045 = €6.75
        # VAT: €39.75 × 0.21 = €8.35
        # Total utility taxes: ~€15.10
        assert 12 < float(result['utility_taxes']) < 18
        
        # Total should be around €60-70
        assert 55 < float(result['total_fiat']) < 75
        
        # Verify breakdown structure
        assert 'breakdown' in result
        assert result['breakdown']['rate_type'] == 'time_of_use'
        assert len(result['breakdown']['periods']) == 3

    
    def test_spain_high_consumption_household(self):
        """Test Spain billing for high consumption household (450 kWh)"""
        # Scenario: Large family home with AC, high peak usage
        tariff_data = {
            'currency': 'EUR',
            'rate_structure': {
                'type': 'time_of_use',
                'periods': [
                    {'name': 'peak', 'hours': [10,11,12,13,18,19,20,21], 'price': 0.40},
                    {'name': 'standard', 'hours': [8,9,14,15,16,17,22,23], 'price': 0.25},
                    {'name': 'off_peak', 'hours': [0,1,2,3,4,5,6,7], 'price': 0.15}
                ]
            },
            'taxes_and_fees': {
                'vat': 0.21,
                'distribution_charge': 0.045
            },
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=450,
            country_code='ES',
            utility_provider='Iberdrola',
            tariff_data=tariff_data
        )
        
        # Verify high consumption results in higher bill
        assert result['consumption_kwh'] == Decimal('450')
        assert 100 < float(result['base_charge']) < 140
        assert 150 < float(result['total_fiat']) < 200


class TestUSAIntegration:
    """Integration tests for USA billing with realistic sample data"""
    
    def test_usa_baseline_consumption(self):
        """Test USA billing for baseline consumption (300 kWh) - Tier 1 only"""
        # Scenario: Efficient household staying within baseline allowance
        tariff_data = {
            'currency': 'USD',
            'rate_structure': {
                'type': 'tiered',
                'tiers': [
                    {'name': 'Tier 1 (Baseline)', 'min_kwh': 0, 'max_kwh': 400, 'price': 0.32},
                    {'name': 'Tier 2', 'min_kwh': 401, 'max_kwh': 800, 'price': 0.40},
                    {'name': 'Tier 3', 'min_kwh': 801, 'max_kwh': None, 'price': 0.50}
                ]
            },
            'taxes_and_fees': {
                'sales_tax': 0.0725,
                'fixed_monthly_fee': 10.00
            },
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=300,
            country_code='US',
            utility_provider='PG&E',
            tariff_data=tariff_data
        )
        
        # Verify calculation
        assert result['consumption_kwh'] == Decimal('300')
        assert result['currency'] == 'USD'
        
        # Base charge: 300 kWh × $0.32 = $96.00
        assert float(result['base_charge']) == pytest.approx(96.00, rel=0.01)
        
        # Utility taxes: Sales tax (7.25%) + fixed fee ($10)
        # Sales tax: $96.00 × 0.0725 = $6.96
        # Fixed fee: $10.00
        # Total: $16.96
        assert float(result['utility_taxes']) == pytest.approx(16.96, rel=0.01)
        
        # Subtotal: $96.00 + $16.96 = $112.96
        # Platform fee (3%): $112.96 × 0.03 = $3.39
        # Platform VAT (7.25%): $3.39 × 0.0725 = $0.25
        # Total: $112.96 + $3.39 + $0.25 = $116.60
        assert 115 < float(result['total_fiat']) < 120
    
    def test_usa_multi_tier_consumption(self):
        """Test USA billing spanning multiple tiers (650 kWh)"""
        # Scenario: High consumption household exceeding baseline
        tariff_data = {
            'currency': 'USD',
            'rate_structure': {
                'type': 'tiered',
                'tiers': [
                    {'name': 'Tier 1 (Baseline)', 'min_kwh': 0, 'max_kwh': 400, 'price': 0.32},
                    {'name': 'Tier 2', 'min_kwh': 401, 'max_kwh': 800, 'price': 0.40},
                    {'name': 'Tier 3', 'min_kwh': 801, 'max_kwh': None, 'price': 0.50}
                ]
            },
            'taxes_and_fees': {
                'sales_tax': 0.0725,
                'fixed_monthly_fee': 10.00
            },
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=650,
            country_code='US',
            utility_provider='PG&E',
            tariff_data=tariff_data
        )
        
        # Base charge calculation:
        # Tier 1: 400 kWh × $0.32 = $128.00
        # Tier 2: 250 kWh × $0.40 = $100.00
        # Total base: $228.00
        assert float(result['base_charge']) == pytest.approx(228.00, rel=0.01)
        
        # Verify breakdown shows both tiers
        assert len(result['breakdown']['tiers']) == 2
        assert result['breakdown']['tiers'][0]['consumption_kwh'] == 400
        assert result['breakdown']['tiers'][1]['consumption_kwh'] == 250


class TestIndiaIntegration:
    """Integration tests for India billing with realistic sample data"""
    
    def test_india_low_consumption(self):
        """Test India billing for low consumption (80 kWh) - Tier 1 only"""
        # Scenario: Small household with minimal usage
        tariff_data = {
            'currency': 'INR',
            'rate_structure': {
                'type': 'tiered',
                'tiers': [
                    {'name': 'Tier 1 (0-100 kWh)', 'min_kwh': 0, 'max_kwh': 100, 'price': 4.50},
                    {'name': 'Tier 2 (101-300 kWh)', 'min_kwh': 101, 'max_kwh': 300, 'price': 6.00},
                    {'name': 'Tier 3 (301+ kWh)', 'min_kwh': 301, 'max_kwh': None, 'price': 7.50}
                ]
            },
            'taxes_and_fees': {
                'vat': 0.18
            },
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=80,
            country_code='IN',
            utility_provider='Tata Power',
            tariff_data=tariff_data
        )
        
        # Base charge: 80 kWh × ₹4.50 = ₹360.00
        assert float(result['base_charge']) == pytest.approx(360.00, rel=0.01)
        
        # VAT: ₹360.00 × 0.18 = ₹64.80
        assert float(result['utility_taxes']) == pytest.approx(64.80, rel=0.01)
        
        # Total should be around ₹440-460
        assert 430 < float(result['total_fiat']) < 470

    
    def test_india_high_consumption(self):
        """Test India billing for high consumption (350 kWh) - All 3 tiers"""
        # Scenario: Large household with AC and appliances
        tariff_data = {
            'currency': 'INR',
            'rate_structure': {
                'type': 'tiered',
                'tiers': [
                    {'name': 'Tier 1 (0-100 kWh)', 'min_kwh': 0, 'max_kwh': 100, 'price': 4.50},
                    {'name': 'Tier 2 (101-300 kWh)', 'min_kwh': 101, 'max_kwh': 300, 'price': 6.00},
                    {'name': 'Tier 3 (301+ kWh)', 'min_kwh': 301, 'max_kwh': None, 'price': 7.50}
                ]
            },
            'taxes_and_fees': {
                'vat': 0.18
            },
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=350,
            country_code='IN',
            utility_provider='Tata Power',
            tariff_data=tariff_data
        )
        
        # Base charge calculation:
        # Tier 1: 100 kWh × ₹4.50 = ₹450.00
        # Tier 2: 200 kWh × ₹6.00 = ₹1,200.00
        # Tier 3: 50 kWh × ₹7.50 = ₹375.00
        # Total: ₹2,025.00
        assert float(result['base_charge']) == pytest.approx(2025.00, rel=0.01)
        
        # Verify all 3 tiers in breakdown
        assert len(result['breakdown']['tiers']) == 3


class TestBrazilIntegration:
    """Integration tests for Brazil billing with realistic sample data"""
    
    def test_brazil_medium_consumption(self):
        """Test Brazil billing for medium consumption (200 kWh)"""
        # Scenario: Average household in São Paulo
        tariff_data = {
            'currency': 'BRL',
            'rate_structure': {
                'type': 'tiered',
                'tiers': [
                    {'name': 'Tier 1 (0-100 kWh)', 'min_kwh': 0, 'max_kwh': 100, 'price': 0.50},
                    {'name': 'Tier 2 (101-300 kWh)', 'min_kwh': 101, 'max_kwh': 300, 'price': 0.70},
                    {'name': 'Tier 3 (301+ kWh)', 'min_kwh': 301, 'max_kwh': None, 'price': 0.90}
                ]
            },
            'taxes_and_fees': {
                'icms_tax': 0.18
            },
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=200,
            country_code='BR',
            utility_provider='Enel São Paulo',
            tariff_data=tariff_data
        )
        
        # Base charge calculation:
        # Tier 1: 100 kWh × R$0.50 = R$50.00
        # Tier 2: 100 kWh × R$0.70 = R$70.00
        # Total: R$120.00
        assert float(result['base_charge']) == pytest.approx(120.00, rel=0.01)
        
        # ICMS tax: R$120.00 × 0.18 = R$21.60
        assert float(result['utility_taxes']) == pytest.approx(21.60, rel=0.01)
        
        # Total should be around R$145-155
        assert 140 < float(result['total_fiat']) < 160


class TestNigeriaIntegration:
    """Integration tests for Nigeria billing with realistic sample data"""
    
    def test_nigeria_band_a_high_supply(self):
        """Test Nigeria billing for Band A (20+ hours supply) - Premium rate"""
        # Scenario: High-income area with excellent power supply
        tariff_data = {
            'currency': 'NGN',
            'rate_structure': {
                'type': 'band_based',
                'bands': [
                    {'name': 'A', 'hours_min': 20, 'price': 225.00},
                    {'name': 'B', 'hours_min': 16, 'price': 63.30},
                    {'name': 'C', 'hours_min': 12, 'price': 50.00},
                    {'name': 'D', 'hours_min': 8, 'price': 43.00},
                    {'name': 'E', 'hours_min': 0, 'price': 40.00}
                ]
            },
            'taxes_and_fees': {
                'vat': 0.075,
                'service_charge': 1500.00
            },
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=200,
            country_code='NG',
            utility_provider='IKEDP',
            tariff_data=tariff_data,
            band_classification='A'
        )
        
        # Base charge: 200 kWh × ₦225.00 = ₦45,000.00
        assert float(result['base_charge']) == pytest.approx(45000.00, rel=0.01)
        
        # Utility taxes: VAT (7.5%) + service charge (₦1,500)
        # VAT: ₦45,000 × 0.075 = ₦3,375.00
        # Service charge: ₦1,500.00
        # Total: ₦4,875.00
        assert float(result['utility_taxes']) == pytest.approx(4875.00, rel=0.01)

    
    def test_nigeria_band_c_medium_supply(self):
        """Test Nigeria billing for Band C (12-16 hours supply) - Mid-tier rate"""
        # Scenario: Middle-income area with moderate power supply
        tariff_data = {
            'currency': 'NGN',
            'rate_structure': {
                'type': 'band_based',
                'bands': [
                    {'name': 'A', 'hours_min': 20, 'price': 225.00},
                    {'name': 'B', 'hours_min': 16, 'price': 63.30},
                    {'name': 'C', 'hours_min': 12, 'price': 50.00},
                    {'name': 'D', 'hours_min': 8, 'price': 43.00},
                    {'name': 'E', 'hours_min': 0, 'price': 40.00}
                ]
            },
            'taxes_and_fees': {
                'vat': 0.075,
                'service_charge': 1000.00
            },
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=150,
            country_code='NG',
            utility_provider='EKEDC',
            tariff_data=tariff_data,
            band_classification='C'
        )
        
        # Base charge: 150 kWh × ₦50.00 = ₦7,500.00
        assert float(result['base_charge']) == pytest.approx(7500.00, rel=0.01)
        
        # Verify band classification in breakdown
        assert result['breakdown']['band']['classification'] == 'C'
        assert result['breakdown']['band']['price_per_kwh'] == 50.00
    
    def test_nigeria_band_e_low_supply(self):
        """Test Nigeria billing for Band E (<8 hours supply) - Subsidized rate"""
        # Scenario: Low-income area with poor power supply
        tariff_data = {
            'currency': 'NGN',
            'rate_structure': {
                'type': 'band_based',
                'bands': [
                    {'name': 'A', 'hours_min': 20, 'price': 225.00},
                    {'name': 'B', 'hours_min': 16, 'price': 63.30},
                    {'name': 'C', 'hours_min': 12, 'price': 50.00},
                    {'name': 'D', 'hours_min': 8, 'price': 43.00},
                    {'name': 'E', 'hours_min': 0, 'price': 40.00}
                ]
            },
            'taxes_and_fees': {
                'vat': 0.075,
                'service_charge': 750.00
            },
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='NG',
            utility_provider='PHED',
            tariff_data=tariff_data,
            band_classification='E'
        )
        
        # Base charge: 100 kWh × ₦40.00 = ₦4,000.00
        assert float(result['base_charge']) == pytest.approx(4000.00, rel=0.01)
        
        # Total should be lower than other bands (subsidized)
        assert float(result['total_fiat']) < 6000.00


class TestEdgeCases:
    """Test edge cases and boundary conditions across all regions"""
    
    def test_zero_consumption(self):
        """Test billing with zero consumption (fixed fees only)"""
        tariff_data = {
            'currency': 'USD',
            'rate_structure': {
                'type': 'flat',
                'rate': 0.30
            },
            'taxes_and_fees': {
                'fixed_monthly_fee': 10.00
            },
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=0,
            country_code='US',
            utility_provider='Test Utility',
            tariff_data=tariff_data
        )
        
        # Base charge should be 0
        assert float(result['base_charge']) == 0.00
        
        # Should still have fixed fee
        assert float(result['utility_taxes']) == 10.00
    
    def test_tier_boundary_consumption(self):
        """Test consumption exactly at tier boundary (400 kWh)"""
        tariff_data = {
            'currency': 'USD',
            'rate_structure': {
                'type': 'tiered',
                'tiers': [
                    {'name': 'Tier 1', 'min_kwh': 0, 'max_kwh': 400, 'price': 0.32},
                    {'name': 'Tier 2', 'min_kwh': 401, 'max_kwh': 800, 'price': 0.40}
                ]
            },
            'taxes_and_fees': {},
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=400,
            country_code='US',
            utility_provider='Test Utility',
            tariff_data=tariff_data
        )
        
        # Should use only Tier 1
        assert len(result['breakdown']['tiers']) == 1
        assert result['breakdown']['tiers'][0]['consumption_kwh'] == 400

    
    def test_very_high_consumption(self):
        """Test billing with very high consumption (1500 kWh)"""
        tariff_data = {
            'currency': 'USD',
            'rate_structure': {
                'type': 'tiered',
                'tiers': [
                    {'name': 'Tier 1', 'min_kwh': 0, 'max_kwh': 400, 'price': 0.32},
                    {'name': 'Tier 2', 'min_kwh': 401, 'max_kwh': 800, 'price': 0.40},
                    {'name': 'Tier 3', 'min_kwh': 801, 'max_kwh': None, 'price': 0.50}
                ]
            },
            'taxes_and_fees': {
                'sales_tax': 0.0725
            },
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=1500,
            country_code='US',
            utility_provider='Test Utility',
            tariff_data=tariff_data
        )
        
        # Should use all 3 tiers
        assert len(result['breakdown']['tiers']) == 3
        
        # Tier 1: 400 kWh × $0.32 = $128.00
        # Tier 2: 400 kWh × $0.40 = $160.00
        # Tier 3: 700 kWh × $0.50 = $350.00
        # Total base: $638.00
        assert float(result['base_charge']) == pytest.approx(638.00, rel=0.01)


class TestCurrencyFormatting:
    """Test that currency formatting is correct for each region"""
    
    def test_spain_euro_formatting(self):
        """Test Spain bill uses EUR currency"""
        tariff_data = {
            'currency': 'EUR',
            'rate_structure': {'type': 'flat', 'rate': 0.30},
            'taxes_and_fees': {},
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='ES',
            utility_provider='Iberdrola',
            tariff_data=tariff_data
        )
        
        assert result['currency'] == 'EUR'
        # Verify decimal precision (2 places)
        assert result['total_fiat'].as_tuple().exponent == -2
    
    def test_usa_dollar_formatting(self):
        """Test USA bill uses USD currency"""
        tariff_data = {
            'currency': 'USD',
            'rate_structure': {'type': 'flat', 'rate': 0.30},
            'taxes_and_fees': {},
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='US',
            utility_provider='PG&E',
            tariff_data=tariff_data
        )
        
        assert result['currency'] == 'USD'

    
    def test_india_rupee_formatting(self):
        """Test India bill uses INR currency"""
        tariff_data = {
            'currency': 'INR',
            'rate_structure': {'type': 'flat', 'rate': 5.00},
            'taxes_and_fees': {},
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='IN',
            utility_provider='Tata Power',
            tariff_data=tariff_data
        )
        
        assert result['currency'] == 'INR'
    
    def test_brazil_real_formatting(self):
        """Test Brazil bill uses BRL currency"""
        tariff_data = {
            'currency': 'BRL',
            'rate_structure': {'type': 'flat', 'rate': 0.60},
            'taxes_and_fees': {},
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='BR',
            utility_provider='Enel',
            tariff_data=tariff_data
        )
        
        assert result['currency'] == 'BRL'
    
    def test_nigeria_naira_formatting(self):
        """Test Nigeria bill uses NGN currency"""
        tariff_data = {
            'currency': 'NGN',
            'rate_structure': {
                'type': 'band_based',
                'bands': [{'name': 'C', 'hours_min': 12, 'price': 50.00}]
            },
            'taxes_and_fees': {},
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='NG',
            utility_provider='IKEDP',
            tariff_data=tariff_data,
            band_classification='C'
        )
        
        assert result['currency'] == 'NGN'


class TestBreakdownStructure:
    """Test that itemized breakdown structure is correct for each region"""
    
    def test_spain_breakdown_has_periods(self):
        """Test Spain breakdown includes time-of-use periods"""
        tariff_data = {
            'currency': 'EUR',
            'rate_structure': {
                'type': 'time_of_use',
                'periods': [
                    {'name': 'peak', 'hours': [10,11,12,13], 'price': 0.40},
                    {'name': 'off_peak', 'hours': [0,1,2,3], 'price': 0.15}
                ]
            },
            'taxes_and_fees': {'vat': 0.21},
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='ES',
            utility_provider='Iberdrola',
            tariff_data=tariff_data
        )
        
        assert 'breakdown' in result
        assert 'periods' in result['breakdown']
        assert len(result['breakdown']['periods']) == 2
        assert 'taxes_and_fees' in result['breakdown']

    
    def test_usa_breakdown_has_tiers(self):
        """Test USA breakdown includes tiered structure"""
        tariff_data = {
            'currency': 'USD',
            'rate_structure': {
                'type': 'tiered',
                'tiers': [
                    {'name': 'Tier 1', 'min_kwh': 0, 'max_kwh': 400, 'price': 0.32}
                ]
            },
            'taxes_and_fees': {'sales_tax': 0.0725},
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=300,
            country_code='US',
            utility_provider='PG&E',
            tariff_data=tariff_data
        )
        
        assert 'breakdown' in result
        assert 'tiers' in result['breakdown']
        assert len(result['breakdown']['tiers']) >= 1
    
    def test_nigeria_breakdown_has_band(self):
        """Test Nigeria breakdown includes band classification"""
        tariff_data = {
            'currency': 'NGN',
            'rate_structure': {
                'type': 'band_based',
                'bands': [{'name': 'C', 'hours_min': 12, 'price': 50.00}]
            },
            'taxes_and_fees': {'vat': 0.075},
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='NG',
            utility_provider='IKEDP',
            tariff_data=tariff_data,
            band_classification='C'
        )
        
        assert 'breakdown' in result
        assert 'band' in result['breakdown']
        assert result['breakdown']['band']['classification'] == 'C'
        assert result['breakdown']['band']['hours_min'] == 12


class TestPlatformFees:
    """Test platform service charge calculations across regions"""
    
    def test_platform_fee_included_by_default(self):
        """Test that 3% platform fee is included by default"""
        tariff_data = {
            'currency': 'USD',
            'rate_structure': {'type': 'flat', 'rate': 0.30},
            'taxes_and_fees': {},
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='US',
            utility_provider='Test',
            tariff_data=tariff_data,
            include_platform_fee=True
        )
        
        # Platform fee should be 3% of subtotal
        assert float(result['platform_service_charge']) > 0
        # Platform VAT should also be present
        assert float(result['platform_vat']) > 0
    
    def test_platform_fee_excluded_when_disabled(self):
        """Test that platform fee can be excluded"""
        tariff_data = {
            'currency': 'USD',
            'rate_structure': {'type': 'flat', 'rate': 0.30},
            'taxes_and_fees': {},
            'subsidies': {}
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='US',
            utility_provider='Test',
            tariff_data=tariff_data,
            include_platform_fee=False
        )
        
        # Platform fees should be zero
        assert float(result['platform_service_charge']) == 0.00
        assert float(result['platform_vat']) == 0.00
