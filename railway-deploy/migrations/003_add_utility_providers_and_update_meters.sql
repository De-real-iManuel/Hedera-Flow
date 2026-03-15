-- Migration 003: Add utility_providers table and update meters table
-- This migration adds the utility_providers table for proper hierarchy
-- and updates the meters table to reference it

-- ============================================================================
-- UTILITY PROVIDERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS utility_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code CHAR(2) NOT NULL,
    state_province VARCHAR(100) NOT NULL,
    provider_name VARCHAR(100) NOT NULL,
    provider_code VARCHAR(20) NOT NULL,
    service_areas TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(country_code, state_province, provider_code)
);

-- Indexes for utility_providers table
CREATE INDEX IF NOT EXISTS idx_utility_providers_country_state ON utility_providers(country_code, state_province);
CREATE INDEX IF NOT EXISTS idx_utility_providers_code ON utility_providers(provider_code);
CREATE INDEX IF NOT EXISTS idx_utility_providers_active ON utility_providers(is_active);

-- ============================================================================
-- UPDATE METERS TABLE
-- ============================================================================
-- Add utility_provider_id column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'meters' AND column_name = 'utility_provider_id'
    ) THEN
        ALTER TABLE meters ADD COLUMN utility_provider_id UUID REFERENCES utility_providers(id);
    END IF;
END $$;

-- Add state_province column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'meters' AND column_name = 'state_province'
    ) THEN
        ALTER TABLE meters ADD COLUMN state_province VARCHAR(100);
    END IF;
END $$;

-- Add index for utility_provider_id
CREATE INDEX IF NOT EXISTS idx_meters_utility_provider ON meters(utility_provider_id);

-- ============================================================================
-- SEED UTILITY PROVIDERS DATA
-- ============================================================================

