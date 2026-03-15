-- ============================================================================
-- NIGERIA DISCOS SEED DATA
-- Task 2.3.1: All 11 Nigerian Distribution Companies with State Coverage
-- Requirements: US-2, FR-4.1
-- ============================================================================

-- AEDC - Abuja Electricity Distribution Company
INSERT INTO tariffs (
    country_code, region, utility_provider, currency,
    rate_structure, taxes_and_fees, subsidies,
    valid_from, valid_until, is_active
) VALUES (
    'NG',
    'FCT, Kogi, Nasarawa, Niger',
    'AEDC',
    'NGN',
    '{
        "type": "band_based",
        "bands": [
            {"name": "A", "hours_min": 20, "price": 225.00},
            {"name": "B", "hours_min": 16, "price": 63.30},
            {"name": "C", "hours_min": 12, "price": 50.00},
            {"name": "D", "hours_min": 8, "price": 43.00},
            {"name": "E", "hours_min": 4, "price": 40.00}
        ]
    }'::jsonb,
    '{"vat": 0.075, "service_charge": 1500}'::jsonb,
    '{}'::jsonb,
    '2024-01-01', NULL, TRUE
) ON CONFLICT DO NOTHING;

-- BEDC - Benin Electricity Distribution Company
INSERT INTO tariffs (
    country_code, region, utility_provider, currency,
    rate_structure, taxes_and_fees, subsidies,
    valid_from, valid_until, is_active
) VALUES (
    'NG',
    'Edo, Delta, Ondo, Ekiti',
    'BEDC',
    'NGN',
    '{
        "type": "band_based",
        "bands": [
            {"name": "A", "hours_min": 20, "price": 225.00},
            {"name": "B", "hours_min": 16, "price": 63.30},
            {"name": "C", "hours_min": 12, "price": 50.00},
            {"name": "D", "hours_min": 8, "price": 43.00},
            {"name": "E", "hours_min": 4, "price": 40.00}
        ]
    }'::jsonb,
    '{"vat": 0.075, "service_charge": 1500}'::jsonb,
    '{}'::jsonb,
    '2024-01-01', NULL, TRUE
) ON CONFLICT DO NOTHING;

-- EKEDP - Eko Electricity Distribution Company
INSERT INTO tariffs (
    country_code, region, utility_provider, currency,
    rate_structure, taxes_and_fees, subsidies,
    valid_from, valid_until, is_active
) VALUES (
    'NG',
    'Lagos (Mainland)',
    'EKEDP',
    'NGN',
    '{
        "type": "band_based",
        "bands": [
            {"name": "A", "hours_min": 20, "price": 225.00},
            {"name": "B", "hours_min": 16, "price": 63.30},
            {"name": "C", "hours_min": 12, "price": 50.00},
            {"name": "D", "hours_min": 8, "price": 43.00},
            {"name": "E", "hours_min": 4, "price": 40.00}
        ]
    }'::jsonb,
    '{"vat": 0.075, "service_charge": 1500}'::jsonb,
    '{}'::jsonb,
    '2024-01-01', NULL, TRUE
) ON CONFLICT DO NOTHING;

-- EEDC - Enugu Electricity Distribution Company
INSERT INTO tariffs (
    country_code, region, utility_provider, currency,
    rate_structure, taxes_and_fees, subsidies,
    valid_from, valid_until, is_active
) VALUES (
    'NG',
    'Enugu, Abia, Anambra, Ebonyi, Imo',
    'EEDC',
    'NGN',
    '{
        "type": "band_based",
        "bands": [
            {"name": "A", "hours_min": 20, "price": 225.00},
            {"name": "B", "hours_min": 16, "price": 63.30},
            {"name": "C", "hours_min": 12, "price": 50.00},
            {"name": "D", "hours_min": 8, "price": 43.00},
            {"name": "E", "hours_min": 4, "price": 40.00}
        ]
    }'::jsonb,
    '{"vat": 0.075, "service_charge": 1500}'::jsonb,
    '{}'::jsonb,
    '2024-01-01', NULL, TRUE
) ON CONFLICT DO NOTHING;

-- IBEDC - Ibadan Electricity Distribution Company
INSERT INTO tariffs (
    country_code, region, utility_provider, currency,
    rate_structure, taxes_and_fees, subsidies,
    valid_from, valid_until, is_active
) VALUES (
    'NG',
    'Oyo, Osun, Ogun, Kwara',
    'IBEDC',
    'NGN',
    '{
        "type": "band_based",
        "bands": [
            {"name": "A", "hours_min": 20, "price": 225.00},
            {"name": "B", "hours_min": 16, "price": 63.30},
            {"name": "C", "hours_min": 12, "price": 50.00},
            {"name": "D", "hours_min": 8, "price": 43.00},
            {"name": "E", "hours_min": 4, "price": 40.00}
        ]
    }'::jsonb,
    '{"vat": 0.075, "service_charge": 1500}'::jsonb,
    '{}'::jsonb,
    '2024-01-01', NULL, TRUE
) ON CONFLICT DO NOTHING;

-- IKEDC - Ikeja Electricity Distribution Company
INSERT INTO tariffs (
    country_code, region, utility_provider, currency,
    rate_structure, taxes_and_fees, subsidies,
    valid_from, valid_until, is_active
) VALUES (
    'NG',
    'Lagos (Island & Ikeja)',
    'IKEDC',
    'NGN',
    '{
        "type": "band_based",
        "bands": [
            {"name": "A", "hours_min": 20, "price": 225.00},
            {"name": "B", "hours_min": 16, "price": 63.30},
            {"name": "C", "hours_min": 12, "price": 50.00},
            {"name": "D", "hours_min": 8, "price": 43.00},
            {"name": "E", "hours_min": 4, "price": 40.00}
        ]
    }'::jsonb,
    '{"vat": 0.075, "service_charge": 1500}'::jsonb,
    '{}'::jsonb,
    '2024-01-01', NULL, TRUE
) ON CONFLICT DO NOTHING;

