"""v2_080_document_review_tables

Revision ID: v2_080_document_review_tables
Revises: v2_073_seed_mapping_data
Create Date: 2026-01-30

Adds document ingestion and review tables:
- document_inbox_item
- document_ocr_result
- document_draft
- document_draft_line
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "v2_080_document_review_tables"
down_revision = "v2_073_seed_mapping_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_inbox_item",
        sa.Column("id", UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by_user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="upload"),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("checksum_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="uploaded"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_document_inbox_org_id", "document_inbox_item", ["org_id"])
    op.create_index("ix_document_inbox_uploaded_by", "document_inbox_item", ["uploaded_by_user_id"])
    op.create_index("ix_document_inbox_status", "document_inbox_item", ["status"])

    op.create_table(
        "document_ocr_result",
        sa.Column("id", UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("inbox_item_id", UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("ocr_engine", sa.String(50), nullable=False, server_default="stub"),
        sa.Column("raw_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("layout_json", JSONB, nullable=True),
        sa.Column("pages", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["inbox_item_id"], ["document_inbox_item.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("inbox_item_id"),
    )
    op.create_index("ix_document_ocr_org_id", "document_ocr_result", ["org_id"])

    op.create_table(
        "document_draft",
        sa.Column("id", UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("inbox_item_id", UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("doc_type_guess", sa.String(50), nullable=True),
        sa.Column("doc_type_confirmed", sa.String(50), nullable=True),
        sa.Column("counterparty_guess", sa.String(255), nullable=True),
        sa.Column("counterparty_id", UUID(as_uuid=True), nullable=True),
        sa.Column("doc_date_guess", sa.Date(), nullable=True),
        sa.Column("doc_date_confirmed", sa.Date(), nullable=True),
        sa.Column("currency_guess", sa.String(3), nullable=True),
        sa.Column("currency_confirmed", sa.String(3), nullable=True),
        sa.Column("invoice_no_guess", sa.String(100), nullable=True),
        sa.Column("invoice_no_confirmed", sa.String(100), nullable=True),
        sa.Column("totals_guess", JSONB, nullable=True),
        sa.Column("totals_confirmed", JSONB, nullable=True),
        sa.Column("draft_json", JSONB, nullable=True),
        sa.Column("validation_json", JSONB, nullable=True),
        sa.Column("last_edited_by", UUID(as_uuid=True), nullable=True),
        sa.Column("submitted_by", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["inbox_item_id"], ["document_inbox_item.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["counterparty_id"], ["clients.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["last_edited_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["submitted_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("inbox_item_id"),
    )
    op.create_index("ix_document_draft_status", "document_draft", ["status"])
    op.create_index("ix_document_draft_org_id", "document_draft", ["org_id"])
    op.create_index("ix_document_draft_counterparty", "document_draft", ["counterparty_id"])
    op.create_index("ix_document_draft_last_editor", "document_draft", ["last_edited_by"])
    op.create_index("ix_document_draft_submitted_by", "document_draft", ["submitted_by"])

    op.create_table(
        "document_draft_line",
        sa.Column("id", UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("draft_id", UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("line_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("description_guess", sa.Text(), nullable=True),
        sa.Column("description_confirmed", sa.Text(), nullable=True),
        sa.Column("qty", sa.Numeric(15, 2), nullable=False, server_default="1.00"),
        sa.Column("unit_price", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("net", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("vat", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("gross", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("vat_code_guess", sa.String(50), nullable=True),
        sa.Column("vat_code_confirmed", sa.String(50), nullable=True),
        sa.Column("nominal_code_guess", sa.String(50), nullable=True),
        sa.Column("nominal_code_confirmed", sa.String(50), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["draft_id"], ["document_draft.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_document_draft_line_draft_id", "document_draft_line", ["draft_id"])
    op.create_index("ix_document_draft_line_org_id", "document_draft_line", ["org_id"])


def downgrade() -> None:
    op.drop_index("ix_document_draft_line_org_id", table_name="document_draft_line")
    op.drop_index("ix_document_draft_line_draft_id", table_name="document_draft_line")
    op.drop_table("document_draft_line")

    op.drop_index("ix_document_draft_submitted_by", table_name="document_draft")
    op.drop_index("ix_document_draft_last_editor", table_name="document_draft")
    op.drop_index("ix_document_draft_counterparty", table_name="document_draft")
    op.drop_index("ix_document_draft_org_id", table_name="document_draft")
    op.drop_index("ix_document_draft_status", table_name="document_draft")
    op.drop_table("document_draft")

    op.drop_index("ix_document_ocr_org_id", table_name="document_ocr_result")
    op.drop_table("document_ocr_result")

    op.drop_index("ix_document_inbox_uploaded_by", table_name="document_inbox_item")
    op.drop_index("ix_document_inbox_status", table_name="document_inbox_item")
    op.drop_index("ix_document_inbox_org_id", table_name="document_inbox_item")
    op.drop_table("document_inbox_item")
