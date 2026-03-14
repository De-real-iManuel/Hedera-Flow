"""Add 'pending' status to prepaid_tokens

Revision ID: 20260312_008
Revises: 007_add_consumption_logs
Create Date: 2026-03-12

Adds 'pending' status to prepaid_tokens table to support two-step payment flow:
1. Token created with status='pending' after user initiates purchase
2. Token updated to status='active' after payment confirmation

This is required for wallet-based payments where:
- User initiates purchase (creates pending token)
- User signs transaction with wallet (MetaMask, WalletConnect)
- Backend confirms transaction and activates token

Requirements: FR-8.6 (Payment verification), US-13 (Wallet signing)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008_add_pending_status'
down_revision = '007_add_consumption_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add 'pending' to allowed status values"""
    
    # Drop the old constraint
    op.drop_constraint('check_prepaid_token_status', 'prepaid_tokens', type_='check')
    
    # Create new constraint with 'pending' status
    op.create_check_constraint(
        'check_prepaid_token_status',
        'prepaid_tokens',
        "status IN ('pending', 'active', 'depleted', 'expired', 'cancelled')"
    )


def downgrade() -> None:
    """Remove 'pending' from allowed status values"""
    
    # Drop the new constraint
    op.drop_constraint('check_prepaid_token_status', 'prepaid_tokens', type_='check')
    
    # Restore old constraint without 'pending'
    op.create_check_constraint(
        'check_prepaid_token_status',
        'prepaid_tokens',
        "status IN ('active', 'depleted', 'expired', 'cancelled')"
    )
