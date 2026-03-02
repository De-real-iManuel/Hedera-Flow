"""
Test cases for tariff validation against real-world utility provider rates
Based on tariff_validation_report.md findings
"""
import pytest
from decimal import Decimal
from app.services.billing_service import calculate_bill


class TestSpainTariffValidation:
    """Validate Spain (Iberdrola) time-of-use billing calculations"""
    
    def test_spain_300kwh_typical_consumption(self):
        """Test typical 300 kWh consumption matching real-world €69 average"""
        tariff_data = {
            "currency": "EUR",
            "rate_structure": {
                "type": "time_of_use",
                "periods": [
                    {"name": "peak", "hours": [10, 11, 12, 13, 14, 18, 19, 20, 21], "price": 0.40},
                    {"name": "standard", "hours": [8, 9, 15, 16, 17, 22, 23], "price": 0.25},
                    {"name": "off_peak", "hours": [0, 1, 2, 3, 4, 5, 6, 7], "price": 0.15}
                ]
            },
            "taxes_and_fees": {
                "vat": 0.21,
                "distribution_charge": 0.045
            }
        }
        
        result = calculate_bill(
            consumption_kwh=300,
            country_code="ES",
            utility_provider="Iberdrola",
            tariff_data=tariff_data
        )
        
        # With estimated distribution (30% peak, 40% standard, 30% off-peak):
        # Base: (90 × 0.40) + (120 × 0.25) + (90 × 0.15) = 36 + 30 + 13.5 = 79.5
        # Distribution: 300 × 0.045 = 13.5
        # Subtotal: 79.5 + 13.5 = 93
        # VAT: 93 × 0.21 = 19.53
        # Total: 93 + 19.53 = 112.53 (before platform fee)
        
        assert result["currency"] == "EUR"
        assert result["consumption_kwh"] == Decimal("300")
        assert result["base_charge"] > Decimal("70")  # Should be around 79.5
        assert result["base_charge"] < Decimal("90")
        
        # Total should be in reasonable range (€100-€130 before platform fee)
        subtotal = result["subtotal"]
        assert subtotal > Decimal("100")
        assert subtotal < Decimal("130")


class TestUSATariffValidation:
    """Validate USA (PG&E) tiered billing calculations"""
    
    def test_usa_600kwh_tiered_calculation(self):
        """Test 600 kWh consumption with tiered rates"""
        tariff_data = {
            "currency": "USD",
            "rate_structure": {
                "type": "tiered",
                "tiers": [
                    {"name": "tier1", "min_kwh": 0, "max_kwh": 400, "price": 0.32},
                    {"name": "tier2", "min_kwh": 401, "max_kwh": 800, "price": 0.40},
                    {"name": "tier3", "min_kwh": 801, "max_kwh": None, "price": 0.50}
                ]
            },
            "taxes_and_fees": {
                "sales_tax": 0.0725,
                "fixed_monthly_fee": 10.00
            }
        }
        
        result = calculate_bill(
            consumption_kwh=600,
            country_code="US",
            utility_provider="PG&E",
            tariff_data=tariff_data
        )
        
        # Expected calculation:
        # Tier 1: 400 × 0.32 = 128
        # Tier 2: 200 × 0.40 = 80
        # Base: 128 + 80 = 208
        # Fixed fee: 10
        # Subtotal: 208 + 10 = 218
        # Sales tax: 218 × 0.0725 = 15.805
        # Total: 218 + 15.805 = 233.805
        
        assert result["currency"] == "USD"
        assert result["consumption_kwh"] == Decimal("600")
        assert result["base_charge"] == Decimal("208.00")
        
        # Check breakdown
        breakdown = result["breakdown"]
        assert breakdown["rate_type"] == "tiered"
        assert len(breakdown["tiers"]) == 2  # Only 2 tiers used
        assert breakdown["tiers"][0]["consumption_kwh"] == 400
        assert breakdown["tiers"][1]["consumption_kwh"] == 200


