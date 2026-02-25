# Docker Setup Guide

This guide explains how to set up and use Docker Compose for local development with PostgreSQL and Redis.

## Prerequisites

- Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop))
- Docker Compose (included with Docker Desktop)

## Quick Start

1. **Start the services:**
   ```bash
   docker-compose up -d
   ```

2. **Check service status:**
   ```bash
   docker-compose ps
   ```

3. **View logs:**
   ```bash
   # All services
   docker-compose logs -f
   
   # Specific service
   docker-compose logs -f postgres
   docker-compose logs -f redis
   ```

4. **Stop the services:**
   ```bash
   docker-compose down
   ```

5. **Stop and remove volumes (clean slate):**
   ```bash
   docker-compose down -v
   ```

## Services

### PostgreSQL (Port 5432)
- **Image:** postgres:16-alpine
- **Database:** hedera_flow
- **User:** hedera_user
- **Password:** hedera_dev_password
- **Connection String:** `postgresql://hedera_user:hedera_dev_password@localhost:5432/hedera_flow`

### Redis (Port 6379)
- **Image:** redis:7-alpine
- **Password:** hedera_redis_password
- **Connection String:** `redis://:hedera_redis_password@localhost:6379/0`

## Database Initialization

The PostgreSQL database is automatically initialized with the schema defined in `backend/init.sql` when the container starts for the first time. This includes:

- All tables (users, meters, verifications, bills, tariffs, disputes, etc.)
- Indexes for performance
- UUID extension
- Constraints and foreign keys

## Connecting to Services

### PostgreSQL

**Using psql (from host):**
```bash
psql postgresql://hedera_user:hedera_dev_password@localhost:5432/hedera_flow
```

**Using Docker exec:**
```bash
docker exec -it hedera-flow-postgres psql -U hedera_user -d hedera_flow
```

**From Python (FastAPI backend):**
```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="hedera_flow",
    user="hedera_user",
    password="hedera_dev_password"
)
```

### Redis

**Using redis-cli (from host):**
```bash
redis-cli -a hedera_redis_password
```

**Using Docker exec:**
```bash
docker exec -it hedera-flow-redis redis-cli -a hedera_redis_password
```

**From Python (FastAPI backend):**
```python
import redis

r = redis.Redis(
    host='localhost',
    port=6379,
    password='hedera_redis_password',
    decode_responses=True
)
```

## Health Checks

Both services have health checks configured:

- **PostgreSQL:** Checks if database accepts connections every 10 seconds
- **Redis:** Checks if Redis responds to commands every 10 seconds

Check health status:
```bash
docker-compose ps
```

## Data Persistence

Data is persisted in Docker volumes:
- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis persistence files

These volumes survive container restarts. To completely reset:
```bash
docker-compose down -v
```

## Troubleshooting

### Port Already in Use

If ports 5432 or 6379 are already in use, you can either:

1. Stop the conflicting service
2. Change the port mapping in `docker-compose.yml`:
   ```yaml
   ports:
     - "5433:5432"  # Use 5433 on host instead
   ```

### Connection Refused

Make sure the containers are running:
```bash
docker-compose ps
```

Check logs for errors:
```bash
docker-compose logs postgres
docker-compose logs redis
```

### Reset Database

To reset the database to initial state:
```bash
docker-compose down -v
docker-compose up -d
```

## Production Notes

⚠️ **Important:** The credentials in `docker-compose.yml` are for development only. 

For production:
- Use strong, unique passwords
- Store credentials in environment variables or secrets management
- Use managed database services (Supabase, AWS RDS, etc.)
- Enable SSL/TLS connections
- Configure proper backup strategies
- Implement network security rules

## Next Steps

After starting the services:

1. Copy `.env.example` to `.env` in the backend directory
2. Update the environment variables if needed
3. Run database migrations (if using Alembic or similar)
4. Start the FastAPI backend
5. Start the Next.js frontend

## Useful Commands

```bash
# Start services in foreground (see logs)
docker-compose up

# Start services in background
docker-compose up -d

# Stop services
docker-compose stop

# Start stopped services
docker-compose start

# Restart services
docker-compose restart

# Remove containers (keeps volumes)
docker-compose down

# Remove containers and volumes
docker-compose down -v

# View logs
docker-compose logs -f

# Execute command in container
docker exec -it hedera-flow-postgres bash
docker exec -it hedera-flow-redis sh

# Check resource usage
docker stats
```
