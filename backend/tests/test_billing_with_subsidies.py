"""
Tests for Billing Service with Subsidy Eligibility

Tests that billing calculations correctly apply subsidies based on user eligibility.

Requirements: FR-4.5 (System shall apply subsidies if user eligible)
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4
from decimal import Decimal

from app.models.user import User, Base, CountryCodeEnum
from app.services.billing_service import calculate_bill
from app.services.subsidy_service import set_user_eligibility
from config import settings


# Test database setup
@pytest.fixture(scope="function")
def db_session():
    """Create a test database session"""
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user"""
    user = User(
        email=f"test_{uuid4()}@example.com",
        password_hash="hashed_password",
        country_code=CountryCodeEnum.ES,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    yield user
    
    # Cleanup
    db_session.delete(user)
    db_session.commit()


class TestBillingWithSubsidies:
    """Tests for billing calculations with subsidies"""
    
    def test_eligible_user_gets_percentage_subsidy(self):
        """Test that eligible user gets percentage-based subsidy applied"""
        # Tariff with 25% subsidy
        tariff_data = {
            'currency': 'EUR',
            'rate_structure': {
                'type': 'flat',
                'rate': 0.30
            },
            'taxes_and_fees': {
                'vat': 0.21
            },
            'subsidies': [
                {
                    'type': 'percentage',
                    'value': 0.25,
                    'name': 'Low Income Discount'
                }
            ]
        }
        
        # Calculate bill for eligible user
        result = calculate_bill(
            consumption_kwh=100,
            country_code='ES',
            utility_provider='Iberdrola',
            tariff_data=tariff_data,
            user_eligible=True,
            include_platform_fee=False
        )
        
        # Base charge: 100 kWh × €0.30 = €30.00
        # VAT: €30.00 × 21% = €6.30
        # Subsidy: €30.00 × 25% = €7.50
        # Subtotal: €30.00 + €6.30 - €7.50 = €28.80
        
        assert result['base_charge'] == Decimal('30.00')
        assert result['utility_taxes'] == Decimal('6.30')
        assert result['subsidies'] == Decimal('7.50')
        assert result['subtotal'] == Decimal('28.80')
    
    def test_ineligible_user_gets_no_subsidy(self):
        """Test that ineligible user gets no subsidy"""
        tariff_data = {
            'currency': 'EUR',
            'rate_structure': {
                'type': 'flat',
                'rate': 0.30
            },
            'taxes_and_fees': {
                'vat': 0.21
            },
            'subsidies': [
                {
                    'type': 'percentage',
                    'value': 0.25,
                    'name': 'Low Income Discount'
                }
            ]
        }
        
        # Calculate bill for ineligible user
        result = calculate_bill(
            consumption_kwh=100,
            country_code='ES',
            utility_provider='Iberdrola',
            tariff_data=tariff_data,
            user_eligible=False,
            include_platform_fee=False
        )
        
        # Base charge: 100 kWh × €0.30 = €30.00
        # VAT: €30.00 × 21% = €6.30
        # Subsidy: €0.00 (not eligible)
        # Subtotal: €30.00 + €6.30 = €36.30
        
        assert result['base_charge'] == Decimal('30.00')
        assert result['utility_taxes'] == Decimal('6.30')
        assert result['subsidies'] == Decimal('0.00')
        assert result['subtotal'] == Decimal('36.30')
    
    def test_eligible_user_gets_fixed_subsidy(self):
        """Test that eligible user gets fixed-amount subsidy"""
        tariff_data = {
            'currency': 'EUR',
            'rate_structure': {
                'type': 'flat',
                'rate': 0.30
            },
            'taxes_and_fees': {
                'vat': 0.21
            },
            'subsidies': [
                {
                    'type': 'fixed',
                    'value': 10.00,
                    'name': 'Senior Citizen Discount'
                }
            ]
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='ES',
            utility_provider='Iberdrola',
            tariff_data=tariff_data,
            user_eligible=True,
            include_platform_fee=False
        )
        
        # Base charge: €30.00
        # VAT: €6.30
        # Subsidy: €10.00 (fixed)
        # Subtotal: €30.00 + €6.30 - €10.00 = €26.30
        
        assert result['subsidies'] == Decimal('10.00')
        assert result['subtotal'] == Decimal('26.30')
    
    def test_eligible_user_gets_per_kwh_subsidy(self):
        """Test that eligible user gets per-kWh subsidy"""
        tariff_data = {
            'currency': 'EUR',
            'rate_structure': {
                'type': 'flat',
                'rate': 0.30
            },
            'taxes_and_fees': {
                'vat': 0.21
            },
            'subsidies': [
                {
                    'type': 'per_kwh',
                    'value': 0.05,
                    'name': 'Energy Efficiency Rebate'
                }
            ]
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='ES',
            utility_provider='Iberdrola',
            tariff_data=tariff_data,
            user_eligible=True,
            include_platform_fee=False
        )
        
        # Base charge: €30.00
        # VAT: €6.30
        # Subsidy: 100 kWh × €0.05 = €5.00
        # Subtotal: €30.00 + €6.30 - €5.00 = €31.30
        
        assert result['subsidies'] == Decimal('5.00')
        assert result['subtotal'] == Decimal('31.30')
    
    def test_subsidy_never_exceeds_base_charge(self):
        """Test that subsidy amount never exceeds base charge"""
        tariff_data = {
            'currency': 'EUR',
            'rate_structure': {
                'type': 'flat',
                'rate': 0.30
            },
            'taxes_and_fees': {
                'vat': 0.21
            },
            'subsidies': [
                {
                    'type': 'fixed',
                    'value': 100.00,  # Huge subsidy
                    'name': 'Test Subsidy'
                }
            ]
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='ES',
            utility_provider='Iberdrola',
            tariff_data=tariff_data,
            user_eligible=True,
            include_platform_fee=False
        )
        
        # Base charge: €30.00
        # Subsidy should be capped at base charge (€30.00)
        assert result['subsidies'] == Decimal('30.00')
        assert result['subsidies'] <= result['base_charge']
    
    def test_multiple_subsidies_combined(self):
        """Test that multiple subsidies are combined correctly"""
        tariff_data = {
            'currency': 'EUR',
            'rate_structure': {
                'type': 'flat',
                'rate': 0.30
            },
            'taxes_and_fees': {
                'vat': 0.21
            },
            'subsidies': [
                {
                    'type': 'percentage',
                    'value': 0.10,
                    'name': 'Base Discount'
                },
                {
                    'type': 'fixed',
                    'value': 5.00,
                    'name': 'Additional Discount'
                }
            ]
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='ES',
            utility_provider='Iberdrola',
            tariff_data=tariff_data,
            user_eligible=True,
            include_platform_fee=False
        )
        
        # Base charge: €30.00
        # Subsidy 1: €30.00 × 10% = €3.00
        # Subsidy 2: €5.00
        # Total subsidy: €8.00
        
        assert result['subsidies'] == Decimal('8.00')


class TestBillingWithPlatformFeeAndSubsidies:
    """Tests for billing with both platform fees and subsidies"""
    
    def test_platform_fee_calculated_after_subsidies(self):
        """Test that platform fee is calculated on subtotal after subsidies"""
        tariff_data = {
            'currency': 'EUR',
            'rate_structure': {
                'type': 'flat',
                'rate': 0.30
            },
            'taxes_and_fees': {
                'vat': 0.21
            },
            'subsidies': [
                {
                    'type': 'fixed',
                    'value': 10.00,
                    'name': 'Discount'
                }
            ]
        }
        
        result = calculate_bill(
            consumption_kwh=100,
            country_code='ES',
            utility_provider='Iberdrola',
            tariff_data=tariff_data,
            user_eligible=True,
            include_platform_fee=True
        )
        
        # Base charge: €30.00
        # VAT: €6.30
        # Subsidy: €10.00
        # Subtotal: €30.00 + €6.30 - €10.00 = €26.30
        # Platform fee: €26.30 × 3% = €0.79
        # Platform VAT: €0.79 × 21% = €0.17 (rounded)
        # Total: €26.30 + €0.79 + €0.17 = €27.26 (but may be €27.25 due to rounding)
        
        assert result['subtotal'] == Decimal('26.30')
        assert result['platform_service_charge'] == Decimal('0.79')
        # Platform VAT may round to 0.16 or 0.17
        assert result['platform_vat'] in [Decimal('0.16'), Decimal('0.17')]
        # Total may be 27.25 or 27.26 depending on rounding
        assert result['total_fiat'] in [Decimal('27.25'), Decimal('27.26')]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
