"""v2_050_add_user_role_column

Revision ID: v2_050_add_user_role_column
Revises: v2_040_org_scoped_platform_uniqueness
Create Date: 2026-01-26

Adds role column to users table for role-based access control.

Valid roles:
- admin: Full access - can manage users, settings, and all data
- manager: Can manage clients, transactions, and view reports
- accountant: Can view and edit transactions and accounts
- viewer: Read-only access to view data
"""

from alembic import op
import sqlalchemy as sa

revision = "v2_050_add_user_role_column"
down_revision = "v2_040_org_scoped_platform_uniqueness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add role column with default value 'viewer'
    op.add_column(
        'users',
        sa.Column('role', sa.String(50), nullable=False, server_default='viewer')
    )

    # Update existing admin users to have 'admin' role
    op.execute("""
        UPDATE users SET role = 'admin' WHERE is_admin = true;
    """)


def downgrade() -> None:
    op.drop_column('users', 'role')