-- Nigeria (11 Distribution Companies)
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('NG', 'FCT', 'Abuja Electricity Distribution Company', 'AEDC', ARRAY['FCT', 'Kogi', 'Nasarawa', 'Niger']),
('NG', 'Edo', 'Benin Electricity Distribution Company', 'BEDC', ARRAY['Edo', 'Delta', 'Ondo', 'Ekiti']),
('NG', 'Lagos', 'Eko Electricity Distribution Company', 'EKEDP', ARRAY['Southern Lagos', 'Agbara']),
('NG', 'Enugu', 'Enugu Electricity Distribution Company', 'EEDC', ARRAY['Abia', 'Anambra', 'Ebonyi', 'Enugu', 'Imo']),
('NG', 'Oyo', 'Ibadan Electricity Distribution Company', 'IBEDP', ARRAY['Oyo', 'Ogun', 'Osun', 'Kwara', 'Ekiti', 'Kogi']),
('NG', 'Lagos', 'Ikeja Electric', 'IKEDP', ARRAY['Northern Lagos']),
('NG', 'Plateau', 'Jos Electricity Distribution Company', 'JEDC', ARRAY['Bauchi', 'Benue', 'Gombe', 'Plateau']),
('NG', 'Kaduna', 'Kaduna Electric', 'KAEDCO', ARRAY['Kaduna', 'Kebbi', 'Sokoto', 'Zamfara']),
('NG', 'Kano', 'Kano Electricity Distribution Company', 'KEDCO', ARRAY['Kano', 'Katsina', 'Jigawa']),
('NG', 'Rivers', 'Port Harcourt Electricity Distribution Company', 'PHED', ARRAY['Akwa Ibom', 'Bayelsa', 'Cross River', 'Rivers']),
('NG', 'Adamawa', 'Yola Electricity Distribution Company', 'YEDC', ARRAY['Adamawa', 'Borno', 'Taraba', 'Yobe'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

-- USA (State-Level Utilities)
-- California
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('US', 'California', 'Pacific Gas and Electric', 'PGE', ARRAY['Northern California', 'Central California']),
('US', 'California', 'Southern California Edison', 'SCE', ARRAY['Central California', 'Southern California']),
('US', 'California', 'San Diego Gas & Electric', 'SDGE', ARRAY['San Diego County', 'Southern Orange County'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

-- Texas
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('US', 'Texas', 'Oncor Electric Delivery', 'ONCOR', ARRAY['Dallas', 'Fort Worth', 'West Texas']),
('US', 'Texas', 'CenterPoint Energy', 'CENTERPOINT', ARRAY['Houston', 'Galveston']),
('US', 'Texas', 'AEP Texas', 'AEP', ARRAY['Corpus Christi', 'South Texas'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

-- New York
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('US', 'New York', 'Consolidated Edison', 'CONED', ARRAY['New York City', 'Westchester County']),
('US', 'New York', 'National Grid', 'NATIONALGRID', ARRAY['Upstate New York', 'Long Island']),
('US', 'New York', 'New York State Electric & Gas', 'NYSEG', ARRAY['Central New York', 'Southern Tier'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

-- India (State Utilities)
-- Delhi
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('IN', 'Delhi', 'Tata Power Delhi Distribution Limited', 'TPDDL', ARRAY['North Delhi', 'North West Delhi']),
('IN', 'Delhi', 'BSES Rajdhani Power Limited', 'BRPL', ARRAY['South Delhi', 'West Delhi']),
('IN', 'Delhi', 'BSES Yamuna Power Limited', 'BYPL', ARRAY['East Delhi', 'Central Delhi'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

-- Maharashtra
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('IN', 'Maharashtra', 'Maharashtra State Electricity Distribution Co', 'MSEDCL', ARRAY['Maharashtra State']),
('IN', 'Maharashtra', 'Tata Power', 'TATAPOWER', ARRAY['Mumbai']),
('IN', 'Maharashtra', 'Adani Electricity Mumbai', 'ADANI', ARRAY['Mumbai Suburbs']),
('IN', 'Maharashtra', 'Brihanmumbai Electric Supply and Transport', 'BEST', ARRAY['Mumbai City'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

-- Karnataka
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('IN', 'Karnataka', 'Bangalore Electricity Supply Company', 'BESCOM', ARRAY['Bangalore', 'Bangalore Rural']),
('IN', 'Karnataka', 'Hubli Electricity Supply Company', 'HESCOM', ARRAY['Hubli', 'Dharwad', 'Belgaum']),
('IN', 'Karnataka', 'Mangalore Electricity Supply Company', 'MESCOM', ARRAY['Mangalore', 'Udupi']),
('IN', 'Karnataka', 'Gulbarga Electricity Supply Company', 'GESCOM', ARRAY['Gulbarga', 'Raichur'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

-- Brazil (Regional Distributors)
-- São Paulo
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('BR', 'São Paulo', 'Enel São Paulo', 'ENEL_SP', ARRAY['São Paulo Metropolitan Area']),
('BR', 'São Paulo', 'CPFL Paulista', 'CPFL_PAULISTA', ARRAY['Interior São Paulo']),
('BR', 'São Paulo', 'CPFL Piratininga', 'CPFL_PIRATININGA', ARRAY['Campinas Region'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

-- Rio de Janeiro
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('BR', 'Rio de Janeiro', 'Enel Rio', 'ENEL_RIO', ARRAY['Rio de Janeiro City', 'Niterói']),
('BR', 'Rio de Janeiro', 'Light', 'LIGHT', ARRAY['Rio de Janeiro Metropolitan Area'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

-- Minas Gerais
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('BR', 'Minas Gerais', 'Cemig', 'CEMIG', ARRAY['Minas Gerais State'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

-- Spain (Regional Coverage)
-- Madrid
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('ES', 'Madrid', 'i-DE (Iberdrola)', 'IDE', ARRAY['Madrid', 'Community of Madrid']),
('ES', 'Madrid', 'UFD (Naturgy)', 'UFD', ARRAY['Madrid Metropolitan Area'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

-- Catalonia
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('ES', 'Catalonia', 'e-distribución (Endesa)', 'EDISTRIBUCION', ARRAY['Barcelona', 'Catalonia']),
('ES', 'Catalonia', 'i-DE (Iberdrola)', 'IDE', ARRAY['Catalonia'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

-- Andalusia
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('ES', 'Andalusia', 'e-distribución (Endesa)', 'EDISTRIBUCION', ARRAY['Seville', 'Málaga', 'Andalusia'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

-- Valencia
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('ES', 'Valencia', 'i-DE (Iberdrola)', 'IDE', ARRAY['Valencia', 'Valencian Community'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

-- Basque Country
INSERT INTO utility_providers (country_code, state_province, provider_name, provider_code, service_areas) VALUES
('ES', 'Basque Country', 'i-DE (Iberdrola)', 'IDE', ARRAY['Bilbao', 'San Sebastián', 'Vitoria'])
ON CONFLICT (country_code, state_province, provider_code) DO NOTHING;

COMMENT ON TABLE utility_providers IS 'Utility provider companies organized by country and state/province';
COMMENT ON COLUMN utility_providers.country_code IS 'ISO 3166-1 alpha-2 country code (ES, US, IN, BR, NG)';
COMMENT ON COLUMN utility_providers.state_province IS 'State or province name';
COMMENT ON COLUMN utility_providers.provider_name IS 'Full name of the utility provider';
COMMENT ON COLUMN utility_providers.provider_code IS 'Short code for the provider (e.g., IKEDP, PGE)';
COMMENT ON COLUMN utility_providers.service_areas IS 'Array of cities/zones served by this provider';
