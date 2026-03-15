"""Add STS token field to prepaid_tokens

Revision ID: 009_add_sts_token
Revises: 008_add_pending_status
Create Date: 2026-03-13 11:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009_add_sts_token'
down_revision = '008_add_pending_status'
branch_labels = None
depends_on = None


def upgrade():
    """Add sts_token column to prepaid_tokens table"""
    # Add sts_token column
    op.add_column('prepaid_tokens', sa.Column('sts_token', sa.String(25), nullable=True))
    
    # Add index for sts_token
    op.create_index('ix_prepaid_tokens_sts_token', 'prepaid_tokens', ['sts_token'])


def downgrade():
    """Remove sts_token column from prepaid_tokens table"""
    # Drop index
    op.drop_index('ix_prepaid_tokens_sts_token', 'prepaid_tokens')
    
    # Drop column
    op.drop_column('prepaid_tokens', 'sts_token')