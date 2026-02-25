"""Initial database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-02-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for Hedera Flow MVP"""
    
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    
    # ============================================================================
    # USERS TABLE
    # ============================================================================
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('country_code', sa.CHAR(2), nullable=False),
        sa.Column('hedera_account_id', sa.String(50), unique=True),
        sa.Column('wallet_type', sa.String(20), server_default='hashpack'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('NOW()')),
        sa.Column('last_login', sa.TIMESTAMP, nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.CheckConstraint("country_code IN ('ES', 'US', 'IN', 'BR', 'NG')", name='users_country_code_check')
    )
    
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_hedera_account', 'users', ['hedera_account_id'])
    op.create_index('idx_users_country', 'users', ['country_code'])
    
    # ============================================================================
    # METERS TABLE
    # ============================================================================
    op.create_table(
        'meters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('meter_id', sa.String(50), nullable=False),
        sa.Column('utility_provider', sa.String(100), nullable=False),
        sa.Column('meter_type', sa.String(20)),
        sa.Column('band_classification', sa.String(10), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('is_primary', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('NOW()')),
        sa.CheckConstraint("meter_type IN ('prepaid', 'postpaid')", name='meters_meter_type_check'),
        sa.UniqueConstraint('user_id', 'meter_id', name='meters_user_id_meter_id_key')
    )
    
    op.create_index('idx_meters_user_id', 'meters', ['user_id'])
    op.create_index('idx_meters_meter_id', 'meters', ['meter_id'])
    
    # ============================================================================
    # TARIFFS TABLE
    # ============================================================================
    op.create_table(
        'tariffs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('country_code', sa.CHAR(2), nullable=False),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('utility_provider', sa.String(100), nullable=False),
        sa.Column('currency', sa.CHAR(3), nullable=False),
        sa.Column('rate_structure', postgresql.JSONB, nullable=False),
        sa.Column('taxes_and_fees', postgresql.JSONB, nullable=True),
        sa.Column('subsidies', postgresql.JSONB, nullable=True),
        sa.Column('valid_from', sa.Date, nullable=False),
        sa.Column('valid_until', sa.Date, nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('NOW()'))
    )
    
    op.create_index('idx_tariffs_country_provider', 'tariffs', ['country_code', 'utility_provider'])
    op.create_index('idx_tariffs_active', 'tariffs', ['is_active', 'valid_from', 'valid_until'])
    
    # ============================================================================
    # VERIFICATIONS TABLE
    # ============================================================================
    op.create_table(
        'verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('meter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reading_value', sa.DECIMAL(12, 2), nullable=False),
        sa.Column('previous_reading', sa.DECIMAL(12, 2), nullable=True),
        sa.Column('consumption_kwh', sa.DECIMAL(12, 2), nullable=True),
        sa.Column('image_ipfs_hash', sa.String(100), nullable=True),
        sa.Column('ocr_engine', sa.String(20), nullable=True),
        sa.Column('confidence', sa.DECIMAL(5, 2), nullable=True),
        sa.Column('raw_ocr_text', sa.Text, nullable=True),
        sa.Column('fraud_score', sa.DECIMAL(5, 2), nullable=True),
        sa.Column('fraud_flags', postgresql.JSONB, nullable=True),
        sa.Column('utility_reading', sa.DECIMAL(12, 2), nullable=True),
        sa.Column('utility_api_response', postgresql.JSONB, nullable=True),
        sa.Column('status', sa.String(20)),
        sa.Column('hcs_topic_id', sa.String(50), nullable=True),
        sa.Column('hcs_sequence_number', sa.BigInteger, nullable=True),
        sa.Column('hcs_timestamp', sa.TIMESTAMP, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('NOW()')),
        sa.CheckConstraint("status IN ('VERIFIED', 'WARNING', 'DISCREPANCY', 'FRAUD_DETECTED')", name='verifications_status_check')
    )
    
    op.create_index('idx_verifications_user_id', 'verifications', ['user_id'])
    op.create_index('idx_verifications_meter_id', 'verifications', ['meter_id'])
    op.create_index('idx_verifications_status', 'verifications', ['status'])
    op.create_index('idx_verifications_created_at', 'verifications', [sa.text('created_at DESC')])
    
    # ============================================================================
    # BILLS TABLE
    # ============================================================================
    op.create_table(
        'bills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('meter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('meters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('verification_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('verifications.id'), nullable=True),
        sa.Column('consumption_kwh', sa.DECIMAL(12, 2), nullable=False),
        sa.Column('base_charge', sa.DECIMAL(12, 2), nullable=False),
        sa.Column('taxes', sa.DECIMAL(12, 2), nullable=False),
        sa.Column('subsidies', sa.DECIMAL(12, 2), server_default='0'),
        sa.Column('total_fiat', sa.DECIMAL(12, 2), nullable=False),
        sa.Column('currency', sa.CHAR(3), nullable=False),
        sa.Column('tariff_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tariffs.id'), nullable=True),
        sa.Column('tariff_snapshot', postgresql.JSONB, nullable=True),
        sa.Column('amount_hbar', sa.DECIMAL(18, 8), nullable=True),
        sa.Column('exchange_rate', sa.DECIMAL(12, 6), nullable=True),
        sa.Column('exchange_rate_timestamp', sa.TIMESTAMP, nullable=True),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('hedera_tx_id', sa.String(100), nullable=True),
        sa.Column('hedera_consensus_timestamp', sa.TIMESTAMP, nullable=True),
        sa.Column('hcs_topic_id', sa.String(50), nullable=True),
        sa.Column('hcs_sequence_number', sa.BigInteger, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('NOW()')),
        sa.Column('paid_at', sa.TIMESTAMP, nullable=True),
        sa.CheckConstraint("status IN ('pending', 'paid', 'disputed', 'refunded')", name='bills_status_check')
    )
    
    op.create_index('idx_bills_user_id', 'bills', ['user_id'])
    op.create_index('idx_bills_meter_id', 'bills', ['meter_id'])
    op.create_index('idx_bills_status', 'bills', ['status'])
    op.create_index('idx_bills_created_at', 'bills', [sa.text('created_at DESC')])
    
    # ============================================================================
    # DISPUTES TABLE
    # ============================================================================
    op.create_table(
        'disputes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('dispute_id', sa.String(50), nullable=False, unique=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reason', sa.String(50)),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('evidence_ipfs_hashes', postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column('escrow_amount_hbar', sa.DECIMAL(18, 8), nullable=True),
        sa.Column('escrow_amount_fiat', sa.DECIMAL(12, 2), nullable=True),
        sa.Column('escrow_currency', sa.CHAR(3), nullable=True),
        sa.Column('escrow_tx_id', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('resolved_at', sa.TIMESTAMP, nullable=True),
        sa.Column('hcs_topic_id', sa.String(50), nullable=True),
        sa.Column('hcs_sequence_number', sa.BigInteger, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('NOW()')),
        sa.CheckConstraint("reason IN ('OVERCHARGE', 'METER_ERROR', 'TARIFF_ERROR', 'OTHER')", name='disputes_reason_check'),
        sa.CheckConstraint("status IN ('pending', 'under_review', 'resolved_user', 'resolved_utility', 'cancelled')", name='disputes_status_check')
    )
    
    op.create_index('idx_disputes_user_id', 'disputes', ['user_id'])
    op.create_index('idx_disputes_bill_id', 'disputes', ['bill_id'])
    op.create_index('idx_disputes_status', 'disputes', ['status'])
    op.create_index('idx_disputes_created_at', 'disputes', [sa.text('created_at DESC')])
    
    # ============================================================================
    # EXCHANGE RATES CACHE TABLE
    # ============================================================================
    op.create_table(
        'exchange_rates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('currency', sa.CHAR(3), nullable=False),
        sa.Column('hbar_price', sa.DECIMAL(12, 6), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('fetched_at', sa.TIMESTAMP, server_default=sa.text('NOW()'))
    )
    
    op.create_index('idx_exchange_rates_currency_time', 'exchange_rates', ['currency', sa.text('fetched_at DESC')])
    
    # ============================================================================
    # AUDIT LOGS TABLE
    # ============================================================================
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', postgresql.JSONB, nullable=True),
        sa.Column('ip_address', postgresql.INET, nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('NOW()'))
    )
    
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id', sa.text('created_at DESC')])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action', sa.text('created_at DESC')])


def downgrade() -> None:
    """Drop all tables"""
    
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('audit_logs')
    op.drop_table('exchange_rates')
    op.drop_table('disputes')
    op.drop_table('bills')
    op.drop_table('verifications')
    op.drop_table('tariffs')
    op.drop_table('meters')
    op.drop_table('users')
    
    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
