"""v2_110_accounts_client_enforcement

Enforce accounts are client-scoped with no orphans.

Requirements (from FINAL_NON_NEGOTIABLE_DB_STANCE.md):
1. accounts.client_id must be NOT NULL
2. Composite FK enforces org consistency (no cross-org accounts)
3. Idempotency uniqueness prevents sync retry duplicates

Revision ID: v2_110_accounts_client_enforcement
Revises: v2_095_client_assignments
Create Date: 2026-02-03
"""

from alembic import op

revision = "v2_110_accounts_client_enforcement"
down_revision = "v2_095_client_assignments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # PRE-FLIGHT: Check for orphan accounts before applying NOT NULL
    # If this fails, manual backfill is required first
    # =========================================================================

    # Step 1: Make client_id NOT NULL
    # NOTE: This will fail if orphan accounts exist. Backfill first if needed.
    op.execute("""
        DO $$
        DECLARE
            orphan_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO orphan_count FROM accounts WHERE client_id IS NULL;
            IF orphan_count > 0 THEN
                RAISE EXCEPTION 'Cannot proceed: % orphan accounts with NULL client_id. Backfill required.', orphan_count;
            END IF;
        END$$;
    """)

    op.execute("""
        ALTER TABLE accounts
        ALTER COLUMN client_id SET NOT NULL;
    """)

    # =========================================================================
    # Step 2: Composite FK to enforce org consistency
    # Requires uq_clients_org_id from v2_095
    # =========================================================================

    op.execute("""
        ALTER TABLE accounts
        ADD CONSTRAINT fk_accounts_client
        FOREIGN KEY (organization_id, client_id)
        REFERENCES clients (organization_id, id)
        ON DELETE CASCADE;
    """)

    # =========================================================================
    # Step 3: Idempotency uniqueness for synced accounts
    # Pattern A: platform_name and platform_id are NOT NULL in our schema
    # =========================================================================

    op.execute("""
        CREATE UNIQUE INDEX ux_accounts_client_platform_idempotency
        ON accounts (client_id, platform_name, platform_id);
    """)

    # =========================================================================
    # Step 4: Documentation
    # =========================================================================

    op.execute("""
        COMMENT ON TABLE accounts IS
        'Client-scoped chart of accounts entries. Each client has independent CoA synced from their accounting platform. Enforced: client_id NOT NULL, composite FK to clients, idempotency uniqueness.';
    """)

    op.execute("""
        COMMENT ON CONSTRAINT fk_accounts_client ON accounts IS
        'Composite FK enforces account belongs to same organization as its client. Prevents cross-org data leakage.';
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ux_accounts_client_platform_idempotency;")
    op.execute("ALTER TABLE accounts DROP CONSTRAINT IF EXISTS fk_accounts_client;")
    op.execute("ALTER TABLE accounts ALTER COLUMN client_id DROP NOT NULL;")
