# Quick Start: Nigeria DisCos Seeding

## Prerequisites

Ensure you have:
- PostgreSQL running (via Docker or local)
- Backend dependencies installed
- Database schema initialized

## Step 1: Activate Virtual Environment

```bash
cd backend

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

## Step 2: Install Dependencies (if needed)

```bash
pip install -r requirements.txt
```

## Step 3: Run Seeding Script

### Option A: Python Script (Recommended)

```bash
python scripts/seed_nigeria_discos.py
```

### Option B: SQL Script

```bash
# Using psql
psql -U postgres -d hedera_flow -f migrations/seed_nigeria_discos.sql

# Using Docker
docker exec -i hedera-flow-postgres psql -U postgres -d hedera_flow < migrations/seed_nigeria_discos.sql
```

## Expected Output

```
Seeding 11 Nigerian DisCos...
======================================================================
✓ AEDC: Abuja Electricity Distribution Company
  States: FCT, Kogi, Nasarawa, Niger
✓ BEDC: Benin Electricity Distribution Company
  States: Edo, Delta, Ondo, Ekiti
✓ EKEDP: Eko Electricity Distribution Company
  States: Lagos (Mainland)
✓ EEDC: Enugu Electricity Distribution Company
  States: Enugu, Abia, Anambra, Ebonyi, Imo
✓ IBEDC: Ibadan Electricity Distribution Company
  States: Oyo, Osun, Ogun, Kwara
✓ IKEDC: Ikeja Electricity Distribution Company
  States: Lagos (Island & Ikeja)
✓ JEDC: Jos Electricity Distribution Company
  States: Plateau, Bauchi, Gombe, Benue
✓ KAEDCO: Kaduna Electricity Distribution Company
  States: Kaduna, Kebbi, Sokoto, Zamfara
✓ KEDCO: Kano Electricity Distribution Company
  States: Kano, Jigawa, Katsina
✓ PHED: Port Harcourt Electricity Distribution Company
  States: Rivers, Bayelsa, Cross River, Akwa Ibom
✓ YEDC: Yola Electricity Distribution Company
  States: Adamawa, Borno, Taraba, Yobe
======================================================================
✓ Successfully seeded 11 Nigerian DisCos!
```

## Verify Installation

```bash
# Connect to database
psql -U postgres -d hedera_flow

# Run verification query
SELECT utility_provider, region, currency 
FROM tariffs 
WHERE country_code = 'NG' 
ORDER BY utility_provider;
```

You should see 11 rows.

## Troubleshooting

### Error: "No module named 'psycopg2'"
```bash
pip install psycopg2-binary
```

### Error: "Connection refused"
```bash
# Check if PostgreSQL is running
docker compose ps

# Start if not running
docker compose up -d
```

### Error: "Database does not exist"
```bash
# Run initial schema migration
python scripts/migrate.py upgrade head
```

## Next Steps

After seeding:
1. Test meter registration with Nigerian DisCos
2. Verify band-based billing calculations
3. Test state-to-DisCo mapping
