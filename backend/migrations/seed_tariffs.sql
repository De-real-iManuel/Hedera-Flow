-- ============================================================================
-- TARIFF DATA SEEDING SCRIPT
-- Hedera Flow MVP - Regional Tariff Data
-- ============================================================================
-- This script seeds tariff data for all 5 supported regions:
-- - Spain (Iberdrola) - Time-of-Use pricing
-- - USA (PG&E California) - Tiered pricing
-- - India (Tata Power) - Tiered pricing
-- - Brazil (Regional) - Tiered pricing
-- - Nigeria (EKEDC) - Band-based pricing
-- ============================================================================

-- Clear existing tariff data (optional - comment out if you want to keep existing data)
-- DELETE FROM tariffs;

-- ============================================================================
-- SPAIN (ES) - IBERDROLA - TIME-OF-USE PRICING
-- ============================================================================
INSERT INTO tariffs (
    country_code,
    region,
    utility_provider,
    currency,
    rate_structure,
    taxes_and_fees,
    subsidies,
    valid_from,
    valid_until,
    is_active
) VALUES (
    'ES',
    'National',
    'Iberdrola',
    'EUR',
    '{
        "type": "time_of_use",
        "periods": [
            {
                "name": "peak",
                "hours": [10, 11, 12, 13, 14, 18, 19, 20, 21],
                "price": 0.40
            },
            {
                "name": "standard",
                "hours": [8, 9, 15, 16, 17, 22, 23],
                "price": 0.25
            },
            {
                "name": "off_peak",
                "hours": [0, 1, 2, 3, 4, 5, 6, 7],
                "price": 0.15
            }
        ]
    }'::jsonb,
    '{
        "vat": 0.21,
        "distribution_charge": 0.045
    }'::jsonb,
    '{}'::jsonb,
    '2024-01-01',
    NULL,
    TRUE
);

-- ============================================================================
-- USA (US) - PG&E CALIFORNIA - TIERED PRICING
-- ============================================================================
INSERT INTO tariffs (
    country_code,
    region,
    utility_provider,
    currency,
    rate_structure,
    taxes_and_fees,
    subsidies,
    valid_from,
    valid_until,
    is_active
) VALUES (
    'US',
    'California',
    'PG&E',
    'USD',
    '{
        "type": "tiered",
        "tiers": [
            {
                "name": "tier1",
                "min_kwh": 0,
                "max_kwh": 400,
                "price": 0.32
            },
            {
                "name": "tier2",
                "min_kwh": 401,
                "max_kwh": 800,
                "price": 0.40
            },
            {
                "name": "tier3",
                "min_kwh": 801,
                "max_kwh": null,
                "price": 0.50
            }
        ]
    }'::jsonb,
    '{
        "sales_tax": 0.0725,
        "fixed_monthly_fee": 10.00
    }'::jsonb,
    '{}'::jsonb,
    '2024-01-01',
    NULL,
    TRUE
);

-- ============================================================================
-- INDIA (IN) - TATA POWER - TIERED PRICING
-- ============================================================================
INSERT INTO tariffs (
    country_code,
    region,
    utility_provider,
    currency,
    rate_structure,
    taxes_and_fees,
    subsidies,
    valid_from,
    valid_until,
    is_active
) VALUES (
    'IN',
    'National',
    'Tata Power',
    'INR',
    '{
        "type": "tiered",
        "tiers": [
            {
                "name": "tier1",
                "min_kwh": 0,
                "max_kwh": 100,
                "price": 4.50
            },
            {
                "name": "tier2",
                "min_kwh": 101,
                "max_kwh": 300,
                "price": 6.00
            },
            {
                "name": "tier3",
                "min_kwh": 301,
                "max_kwh": null,
                "price": 7.50
            }
        ]
    }'::jsonb,
    '{
        "vat": 0.18
    }'::jsonb,
    '{}'::jsonb,
    '2024-01-01',
    NULL,
    TRUE
);

-- ============================================================================
-- BRAZIL (BR) - REGIONAL PROVIDER - TIERED PRICING
-- ============================================================================
INSERT INTO tariffs (
    country_code,
    region,
    utility_provider,
    currency,
    rate_structure,
    taxes_and_fees,
    subsidies,
    valid_from,
    valid_until,
    is_active
) VALUES (
    'BR',
    'National',
    'Regional Provider',
    'BRL',
    '{
        "type": "tiered",
        "tiers": [
            {
                "name": "tier1",
                "min_kwh": 0,
                "max_kwh": 100,
                "price": 0.50
            },
            {
                "name": "tier2",
                "min_kwh": 101,
                "max_kwh": 300,
                "price": 0.70
            },
            {
                "name": "tier3",
                "min_kwh": 301,
                "max_kwh": null,
                "price": 0.90
            }
        ]
    }'::jsonb,
    '{
        "icms_tax": 0.20
    }'::jsonb,
    '{}'::jsonb,
    '2024-01-01',
    NULL,
    TRUE
);

-- ============================================================================
-- NIGERIA (NG) - EKEDC - BAND-BASED PRICING
-- ============================================================================
INSERT INTO tariffs (
    country_code,
    region,
    utility_provider,
    currency,
    rate_structure,
    taxes_and_fees,
    subsidies,
    valid_from,
    valid_until,
    is_active
) VALUES (
    'NG',
    'National',
    'EKEDC',
    'NGN',
    '{
        "type": "band_based",
        "bands": [
            {
                "name": "A",
                "hours_min": 20,
                "price": 225.00
            },
            {
                "name": "B",
                "hours_min": 16,
                "price": 63.30
            },
            {
                "name": "C",
                "hours_min": 12,
                "price": 50.00
            },
            {
                "name": "D",
                "hours_min": 8,
                "price": 43.00
            },
            {
                "name": "E",
                "hours_min": 0,
                "price": 40.00
            }
        ]
    }'::jsonb,
    '{
        "vat": 0.075,
        "service_charge": 1500
    }'::jsonb,
    '{}'::jsonb,
    '2024-01-01',
    NULL,
    TRUE
);

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================
-- Run this to verify all tariffs were inserted successfully
SELECT 
    country_code,
    utility_provider,
    currency,
    is_active,
    valid_from
FROM tariffs
ORDER BY country_code;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✓ Successfully seeded 5 tariffs for Spain, USA, India, Brazil, and Nigeria!';
END $$;
