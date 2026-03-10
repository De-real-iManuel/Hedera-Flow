"""Add smart_meter_keys table for cryptographic meter signatures

Revision ID: 20260305_006
Revises: 20260303_005
Create Date: 2026-03-05

Creates smart_meter_keys table to support smart meter signature verification:
- ED25519 keypair storage for each meter
- Private key encryption (AES-256) for security
- Public key for signature verification
- Supports cryptographic proof of consumption data

Requirements: FR-9.1 to FR-9.3 (Smart Meter Simulation - Keypair Generation)
Spec: prepaid-smart-meter-mvp
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_smart_meter_keys'
down_revision = '005_add_prepaid_tokens'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create smart_meter_keys table"""
    
    op.create_table(
        'smart_meter_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('meter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meters.id', ondelete='CASCADE'), nullable=False, unique=True),
        
        # Keypair
        sa.Column('public_key', sa.TEXT(), nullable=False),
        sa.Column('private_key_encrypted', sa.TEXT(), nullable=False),
        sa.Column('encryption_iv', sa.TEXT(), nullable=False),
        
        # Metadata
        sa.Column('algorithm', sa.String(length=20), nullable=False, server_default='ED25519'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_used_at', sa.TIMESTAMP(timezone=True), nullable=True)
    )
    
    # Create index for efficient meter lookup
    op.create_index('idx_smart_meter_keys_meter_id', 'smart_meter_keys', ['meter_id'], unique=True)


def downgrade() -> None:
    """Drop smart_meter_keys table"""
    
    # Drop index
    op.drop_index('idx_smart_meter_keys_meter_id', table_name='smart_meter_keys')
    
    # Drop table
    op.drop_table('smart_meter_keys')
