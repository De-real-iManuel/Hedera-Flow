# Database Migrations Guide

This guide explains how to manage database migrations for the Hedera Flow MVP using Alembic.

## Overview

We use [Alembic](https://alembic.sqlalchemy.org/) for database schema migrations. Alembic provides:
- Version control for database schema
- Upgrade and downgrade capabilities
- Migration history tracking
- Safe schema changes in production

## Quick Start

### Apply All Migrations

```bash
cd backend
python scripts/migrate.py upgrade head
```

### Check Current Migration Status

```bash
python scripts/migrate.py current
```

### View Migration History

```bash
python scripts/migrate.py history
```

## Migration Commands

### 1. Upgrade Database

Apply migrations to bring database to a specific revision:

```bash
# Upgrade to latest
python scripts/migrate.py upgrade head

# Upgrade to specific revision
python scripts/migrate.py upgrade 001_initial_schema

# Upgrade by one version
python scripts/migrate.py upgrade +1
```

### 2. Downgrade Database

Rollback migrations:

```bash
# Rollback one migration
python scripts/migrate.py downgrade -1

# Rollback to specific revision
python scripts/migrate.py downgrade 001_initial_schema

# Rollback all migrations
python scripts/migrate.py downgrade base
```

### 3. Create New Migration

Create a new migration file:

```bash
python scripts/migrate.py revision -m "add user preferences table"
```

This creates a new file in `migrations/versions/` with upgrade() and downgrade() functions.

### 4. Check Current Revision

See which migration is currently applied:

```bash
python scripts/migrate.py current
```

### 5. View Migration History

See all migrations and their status:

```bash
python scripts/migrate.py history
```

### 6. Stamp Database

Mark database as being at a specific revision without running migrations:

```bash
# Useful when manually applying schema or syncing existing database
python scripts/migrate.py stamp head
```

## Migration File Structure

```
backend/
├── alembic.ini                    # Alembic configuration
├── migrations/
│   ├── env.py                     # Migration environment
│   ├── script.py.mako             # Template for new migrations
│   └── versions/                  # Migration files
│       ├── 20260219_001_initial_schema.py
│       └── ...
└── scripts/
    └── migrate.py                 # Migration management script
```

## Creating Migrations

### Manual Migration

1. Create migration file:
```bash
python scripts/migrate.py revision -m "add column to users"
```

2. Edit the generated file in `migrations/versions/`:
```python
def upgrade() -> None:
    op.add_column('users', sa.Column('phone', sa.String(20)))

def downgrade() -> None:
    op.drop_column('users', 'phone')
```

3. Apply migration:
```bash
python scripts/migrate.py upgrade head
```

### Common Operations

**Add Column:**
```python
def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(20)))

def downgrade():
    op.drop_column('users', 'phone')
```

**Drop Column:**
```python
def upgrade():
    op.drop_column('users', 'old_field')

def downgrade():
    op.add_column('users', sa.Column('old_field', sa.String(50)))
```

**Create Table:**
```python
def upgrade():
    op.create_table(
        'new_table',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False)
    )

def downgrade():
    op.drop_table('new_table')
```

**Add Index:**
```python
def upgrade():
    op.create_index('idx_users_email', 'users', ['email'])

def downgrade():
    op.drop_index('idx_users_email', 'users')
```

**Add Foreign Key:**
```python
def upgrade():
    op.create_foreign_key(
        'fk_orders_user_id',
        'orders', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )

def downgrade():
    op.drop_constraint('fk_orders_user_id', 'orders', type_='foreignkey')
```

## Environment Setup

### Local Development

1. Ensure PostgreSQL is running:
```bash
docker-compose up -d postgres
```

2. Set DATABASE_URL in `.env`:
```bash
DATABASE_URL=postgresql://hedera_user:hedera_pass@localhost:5432/hedera_flow
```

3. Run migrations:
```bash
python scripts/migrate.py upgrade head
```

### Supabase (Production)

1. Get connection string from Supabase dashboard
2. Set DATABASE_URL in `.env`:
```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
```

3. Run migrations:
```bash
python scripts/migrate.py upgrade head
```

## Best Practices

### 1. Always Test Migrations

Test both upgrade and downgrade:
```bash
# Apply migration
python scripts/migrate.py upgrade head

# Test rollback
python scripts/migrate.py downgrade -1

# Re-apply
python scripts/migrate.py upgrade head
```

### 2. Keep Migrations Small

Create focused migrations that do one thing:
- ✅ Good: "add email verification column"
- ❌ Bad: "update user schema and add new tables"

### 3. Never Edit Applied Migrations

Once a migration is applied to production, never edit it. Create a new migration instead.

### 4. Use Transactions

Migrations run in transactions by default. For operations that can't run in transactions:
```python
def upgrade():
    op.execute("CREATE INDEX CONCURRENTLY idx_name ON table(column)")
```

### 5. Add Comments

Document complex migrations:
```python
def upgrade():
    """
    Add user preferences table for storing UI settings.
    Related to ticket: HFLOW-123
    """
    op.create_table(...)
```

## Troubleshooting

### Migration Failed Mid-Way

If a migration fails, Alembic may leave the database in an inconsistent state:

1. Check current revision:
```bash
python scripts/migrate.py current
```

2. Manually fix the database if needed

3. Stamp the database at the correct revision:
```bash
python scripts/migrate.py stamp <revision>
```

### Database Out of Sync

If your database schema doesn't match migrations:

1. Check what's applied:
```bash
python scripts/migrate.py current
```

2. Either:
   - Apply missing migrations: `python scripts/migrate.py upgrade head`
   - Or stamp database: `python scripts/migrate.py stamp head`

### Connection Issues

If you get connection errors:

1. Verify DATABASE_URL in `.env`
2. Check database is running: `docker ps` or Supabase dashboard
3. Test connection: `python test_supabase_connection.py`

## Migration Workflow

### Development Workflow

1. Make schema changes
2. Create migration: `python scripts/migrate.py revision -m "description"`
3. Edit migration file
4. Test upgrade: `python scripts/migrate.py upgrade head`
5. Test downgrade: `python scripts/migrate.py downgrade -1`
6. Re-apply: `python scripts/migrate.py upgrade head`
7. Commit migration file to git

### Production Deployment

1. Backup database
2. Test migrations on staging
3. Apply to production: `python scripts/migrate.py upgrade head`
4. Verify application works
5. If issues, rollback: `python scripts/migrate.py downgrade -1`

## Existing Migrations

### 001_initial_schema (2026-02-19)

Creates all initial tables:
- users
- meters
- tariffs
- verifications
- bills
- disputes
- exchange_rates
- audit_logs

Includes all indexes and foreign key constraints.

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Support

For issues or questions:
1. Check this guide
2. Review Alembic documentation
3. Check migration history: `python scripts/migrate.py history`
4. Verify database connection: `python test_supabase_connection.py`
