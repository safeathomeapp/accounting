"""v2_030_fk_index_gaps_ai_analysis_results

Revision ID: v2_030_fk_index_gaps_ai_analysis_results
Revises: v2_020_currency_and_amount_checks
Create Date: 2026-01-24

The initial Alembic migration creates foreign keys from:
- ai_analysis_results.suggested_account_id -> accounts.id
- ai_analysis_results.suggested_account_id_local -> accounts.id

...but does not create indexes on those FK columns. This migration adds them.
"""

from alembic import op

revision = "v2_030_fk_index_gaps_ai_analysis_results"
down_revision = "v2_020_currency_and_amount_checks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_ai_analysis_results_suggested_account_id",
        "ai_analysis_results",
        ["suggested_account_id"],
        unique=False,
    )
    op.create_index(
        "ix_ai_analysis_results_suggested_account_id_local",
        "ai_analysis_results",
        ["suggested_account_id_local"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ai_analysis_results_suggested_account_id_local", table_name="ai_analysis_results")
    op.drop_index("ix_ai_analysis_results_suggested_account_id", table_name="ai_analysis_results")
