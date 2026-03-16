"""v2_115_document_client_context

Add client_id to document_inbox_item and document_draft tables
to support client-scoped document review workflow.

Revision ID: v2_115_document_client_context
Revises: v2_114_auth_security_definer
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v2_115_document_client_context"
down_revision = "v2_114_auth_security_definer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add client_id to document_inbox_item
    op.add_column(
        "document_inbox_item",
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_document_inbox_item_client_id",
        "document_inbox_item",
        ["client_id"],
    )

    # Add client_id to document_draft
    op.add_column(
        "document_draft",
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_document_draft_client_id",
        "document_draft",
        ["client_id"],
    )


def downgrade() -> None:
    # Remove client_id from document_draft
    op.drop_index("ix_document_draft_client_id", table_name="document_draft")
    op.drop_column("document_draft", "client_id")

    # Remove client_id from document_inbox_item
    op.drop_index("ix_document_inbox_item_client_id", table_name="document_inbox_item")
    op.drop_column("document_inbox_item", "client_id")
