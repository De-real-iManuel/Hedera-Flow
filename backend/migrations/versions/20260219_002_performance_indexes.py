"""Add performance optimization indexes

Revision ID: 002_performance_indexes
Revises: 001_initial_schema
Create Date: 2026-02-19 12:00:00.000000

This migration adds additional indexes for performance optimization to meet:
- NFR-1.6: API response time < 500ms (95th percentile)
- NFR-3.2: Database shall support 1M+ verifications

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_performance_indexes'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance optimization indexes"""
    
    # ============================================================================
    # USERS TABLE - Additional Indexes
    # ============================================================================
    
    # Composite index for active users by country (common query pattern)
    op.create_index(
        'idx_users_active_country',
        'users',
        ['is_active', 'country_code'],
        postgresql_where=sa.text('is_active = true')
    )
    
    # Index for last login queries (admin analytics)
    op.create_index(
        'idx_users_last_login',
        'users',
        [sa.text('last_login DESC')],
        postgresql_where=sa.text('last_login IS NOT NULL')
    )
    
    # ============================================================================
    # METERS TABLE - Additional Indexes
    # ============================================================================
    
    # Composite index for user's primary meter lookup
    op.create_index(
        'idx_meters_user_primary',
        'meters',
        ['user_id', 'is_primary'],
        postgresql_where=sa.text('is_primary = true')
    )
    
    # Index for utility provider queries (analytics)
    op.create_index(
        'idx_meters_utility_provider',
        'meters',
        ['utility_provider']
    )
    
    # Composite index for Nigeria band classification queries
    op.create_index(
        'idx_meters_band_classification',
        'meters',
        ['utility_provider', 'band_classification'],
        postgresql_where=sa.text("band_classification IS NOT NULL")
    )
    
    # ============================================================================
    # TARIFFS TABLE - Additional Indexes
    # ============================================================================
    
    # Composite index for active tariff lookups by region
    op.create_index(
        'idx_tariffs_region_active',
        'tariffs',
        ['country_code', 'region', 'utility_provider', 'is_active'],
        postgresql_where=sa.text('is_active = true')
    )
    
    # Index for date range queries (finding valid tariffs)
    op.create_index(
        'idx_tariffs_validity_dates',
        'tariffs',
        ['valid_from', 'valid_until']
    )
    
    # ============================================================================
    # VERIFICATIONS TABLE - Additional Indexes
    # ============================================================================
    
    # Composite index for user's recent verifications (dashboard query)
    op.create_index(
        'idx_verifications_user_recent',
        'verifications',
        ['user_id', sa.text('created_at DESC')],
        postgresql_include=['status', 'reading_value', 'confidence']
    )
    
    # Composite index for meter's verification history
    op.create_index(
        'idx_verifications_meter_history',
        'verifications',
        ['meter_id', sa.text('created_at DESC')],
        postgresql_include=['reading_value', 'consumption_kwh']
    )
    
    # Index for fraud detection queries
    op.create_index(
        'idx_verifications_fraud_score',
        'verifications',
        ['fraud_score'],
        postgresql_where=sa.text('fraud_score > 0.4')
    )
    
    # Index for HCS sequence number lookups
    op.create_index(
        'idx_verifications_hcs',
        'verifications',
        ['hcs_topic_id', 'hcs_sequence_number']
    )
    
    # Composite index for status-based queries with date
    op.create_index(
        'idx_verifications_status_date',
        'verifications',
        ['status', sa.text('created_at DESC')]
    )
    
    # ============================================================================
    # BILLS TABLE - Additional Indexes
    # ============================================================================
    
    # Composite index for user's bill history with status
    op.create_index(
        'idx_bills_user_status',
        'bills',
        ['user_id', 'status', sa.text('created_at DESC')],
        postgresql_include=['total_fiat', 'currency']
    )
    
    # Index for pending bills (payment processing)
    op.create_index(
        'idx_bills_pending',
        'bills',
        [sa.text('created_at DESC')],
        postgresql_where=sa.text("status = 'pending'")
    )
    
    # Index for paid bills by date (analytics)
    op.create_index(
        'idx_bills_paid_date',
        'bills',
        [sa.text('paid_at DESC')],
        postgresql_where=sa.text("status = 'paid' AND paid_at IS NOT NULL")
    )
    
    # Index for Hedera transaction lookups
    op.create_index(
        'idx_bills_hedera_tx',
        'bills',
        ['hedera_tx_id'],
        postgresql_where=sa.text('hedera_tx_id IS NOT NULL')
    )
    
    # Composite index for verification-bill relationship
    op.create_index(
        'idx_bills_verification',
        'bills',
        ['verification_id', 'status']
    )
    
    # Index for tariff usage analytics
    op.create_index(
        'idx_bills_tariff',
        'bills',
        ['tariff_id', sa.text('created_at DESC')]
    )
    
    # ============================================================================
    # DISPUTES TABLE - Additional Indexes
    # ============================================================================
    
    # Composite index for user's dispute history
    op.create_index(
        'idx_disputes_user_status',
        'disputes',
        ['user_id', 'status', sa.text('created_at DESC')]
    )
    
    # Index for pending disputes (admin review queue)
    op.create_index(
        'idx_disputes_pending',
        'disputes',
        [sa.text('created_at DESC')],
        postgresql_where=sa.text("status IN ('pending', 'under_review')")
    )
    
    # Index for dispute resolution tracking
    op.create_index(
        'idx_disputes_resolved',
        'disputes',
        ['resolved_by', sa.text('resolved_at DESC')],
        postgresql_where=sa.text('resolved_at IS NOT NULL')
    )
    
    # Index for dispute reason analytics
    op.create_index(
        'idx_disputes_reason',
        'disputes',
        ['reason', 'status']
    )
    
    # ============================================================================
    # EXCHANGE RATES TABLE - Additional Indexes
    # ============================================================================
    
    # Composite index for latest rate by currency (most common query)
    op.create_index(
        'idx_exchange_rates_latest',
        'exchange_rates',
        ['currency', sa.text('fetched_at DESC')],
        postgresql_include=['hbar_price', 'source']
    )
    
    # Index for rate source analytics
    op.create_index(
        'idx_exchange_rates_source',
        'exchange_rates',
        ['source', sa.text('fetched_at DESC')]
    )
    
    # ============================================================================
    # AUDIT LOGS TABLE - Additional Indexes
    # ============================================================================
    
    # Composite index for entity-specific audit trails
    op.create_index(
        'idx_audit_logs_entity',
        'audit_logs',
        ['entity_type', 'entity_id', sa.text('created_at DESC')]
    )
    
    # Index for IP-based security queries
    op.create_index(
        'idx_audit_logs_ip',
        'audit_logs',
        ['ip_address', sa.text('created_at DESC')]
    )
    
    # Composite index for action-based queries by user
    op.create_index(
        'idx_audit_logs_user_action',
        'audit_logs',
        ['user_id', 'action', sa.text('created_at DESC')]
    )


