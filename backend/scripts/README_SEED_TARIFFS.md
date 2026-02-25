# Tariff Data Seeding Guide

## Overview
This script seeds tariff data for all 5 supported regions:
- 🇪🇸 Spain (Iberdrola) - Time-of-Use pricing
- 🇺🇸 USA (PG&E California) - Tiered pricing
- 🇮🇳 India (Tata Power) - Tiered pricing
- 🇧🇷 Brazil (Regional) - Tiered pricing
- 🇳🇬 Nigeria (EKEDC) - Band-based pricing

## Prerequisites

### 1. Database Setup
Ensure PostgreSQL is running and accessible. You have two options:

#### Option A: Docker (Recommended for Development)
```bash
# Start PostgreSQL and Redis containers
docker-compose up -d postgres redis

# Verify containers are running
docker ps

# Check database is ready
docker exec hedera-flow-postgres pg_isready -U hedera_user -d hedera_flow
```

#### Option B: Local PostgreSQL Installation
Ensure PostgreSQL 16+ is installed and running with:
- Database: `hedera_flow`
- User: `hedera_user`
- Password: `hedera_dev_password`
- Port: `5432`

### 2. Environment Configuration
Create a `.env` file in the `backend` directory:

```bash
# From backend directory
cp .env.example .env
```

Ensure the `DATABASE_URL` is set correctly:
```env
DATABASE_URL=postgresql://hedera_user:hedera_dev_password@localhost:5432/hedera_flow
```

### 3. Database Schema
Ensure the database schema is created. Run migrations:

```bash
# From backend directory
cd backend

# Apply schema
python scripts/apply_schema.py

# Or run migrations
alembic upgrade head
```

### 4. Python Dependencies
Install required packages:

```bash
# From backend directory
pip install -r requirements.txt
```

## Running the Seed Script

### Method 1: Direct Execution
```bash
# From backend directory
python scripts/seed_tariffs.py
```

### Method 2: From Project Root
```bash
# From project root
python backend/scripts/seed_tariffs.py
```

## Expected Output

```
Seeding tariff data for Spain, USA, India, Brazil, and Nigeria...
======================================================================
✓ Seeded tariff for ES - Iberdrola
✓ Seeded tariff for US - PG&E
✓ Seeded tariff for IN - Tata Power
✓ Seeded tariff for BR - Regional Provider
✓ Seeded tariff for NG - EKEDC

✓ Successfully seeded 5 tariffs!
```

## Verifying the Data

### Using psql
```bash
# Connect to database
psql -U hedera_user -d hedera_flow -h localhost

# Query tariffs
SELECT country_code, utility_provider, currency, is_active 
FROM tariffs 
ORDER BY country_code;

# View detailed tariff structure
SELECT country_code, utility_provider, rate_structure 
FROM tariffs 
WHERE country_code = 'ES';
```

### Using Python
```python
import psycopg2
from config import settings

conn = psycopg2.connect(settings.database_url)
cursor = conn.cursor()

cursor.execute("SELECT country_code, utility_provider FROM tariffs")
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}")

cursor.close()
conn.close()
```

## Tariff Data Structure

### Spain (ES) - Time-of-Use
```json
{
  "type": "time_of_use",
  "periods": [
    {"name": "peak", "hours": [10-14, 18-21], "price": 0.40},
    {"name": "standard", "hours": [8-9, 15-17, 22-23], "price": 0.25},
    {"name": "off_peak", "hours": [0-7], "price": 0.15}
  ]
}
```
- VAT: 21%
- Distribution charge: €0.045/kWh

### USA (US) - Tiered
```json
{
  "type": "tiered",
  "tiers": [
    {"name": "tier1", "min_kwh": 0, "max_kwh": 400, "price": 0.32},
    {"name": "tier2", "min_kwh": 401, "max_kwh": 800, "price": 0.40},
    {"name": "tier3", "min_kwh": 801, "max_kwh": null, "price": 0.50}
  ]
}
```
- Sales tax: 7.25%
- Fixed monthly fee: $10.00

### India (IN) - Tiered
```json
{
  "type": "tiered",
  "tiers": [
    {"name": "tier1", "min_kwh": 0, "max_kwh": 100, "price": 4.50},
    {"name": "tier2", "min_kwh": 101, "max_kwh": 300, "price": 6.00},
    {"name": "tier3", "min_kwh": 301, "max_kwh": null, "price": 7.50}
  ]
}
```
- VAT: 18%

### Brazil (BR) - Tiered
```json
{
  "type": "tiered",
  "tiers": [
    {"name": "tier1", "min_kwh": 0, "max_kwh": 100, "price": 0.50},
    {"name": "tier2", "min_kwh": 101, "max_kwh": 300, "price": 0.70},
    {"name": "tier3", "min_kwh": 301, "max_kwh": null, "price": 0.90}
  ]
}
```
- ICMS tax: 20%

### Nigeria (NG) - Band-Based
```json
{
  "type": "band_based",
  "bands": [
    {"name": "A", "hours_min": 20, "price": 225.00},
    {"name": "B", "hours_min": 16, "price": 63.30},
    {"name": "C", "hours_min": 12, "price": 50.00},
    {"name": "D", "hours_min": 8, "price": 43.00},
    {"name": "E", "hours_min": 0, "price": 40.00}
  ]
}
```
- VAT: 7.5%
- Service charge: ₦1,500

## Troubleshooting

### Error: "could not connect to server"
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env file
- Verify port 5432 is not blocked by firewall

### Error: "relation 'tariffs' does not exist"
- Run database migrations first: `alembic upgrade head`
- Or apply schema: `python scripts/apply_schema.py`

### Error: "duplicate key value violates unique constraint"
- Tariffs already exist in database
- To re-seed, delete existing tariffs first:
  ```sql
  DELETE FROM tariffs;
  ```

### Error: "ModuleNotFoundError: No module named 'config'"
- Ensure you're running from the backend directory
- Or add backend to PYTHONPATH:
  ```bash
  export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
  ```

## Re-seeding Data

To re-seed tariffs (e.g., after data changes):

```bash
# Connect to database
psql -U hedera_user -d hedera_flow -h localhost

# Delete existing tariffs
DELETE FROM tariffs;

# Exit psql
\q

# Run seed script again
python scripts/seed_tariffs.py
```

## Production Deployment

For production (Supabase), update the DATABASE_URL in your .env:

```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:6543/postgres
```

Then run the seed script:
```bash
python scripts/seed_tariffs.py
```

## Notes

- Tariffs are valid from 2024-01-01 with no expiration date
- All tariffs are marked as active (`is_active = TRUE`)
- Prices are in local currencies (EUR, USD, INR, BRL, NGN)
- Rate structures are stored as JSONB for flexibility
- Taxes and fees are region-specific

## Next Steps

After seeding tariffs:
1. ✅ Verify data in database
2. ✅ Test billing calculation with seeded tariffs
3. ✅ Implement tariff fetching API endpoint
4. ✅ Add tariff caching in Redis
