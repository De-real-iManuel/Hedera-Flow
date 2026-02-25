"""
Billing calculation service for Hedera Flow MVP

Implements regional tariff-based billing calculations for:
- Spain (ES): Time-of-use rates
- USA (US): Tiered rates
- India (IN): Tiered rates
- Brazil (BR): Tiered rates
- Nigeria (NG): Band-based tiered rates

Requirements: FR-4.1, FR-4.2, US-5
"""
from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.services.tariff_service import get_tariff, TariffNotFoundError

logger = logging.getLogger(__name__)


class BillingCalculationError(Exception):
    """Raised when billing calculation fails"""
    pass


def calculate_bill_with_tariff_fetch(
    db: Session,
    consumption_kwh: float,
    country_code: str,
    utility_provider: str,
    band_classification: Optional[str] = None,
    hourly_consumption: Optional[Dict[int, float]] = None,
    include_platform_fee: bool = True,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Calculate electricity bill by fetching tariff from database/cache.
    
    This is a convenience function that combines tariff fetching and bill calculation.
    
    Args:
        db: Database session
        consumption_kwh: Total electricity consumption in kWh
        country_code: Country code (ES, US, IN, BR, NG)
        utility_provider: Name of utility provider
        band_classification: Nigeria band classification (A, B, C, D, E) - required for NG
        hourly_consumption: Hourly consumption breakdown for time-of-use (optional for ES)
        include_platform_fee: Whether to include 3% platform service charge (default: True)
        use_cache: Whether to use Redis cache for tariff (default: True)
    
    Returns:
        Dictionary containing bill calculation results (same as calculate_bill)
    
    Raises:
        BillingCalculationError: If calculation fails
        TariffNotFoundError: If no active tariff found
    """
    try:
        # Fetch tariff from database/cache
        tariff_data = get_tariff(
            db=db,
            country_code=country_code,
            utility_provider=utility_provider,
            use_cache=use_cache
        )
        
        # Calculate bill using fetched tariff
        return calculate_bill(
            consumption_kwh=consumption_kwh,
            country_code=country_code,
            utility_provider=utility_provider,
            tariff_data=tariff_data,
            band_classification=band_classification,
            hourly_consumption=hourly_consumption,
            include_platform_fee=include_platform_fee
        )
        
    except TariffNotFoundError:
        raise
    except BillingCalculationError:
        raise
    except Exception as e:
        logger.error(f"Bill calculation with tariff fetch error: {e}", exc_info=True)
        raise BillingCalculationError(f"Failed to calculate bill: {str(e)}")


def calculate_bill(
    consumption_kwh: float,
    country_code: str,
    utility_provider: str,
    tariff_data: Dict[str, Any],
    band_classification: Optional[str] = None,
    hourly_consumption: Optional[Dict[int, float]] = None,
    include_platform_fee: bool = True
) -> Dict[str, Any]:
    """
    Calculate electricity bill based on regional tariff structure.
    
    Args:
        consumption_kwh: Total electricity consumption in kWh
        country_code: Country code (ES, US, IN, BR, NG)
        utility_provider: Name of utility provider
        tariff_data: Tariff structure from database (rate_structure, taxes_and_fees, subsidies)
        band_classification: Nigeria band classification (A, B, C, D, E) - required for NG
        hourly_consumption: Hourly consumption breakdown for time-of-use (optional for ES)
        include_platform_fee: Whether to include 3% platform service charge (default: True)
    
    Returns:
        Dictionary containing:
            - consumption_kwh: Total consumption
            - base_charge: Charge before taxes
            - utility_taxes: Utility taxes and fees
            - subsidies: Total subsidies applied
            - subtotal: Base + utility taxes - subsidies
            - platform_service_charge: 3% platform fee
            - platform_vat: VAT on platform service charge
            - total_fiat: Final bill amount
            - currency: Currency code
            - breakdown: Itemized breakdown of charges
    
    Raises:
        BillingCalculationError: If calculation fails or invalid parameters
    """
    try:
        # Validate inputs
        if consumption_kwh < 0:
            raise BillingCalculationError("Consumption cannot be negative")
        
        if country_code not in ['ES', 'US', 'IN', 'BR', 'NG']:
            raise BillingCalculationError(f"Unsupported country code: {country_code}")
        
        # Extract tariff components
        rate_structure = tariff_data.get('rate_structure', {})
        taxes_and_fees = tariff_data.get('taxes_and_fees', {})
        subsidies = tariff_data.get('subsidies', {})
        currency = tariff_data.get('currency', 'USD')
        
        rate_type = rate_structure.get('type')
        
        # Calculate base charge based on rate structure type
        if rate_type == 'flat':
            base_charge, breakdown = _calculate_flat(
                consumption_kwh,
                rate_structure
            )
        elif rate_type == 'time_of_use':
            base_charge, breakdown = _calculate_time_of_use(
                consumption_kwh, 
                rate_structure, 
                hourly_consumption
            )
        elif rate_type == 'tiered':
            base_charge, breakdown = _calculate_tiered(
                consumption_kwh, 
                rate_structure
            )
        elif rate_type == 'band_based':
            if not band_classification:
                raise BillingCalculationError("Band classification required for Nigeria")
            base_charge, breakdown = _calculate_band_based(
                consumption_kwh, 
                rate_structure, 
                band_classification
            )
        else:
            raise BillingCalculationError(f"Unknown rate structure type: {rate_type}")
        
        # Calculate utility taxes and fees
        utility_taxes = _calculate_taxes_and_fees(base_charge, taxes_and_fees, breakdown)
        
        # Calculate subsidies (if any)
        subsidies_total = _calculate_subsidies(base_charge, subsidies)
        
        # Calculate subtotal (base + utility taxes - subsidies)
        subtotal = Decimal(str(base_charge)) + Decimal(str(utility_taxes)) - Decimal(str(subsidies_total))
        
        # Ensure non-negative subtotal
        if subtotal < 0:
            subtotal = Decimal('0.00')
        
        # Calculate platform service charge (3% of subtotal)
        platform_service_charge = Decimal('0.00')
        platform_vat = Decimal('0.00')
        
        if include_platform_fee:
            platform_service_charge = subtotal * Decimal('0.03')
            # VAT on platform service charge (use country-specific VAT rate)
            vat_rate = taxes_and_fees.get('vat', 0.075)  # Default to 7.5% if not specified
            platform_vat = platform_service_charge * Decimal(str(vat_rate))
        
        # Calculate final total
        total_fiat = subtotal + platform_service_charge + platform_vat
        
        return {
            'consumption_kwh': Decimal(str(consumption_kwh)),
            'base_charge': Decimal(str(base_charge)).quantize(Decimal('0.01')),
            'utility_taxes': Decimal(str(utility_taxes)).quantize(Decimal('0.01')),
            'subsidies': Decimal(str(subsidies_total)).quantize(Decimal('0.01')),
            'subtotal': Decimal(str(subtotal)).quantize(Decimal('0.01')),
            'platform_service_charge': platform_service_charge.quantize(Decimal('0.01')),
            'platform_vat': platform_vat.quantize(Decimal('0.01')),
            'total_fiat': Decimal(str(total_fiat)).quantize(Decimal('0.01')),
            'currency': currency,
            'breakdown': breakdown,
            'tariff_type': rate_type,
            'utility_provider': utility_provider,
            'country_code': country_code
        }
        
    except BillingCalculationError:
        raise
    except Exception as e:
        logger.error(f"Billing calculation error: {e}", exc_info=True)
        raise BillingCalculationError(f"Failed to calculate bill: {str(e)}")


def _calculate_time_of_use(
    consumption_kwh: float,
    rate_structure: Dict[str, Any],
    hourly_consumption: Optional[Dict[int, float]] = None
) -> tuple[float, Dict[str, Any]]:
    """
    Calculate bill for time-of-use rate structure (Spain).
    
    If hourly_consumption is provided, uses actual hourly breakdown.
    Otherwise, estimates based on typical consumption patterns.
    """
    periods = rate_structure.get('periods', [])
    
    if not periods:
        raise BillingCalculationError("No periods defined in time-of-use structure")
    
    breakdown = {
        'rate_type': 'time_of_use',
        'periods': []
    }
    
    total_charge = 0.0
    
    if hourly_consumption:
        # Use actual hourly consumption
        for period in periods:
            period_name = period['name']
            period_hours = period['hours']
            period_price = period['price']
            
            period_consumption = sum(
                hourly_consumption.get(hour, 0) 
                for hour in period_hours
            )
            period_charge = period_consumption * period_price
            
            breakdown['periods'].append({
                'name': period_name,
                'hours': period_hours,
                'consumption_kwh': round(period_consumption, 2),
                'price_per_kwh': period_price,
                'charge': round(period_charge, 2)
            })
            
            total_charge += period_charge
    else:
        # Estimate based on typical patterns
        # Peak: 30%, Standard: 40%, Off-peak: 30%
        distribution = {
            'peak': 0.30,
            'standard': 0.40,
            'off_peak': 0.30
        }
        
        for period in periods:
            period_name = period['name']
            period_price = period['price']
            
            # Use distribution or default to equal split
            period_ratio = distribution.get(period_name, 1.0 / len(periods))
            period_consumption = consumption_kwh * period_ratio
            period_charge = period_consumption * period_price
            
            breakdown['periods'].append({
                'name': period_name,
                'consumption_kwh': round(period_consumption, 2),
                'price_per_kwh': period_price,
                'charge': round(period_charge, 2),
                'estimated': True
            })
            
            total_charge += period_charge
    
    return total_charge, breakdown


def _calculate_tiered(
    consumption_kwh: float,
    rate_structure: Dict[str, Any]
) -> tuple[float, Dict[str, Any]]:
    """
    Calculate bill for tiered rate structure (USA, India, Brazil).
    
    Tiers are defined with min_kwh and max_kwh (inclusive).
    For example:
    - Tier 1: 0-400 means 0 to 400 kWh (400 kWh total)
    - Tier 2: 401-800 means 401 to 800 kWh (400 kWh total)
    """
    tiers = rate_structure.get('tiers', [])
    
    if not tiers:
        raise BillingCalculationError("No tiers defined in tiered structure")
    
    breakdown = {
        'rate_type': 'tiered',
        'tiers': []
    }
    
    total_charge = 0.0
    consumed_so_far = 0.0
    
    for tier in tiers:
        tier_name = tier['name']
        tier_min = tier['min_kwh']
        tier_max = tier.get('max_kwh')  # None means unlimited
        tier_price = tier['price']
        
        # Calculate how much consumption falls in this tier
        if consumption_kwh <= consumed_so_far:
            # No consumption in this tier
            break
        
        if tier_max is None:
            # Unlimited tier (last tier) - all remaining consumption
            tier_consumption = consumption_kwh - consumed_so_far
        else:
            # Calculate consumption in this tier
            # Consumption in tier = min(remaining, tier_max) - consumed_so_far
            tier_consumption = min(consumption_kwh, tier_max) - consumed_so_far
        
        if tier_consumption > 0:
            tier_charge = tier_consumption * tier_price
            
            breakdown['tiers'].append({
                'name': tier_name,
                'min_kwh': tier_min,
                'max_kwh': tier_max,
                'consumption_kwh': round(tier_consumption, 2),
                'price_per_kwh': tier_price,
                'charge': round(tier_charge, 2)
            })
            
            total_charge += tier_charge
            consumed_so_far += tier_consumption
    
    return total_charge, breakdown


def _calculate_flat(
    consumption_kwh: float,
    rate_structure: Dict[str, Any]
) -> tuple[float, Dict[str, Any]]:
    """
    Calculate bill for flat rate structure.
    
    Flat rate: consumption × rate
    Simple calculation where all kWh are charged at the same rate.
    
    Args:
        consumption_kwh: Total electricity consumption in kWh
        rate_structure: Rate structure containing 'rate' field
    
    Returns:
        Tuple of (total_charge, breakdown)
    
    Raises:
        BillingCalculationError: If rate is not defined
    """
    rate = rate_structure.get('rate')
    
    if rate is None:
        raise BillingCalculationError("No rate defined in flat rate structure")
    
    if rate < 0:
        raise BillingCalculationError("Rate cannot be negative")
    
    total_charge = consumption_kwh * rate
    
    breakdown = {
        'rate_type': 'flat',
        'rate_per_kwh': rate,
        'consumption_kwh': round(consumption_kwh, 2),
        'charge': round(total_charge, 2)
    }
    
    return total_charge, breakdown


def _calculate_band_based(
    consumption_kwh: float,
    rate_structure: Dict[str, Any],
    band_classification: str
) -> tuple[float, Dict[str, Any]]:
    """
    Calculate bill for band-based rate structure (Nigeria).
    
    Band classification determines the rate per kWh based on hours of supply.
    """
    bands = rate_structure.get('bands', [])
    
    if not bands:
        raise BillingCalculationError("No bands defined in band-based structure")
    
    # Find the band matching the classification
    band_data = None
    for band in bands:
        if band['name'] == band_classification:
            band_data = band
            break
    
    if not band_data:
        raise BillingCalculationError(f"Invalid band classification: {band_classification}")
    
    band_price = band_data['price']
    total_charge = consumption_kwh * band_price
    
    breakdown = {
        'rate_type': 'band_based',
        'band': {
            'classification': band_classification,
            'hours_min': band_data['hours_min'],
            'consumption_kwh': round(consumption_kwh, 2),
            'price_per_kwh': band_price,
            'charge': round(total_charge, 2)
        }
    }
    
    return total_charge, breakdown


def _calculate_taxes_and_fees(
    base_charge: float,
    taxes_and_fees: Dict[str, Any],
    breakdown: Dict[str, Any]
) -> float:
    """
    Calculate total taxes and fees.
    
    Supports:
    - VAT (percentage of base charge)
    - Sales tax (percentage of base charge)
    - Distribution charge (per kWh)
    - Fixed monthly fees
    - Service charges
    """
    total_taxes = 0.0
    tax_breakdown = []
    
    # VAT (Spain, India, Nigeria)
    if 'vat' in taxes_and_fees:
        vat_rate = taxes_and_fees['vat']
        vat_amount = base_charge * vat_rate
        total_taxes += vat_amount
        tax_breakdown.append({
            'name': 'VAT',
            'rate': vat_rate,
            'amount': round(vat_amount, 2)
        })
    
    # Sales tax (USA)
    if 'sales_tax' in taxes_and_fees:
        sales_tax_rate = taxes_and_fees['sales_tax']
        sales_tax_amount = base_charge * sales_tax_rate
        total_taxes += sales_tax_amount
        tax_breakdown.append({
            'name': 'Sales Tax',
            'rate': sales_tax_rate,
            'amount': round(sales_tax_amount, 2)
        })
    
    # ICMS tax (Brazil)
    if 'icms_tax' in taxes_and_fees:
        icms_rate = taxes_and_fees['icms_tax']
        icms_amount = base_charge * icms_rate
        total_taxes += icms_amount
        tax_breakdown.append({
            'name': 'ICMS Tax',
            'rate': icms_rate,
            'amount': round(icms_amount, 2)
        })
    
    # Distribution charge (Spain - per kWh)
    if 'distribution_charge' in taxes_and_fees:
        dist_rate = taxes_and_fees['distribution_charge']
        # Get total consumption from breakdown
        consumption = _get_total_consumption_from_breakdown(breakdown)
        dist_amount = consumption * dist_rate
        total_taxes += dist_amount
        tax_breakdown.append({
            'name': 'Distribution Charge',
            'rate_per_kwh': dist_rate,
            'amount': round(dist_amount, 2)
        })
    
    # Fixed monthly fee (USA)
    if 'fixed_monthly_fee' in taxes_and_fees:
        fixed_fee = taxes_and_fees['fixed_monthly_fee']
        total_taxes += fixed_fee
        tax_breakdown.append({
            'name': 'Fixed Monthly Fee',
            'amount': round(fixed_fee, 2)
        })
    
    # Service charge (Nigeria)
    if 'service_charge' in taxes_and_fees:
        service_charge = taxes_and_fees['service_charge']
        total_taxes += service_charge
        tax_breakdown.append({
            'name': 'Service Charge',
            'amount': round(service_charge, 2)
        })
    
    # Add tax breakdown to main breakdown
    breakdown['taxes_and_fees'] = tax_breakdown
    
    return total_taxes


def _calculate_subsidies(
    base_charge: float,
    subsidies: Dict[str, Any]
) -> float:
    """
    Calculate total subsidies (if any).
    
    Subsidies reduce the final bill amount.
    """
    # For MVP, subsidies are not implemented
    # This is a placeholder for future enhancement
    return 0.0


def _get_total_consumption_from_breakdown(breakdown: Dict[str, Any]) -> float:
    """
    Extract total consumption from breakdown for per-kWh calculations.
    """
    rate_type = breakdown.get('rate_type')
    
    if rate_type == 'flat':
        return breakdown.get('consumption_kwh', 0)
    elif rate_type == 'time_of_use':
        return sum(
            period['consumption_kwh'] 
            for period in breakdown.get('periods', [])
        )
    elif rate_type == 'tiered':
        return sum(
            tier['consumption_kwh'] 
            for tier in breakdown.get('tiers', [])
        )
    elif rate_type == 'band_based':
        return breakdown.get('band', {}).get('consumption_kwh', 0)
    
    return 0.0
