"""Add utility_providers table

Revision ID: 003_add_utility_providers
Revises: 002_performance_indexes
Create Date: 2026-02-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_add_utility_providers'
down_revision: Union[str, None] = '002_performance_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create utility_providers table and update meters table"""
    
    # ============================================================================
    # UTILITY PROVIDERS TABLE
    # ============================================================================
    op.create_table(
        'utility_providers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('country_code', sa.CHAR(2), nullable=False),
        sa.Column('state_province', sa.String(100), nullable=False),
        sa.Column('provider_name', sa.String(100), nullable=False),
        sa.Column('provider_code', sa.String(20), nullable=False),
        sa.Column('service_areas', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint("country_code IN ('ES', 'US', 'IN', 'BR', 'NG')", name='utility_providers_country_code_check')
    )
    
    # Create indexes
    op.create_index('idx_utility_providers_country', 'utility_providers', ['country_code'])
    op.create_index('idx_utility_providers_state', 'utility_providers', ['state_province'])
    op.create_index('idx_utility_providers_country_state', 'utility_providers', ['country_code', 'state_province'])
    op.create_index('idx_utility_providers_code', 'utility_providers', ['provider_code'])
    op.create_index('idx_utility_providers_active', 'utility_providers', ['is_active'])
    
    # Create unique constraint
    op.create_unique_constraint(
        'utility_providers_country_state_code_key',
        'utility_providers',
        ['country_code', 'state_province', 'provider_code']
    )
    
    # ============================================================================
    # UPDATE METERS TABLE
    # ============================================================================
    # Add utility_provider_id column (nullable initially for migration)
    op.add_column(
        'meters',
        sa.Column('utility_provider_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Add state_province column (nullable initially for migration)
    op.add_column(
        'meters',
        sa.Column('state_province', sa.String(100), nullable=True)
    )
    
    # Create foreign key constraint
    op.create_foreign_key(
        'meters_utility_provider_id_fkey',
        'meters',
        'utility_providers',
        ['utility_provider_id'],
        ['id']
    )
    
    # Create index on utility_provider_id
    op.create_index('idx_meters_utility_provider_id', 'meters', ['utility_provider_id'])


def downgrade() -> None:
    """Drop utility_providers table and revert meters table changes"""
    
    # Drop meters table changes
    op.drop_index('idx_meters_utility_provider_id', table_name='meters')
    op.drop_constraint('meters_utility_provider_id_fkey', 'meters', type_='foreignkey')
    op.drop_column('meters', 'state_province')
    op.drop_column('meters', 'utility_provider_id')
    
    # Drop utility_providers table
    op.drop_index('idx_utility_providers_active', table_name='utility_providers')
    op.drop_index('idx_utility_providers_code', table_name='utility_providers')
    op.drop_index('idx_utility_providers_country_state', table_name='utility_providers')
    op.drop_index('idx_utility_providers_state', table_name='utility_providers')
    op.drop_index('idx_utility_providers_country', table_name='utility_providers')
    op.drop_table('utility_providers')
