"""v2_072_mapping_coverage_view

Revision ID: v2_072_mapping_coverage_view
Revises: v2_071_cashflow_facts_and_quarantine
Create Date: 2026-01-27

Creates a SQL view for monitoring mapping coverage per organization/platform.
Used by the data quality dashboard to show how many transactions are mapped,
quarantined, or unmapped.
"""

from alembic import op

revision = "v2_072_mapping_coverage_view"
down_revision = "v2_071_cashflow_facts_and_quarantine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE VIEW mapping_coverage_stats AS
        SELECT
            t.organization_id,
            t.platform_name,
            COUNT(*)::integer AS total_transactions,
            COUNT(f.id)::integer AS mapped_count,
            COUNT(q.id)::integer AS quarantined_count,
            (COUNT(*) - COUNT(f.id) - COUNT(q.id))::integer AS unmapped_count,
            CASE
                WHEN COUNT(*) = 0 THEN 0.0
                ELSE ROUND((COUNT(f.id)::numeric / COUNT(*)::numeric) * 100, 2)
            END AS coverage_pct
        FROM transactions t
        LEFT JOIN cashflow_facts_v1 f ON f.transaction_id = t.id
        LEFT JOIN ingestion_quarantine q ON q.transaction_id = t.id AND q.resolved_at IS NULL
        GROUP BY t.organization_id, t.platform_name
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS mapping_coverage_stats")
