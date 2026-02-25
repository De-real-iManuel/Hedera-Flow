"""
Demo script to showcase billing calculations for all 5 regions

Run: python backend/scripts/demo_billing_calculations.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import billing service directly to avoid config dependencies
import importlib.util
spec = importlib.util.spec_from_file_location(
    "billing_service",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                 "app", "services", "billing_service.py")
)
billing_service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(billing_service)

from decimal import Decimal


def print_bill(result, title):
    """Pretty print a bill calculation result"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    print(f"Consumption: {result['consumption_kwh']} kWh")
    print(f"Utility: {result['utility_provider']}")
    print(f"Country: {result['country_code']}")
    print(f"Tariff Type: {result['tariff_type']}")
    print(f"\n--- Charges ---")
    print(f"Base Charge: {result['currency']} {result['base_charge']}")
    print(f"Taxes & Fees: {result['currency']} {result['taxes']}")
    print(f"Subsidies: {result['currency']} {result['subsidies']}")
    print(f"\n--- TOTAL: {result['currency']} {result['total_fiat']} ---")
    
    # Print breakdown
    print(f"\n--- Breakdown ---")
    breakdown = result['breakdown']
    
    if result['tariff_type'] == 'time_of_use':
        for period in breakdown['periods']:
            print(f"  {period['name'].title()}: {period['consumption_kwh']} kWh × "
                  f"{result['currency']} {period['price_per_kwh']} = "
                  f"{result['currency']} {period['charge']}")
    
    elif result['tariff_type'] == 'tiered':
        for tier in breakdown['tiers']:
            print(f"  {tier['name'].title()}: {tier['consumption_kwh']} kWh × "
                  f"{result['currency']} {tier['price_per_kwh']} = "
                  f"{result['currency']} {tier['charge']}")
    
    elif result['tariff_type'] == 'band_based':
        band = breakdown['band']
        print(f"  Band {band['classification']}: {band['consumption_kwh']} kWh × "
              f"{result['currency']} {band['price_per_kwh']} = "
              f"{result['currency']} {band['charge']}")
    
    # Print taxes
    if 'taxes_and_fees' in breakdown:
        print(f"\n--- Taxes & Fees ---")
        for tax in breakdown['taxes_and_fees']:
            if 'rate' in tax:
                print(f"  {tax['name']}: {tax['rate']*100}% = {result['currency']} {tax['amount']}")
            elif 'rate_per_kwh' in tax:
                print(f"  {tax['name']}: {result['currency']} {tax['rate_per_kwh']}/kWh = "
                      f"{result['currency']} {tax['amount']}")
            else:
                print(f"  {tax['name']}: {result['currency']} {tax['amount']}")


def demo_spain():
    """Demo Spain time-of-use billing"""
    tariff_data = {
        'currency': 'EUR',
        'rate_structure': {
            'type': 'time_of_use',
            'periods': [
                {'name': 'peak', 'hours': [10, 11, 12, 13, 14, 18, 19, 20, 21], 'price': 0.40},
                {'name': 'standard', 'hours': [8, 9, 15, 16, 17, 22, 23], 'price': 0.25},
                {'name': 'off_peak', 'hours': [0, 1, 2, 3, 4, 5, 6, 7], 'price': 0.15}
            ]
        },
        'taxes_and_fees': {
            'vat': 0.21,
            'distribution_charge': 0.045
        },
        'subsidies': {}
    }
    
    result = billing_service.calculate_bill(
        consumption_kwh=300,
        country_code='ES',
        utility_provider='Iberdrola',
        tariff_data=tariff_data
    )
    
    print_bill(result, "SPAIN - Time-of-Use Billing (Iberdrola)")


def demo_usa():
    """Demo USA tiered billing"""
    tariff_data = {
        'currency': 'USD',
        'rate_structure': {
            'type': 'tiered',
            'tiers': [
                {'name': 'tier1', 'min_kwh': 0, 'max_kwh': 400, 'price': 0.32},
                {'name': 'tier2', 'min_kwh': 401, 'max_kwh': 800, 'price': 0.40},
                {'name': 'tier3', 'min_kwh': 801, 'max_kwh': None, 'price': 0.50}
            ]
        },
        'taxes_and_fees': {
            'sales_tax': 0.0725,
            'fixed_monthly_fee': 10.00
        },
        'subsidies': {}
    }
    
    result = billing_service.calculate_bill(
        consumption_kwh=900,
        country_code='US',
        utility_provider='PG&E',
        tariff_data=tariff_data
    )
    
    print_bill(result, "USA - Tiered Billing (PG&E California)")


def demo_india():
    """Demo India tiered billing"""
    tariff_data = {
        'currency': 'INR',
        'rate_structure': {
            'type': 'tiered',
            'tiers': [
                {'name': 'tier1', 'min_kwh': 0, 'max_kwh': 100, 'price': 4.50},
                {'name': 'tier2', 'min_kwh': 101, 'max_kwh': 300, 'price': 6.00},
                {'name': 'tier3', 'min_kwh': 301, 'max_kwh': None, 'price': 7.50}
            ]
        },
        'taxes_and_fees': {
            'vat': 0.18
        },
        'subsidies': {}
    }
    
    result = billing_service.calculate_bill(
        consumption_kwh=250,
        country_code='IN',
        utility_provider='Tata Power',
        tariff_data=tariff_data
    )
    
    print_bill(result, "INDIA - Tiered Billing (Tata Power)")


def demo_brazil():
    """Demo Brazil tiered billing"""
    tariff_data = {
        'currency': 'BRL',
        'rate_structure': {
            'type': 'tiered',
            'tiers': [
                {'name': 'tier1', 'min_kwh': 0, 'max_kwh': 100, 'price': 0.50},
                {'name': 'tier2', 'min_kwh': 101, 'max_kwh': 300, 'price': 0.70},
                {'name': 'tier3', 'min_kwh': 301, 'max_kwh': None, 'price': 0.90}
            ]
        },
        'taxes_and_fees': {
            'icms_tax': 0.20
        },
        'subsidies': {}
    }
    
    result = billing_service.calculate_bill(
        consumption_kwh=200,
        country_code='BR',
        utility_provider='Regional Provider',
        tariff_data=tariff_data
    )
    
    print_bill(result, "BRAZIL - Tiered Billing (Regional Provider)")


def demo_nigeria():
    """Demo Nigeria band-based billing"""
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
            'service_charge': 1500
        },
        'subsidies': {}
    }
    
    # Demo Band C
    result = billing_service.calculate_bill(
        consumption_kwh=200,
        country_code='NG',
        utility_provider='EKEDC',
        tariff_data=tariff_data,
        band_classification='C'
    )
    
    print_bill(result, "NIGERIA - Band C Billing (EKEDC Lagos)")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  HEDERA FLOW - BILLING CALCULATION DEMO")
    print("  Showcasing regional tariff support for 5 countries")
    print("="*70)
    
    demo_spain()
    demo_usa()
    demo_india()
    demo_brazil()
    demo_nigeria()
    
    print("\n" + "="*70)
    print("  Demo Complete!")
    print("  All 5 regional billing calculations executed successfully")
    print("="*70 + "\n")
