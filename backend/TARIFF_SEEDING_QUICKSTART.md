# Tariff Seeding - Quick Start Guide

## Two Methods Available

### Method 1: Python Script (Recommended)
**Best for:** Development workflow, automated seeding, integration with other scripts

```bash
# From backend directory
python scripts/seed_tariffs.py
```

**Advantages:**
- ✅ Validates data before insertion
- ✅ Better error handling
- ✅ Can be integrated into deployment scripts
- ✅ Uses application configuration

**Requirements:**
- Python 3.11+
- psycopg2-binary installed
- .env file configured
- Database accessible

### Method 2: SQL File (Alternative)
**Best for:** Direct database access, manual seeding, SQL client users

```bash
# Using psql
psql -U hedera_user -d hedera_flow -h localhost -f migrations/seed_tariffs.sql

# Or from within psql
\i migrations/seed_tariffs.sql
```

**Advantages:**
- ✅ No Python dependencies needed
- ✅ Can be run from any SQL client
- ✅ Easy to review and modify
- ✅ Works with database migration tools

**Requirements:**
- PostgreSQL client (psql)
- Database credentials
- Direct database access

## Quick Setup (First Time)

### 1. Start Database
```bash
# Using Docker (recommended)
docker-compose up -d postgres

# Verify it's running
docker ps | grep postgres
```

### 2. Apply Schema
```bash
# From backend directory
python scripts/apply_schema.py
```

### 3. Seed Tariffs
```bash
# Choose one method:

# Method 1: Python
python scripts/seed_tariffs.py

# Method 2: SQL
psql -U hedera_user -d hedera_flow -h localhost -f migrations/seed_tariffs.sql
```

### 4. Verify
```bash
# Connect to database
psql -U hedera_user -d hedera_flow -h localhost

# Check tariffs
SELECT country_code, utility_provider, currency FROM tariffs;

# Should show:
# ES | Iberdrola         | EUR
# US | PG&E              | USD
# IN | Tata Power        | INR
# BR | Regional Provider | BRL
# NG | EKEDC             | NGN
```

## Seeded Tariff Summary

| Country | Provider | Currency | Type | Valid From |
|---------|----------|----------|------|------------|
| 🇪🇸 Spain | Iberdrola | EUR | Time-of-Use | 2024-01-01 |
| 🇺🇸 USA | PG&E | USD | Tiered | 2024-01-01 |
| 🇮🇳 India | Tata Power | INR | Tiered | 2024-01-01 |
| 🇧🇷 Brazil | Regional | BRL | Tiered | 2024-01-01 |
| 🇳🇬 Nigeria | EKEDC | NGN | Band-Based | 2024-01-01 |

## Troubleshooting

### "Database connection failed"
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Or check local PostgreSQL
pg_isready -U hedera_user -d hedera_flow
```

### "Table 'tariffs' does not exist"
```bash
# Apply schema first
python scripts/apply_schema.py

# Or run migrations
alembic upgrade head
```

### "Duplicate key error"
```bash
# Tariffs already exist - delete them first
psql -U hedera_user -d hedera_flow -h localhost -c "DELETE FROM tariffs;"

# Then re-run seed script
```

## Next Steps

After seeding tariffs:
1. ✅ Test tariff fetching: `SELECT * FROM tariffs WHERE country_code = 'ES';`
2. ✅ Implement billing calculation using seeded tariffs
3. ✅ Add tariff caching in Redis
4. ✅ Create API endpoint: `GET /api/tariffs?country=ES`

## Documentation

For detailed information, see:
- **Python Script Details:** `scripts/README_SEED_TARIFFS.md`
- **SQL File:** `migrations/seed_tariffs.sql`
- **Database Schema:** `schema.sql`
- **Requirements:** `.kiro/specs/hedera-flow-mvp/requirements.md`
