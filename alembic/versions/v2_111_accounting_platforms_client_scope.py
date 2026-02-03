"""v2_111_accounting_platforms_client_scope

Fix semantic collision and add client-scoped platform connections.

Requirements (from FINAL_NON_NEGOTIABLE_DB_STANCE.md):
1. Rename client_id -> oauth_client_id (remove semantic collision)
2. Add managed_client_id as business client FK
3. Composite FK enforces org consistency (declarative, no trigger)

Revision ID: v2_111_accounting_platforms_client_scope
Revises: v2_110_accounts_client_enforcement
Create Date: 2026-02-03
"""

from alembic import op

revision = "v2_111_accounting_platforms_client_scope"
down_revision = "v2_110_accounts_client_enforcement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # Step 1: Rename misleading column
    # client_id is currently OAuth client ID, not business client
    # =========================================================================

    op.execute("""
        ALTER TABLE accounting_platforms
        RENAME COLUMN client_id TO oauth_client_id;
    """)

    # =========================================================================
    # Step 2: Add managed_client_id for business client
    # =========================================================================

    op.execute("""
        ALTER TABLE accounting_platforms
        ADD COLUMN managed_client_id UUID NULL;
    """)

    # =========================================================================
    # Step 3: Add composite unique on accounting_platforms for FK reference
    # (May already exist - do idempotently)
    # =========================================================================

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_accounting_platforms_org_id'
            ) THEN
                ALTER TABLE accounting_platforms
                ADD CONSTRAINT uq_accounting_platforms_org_id
                UNIQUE (organization_id, id);
            END IF;
        END$$;
    """)

    # =========================================================================
    # Step 4: Composite FK enforces org consistency (declarative)
    # managed_client must belong to same organization
    # =========================================================================

    op.execute("""
        ALTER TABLE accounting_platforms
        ADD CONSTRAINT fk_accounting_platforms_managed_client
        FOREIGN KEY (organization_id, managed_client_id)
        REFERENCES clients (organization_id, id)
        ON DELETE SET NULL;
    """)

    # =========================================================================
    # Step 5: Documentation
    # =========================================================================

    op.execute("""
        COMMENT ON COLUMN accounting_platforms.oauth_client_id IS
        'OAuth client ID from the provider (Xero, QBO). NOT the business client. Renamed from client_id to remove semantic collision.';
    """)

    op.execute("""
        COMMENT ON COLUMN accounting_platforms.managed_client_id IS
        'Business client whose external accounting realm this connection represents. Composite FK enforces same-org. Nullable during transition; target: NOT NULL for all new connections.';
    """)

    op.execute("""
        COMMENT ON CONSTRAINT fk_accounting_platforms_managed_client ON accounting_platforms IS
        'Composite FK ensures managed business client belongs to same organization. Declarative enforcement, no trigger required.';
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE accounting_platforms DROP CONSTRAINT IF EXISTS fk_accounting_platforms_managed_client;")
    op.execute("ALTER TABLE accounting_platforms DROP CONSTRAINT IF EXISTS uq_accounting_platforms_org_id;")
    op.execute("ALTER TABLE accounting_platforms DROP COLUMN IF EXISTS managed_client_id;")
    op.execute("ALTER TABLE accounting_platforms RENAME COLUMN oauth_client_id TO client_id;")
