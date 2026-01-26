"""v2_060_add_client_id_to_accounts

Revision ID: v2_060_add_client_id_to_accounts
Revises: v2_050_add_user_role_column
Create Date: 2026-01-26

Adds client_id to accounts table to support client-specific charts of accounts.

In a multi-client accountancy practice, each client is a separate business
with their own accounting software (Xero, QuickBooks, etc.) and their own
chart of accounts. This migration enables that model.

Changes:
- Adds client_id column to accounts table
- Creates index on client_id
- Creates unique constraint on (client_id, code)
- Drops old organization-level unique constraint
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "v2_060_add_client_id_to_accounts"
down_revision = "v2_050_add_user_role_column"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add client_id column (nullable for now to allow migration of existing data)
    op.add_column(
        'accounts',
        sa.Column('client_id', UUID(as_uuid=True), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_accounts_client_id',
        'accounts',
        'clients',
        ['client_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Create index on client_id
    op.create_index('ix_accounts_client_id', 'accounts', ['client_id'])

    # Drop old organization-level unique constraint if it exists
    # This was: ix_accounts_org_code on (organization_id, code)
    try:
        op.drop_index('ix_accounts_org_code', 'accounts')
    except:
        pass  # Index may not exist

    # Create new client-level unique constraint
    # Each client can have one account per code
    op.create_index(
        'ix_accounts_client_code',
        'accounts',
        ['client_id', 'code'],
        unique=True
    )


def downgrade() -> None:
    # Drop new constraint and index
    op.drop_index('ix_accounts_client_code', 'accounts')
    op.drop_index('ix_accounts_client_id', 'accounts')
    op.drop_constraint('fk_accounts_client_id', 'accounts', type_='foreignkey')
    op.drop_column('accounts', 'client_id')

    # Recreate old constraint
    op.create_index(
        'ix_accounts_org_code',
        'accounts',
        ['organization_id', 'code'],
        unique=True
    )
