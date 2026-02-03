"""v2_112_users_pending_invariant

Enforce pending user state invariant in database.

Requirements (from FINAL_NON_NEGOTIABLE_DB_STANCE.md):
1. Add status column with CHECK constraint
2. Enforce: pending may have NULL org; non-pending must have org
3. Set timestamp and boolean defaults

Revision ID: v2_112_users_pending_invariant
Revises: v2_111_accounting_platforms_client_scope
Create Date: 2026-02-03
"""

from alembic import op

revision = "v2_112_users_pending_invariant"
down_revision = "v2_111_accounting_platforms_client_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # Step 1: Add status column
    # Default to 'pending' for new users
    # =========================================================================

    op.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS status VARCHAR(20);
    """)

    # =========================================================================
    # Step 2: Backfill existing users based on organization_id
    # =========================================================================

    op.execute("""
        UPDATE users SET status = 'active' WHERE organization_id IS NOT NULL AND status IS NULL;
    """)

    op.execute("""
        UPDATE users SET status = 'pending' WHERE organization_id IS NULL AND status IS NULL;
    """)

    # =========================================================================
    # Step 3: Add NOT NULL and CHECK constraints
    # =========================================================================

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN status SET NOT NULL;
    """)

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN status SET DEFAULT 'pending';
    """)

    op.execute("""
        ALTER TABLE users
        ADD CONSTRAINT ck_users_status_values
        CHECK (status IN ('pending', 'active', 'suspended', 'disabled'));
    """)

    # =========================================================================
    # Step 4: Enforce pending/org invariant
    # pending users may have NULL org; all others must have org
    # =========================================================================

    op.execute("""
        ALTER TABLE users
        ADD CONSTRAINT ck_users_org_status
        CHECK (
            (status = 'pending' AND organization_id IS NULL)
            OR
            (status <> 'pending' AND organization_id IS NOT NULL)
        );
    """)

    # =========================================================================
    # Step 5: Set defaults for timestamp and boolean columns
    # =========================================================================

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN created_at SET DEFAULT now();
    """)

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN updated_at SET DEFAULT now();
    """)

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN is_active SET DEFAULT true;
    """)

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN is_admin SET DEFAULT false;
    """)

    # =========================================================================
    # Step 6: Documentation
    # =========================================================================

    op.execute("""
        COMMENT ON COLUMN users.status IS
        'User lifecycle status. Pending users have NULL org_id (registration in progress). Active/suspended/disabled users must have org_id.';
    """)

    op.execute("""
        COMMENT ON CONSTRAINT ck_users_org_status ON users IS
        'DB-enforced invariant: pending users may have NULL org; non-pending users must have org. Prevents active users without tenant context.';
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_org_status;")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_status_values;")
    op.execute("ALTER TABLE users ALTER COLUMN status DROP DEFAULT;")
    op.execute("ALTER TABLE users ALTER COLUMN status DROP NOT NULL;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS status;")
    # Note: We don't remove defaults for created_at, updated_at, is_active, is_admin
    # as they are harmless and expected
