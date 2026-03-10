"""Add prepaid_tokens table for prepaid electricity token management

Revision ID: 20260303_005
Revises: 20260222_004
Create Date: 2026-03-03

Creates prepaid_tokens table to support prepaid electricity token system:
- Token purchase and issuance tracking
- HBAR/USDC payment support
- Units purchased and remaining balance
- Token status lifecycle (active, depleted, expired, cancelled)
- Hedera transaction and HCS logging references

Requirements: FR-8.1 to FR-8.12 (Prepaid Token Management)
Spec: prepaid-smart-meter-mvp
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_prepaid_tokens'
down_revision = '004_add_subsidy_eligibility'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create prepaid_tokens table"""
    
    op.create_table(
        'prepaid_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('token_id', sa.String(length=50), nullable=False, unique=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('meter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meters.id', ondelete='CASCADE'), nullable=False),
        
        # Purchase Details
        sa.Column('units_purchased', sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column('units_remaining', sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column('amount_paid_hbar', sa.DECIMAL(precision=18, scale=8), nullable=True),
        sa.Column('amount_paid_usdc', sa.DECIMAL(precision=18, scale=6), nullable=True),
        sa.Column('amount_paid_fiat', sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.CHAR(length=3), nullable=False),
        sa.Column('exchange_rate', sa.DECIMAL(precision=12, scale=6), nullable=False),
        sa.Column('tariff_rate', sa.DECIMAL(precision=12, scale=6), nullable=False),
        
        # Status
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        
        # Hedera Transaction
        sa.Column('hedera_tx_id', sa.String(length=100), nullable=True),
        sa.Column('hedera_consensus_timestamp', sa.TIMESTAMP(timezone=True), nullable=True),
        
        # Blockchain Logging (HCS)
        sa.Column('hcs_topic_id', sa.String(length=50), nullable=True),
        sa.Column('hcs_sequence_number', sa.BigInteger(), nullable=True),
        
        # Timestamps
        sa.Column('issued_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('depleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        
        # Constraints
        sa.CheckConstraint("status IN ('active', 'depleted', 'expired', 'cancelled')", name='check_prepaid_token_status')
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_prepaid_tokens_user_id', 'prepaid_tokens', ['user_id'], unique=False)
    op.create_index('idx_prepaid_tokens_meter_id', 'prepaid_tokens', ['meter_id'], unique=False)
    op.create_index('idx_prepaid_tokens_status', 'prepaid_tokens', ['status'], unique=False)
    op.create_index('idx_prepaid_tokens_issued_at', 'prepaid_tokens', ['issued_at'], unique=False)


def downgrade() -> None:
    """Drop prepaid_tokens table"""
    
    # Drop indexes
    op.drop_index('idx_prepaid_tokens_issued_at', table_name='prepaid_tokens')
    op.drop_index('idx_prepaid_tokens_status', table_name='prepaid_tokens')
    op.drop_index('idx_prepaid_tokens_meter_id', table_name='prepaid_tokens')
    op.drop_index('idx_prepaid_tokens_user_id', table_name='prepaid_tokens')
    
    # Drop table
    op.drop_table('prepaid_tokens')
