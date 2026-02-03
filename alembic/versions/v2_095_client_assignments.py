"""v2_095_client_assignments

Add client_assignments table for user-to-client workflow assignments.

Key design decisions:
1. Composite FKs enforce same-org constraint at DB level (prevents cross-org bugs)
2. CHECK constraint on assignment_role (prevents role drift)
3. Partial indexes for active assignments (common query pattern)
4. RLS on organization_id (tenant isolation)

Revision ID: v2_095_client_assignments
Revises: v2_090_rls_policies
Create Date: 2026-02-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v2_095_client_assignments"
down_revision = "v2_090_rls_policies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # STEP 1: Add composite unique constraints to parent tables
    # These enable composite FKs that enforce same-org membership
    # =========================================================================

    # clients: UNIQUE (organization_id, id) for composite FK
    op.execute("""
        ALTER TABLE clients
        ADD CONSTRAINT uq_clients_org_id UNIQUE (organization_id, id);
    """)

    # users: UNIQUE (organization_id, id) for composite FK
    # Note: organization_id can be NULL during registration, but that's OK:
    # - The id is already unique (PK), so (org_id, id) pairs are naturally unique
    # - NULL org_id rows won't match FK lookups (FKs require non-NULL values)
    # - Assignments only reference users with org_id (active users)
    op.execute("""
        ALTER TABLE users
        ADD CONSTRAINT uq_users_org_id UNIQUE (organization_id, id);
    """)

    # =========================================================================
    # STEP 2: Create client_assignments table with composite FKs
    # =========================================================================

    op.execute("""
        CREATE TABLE client_assignments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id UUID NOT NULL,
            client_id UUID NOT NULL,
            user_id UUID NOT NULL,

            -- Assignment role with CHECK constraint (no role drift)
            assignment_role VARCHAR(50) NOT NULL DEFAULT 'accountant'
                CHECK (assignment_role IN ('primary', 'accountant', 'reviewer', 'backup')),

            -- Status - allows soft-disable without delete
            is_active BOOLEAN NOT NULL DEFAULT TRUE,

            -- Who made the assignment (also org-scoped)
            assigned_by UUID,
            assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),

            -- Standard timestamps
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

            -- Composite FK to clients: enforces client belongs to same org
            CONSTRAINT fk_client_assignments_client
                FOREIGN KEY (organization_id, client_id)
                REFERENCES clients (organization_id, id)
                ON DELETE CASCADE,

            -- Composite FK to users: enforces user belongs to same org
            CONSTRAINT fk_client_assignments_user
                FOREIGN KEY (organization_id, user_id)
                REFERENCES users (organization_id, id)
                ON DELETE CASCADE,

            -- Composite FK for assigned_by: enforces assigner belongs to same org
            CONSTRAINT fk_client_assignments_assigner
                FOREIGN KEY (organization_id, assigned_by)
                REFERENCES users (organization_id, id)
                ON DELETE SET NULL,

            -- Simple FK to organization for RLS
            CONSTRAINT fk_client_assignments_org
                FOREIGN KEY (organization_id)
                REFERENCES organizations (id)
                ON DELETE CASCADE,

            -- One assignment per user per client
            CONSTRAINT uq_client_assignments_client_user
                UNIQUE (client_id, user_id)
        );
    """)

    # =========================================================================
    # STEP 3: Create indexes for common queries
    # =========================================================================

    # "Show me my clients" - user's active assignments
    op.execute("""
        CREATE INDEX ix_client_assignments_user_active
        ON client_assignments (user_id)
        WHERE is_active = TRUE;
    """)

    # "Who's assigned to this client?" - client's active team
    op.execute("""
        CREATE INDEX ix_client_assignments_client_active
        ON client_assignments (client_id)
        WHERE is_active = TRUE;
    """)

    # RLS + user lookup (for "my clients in this org" with RLS context)
    op.execute("""
        CREATE INDEX ix_client_assignments_org_user_active
        ON client_assignments (organization_id, user_id)
        WHERE is_active = TRUE;
    """)

    # General org index for RLS enforcement
    op.execute("""
        CREATE INDEX ix_client_assignments_org
        ON client_assignments (organization_id);
    """)

    # =========================================================================
    # STEP 4: Add updated_at trigger
    # =========================================================================

    op.execute("""
        CREATE TRIGGER set_updated_at_client_assignments
        BEFORE UPDATE ON client_assignments
        FOR EACH ROW
        EXECUTE FUNCTION public.set_updated_at();
    """)

    # =========================================================================
    # STEP 5: Enable RLS
    # =========================================================================

    op.execute("ALTER TABLE client_assignments ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE client_assignments FORCE ROW LEVEL SECURITY;")

    op.execute("""
        CREATE POLICY p_client_assignments_tenant_isolation
        ON client_assignments
        FOR ALL
        TO PUBLIC
        USING (organization_id = current_setting('app.org_id', true)::uuid)
        WITH CHECK (organization_id = current_setting('app.org_id', true)::uuid);
    """)

    # =========================================================================
    # STEP 6: Grant permissions
    # =========================================================================

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON client_assignments TO app_user;")
    op.execute("GRANT SELECT ON client_assignments TO app_readonly;")
    op.execute("GRANT ALL ON client_assignments TO app_admin;")

    # =========================================================================
    # STEP 7: Add documentation
    # =========================================================================

    op.execute("""
        COMMENT ON TABLE client_assignments IS
        'User-to-client workflow assignments. Composite FKs enforce same-org membership at DB level. Assignments are for workload distribution, NOT access control.';
    """)

    op.execute("""
        COMMENT ON CONSTRAINT fk_client_assignments_client ON client_assignments IS
        'Composite FK ensures client belongs to same organization as assignment.';
    """)

    op.execute("""
        COMMENT ON CONSTRAINT fk_client_assignments_user ON client_assignments IS
        'Composite FK ensures user belongs to same organization as assignment.';
    """)


def downgrade() -> None:
    # Drop client_assignments
    op.execute("DROP POLICY IF EXISTS p_client_assignments_tenant_isolation ON client_assignments;")
    op.execute("DROP TRIGGER IF EXISTS set_updated_at_client_assignments ON client_assignments;")
    op.execute("DROP TABLE IF EXISTS client_assignments;")

    # Remove composite unique constraints from parent tables
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS uq_users_org_id;")
    op.execute("ALTER TABLE clients DROP CONSTRAINT IF EXISTS uq_clients_org_id;")
