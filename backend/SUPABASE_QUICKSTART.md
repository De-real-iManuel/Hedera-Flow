# Supabase Quick Start Guide

Quick reference for setting up Supabase for Hedera Flow MVP.

## 1. Create Supabase Project (5 minutes)

1. Go to [supabase.com](https://supabase.com) → Sign up
2. Click "New Project"
3. Fill in:
   - Name: `hedera-flow-mvp`
   - Database Password: (generate strong password)
   - Region: Choose closest to you
   - Plan: Free
4. Click "Create new project"
5. Wait 2-3 minutes

## 2. Get Connection String

1. Go to **Settings** → **Database**
2. Copy **Connection string** (URI format):
   ```
   postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
3. Replace `[PASSWORD]` with your actual password

## 3. Configure Backend

Create `backend/.env` file:

```bash
# Copy from .env.example
cp .env.example .env

# Edit .env and update DATABASE_URL
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
```

## 4. Initialize Database

```bash
cd backend

# Option 1: Using Python script (recommended)
python supabase_init.py

# Option 2: Using Supabase SQL Editor
# - Go to SQL Editor in Supabase dashboard
# - Copy contents of init.sql
# - Paste and click "Run"
```

## 5. Set Up Redis (Upstash)

1. Go to [upstash.com](https://upstash.com) → Sign up
2. Click "Create Database"
3. Name: `hedera-flow-cache`
4. Region: Same as Supabase
5. Copy connection string:
   ```
   rediss://default:[PASSWORD]@[ENDPOINT].upstash.io:6379
   ```
6. Add to `.env`:
   ```bash
   REDIS_URL=rediss://default:[PASSWORD]@[ENDPOINT].upstash.io:6379
   ```

## 6. Test Connection

```bash
cd backend
python test_supabase_connection.py
```

Expected output:
```
✅ Connected to PostgreSQL
✅ Found 8 tables
✅ Connected to Redis
🎉 All tests passed!
```

## 7. Development Workflow

### Local Development (Docker)
```bash
# Use local PostgreSQL + Redis
docker-compose up -d

# Update .env
DATABASE_URL=postgresql://hedera_user:hedera_dev_password@localhost:5432/hedera_flow
REDIS_URL=redis://:hedera_redis_password@localhost:6379/0
```

### Production (Supabase)
```bash
# Use Supabase connection string
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:6543/postgres
REDIS_URL=rediss://default:[PASSWORD]@[ENDPOINT].upstash.io:6379
```

## Troubleshooting

### Connection Timeout
- Check internet connection
- Verify password is correct
- Try connection pooler (port 6543 instead of 5432)

### SSL Errors
Add `?sslmode=require` to DATABASE_URL:
```
postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres?sslmode=require
```

### Tables Not Found
Run initialization script:
```bash
python supabase_init.py
```

## Useful Commands

```bash
# Test connection
python test_supabase_connection.py

# Initialize database
python supabase_init.py

# Connect with psql
psql "postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres"

# List tables
psql "$DATABASE_URL" -c "\dt"
```

## Next Steps

✅ Task 1.5: Set up Supabase project (COMPLETE)  
⏭️ Task 1.6: Configure environment variables  
⏭️ Task 1.7: Set up GitHub repository and CI/CD

## Resources

- [Full Setup Guide](../SUPABASE_SETUP.md)
- [Supabase Docs](https://supabase.com/docs)
- [Upstash Docs](https://docs.upstash.com/redis)
