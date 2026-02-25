# Supabase Setup Guide - Hedera Flow MVP

This guide walks you through setting up Supabase for the Hedera Flow MVP project.

## Overview

Supabase provides:
- **PostgreSQL Database** - Managed database with automatic backups
- **Redis** - Available through Supabase partners or Upstash integration
- **Authentication** - Built-in auth (we'll use custom JWT)
- **Storage** - For file uploads (optional, we use IPFS)
- **Real-time** - WebSocket subscriptions (future feature)

## Step 1: Create Supabase Account

1. Go to [https://supabase.com](https://supabase.com)
2. Click "Start your project"
3. Sign up with GitHub, Google, or email
4. Verify your email address

## Step 2: Create New Project

1. Click "New Project" in the dashboard
2. Fill in project details:
   - **Name**: `hedera-flow-mvp`
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your users:
     - Europe: `eu-west-1` (Ireland) or `eu-central-1` (Frankfurt)
     - USA: `us-east-1` (N. Virginia) or `us-west-1` (Oregon)
     - Asia: `ap-southeast-1` (Singapore)
   - **Pricing Plan**: Free tier (sufficient for MVP)

3. Click "Create new project"
4. Wait 2-3 minutes for provisioning

## Step 3: Get Database Connection Details

Once your project is ready:

1. Go to **Settings** → **Database**
2. Find the **Connection string** section
3. Copy the connection details:

```
Host: db.xxxxxxxxxxxxx.supabase.co
Database name: postgres
Port: 5432
User: postgres
Password: [your-database-password]
```

4. Copy the **Connection string** (URI format):
```
postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
```

## Step 4: Configure Environment Variables

Update your `backend/.env` file with Supabase credentials:

```bash
# Supabase Database Configuration
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
POSTGRES_HOST=db.xxxxxxxxxxxxx.supabase.co
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=[YOUR-PASSWORD]
POSTGRES_DB=postgres

# Supabase Project Details
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=[your-anon-key]
SUPABASE_SERVICE_ROLE_KEY=[your-service-role-key]
```

### Finding Supabase API Keys

1. Go to **Settings** → **API**
2. Copy the following:
   - **Project URL**: `https://xxxxxxxxxxxxx.supabase.co`
   - **anon public key**: For client-side requests (not needed for MVP)
   - **service_role key**: For server-side admin operations

## Step 5: Initialize Database Schema

### Option A: Using Supabase SQL Editor (Recommended)

1. Go to **SQL Editor** in Supabase dashboard
2. Click "New query"
3. Copy the contents of `backend/init.sql`
4. Paste into the SQL editor
5. Click "Run" to execute

### Option B: Using psql Command Line

```bash
# Install psql if not already installed
# On macOS: brew install postgresql
# On Ubuntu: sudo apt-get install postgresql-client
# On Windows: Download from postgresql.org

# Connect to Supabase database
psql "postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres"

# Run the init script
\i backend/init.sql

# Verify tables were created
\dt
```

### Option C: Using Python Script

```bash
cd backend
python -c "
import psycopg2
from config import settings

conn = psycopg2.connect(settings.database_url)
cursor = conn.cursor()

with open('init.sql', 'r') as f:
    cursor.execute(f.read())

conn.commit()
cursor.close()
conn.close()
print('Database initialized successfully!')
"
```

## Step 6: Set Up Redis (Upstash Integration)

Supabase doesn't provide Redis directly. Use Upstash (free tier):

1. Go to [https://upstash.com](https://upstash.com)
2. Sign up with GitHub or email
3. Click "Create Database"
4. Configure:
   - **Name**: `hedera-flow-cache`
   - **Type**: Regional
   - **Region**: Same as your Supabase region
   - **TLS**: Enabled
5. Copy the connection details:

```bash
REDIS_URL=rediss://default:[PASSWORD]@[ENDPOINT]:6379
```

6. Add to your `backend/.env`:

```bash
# Upstash Redis Configuration
REDIS_URL=rediss://default:[PASSWORD]@[ENDPOINT]:6379
REDIS_HOST=[ENDPOINT]
REDIS_PORT=6379
REDIS_PASSWORD=[PASSWORD]
```

## Step 7: Configure Connection Pooling (Production)

For production, enable connection pooling:

1. Go to **Settings** → **Database**
2. Find **Connection Pooling** section
3. Enable **Transaction Mode** pooling
4. Copy the pooler connection string:

```
postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:6543/postgres
```

5. Use this for your production `DATABASE_URL` (note port 6543 instead of 5432)

## Step 8: Set Up Database Backups

Supabase automatically backs up your database daily (free tier).

To enable Point-in-Time Recovery (PITR):
1. Upgrade to Pro plan ($25/month)
2. Go to **Settings** → **Database**
3. Enable **Point-in-Time Recovery**

For MVP, daily backups are sufficient.

## Step 9: Test Database Connection

Create a test script to verify connectivity:

```python
# backend/test_supabase_connection.py
import psycopg2
from config import settings

def test_connection():
    try:
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connected to PostgreSQL: {version[0]}")
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print(f"✅ Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
```

Run the test:
```bash
cd backend
python test_supabase_connection.py
```

## Step 10: Configure Security

### Row Level Security (RLS)

Enable RLS for sensitive tables:

```sql
-- Enable RLS on users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read their own data
CREATE POLICY "Users can view own data"
ON users FOR SELECT
USING (auth.uid()::text = id::text);

-- Policy: Users can update their own data
CREATE POLICY "Users can update own data"
ON users FOR UPDATE
USING (auth.uid()::text = id::text);
```

### Database Roles

Supabase creates these roles automatically:
- `postgres` - Superuser (use for migrations)
- `authenticator` - Used by Supabase Auth
- `anon` - Anonymous access (public API)
- `authenticated` - Authenticated users

For our MVP, we'll use the `postgres` role with custom JWT auth.

## Step 11: Set Up Monitoring

1. Go to **Reports** in Supabase dashboard
2. Monitor:
   - Database size
   - Active connections
   - Query performance
   - API requests

3. Set up alerts:
   - Go to **Settings** → **Alerts**
   - Configure email notifications for:
     - High database usage (>80%)
     - Connection pool exhaustion
     - Slow queries (>1s)

## Step 12: Local Development vs Production

### Local Development (Docker)
- Use `docker-compose.yml` for local PostgreSQL + Redis
- Fast iteration, no internet required
- Run: `docker-compose up -d`

### Production (Supabase)
- Use Supabase for deployed backend
- Managed backups and scaling
- Update `DATABASE_URL` in production environment

### Hybrid Approach (Recommended for MVP)
- Develop locally with Docker
- Test on Supabase staging environment
- Deploy to Supabase production

## Environment-Specific Configuration

Create separate `.env` files:

### `.env.local` (Docker)
```bash
DATABASE_URL=postgresql://hedera_user:hedera_dev_password@localhost:5432/hedera_flow
REDIS_URL=redis://:hedera_redis_password@localhost:6379/0
```

### `.env.staging` (Supabase Staging)
```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.staging-xxxxx.supabase.co:5432/postgres
REDIS_URL=rediss://default:[PASSWORD]@staging-xxxxx.upstash.io:6379
```

### `.env.production` (Supabase Production)
```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:6543/postgres
REDIS_URL=rediss://default:[PASSWORD]@xxxxx.upstash.io:6379
```

## Troubleshooting

### Connection Timeout
- Check if your IP is whitelisted (Supabase allows all IPs by default)
- Verify firewall settings
- Try connection pooler (port 6543)

### SSL Certificate Errors
Add `?sslmode=require` to connection string:
```
postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres?sslmode=require
```

### Too Many Connections
- Use connection pooling (port 6543)
- Implement connection pooling in your app (SQLAlchemy pool)
- Close connections properly

### Slow Queries
- Check **Reports** → **Query Performance**
- Add indexes for frequently queried columns
- Use `EXPLAIN ANALYZE` to debug

## Next Steps

After Supabase setup is complete:

1. ✅ Supabase project created
2. ✅ Database connection configured
3. ✅ Schema initialized
4. ✅ Redis (Upstash) configured
5. ✅ Connection tested
6. ⏭️ Continue to Task 1.6: Configure environment variables
7. ⏭️ Continue to Task 1.7: Set up GitHub repository and CI/CD

## Useful Commands

```bash
# Test database connection
psql "$DATABASE_URL" -c "SELECT version();"

# List all tables
psql "$DATABASE_URL" -c "\dt"

# Check database size
psql "$DATABASE_URL" -c "SELECT pg_size_pretty(pg_database_size('postgres'));"

# View active connections
psql "$DATABASE_URL" -c "SELECT count(*) FROM pg_stat_activity;"

# Backup database (local)
pg_dump "$DATABASE_URL" > backup.sql

# Restore database (local)
psql "$DATABASE_URL" < backup.sql
```

## Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Upstash Redis Documentation](https://docs.upstash.com/redis)

---

**Status**: Setup guide complete ✅  
**Next Task**: 1.6 Configure environment variables
