# Nigeria DisCos Implementation

**Task**: 2.3.1 - Nigeria: 11 DisCos with state coverage  
**Requirements**: US-2, FR-4.1  
**Status**: ✅ Implemented

## Overview

This implementation seeds all 11 Nigerian Distribution Companies (DisCos) with their respective state coverage and band-based tariff structures.

## Nigerian DisCos Coverage

| DisCo Code | Full Name | States Covered |
|------------|-----------|----------------|
| **AEDC** | Abuja Electricity Distribution Company | FCT, Kogi, Nasarawa, Niger |
| **BEDC** | Benin Electricity Distribution Company | Edo, Delta, Ondo, Ekiti |
| **EKEDP** | Eko Electricity Distribution Company | Lagos (Mainland) |
| **EEDC** | Enugu Electricity Distribution Company | Enugu, Abia, Anambra, Ebonyi, Imo |
| **IBEDC** | Ibadan Electricity Distribution Company | Oyo, Osun, Ogun, Kwara |
| **IKEDC** | Ikeja Electricity Distribution Company | Lagos (Island & Ikeja) |
| **JEDC** | Jos Electricity Distribution Company | Plateau, Bauchi, Gombe, Benue |
| **KAEDCO** | Kaduna Electricity Distribution Company | Kaduna, Kebbi, Sokoto, Zamfara |
| **KEDCO** | Kano Electricity Distribution Company | Kano, Jigawa, Katsina |
| **PHED** | Port Harcourt Electricity Distribution Company | Rivers, Bayelsa, Cross River, Akwa Ibom |
| **YEDC** | Yola Electricity Distribution Company | Adamawa, Borno, Taraba, Yobe |

## Band Classification System

All DisCos use the Nigerian band-based tariff system:

| Band | Minimum Hours/Day | Price (NGN/kWh) |
|------|-------------------|-----------------|
| A | 20+ hours | ₦225.00 |
| B | 16+ hours | ₦63.30 |
| C | 12+ hours | ₦50.00 |
| D | 8+ hours | ₦43.00 |
| E | 4+ hours | ₦40.00 |

## Taxes and Fees

All DisCos apply:
- **VAT**: 7.5%
- **Service Charge**: ₦1,500 (fixed monthly)

## Usage

### Option 1: Python Script

```bash
cd backend
python scripts/seed_nigeria_discos.py
```

### Option 2: SQL Script

```bash
cd backend
psql -U postgres -d hedera_flow -f migrations/seed_nigeria_discos.sql
```

### Option 3: Via Docker

```bash
docker exec -i hedera-flow-postgres psql -U postgres -d hedera_flow < backend/migrations/seed_nigeria_discos.sql
```

## Verification

After seeding, verify the data:

```sql
SELECT 
    utility_provider,
    region,
    currency,
    is_active,
    jsonb_array_length(rate_structure->'bands') as band_count
FROM tariffs
WHERE country_code = 'NG'
ORDER BY utility_provider;
```

Expected output: 11 rows (one for each DisCo)

## API Integration

Users can now:

1. **Register meters** with any of the 11 DisCos
2. **Select their band classification** (A, B, C, D, or E)
3. **Get accurate billing** based on their DisCo and band

### Example API Request

```json
POST /api/meters
{
  "meter_id": "12345678901",
  "utility_provider": "IKEDC",
  "meter_type": "prepaid",
  "band_classification": "B",
  "address": "Victoria Island, Lagos"
}
```

## Files Created

1. `backend/scripts/seed_nigeria_discos.py` - Python seeding script
2. `backend/migrations/seed_nigeria_discos.sql` - SQL seeding script
3. `backend/NIGERIA_DISCOS.md` - This documentation

## Next Steps

- [ ] Add DisCo-specific meter ID validation patterns
- [ ] Implement state-to-DisCo mapping for auto-selection
- [ ] Add DisCo contact information and support channels
- [ ] Implement real-time tariff updates from NERC

## References

- Nigerian Electricity Regulatory Commission (NERC)
- Multi-Year Tariff Order (MYTO) 2024
- Band-based tariff structure guidelines
