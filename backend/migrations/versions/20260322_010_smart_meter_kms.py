"""Add kms_key_id to smart_meter_keys, make private_key_encrypted nullable

Revision ID: 010_smart_meter_kms
Revises: 007_add_consumption_logs
Create Date: 2026-03-22

TOKENIZE TRUST: Private key never touches the database.
KMS HSM is the only place the private key lives.
"""
from alembic import op
import sqlalchemy as sa

revision = '010_smart_meter_kms'
down_revision = '007_add_consumption_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add kms_key_id column
    op.execute("""
        ALTER TABLE smart_meter_keys
        ADD COLUMN IF NOT EXISTS kms_key_id VARCHAR(255)
    """)
    # Make private_key_encrypted and encryption_iv nullable
    op.execute("""
        ALTER TABLE smart_meter_keys
        ALTER COLUMN private_key_encrypted DROP NOT NULL
    """)
    op.execute("""
        ALTER TABLE smart_meter_keys
        ALTER COLUMN encryption_iv DROP NOT NULL
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE smart_meter_keys DROP COLUMN IF EXISTS kms_key_id")
