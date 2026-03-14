"""
Test suite for prepaid token preview endpoint
Tests real-time HBAR equivalent calculation
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from uuid import uuid4

from app.services.prepaid_token_service import PrepaidTokenService


def test_preview_endpoint_calculates_hbar_amount(client, auth_headers, test_meter):
    """
    Test that preview endpoint calculates HBAR amount correctly
    
    Requirements:
        - FR-8.3: System shall calculate kWh units based on current tariff rate
        - US-13: Real-time HBAR equivalent calculation
    """
    # Arrange
    request_data = {
        "meter_id": str(test_meter.id),
        "amount_fiat": 50.0,
        "currency": "EUR",
        "payment_method": "HBAR"
    }
    
    # Mock exchange rate service
    with patch('app.services.exchange_rate_service.ExchangeRateService.get_hbar_rate') as mock_rate:
        mock_rate.return_value = 0.34  # €0.34 per HBAR
        
        # Mock tariff calculation
        with patch.object(PrepaidTokenService, 'calculate_units_from_fiat') as mock_calc:
            mock_calc.return_value = {
                'units_kwh': 125.0,
                'tariff_rate': 0.40,
                'currency': 'EUR'
            }
            
            # Act
            response = client.post(
                "/api/prepaid/preview",
                json=request_data,
                headers=auth_headers
            )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    assert data['amount_fiat'] == 50.0
    assert data['currency'] == 'EUR'
    assert data['amount_hbar'] is not None
    assert abs(data['amount_hbar'] - 147.06) < 0.1  # 50 / 0.34 ≈ 147.06
    assert data['units_kwh'] == 125.0
    assert data['exchange_rate'] == 0.34
    assert data['tariff_rate'] == 0.40


def test_preview_endpoint_calculates_usdc_amount(client, auth_headers, test_meter):
    """
    Test that preview endpoint calculates USDC amount correctly
    """
    # Arrange
    request_data = {
        "meter_id": str(test_meter.id),
        "amount_fiat": 50.0,
        "currency": "USD",
        "payment_method": "USDC"
    }
    
    # Mock tariff calculation
    with patch.object(PrepaidTokenService, 'calculate_units_from_fiat') as mock_calc:
        mock_calc.return_value = {
            'units_kwh': 125.0,
            'tariff_rate': 0.40,
            'currency': 'USD'
        }
        
        # Act
        response = client.post(
            "/api/prepaid/preview",
            json=request_data,
            headers=auth_headers
        )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    assert data['amount_fiat'] == 50.0
    assert data['currency'] == 'USD'
    assert data['amount_usdc'] == 50.0  # 1:1 for USD
    assert data['amount_hbar'] is None
    assert data['units_kwh'] == 125.0


def test_preview_endpoint_updates_on_amount_change(client, auth_headers, test_meter):
    """
    Test that preview recalculates when amount changes (simulating real-time updates)
    """
    # Mock services
    with patch('app.services.exchange_rate_service.ExchangeRateService.get_hbar_rate') as mock_rate:
        mock_rate.return_value = 0.34
        
        with patch.object(PrepaidTokenService, 'calculate_units_from_fiat') as mock_calc:
            # Test with 50 EUR
            mock_calc.return_value = {
                'units_kwh': 125.0,
                'tariff_rate': 0.40,
                'currency': 'EUR'
            }
            
            response1 = client.post(
                "/api/prepaid/preview",
                json={
                    "meter_id": str(test_meter.id),
                    "amount_fiat": 50.0,
                    "currency": "EUR",
                    "payment_method": "HBAR"
                },
                headers=auth_headers
            )
            
            # Test with 100 EUR
            mock_calc.return_value = {
                'units_kwh': 250.0,
                'tariff_rate': 0.40,
                'currency': 'EUR'
            }
            
            response2 = client.post(
                "/api/prepaid/preview",
                json={
                    "meter_id": str(test_meter.id),
                    "amount_fiat": 100.0,
                    "currency": "EUR",
                    "payment_method": "HBAR"
                },
                headers=auth_headers
            )
    
    # Assert both requests succeeded
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Verify amounts doubled
    assert data2['amount_fiat'] == data1['amount_fiat'] * 2
    assert abs(data2['amount_hbar'] - data1['amount_hbar'] * 2) < 0.1
    assert data2['units_kwh'] == data1['units_kwh'] * 2


def test_preview_endpoint_requires_authentication(client, test_meter):
    """Test that preview endpoint requires authentication"""
    response = client.post(
        "/api/prepaid/preview",
        json={
            "meter_id": str(test_meter.id),
            "amount_fiat": 50.0,
            "currency": "EUR",
            "payment_method": "HBAR"
        }
    )
    
    assert response.status_code == 401


def test_preview_endpoint_validates_meter_ownership(client, auth_headers):
    """Test that preview endpoint validates meter belongs to user"""
    # Use a random meter ID that doesn't belong to the user
    random_meter_id = str(uuid4())
    
    response = client.post(
        "/api/prepaid/preview",
        json={
            "meter_id": random_meter_id,
            "amount_fiat": 50.0,
            "currency": "EUR",
            "payment_method": "HBAR"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()['detail'].lower()


def test_preview_endpoint_validates_amount(client, auth_headers, test_meter):
    """Test that preview endpoint validates amount is positive"""
    response = client.post(
        "/api/prepaid/preview",
        json={
            "meter_id": str(test_meter.id),
            "amount_fiat": -50.0,
            "currency": "EUR",
            "payment_method": "HBAR"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


def test_preview_endpoint_handles_exchange_rate_failure(client, auth_headers, test_meter):
    """Test that preview endpoint handles exchange rate service failures gracefully"""
    with patch('app.services.exchange_rate_service.ExchangeRateService.get_hbar_rate') as mock_rate:
        mock_rate.side_effect = Exception("Exchange rate service unavailable")
        
        response = client.post(
            "/api/prepaid/preview",
            json={
                "meter_id": str(test_meter.id),
                "amount_fiat": 50.0,
                "currency": "EUR",
                "payment_method": "HBAR"
            },
            headers=auth_headers
        )
    
    assert response.status_code == 503
    assert "failed to calculate preview" in response.json()['detail'].lower()
