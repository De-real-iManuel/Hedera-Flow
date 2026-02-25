# Hedera Flow Backend

FastAPI backend for the Hedera Flow MVP - blockchain-powered utility verification platform.

## Tech Stack

- **Framework**: FastAPI 0.109.0
- **Python**: 3.11+
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Blockchain**: Hedera Testnet
- **OCR**: Google Cloud Vision API

## Project Structure

```
backend/
├── main.py                 # Application entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── app/
│   ├── api/              # API route handlers
│   ├── models/           # SQLAlchemy database models
│   ├── schemas/          # Pydantic request/response schemas
│   ├── services/         # Business logic services
│   └── utils/            # Utility functions
└── tests/                # Test suite
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Database

#### Option A: Local Development (Docker)

```bash
# Start PostgreSQL + Redis with Docker Compose
cd ..
docker-compose up -d

# Verify containers are running
docker ps

# Run database migrations
cd backend
python scripts/migrate.py upgrade head
```

#### Option B: Production (Supabase)

See [Database Setup Guide](DATABASE_SETUP.md) for complete instructions.

```bash
# 1. Create Supabase project at supabase.com
# 2. Get connection string from Settings → Database
# 3. Update .env with Supabase credentials
# 4. Run migrations
python scripts/migrate.py upgrade head

# 5. Test connection
python test_supabase_connection.py
```

### 4. Configure Environment

```bash
# Copy example environment file
copy .env.example .env

# Edit .env with your configuration
# - DATABASE_URL (local or Supabase)
# - REDIS_URL (local or Upstash)
# - Hedera testnet accounts
# - API keys
```

### 5. Set Up Hedera Testnet Accounts

Create Treasury and Operator accounts for blockchain operations:

```bash
# Option 1: Automated script (recommended)
python scripts/create_hedera_accounts.py

# Option 2: Manual setup via Hedera Portal
# See scripts/hedera_account_setup.md for instructions

# Verify configuration
python scripts/test_hedera_accounts.py
```

See [scripts/README_HEDERA_ACCOUNTS.md](scripts/README_HEDERA_ACCOUNTS.md) for detailed instructions.

**Quick Start**:
1. Get testnet HBAR from [Hedera Portal](https://portal.hedera.com/)
2. Run `python scripts/create_hedera_accounts.py`
3. Update `.env` with account IDs and private keys
4. Verify with `python scripts/test_hedera_accounts.py`

### 6. Run Development Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health status

### Authentication (Coming Soon)
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/wallet-connect` - HashPack wallet connection

### Meters (Coming Soon)
- `POST /api/meters` - Register meter
- `GET /api/meters` - List user meters

### Verification (Coming Soon)
- `POST /api/verify` - Verify meter reading
- `GET /api/verifications` - List verifications

### Payments (Coming Soon)
- `GET /api/exchange-rate/:currency` - Get HBAR exchange rate
- `POST /api/payments/prepare` - Prepare payment
- `POST /api/payments/confirm` - Confirm payment

### Disputes (Coming Soon)
- `POST /api/disputes` - Create dispute
- `GET /api/disputes/:id` - Get dispute details

## Development

### Database Migrations

We use Alembic for database schema version control:

```bash
# Apply all migrations
python scripts/migrate.py upgrade head

# Check current migration
python scripts/migrate.py current

# Create new migration
python scripts/migrate.py revision -m "description"

# Rollback one migration
python scripts/migrate.py downgrade -1
```

See [DATABASE_SETUP.md](DATABASE_SETUP.md) for complete guide.

### Database Management

```bash
# Run database migrations (recommended)
python scripts/migrate.py upgrade head

# Check migration status
python scripts/migrate.py current

# View migration history
python scripts/migrate.py history

# Alternative: Initialize database directly (creates tables + seeds tariff data)
python supabase_init.py

# Test database connection
python test_supabase_connection.py

# Connect with psql (if installed)
psql "$DATABASE_URL"
```

See [MIGRATIONS.md](MIGRATIONS.md) for complete migration guide.

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Document functions with docstrings

### Testing
```bash
pytest
```

## Next Steps

1. ✅ Set up Docker Compose (PostgreSQL + Redis) - Task 1.4
2. ✅ Configure Supabase project - Task 1.5
3. ✅ Configure environment variables - Task 1.6
4. ✅ Create Hedera testnet accounts - Task 3.1
5. ✅ Fund Hedera accounts with testnet HBAR - Task 3.2
6. ⏭️ Set up GitHub repository and CI/CD - Task 1.7
7. ⏭️ Create HCS topics - Task 3.3
8. ⏭️ Test basic HBAR transfers - Task 3.4
9. ⏭️ Implement authentication endpoints - Task 6.1

## Resources

- [DATABASE_SETUP.md](DATABASE_SETUP.md) - Complete database setup guide
- [MIGRATIONS.md](MIGRATIONS.md) - Database migration guide
- [MIGRATION_QUICK_REFERENCE.md](MIGRATION_QUICK_REFERENCE.md) - Quick migration commands
- [scripts/README_HEDERA_ACCOUNTS.md](scripts/README_HEDERA_ACCOUNTS.md) - Hedera account setup guide
- [scripts/hedera_account_setup.md](scripts/hedera_account_setup.md) - Quick Hedera setup
- [scripts/FUNDING_GUIDE.md](scripts/FUNDING_GUIDE.md) - Comprehensive funding guide
- [scripts/FUNDING_QUICKSTART.md](scripts/FUNDING_QUICKSTART.md) - Quick funding reference
- [TASK_3.1_SUMMARY.md](TASK_3.1_SUMMARY.md) - Hedera accounts task summary
- [TASK_3.2_SUMMARY.md](TASK_3.2_SUMMARY.md) - Hedera funding task summary
- [Supabase Setup Guide](../SUPABASE_SETUP.md) - Complete Supabase configuration
- [Supabase Quick Start](SUPABASE_QUICKSTART.md) - Quick reference guide
- [Docker Setup](../DOCKER_SETUP.md) - Local development with Docker
- [Design Document](../.kiro/specs/hedera-flow-mvp/design.md) - Technical architecture

## License

MIT
