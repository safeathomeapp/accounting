"""v2_095_client_assignments

Add client_assignments table for user-to-client workflow assignments.

Clients belong to Organizations (for access control via RLS).
Assignments are for workflow/responsibility, not access control.
All users in an organization can still access all clients.

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
    # Create client_assignments table
    op.create_table(
        "client_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),

        # Assignment role: primary, accountant, reviewer, backup
        sa.Column("assignment_role", sa.String(50), nullable=False, server_default="accountant"),

        # Status - allows soft-disable without delete
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),

        # Who made the assignment
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),

        # Standard timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),

        # Primary key
        sa.PrimaryKeyConstraint("id"),

        # Foreign keys
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="SET NULL"),

        # One assignment per user per client (can have multiple users per client)
        sa.UniqueConstraint("client_id", "user_id", name="uq_client_assignments_client_user"),
    )

    # Indexes for common queries
    # "Show me my clients" - user's active assignments
    op.create_index(
        "ix_client_assignments_user_active",
        "client_assignments",
        ["user_id"],
        postgresql_where=sa.text("is_active = true")
    )

    # "Who's assigned to this client?"
    op.create_index(
        "ix_client_assignments_client",
        "client_assignments",
        ["client_id"]
    )

    # RLS enforcement
    op.create_index(
        "ix_client_assignments_org",
        "client_assignments",
        ["organization_id"]
    )

    # Add updated_at trigger
    op.execute("""
        CREATE TRIGGER set_updated_at_client_assignments
        BEFORE UPDATE ON client_assignments
        FOR EACH ROW
        EXECUTE FUNCTION public.set_updated_at();
    """)

    # Enable RLS
    op.execute("ALTER TABLE client_assignments ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE client_assignments FORCE ROW LEVEL SECURITY;")

    # Create RLS policy
    op.execute("""
        CREATE POLICY p_client_assignments_tenant_isolation
        ON client_assignments
        FOR ALL
        TO PUBLIC
        USING (organization_id = current_setting('app.org_id', true)::uuid)
        WITH CHECK (organization_id = current_setting('app.org_id', true)::uuid);
    """)

    # Grant permissions to roles
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON client_assignments TO app_user;")
    op.execute("GRANT SELECT ON client_assignments TO app_readonly;")
    op.execute("GRANT ALL ON client_assignments TO app_admin;")

    # Add table comment
    op.execute("""
        COMMENT ON TABLE client_assignments IS
        'User-to-client workflow assignments. Assignments are for workload distribution and responsibility tracking, NOT access control. All users in an organization can access all clients via RLS on organization_id.';
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS p_client_assignments_tenant_isolation ON client_assignments;")
    op.execute("DROP TRIGGER IF EXISTS set_updated_at_client_assignments ON client_assignments;")
    op.drop_table("client_assignments")
