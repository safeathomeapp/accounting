"""v2_073_seed_mapping_data

Revision ID: v2_073_seed_mapping_data
Revises: v2_072_mapping_coverage_view
Create Date: 2026-01-27

Seeds the platform_transaction_mapping table with all known Xero, QuickBooks,
and Mock type/status combinations. Definitions are imported from the canonical
mapping definitions module (single source of truth).
"""

from alembic import op
import sqlalchemy as sa

revision = "v2_073_seed_mapping_data"
down_revision = "v2_072_mapping_coverage_view"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Import definitions from the single source of truth
    from backend.canonical.mapping_definitions import PLATFORM_MAPPINGS

    # Build the table reference for bulk insert
    mapping_table = sa.table(
        'platform_transaction_mapping',
        sa.column('platform_name', sa.String),
        sa.column('source_type', sa.String),
        sa.column('source_status', sa.String),
        sa.column('normalized_type', sa.String),
        sa.column('normalized_status', sa.String),
        sa.column('canonical_bucket', sa.String),
        sa.column('effective_date_source', sa.String),
        sa.column('priority', sa.Integer),
        sa.column('is_active', sa.Boolean),
    )

    rows = []
    for m in PLATFORM_MAPPINGS:
        rows.append({
            "platform_name": m["platform_name"],
            "source_type": m["source_type"],
            "source_status": m["source_status"],
            "normalized_type": m["normalized_type"],
            "normalized_status": m["normalized_status"],
            "canonical_bucket": m["canonical_bucket"],
            "effective_date_source": m.get("effective_date_source", "TRANSACTION_DATE"),
            "priority": m.get("priority", 0),
            "is_active": True,
        })

    op.bulk_insert(mapping_table, rows)


def downgrade() -> None:
    # Remove all seeded rows
    op.execute(
        "DELETE FROM platform_transaction_mapping "
        "WHERE platform_name IN ('xero', 'quickbooks', 'mock')"
    )