-- JEDC - Jos Electricity Distribution Company
INSERT INTO tariffs (
    country_code, region, utility_provider, currency,
    rate_structure, taxes_and_fees, subsidies,
    valid_from, valid_until, is_active
) VALUES (
    'NG',
    'Plateau, Bauchi, Gombe, Benue',
    'JEDC',
    'NGN',
    '{
        "type": "band_based",
        "bands": [
            {"name": "A", "hours_min": 20, "price": 225.00},
            {"name": "B", "hours_min": 16, "price": 63.30},
            {"name": "C", "hours_min": 12, "price": 50.00},
            {"name": "D", "hours_min": 8, "price": 43.00},
            {"name": "E", "hours_min": 4, "price": 40.00}
        ]
    }'::jsonb,
    '{"vat": 0.075, "service_charge": 1500}'::jsonb,
    '{}'::jsonb,
    '2024-01-01', NULL, TRUE
) ON CONFLICT DO NOTHING;

-- KAEDCO - Kaduna Electricity Distribution Company
INSERT INTO tariffs (
    country_code, region, utility_provider, currency,
    rate_structure, taxes_and_fees, subsidies,
    valid_from, valid_until, is_active
) VALUES (
    'NG',
    'Kaduna, Kebbi, Sokoto, Zamfara',
    'KAEDCO',
    'NGN',
    '{
        "type": "band_based",
        "bands": [
            {"name": "A", "hours_min": 20, "price": 225.00},
            {"name": "B", "hours_min": 16, "price": 63.30},
            {"name": "C", "hours_min": 12, "price": 50.00},
            {"name": "D", "hours_min": 8, "price": 43.00},
            {"name": "E", "hours_min": 4, "price": 40.00}
        ]
    }'::jsonb,
    '{"vat": 0.075, "service_charge": 1500}'::jsonb,
    '{}'::jsonb,
    '2024-01-01', NULL, TRUE
) ON CONFLICT DO NOTHING;

-- KEDCO - Kano Electricity Distribution Company
INSERT INTO tariffs (
    country_code, region, utility_provider, currency,
    rate_structure, taxes_and_fees, subsidies,
    valid_from, valid_until, is_active
) VALUES (
    'NG',
    'Kano, Jigawa, Katsina',
    'KEDCO',
    'NGN',
    '{
        "type": "band_based",
        "bands": [
            {"name": "A", "hours_min": 20, "price": 225.00},
            {"name": "B", "hours_min": 16, "price": 63.30},
            {"name": "C", "hours_min": 12, "price": 50.00},
            {"name": "D", "hours_min": 8, "price": 43.00},
            {"name": "E", "hours_min": 4, "price": 40.00}
        ]
    }'::jsonb,
    '{"vat": 0.075, "service_charge": 1500}'::jsonb,
    '{}'::jsonb,
    '2024-01-01', NULL, TRUE
) ON CONFLICT DO NOTHING;

-- PHED - Port Harcourt Electricity Distribution Company
INSERT INTO tariffs (
    country_code, region, utility_provider, currency,
    rate_structure, taxes_and_fees, subsidies,
    valid_from, valid_until, is_active
) VALUES (
    'NG',
    'Rivers, Bayelsa, Cross River, Akwa Ibom',
    'PHED',
    'NGN',
    '{
        "type": "band_based",
        "bands": [
            {"name": "A", "hours_min": 20, "price": 225.00},
            {"name": "B", "hours_min": 16, "price": 63.30},
            {"name": "C", "hours_min": 12, "price": 50.00},
            {"name": "D", "hours_min": 8, "price": 43.00},
            {"name": "E", "hours_min": 4, "price": 40.00}
        ]
    }'::jsonb,
    '{"vat": 0.075, "service_charge": 1500}'::jsonb,
    '{}'::jsonb,
    '2024-01-01', NULL, TRUE
) ON CONFLICT DO NOTHING;

-- YEDC - Yola Electricity Distribution Company
INSERT INTO tariffs (
    country_code, region, utility_provider, currency,
    rate_structure, taxes_and_fees, subsidies,
    valid_from, valid_until, is_active
) VALUES (
    'NG',
    'Adamawa, Borno, Taraba, Yobe',
    'YEDC',
    'NGN',
    '{
        "type": "band_based",
        "bands": [
            {"name": "A", "hours_min": 20, "price": 225.00},
            {"name": "B", "hours_min": 16, "price": 63.30},
            {"name": "C", "hours_min": 12, "price": 50.00},
            {"name": "D", "hours_min": 8, "price": 43.00},
            {"name": "E", "hours_min": 4, "price": 40.00}
        ]
    }'::jsonb,
    '{"vat": 0.075, "service_charge": 1500}'::jsonb,
    '{}'::jsonb,
    '2024-01-01', NULL, TRUE
) ON CONFLICT DO NOTHING;

-- Verification Query
SELECT 
    utility_provider,
    region,
    currency,
    is_active
FROM tariffs
WHERE country_code = 'NG'
ORDER BY utility_provider;

-- Success Message
DO $$
BEGIN
    RAISE NOTICE '✓ Successfully seeded 11 Nigerian DisCos with state coverage!';
END $$;
