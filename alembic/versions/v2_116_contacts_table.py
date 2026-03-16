"""v2_116_contacts_table

Create contacts table for storing client's vendors/customers/suppliers.

Domain Model:
- Organization = The accounting firm
- Client = A business whose books the org manages
- Contact = A vendor/customer that the Client transacts with

Revision ID: v2_116_contacts_table
Revises: v2_115_document_client_context
Create Date: 2026-02-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v2_116_contacts_table"
down_revision = "v2_115_document_client_context"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create contacts table
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("contact_type", sa.String(50), nullable=False, server_default="vendor"),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("tax_number", sa.String(50), nullable=True),
        sa.Column("payment_terms", sa.String(50), nullable=True),
        sa.Column("default_nominal_code", sa.String(50), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True, server_default="GBP"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("platform_id", sa.String(500), nullable=True),
        sa.Column("platform_name", sa.String(50), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index("ix_contacts_client_id", "contacts", ["client_id"])
    op.create_index("ix_contacts_organization_id", "contacts", ["organization_id"])
    op.create_index("ix_contacts_name", "contacts", ["name"])
    op.create_index("ix_contacts_email", "contacts", ["email"])
    op.create_index("ix_contacts_is_active", "contacts", ["is_active"])
    op.create_index("ix_contacts_client_name", "contacts", ["client_id", "name"])

    # Partial unique index for platform sync
    op.execute("""
        CREATE UNIQUE INDEX ix_contacts_client_platform
        ON contacts (client_id, platform_name, platform_id)
        WHERE platform_id IS NOT NULL
    """)

    # Enable RLS
    op.execute("ALTER TABLE contacts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE contacts FORCE ROW LEVEL SECURITY")

    # RLS Policies
    op.execute("""
        CREATE POLICY contacts_org_isolation ON contacts
        FOR ALL
        USING (organization_id = current_setting('app.current_org_id', true)::uuid)
        WITH CHECK (organization_id = current_setting('app.current_org_id', true)::uuid)
    """)

    # Updated_at trigger
    op.execute("""
        CREATE TRIGGER set_contacts_updated_at
        BEFORE UPDATE ON contacts
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS set_contacts_updated_at ON contacts")
    op.execute("DROP POLICY IF EXISTS contacts_org_isolation ON contacts")
    op.drop_table("contacts")
