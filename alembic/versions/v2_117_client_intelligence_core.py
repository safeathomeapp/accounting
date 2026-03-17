"""v2_117_client_intelligence_core

Add the lean, additive client intelligence schema:
- client_intelligence_profile
- client_supplier_alias
- client_accounting_pattern
- client_intelligence_event

Revision ID: v2_117_client_intelligence_core
Revises: v2_116_contacts_table
Create Date: 2026-03-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v2_117_client_intelligence_core"
down_revision = "v2_116_contacts_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_intelligence_profile",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("last_reviewed_document_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("client_id", name="uq_client_intelligence_profile_client"),
        sa.CheckConstraint("schema_version >= 1", name="ck_client_intelligence_profile_schema_version"),
    )
    op.create_index("ix_client_intelligence_profile_organization_id", "client_intelligence_profile", ["organization_id"])
    op.create_index("ix_client_intelligence_profile_client_id", "client_intelligence_profile", ["client_id"])
    op.create_index("ix_client_intelligence_profile_status", "client_intelligence_profile", ["status"])
    op.create_index("ix_client_intelligence_profile_org_client", "client_intelligence_profile", ["organization_id", "client_id"])

    op.create_table(
        "client_supplier_alias",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("client_intelligence_profile.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias_text", sa.String(255), nullable=False),
        sa.Column("alias_normalized", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("match_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("confidence_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("match_count >= 0", name="ck_client_supplier_alias_match_count"),
        sa.CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
            name="ck_client_supplier_alias_confidence",
        ),
        sa.UniqueConstraint(
            "client_id",
            "contact_id",
            "alias_normalized",
            "source_type",
            name="uq_client_supplier_alias_client_contact_alias_source",
        ),
    )
    op.create_index("ix_client_supplier_alias_organization_id", "client_supplier_alias", ["organization_id"])
    op.create_index("ix_client_supplier_alias_client_id", "client_supplier_alias", ["client_id"])
    op.create_index("ix_client_supplier_alias_profile_id", "client_supplier_alias", ["profile_id"])
    op.create_index("ix_client_supplier_alias_contact_id", "client_supplier_alias", ["contact_id"])
    op.create_index("ix_client_supplier_alias_is_active", "client_supplier_alias", ["is_active"])
    op.create_index("ix_client_supplier_alias_client_alias", "client_supplier_alias", ["client_id", "alias_normalized"])
    op.create_index("ix_client_supplier_alias_org_client", "client_supplier_alias", ["organization_id", "client_id"])

    op.create_table(
        "client_accounting_pattern",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("client_intelligence_profile.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pattern_type", sa.String(50), nullable=False),
        sa.Column("pattern_key", sa.String(255), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("suggested_nominal_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("suggested_tax_code", sa.String(50), nullable=True),
        sa.Column("suggested_document_type", sa.String(50), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("usage_count >= 0", name="ck_client_accounting_pattern_usage_count"),
        sa.CheckConstraint("success_count >= 0", name="ck_client_accounting_pattern_success_count"),
        sa.CheckConstraint("success_count <= usage_count", name="ck_client_accounting_pattern_success_lte_usage"),
        sa.CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
            name="ck_client_accounting_pattern_confidence",
        ),
    )
    op.create_index("ix_client_accounting_pattern_organization_id", "client_accounting_pattern", ["organization_id"])
    op.create_index("ix_client_accounting_pattern_client_id", "client_accounting_pattern", ["client_id"])
    op.create_index("ix_client_accounting_pattern_profile_id", "client_accounting_pattern", ["profile_id"])
    op.create_index("ix_client_accounting_pattern_contact_id", "client_accounting_pattern", ["contact_id"])
    op.create_index("ix_client_accounting_pattern_suggested_nominal_account_id", "client_accounting_pattern", ["suggested_nominal_account_id"])
    op.create_index("ix_client_accounting_pattern_is_active", "client_accounting_pattern", ["is_active"])
    op.create_index("ix_client_accounting_pattern_client_key", "client_accounting_pattern", ["client_id", "pattern_type", "pattern_key"])
    op.create_index("ix_client_accounting_pattern_org_client", "client_accounting_pattern", ["organization_id", "client_id"])

    op.create_table(
        "client_intelligence_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("client_intelligence_profile.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("source_inbox_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_inbox_item.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_draft_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_draft.id", ondelete="SET NULL"), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_client_intelligence_event_organization_id", "client_intelligence_event", ["organization_id"])
    op.create_index("ix_client_intelligence_event_client_id", "client_intelligence_event", ["client_id"])
    op.create_index("ix_client_intelligence_event_profile_id", "client_intelligence_event", ["profile_id"])
    op.create_index("ix_client_intelligence_event_source_inbox_item_id", "client_intelligence_event", ["source_inbox_item_id"])
    op.create_index("ix_client_intelligence_event_source_draft_id", "client_intelligence_event", ["source_draft_id"])
    op.create_index("ix_client_intelligence_event_created_by_user_id", "client_intelligence_event", ["created_by_user_id"])
    op.create_index("ix_client_intelligence_event_created_at", "client_intelligence_event", ["created_at"])
    op.create_index("ix_client_intelligence_event_client_profile_created", "client_intelligence_event", ["client_id", "profile_id", "created_at"])
    op.create_index("ix_client_intelligence_event_org_client", "client_intelligence_event", ["organization_id", "client_id"])

    op.execute("""
        CREATE TRIGGER set_client_intelligence_profile_updated_at
        BEFORE UPDATE ON client_intelligence_profile
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at()
    """)
    op.execute("""
        CREATE TRIGGER set_client_supplier_alias_updated_at
        BEFORE UPDATE ON client_supplier_alias
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at()
    """)
    op.execute("""
        CREATE TRIGGER set_client_accounting_pattern_updated_at
        BEFORE UPDATE ON client_accounting_pattern
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at()
    """)

    for table_name in (
        "client_intelligence_profile",
        "client_supplier_alias",
        "client_accounting_pattern",
        "client_intelligence_event",
    ):
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY p_{table_name}_tenant_isolation
            ON {table_name}
            FOR ALL
            TO PUBLIC
            USING (organization_id = current_setting('app.org_id', true)::uuid)
            WITH CHECK (organization_id = current_setting('app.org_id', true)::uuid)
        """)


