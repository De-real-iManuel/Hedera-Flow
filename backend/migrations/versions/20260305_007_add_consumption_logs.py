"""Add consumption_logs table for smart meter consumption tracking

Revision ID: 20260305_007
Revises: 20260305_006
Create Date: 2026-03-05

Creates consumption_logs table to support smart meter consumption logging:
- Cryptographically signed consumption data
- Signature verification status
- Prepaid token deduction tracking
- HCS logging integration
- Consumption history and audit trail

Requirements: FR-9.4 to FR-9.9 (Smart Meter Simulation - Signature & Logging)
Spec: prepaid-smart-meter-mvp
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_add_consumption_logs'
down_revision = '006_add_smart_meter_keys'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create consumption_logs table"""
    
    op.create_table(
        'consumption_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('meter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('prepaid_tokens.id'), nullable=True),
        
        # Consumption Data
        sa.Column('consumption_kwh', sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column('reading_before', sa.DECIMAL(precision=12, scale=2), nullable=True),
        sa.Column('reading_after', sa.DECIMAL(precision=12, scale=2), nullable=True),
        sa.Column('timestamp', sa.BIGINT(), nullable=False),
        
        # Signature
        sa.Column('signature', sa.TEXT(), nullable=False),
        sa.Column('public_key', sa.TEXT(), nullable=False),
        sa.Column('signature_valid', sa.BOOLEAN(), nullable=False),
        
        # Token Deduction
        sa.Column('units_deducted', sa.DECIMAL(precision=12, scale=2), nullable=True),
        sa.Column('units_remaining', sa.DECIMAL(precision=12, scale=2), nullable=True),
        
        # Blockchain Logging
        sa.Column('hcs_topic_id', sa.String(length=50), nullable=True),
        sa.Column('hcs_sequence_number', sa.BIGINT(), nullable=True),
        
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_consumption_logs_meter_created', 'consumption_logs', ['meter_id', sa.text('created_at DESC')])
    op.create_index('idx_consumption_logs_token', 'consumption_logs', ['token_id'])
    op.create_index('idx_consumption_logs_timestamp', 'consumption_logs', [sa.text('timestamp DESC')])


def downgrade() -> None:
    """Drop consumption_logs table"""
    
    # Drop indexes
    op.drop_index('idx_consumption_logs_timestamp', table_name='consumption_logs')
    op.drop_index('idx_consumption_logs_token', table_name='consumption_logs')
    op.drop_index('idx_consumption_logs_meter_created', table_name='consumption_logs')
    
    # Drop table
    op.drop_table('consumption_logs')
