"""v2_118_document_draft_confirmed_contact

Add explicit confirmed_contact_id to document_draft so confirmed counterparties
resolve to client-scoped contacts instead of overloading the legacy
counterparty_id field.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "v2_118_document_draft_confirmed_contact"
down_revision = "v2_117_client_intelligence_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document_draft",
        sa.Column(
            "confirmed_contact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contacts.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_document_draft_confirmed_contact_id",
        "document_draft",
        ["confirmed_contact_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_document_draft_confirmed_contact_id", table_name="document_draft")
    op.drop_column("document_draft", "confirmed_contact_id")