def downgrade() -> None:
    for table_name in (
        "client_intelligence_event",
        "client_accounting_pattern",
        "client_supplier_alias",
        "client_intelligence_profile",
    ):
        op.execute(f"DROP POLICY IF EXISTS p_{table_name}_tenant_isolation ON {table_name}")

    op.execute("DROP TRIGGER IF EXISTS set_client_accounting_pattern_updated_at ON client_accounting_pattern")
    op.execute("DROP TRIGGER IF EXISTS set_client_supplier_alias_updated_at ON client_supplier_alias")
    op.execute("DROP TRIGGER IF EXISTS set_client_intelligence_profile_updated_at ON client_intelligence_profile")

    op.drop_index("ix_client_intelligence_event_org_client", table_name="client_intelligence_event")
    op.drop_index("ix_client_intelligence_event_client_profile_created", table_name="client_intelligence_event")
    op.drop_index("ix_client_intelligence_event_created_at", table_name="client_intelligence_event")
    op.drop_index("ix_client_intelligence_event_created_by_user_id", table_name="client_intelligence_event")
    op.drop_index("ix_client_intelligence_event_source_draft_id", table_name="client_intelligence_event")
    op.drop_index("ix_client_intelligence_event_source_inbox_item_id", table_name="client_intelligence_event")
    op.drop_index("ix_client_intelligence_event_profile_id", table_name="client_intelligence_event")
    op.drop_index("ix_client_intelligence_event_client_id", table_name="client_intelligence_event")
    op.drop_index("ix_client_intelligence_event_organization_id", table_name="client_intelligence_event")
    op.drop_table("client_intelligence_event")

    op.drop_index("ix_client_accounting_pattern_org_client", table_name="client_accounting_pattern")
    op.drop_index("ix_client_accounting_pattern_client_key", table_name="client_accounting_pattern")
    op.drop_index("ix_client_accounting_pattern_is_active", table_name="client_accounting_pattern")
    op.drop_index("ix_client_accounting_pattern_suggested_nominal_account_id", table_name="client_accounting_pattern")
    op.drop_index("ix_client_accounting_pattern_contact_id", table_name="client_accounting_pattern")
    op.drop_index("ix_client_accounting_pattern_profile_id", table_name="client_accounting_pattern")
    op.drop_index("ix_client_accounting_pattern_client_id", table_name="client_accounting_pattern")
    op.drop_index("ix_client_accounting_pattern_organization_id", table_name="client_accounting_pattern")
    op.drop_table("client_accounting_pattern")

    op.drop_index("ix_client_supplier_alias_org_client", table_name="client_supplier_alias")
    op.drop_index("ix_client_supplier_alias_client_alias", table_name="client_supplier_alias")
    op.drop_index("ix_client_supplier_alias_is_active", table_name="client_supplier_alias")
    op.drop_index("ix_client_supplier_alias_contact_id", table_name="client_supplier_alias")
    op.drop_index("ix_client_supplier_alias_profile_id", table_name="client_supplier_alias")
    op.drop_index("ix_client_supplier_alias_client_id", table_name="client_supplier_alias")
    op.drop_index("ix_client_supplier_alias_organization_id", table_name="client_supplier_alias")
    op.drop_table("client_supplier_alias")

    op.drop_index("ix_client_intelligence_profile_org_client", table_name="client_intelligence_profile")
    op.drop_index("ix_client_intelligence_profile_status", table_name="client_intelligence_profile")
    op.drop_index("ix_client_intelligence_profile_client_id", table_name="client_intelligence_profile")
    op.drop_index("ix_client_intelligence_profile_organization_id", table_name="client_intelligence_profile")
    op.drop_table("client_intelligence_profile")
