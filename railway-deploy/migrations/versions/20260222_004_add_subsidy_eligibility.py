"""Add subsidy eligibility fields to users table

Revision ID: 20260222_004
Revises: 20260221_003
Create Date: 2026-02-22

Adds subsidy eligibility tracking fields to users table:
- subsidy_eligible: Boolean flag for eligibility
- subsidy_type: Type of subsidy (low_income, senior_citizen, disability, energy_efficiency)
- subsidy_verified_at: Timestamp when eligibility was verified
- subsidy_expires_at: Timestamp when eligibility expires

Requirements: FR-4.5 (System shall apply subsidies if user eligible)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_subsidy_eligibility'
down_revision = '003_add_utility_providers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add subsidy eligibility fields to users table"""
    
    # Add subsidy eligibility columns
    op.add_column('users', sa.Column('subsidy_eligible', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('subsidy_type', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('subsidy_verified_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('users', sa.Column('subsidy_expires_at', sa.TIMESTAMP(timezone=True), nullable=True))
    
    # Add index for subsidy eligibility queries
    op.create_index('idx_users_subsidy_eligible', 'users', ['subsidy_eligible'], unique=False)
    op.create_index('idx_users_subsidy_expires', 'users', ['subsidy_expires_at'], unique=False)


def downgrade() -> None:
    """Remove subsidy eligibility fields from users table"""
    
    # Drop indexes
    op.drop_index('idx_users_subsidy_expires', table_name='users')
    op.drop_index('idx_users_subsidy_eligible', table_name='users')
    
    # Drop columns
    op.drop_column('users', 'subsidy_expires_at')
    op.drop_column('users', 'subsidy_verified_at')
    op.drop_column('users', 'subsidy_type')
    op.drop_column('users', 'subsidy_eligible')