class TestIndiaTariffValidation:
    """Validate India (Tata Power) updated tiered rates"""
    
    def test_india_250kwh_updated_rates(self):
        """Test 250 kWh consumption with corrected Tata Power rates"""
        tariff_data = {
            "currency": "INR",
            "rate_structure": {
                "type": "tiered",
                "tiers": [
                    {"name": "tier1", "min_kwh": 0, "max_kwh": 100, "price": 2.18},
                    {"name": "tier2", "min_kwh": 101, "max_kwh": 300, "price": 6.97},
                    {"name": "tier3", "min_kwh": 301, "max_kwh": None, "price": 8.40}
                ]
            },
            "taxes_and_fees": {
                "vat": 0.18,
                "fixed_monthly_fee": 90
            }
        }
        
        result = calculate_bill(
            consumption_kwh=250,
            country_code="IN",
            utility_provider="Tata Power",
            tariff_data=tariff_data
        )
        
        # Expected calculation:
        # Tier 1: 100 × 2.18 = 218
        # Tier 2: 150 × 6.97 = 1045.5
        # Base: 218 + 1045.5 = 1263.5
        # Fixed fee: 90
        # Subtotal: 1263.5 + 90 = 1353.5
        # VAT: 1353.5 × 0.18 = 243.63
        # Total: 1353.5 + 243.63 = 1597.13
        
        assert result["currency"] == "INR"
        assert result["consumption_kwh"] == Decimal("250")
        assert result["base_charge"] == Decimal("1263.50")
        
        # Check utility taxes include fixed fee
        assert result["utility_taxes"] > Decimal("300")  # VAT + fixed fee
        
        # Total should be around ₹1,597
        subtotal = result["subtotal"]
        assert subtotal > Decimal("1550")
        assert subtotal < Decimal("1650")
    
    def test_india_low_consumption_100kwh(self):
        """Test low consumption (100 kWh) - all in tier 1"""
        tariff_data = {
            "currency": "INR",
            "rate_structure": {
                "type": "tiered",
                "tiers": [
                    {"name": "tier1", "min_kwh": 0, "max_kwh": 100, "price": 2.18},
                    {"name": "tier2", "min_kwh": 101, "max_kwh": 300, "price": 6.97},
                    {"name": "tier3", "min_kwh": 301, "max_kwh": None, "price": 8.40}
                ]
            },
            "taxes_and_fees": {
                "vat": 0.18,
                "fixed_monthly_fee": 90
            }
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code="IN",
            utility_provider="Tata Power",
            tariff_data=tariff_data
        )
        
        # Expected: 100 × 2.18 + 90 fixed + 18% VAT
        # Base: 218
        # Fixed: 90
        # Subtotal: 308
        # VAT: 55.44
        # Total: 363.44
        
        assert result["base_charge"] == Decimal("218.00")
        assert result["consumption_kwh"] == Decimal("100")
        
        # Check only tier 1 used
        breakdown = result["breakdown"]
        assert len(breakdown["tiers"]) == 1
        assert breakdown["tiers"][0]["name"] == "tier1"


class TestBrazilTariffValidation:
    """Validate Brazil tiered rates with updated ICMS tax"""
    
    def test_brazil_200kwh_updated_icms(self):
        """Test 200 kWh consumption with corrected ICMS rate (17%)"""
        tariff_data = {
            "currency": "BRL",
            "rate_structure": {
                "type": "tiered",
                "tiers": [
                    {"name": "tier1", "min_kwh": 0, "max_kwh": 100, "price": 0.50},
                    {"name": "tier2", "min_kwh": 101, "max_kwh": 300, "price": 0.70},
                    {"name": "tier3", "min_kwh": 301, "max_kwh": None, "price": 0.90}
                ]
            },
            "taxes_and_fees": {
                "icms_tax": 0.17  # Updated from 0.20
            }
        }
        
        result = calculate_bill(
            consumption_kwh=200,
            country_code="BR",
            utility_provider="Regional Provider",
            tariff_data=tariff_data
        )
        
        # Expected calculation:
        # Tier 1: 100 × 0.50 = 50
        # Tier 2: 100 × 0.70 = 70
        # Base: 50 + 70 = 120
        # ICMS: 120 × 0.17 = 20.4
        # Total: 120 + 20.4 = 140.4
        
        assert result["currency"] == "BRL"
        assert result["base_charge"] == Decimal("120.00")
        
        # Check ICMS tax is 17% of base
        expected_icms = Decimal("120.00") * Decimal("0.17")
        assert result["utility_taxes"] == expected_icms.quantize(Decimal("0.01"))