def downgrade() -> None:
    """Remove performance optimization indexes"""
    
    # Drop indexes in reverse order
    
    # Audit logs indexes
    op.drop_index('idx_audit_logs_user_action', table_name='audit_logs')
    op.drop_index('idx_audit_logs_ip', table_name='audit_logs')
    op.drop_index('idx_audit_logs_entity', table_name='audit_logs')
    
    # Exchange rates indexes
    op.drop_index('idx_exchange_rates_source', table_name='exchange_rates')
    op.drop_index('idx_exchange_rates_latest', table_name='exchange_rates')
    
    # Disputes indexes
    op.drop_index('idx_disputes_reason', table_name='disputes')
    op.drop_index('idx_disputes_resolved', table_name='disputes')
    op.drop_index('idx_disputes_pending', table_name='disputes')
    op.drop_index('idx_disputes_user_status', table_name='disputes')
    
    # Bills indexes
    op.drop_index('idx_bills_tariff', table_name='bills')
    op.drop_index('idx_bills_verification', table_name='bills')
    op.drop_index('idx_bills_hedera_tx', table_name='bills')
    op.drop_index('idx_bills_paid_date', table_name='bills')
    op.drop_index('idx_bills_pending', table_name='bills')
    op.drop_index('idx_bills_user_status', table_name='bills')
    
    # Verifications indexes
    op.drop_index('idx_verifications_status_date', table_name='verifications')
    op.drop_index('idx_verifications_hcs', table_name='verifications')
    op.drop_index('idx_verifications_fraud_score', table_name='verifications')
    op.drop_index('idx_verifications_meter_history', table_name='verifications')
    op.drop_index('idx_verifications_user_recent', table_name='verifications')
    
    # Tariffs indexes
    op.drop_index('idx_tariffs_validity_dates', table_name='tariffs')
    op.drop_index('idx_tariffs_region_active', table_name='tariffs')
    
    # Meters indexes
    op.drop_index('idx_meters_band_classification', table_name='meters')
    op.drop_index('idx_meters_utility_provider', table_name='meters')
    op.drop_index('idx_meters_user_primary', table_name='meters')
    
    # Users indexes
    op.drop_index('idx_users_last_login', table_name='users')
    op.drop_index('idx_users_active_country', table_name='users')
