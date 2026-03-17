"""v2_119_drop_document_draft_counterparty_id

Retire the legacy document_draft.counterparty_id column now that
confirmed_contact_id is the canonical confirmed counterparty path.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "v2_119_drop_document_draft_counterparty_id"
down_revision = "v2_118_document_draft_confirmed_contact"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("document_draft_counterparty_id_fkey", "document_draft", type_="foreignkey")
    op.drop_index("ix_document_draft_counterparty", table_name="document_draft")
    op.drop_column("document_draft", "counterparty_id")


def downgrade() -> None:
    op.add_column(
        "document_draft",
        sa.Column("counterparty_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "document_draft_counterparty_id_fkey",
        "document_draft",
        "clients",
        ["counterparty_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_document_draft_counterparty", "document_draft", ["counterparty_id"])