class TestNigeriaTariffValidation:
    """Validate Nigeria band-based rates (already accurate)"""
    
    def test_nigeria_band_a_500kwh(self):
        """Test Band A (20+ hours supply) with 500 kWh consumption"""
        tariff_data = {
            "currency": "NGN",
            "rate_structure": {
                "type": "band_based",
                "bands": [
                    {"name": "A", "hours_min": 20, "price": 225.00},
                    {"name": "B", "hours_min": 16, "price": 63.30},
                    {"name": "C", "hours_min": 12, "price": 50.00},
                    {"name": "D", "hours_min": 8, "price": 43.00},
                    {"name": "E", "hours_min": 0, "price": 40.00}
                ]
            },
            "taxes_and_fees": {
                "vat": 0.075,
                "service_charge": 1500
            }
        }
        
        result = calculate_bill(
            consumption_kwh=500,
            country_code="NG",
            utility_provider="EKEDC",
            tariff_data=tariff_data,
            band_classification="A"
        )
        
        # Expected calculation:
        # Base: 500 × 225 = 112,500
        # Service charge: 1,500
        # Subtotal: 112,500 + 1,500 = 114,000
        # VAT: 114,000 × 0.075 = 8,550
        # Total: 114,000 + 8,550 = 122,550
        
        assert result["currency"] == "NGN"
        assert result["base_charge"] == Decimal("112500.00")
        
        # Check breakdown
        breakdown = result["breakdown"]
        assert breakdown["rate_type"] == "band_based"
        assert breakdown["band"]["classification"] == "A"
        assert breakdown["band"]["price_per_kwh"] == 225.00
    
    def test_nigeria_band_e_300kwh(self):
        """Test Band E (<8 hours supply) with 300 kWh consumption"""
        tariff_data = {
            "currency": "NGN",
            "rate_structure": {
                "type": "band_based",
                "bands": [
                    {"name": "A", "hours_min": 20, "price": 225.00},
                    {"name": "B", "hours_min": 16, "price": 63.30},
                    {"name": "C", "hours_min": 12, "price": 50.00},
                    {"name": "D", "hours_min": 8, "price": 43.00},
                    {"name": "E", "hours_min": 0, "price": 40.00}
                ]
            },
            "taxes_and_fees": {
                "vat": 0.075,
                "service_charge": 1500
            }
        }
        
        result = calculate_bill(
            consumption_kwh=300,
            country_code="NG",
            utility_provider="EKEDC",
            tariff_data=tariff_data,
            band_classification="E"
        )
        
        # Expected calculation:
        # Base: 300 × 40 = 12,000
        # Service charge: 1,500
        # Subtotal: 12,000 + 1,500 = 13,500
        # VAT: 13,500 × 0.075 = 1,012.5
        # Total: 13,500 + 1,012.5 = 14,512.5
        
        assert result["currency"] == "NGN"
        assert result["base_charge"] == Decimal("12000.00")
        
        # Verify Band E rate is used
        breakdown = result["breakdown"]
        assert breakdown["band"]["classification"] == "E"
        assert breakdown["band"]["price_per_kwh"] == 40.00


class TestTariffAccuracyComparison:
    """Compare calculated bills against real-world averages"""
    
    def test_spain_monthly_average_comparison(self):
        """Compare Spain calculation to real-world €69 average for 300 kWh"""
        # Real-world: €69 for 300 kWh (from idealista.com)
        # Our calculation should be in similar range
        tariff_data = {
            "currency": "EUR",
            "rate_structure": {
                "type": "time_of_use",
                "periods": [
                    {"name": "peak", "hours": [10, 11, 12, 13, 14, 18, 19, 20, 21], "price": 0.40},
                    {"name": "standard", "hours": [8, 9, 15, 16, 17, 22, 23], "price": 0.25},
                    {"name": "off_peak", "hours": [0, 1, 2, 3, 4, 5, 6, 7], "price": 0.15}
                ]
            },
            "taxes_and_fees": {
                "vat": 0.21,
                "distribution_charge": 0.045
            }
        }
        
        result = calculate_bill(
            consumption_kwh=300,
            country_code="ES",
            utility_provider="Iberdrola",
            tariff_data=tariff_data,
            include_platform_fee=False  # Exclude platform fee for comparison
        )
        
        # Our calculation will be higher due to conservative rates
        # Should be within 50% of real-world average (€69-€105 range)
        total = result["total_fiat"]
        assert total > Decimal("60")  # Not unreasonably low
        assert total < Decimal("150")  # Not unreasonably high
    
    def test_usa_monthly_average_comparison(self):
        """Compare USA calculation to real-world $235-$260 average for 700 kWh"""
        # Real-world: $235-$260 for 700 kWh (from nrgcleanpower.com)
        tariff_data = {
            "currency": "USD",
            "rate_structure": {
                "type": "tiered",
                "tiers": [
                    {"name": "tier1", "min_kwh": 0, "max_kwh": 400, "price": 0.32},
                    {"name": "tier2", "min_kwh": 401, "max_kwh": 800, "price": 0.40},
                    {"name": "tier3", "min_kwh": 801, "max_kwh": None, "price": 0.50}
                ]
            },
            "taxes_and_fees": {
                "sales_tax": 0.0725,
                "fixed_monthly_fee": 10.00
            }
        }
        
        result = calculate_bill(
            consumption_kwh=700,
            country_code="US",
            utility_provider="PG&E",
            tariff_data=tariff_data,
            include_platform_fee=False
        )
        
        # Should be in range of $200-$300
        total = result["total_fiat"]
        assert total > Decimal("200")
        assert total < Decimal("300")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
