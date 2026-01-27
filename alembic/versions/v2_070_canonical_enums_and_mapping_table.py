"""v2_070_canonical_enums_and_mapping_table

Revision ID: v2_070_canonical_enums_and_mapping_table
Revises: v2_060_add_client_id_to_accounts
Create Date: 2026-01-27

Creates the canonical data mapping infrastructure:
- 4 PostgreSQL enums for normalized transaction classification
- platform_transaction_mapping table linking platform types/statuses to canonical buckets

This is Layer 2 of the architecture:
  transactions -> MappingEngine -> platform_transaction_mapping -> cashflow_facts_v1
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM as PG_ENUM

revision = "v2_070_canonical_enums_and_mapping_table"
down_revision = "v2_060_add_client_id_to_accounts"
branch_labels = None
depends_on = None

# Enum types for standalone create/drop operations
normalized_txn_type = sa.Enum(
    'SALES_INVOICE', 'PURCHASE_INVOICE', 'CREDIT_NOTE',
    'BANK_PAYMENT', 'BANK_RECEIPT', 'JOURNAL', 'TRANSFER', 'OTHER',
    name='normalized_txn_type'
)

normalized_txn_status = sa.Enum(
    'DRAFT', 'AWAITING_APPROVAL', 'APPROVED', 'SENT', 'PAID', 'VOIDED', 'UNKNOWN',
    name='normalized_txn_status'
)

cashflow_bucket = sa.Enum(
    'AR_CURRENT', 'AR_OVERDUE', 'AP_CURRENT', 'AP_OVERDUE',
    'CASH_IN', 'CASH_OUT', 'NON_CASH', 'IGNORE',
    name='cashflow_bucket'
)

date_source = sa.Enum(
    'DUE_DATE', 'TRANSACTION_DATE',
    name='date_source'
)

# PostgreSQL ENUM references for use in create_table (create_type=False)
_ntt_col = PG_ENUM(
    'SALES_INVOICE', 'PURCHASE_INVOICE', 'CREDIT_NOTE',
    'BANK_PAYMENT', 'BANK_RECEIPT', 'JOURNAL', 'TRANSFER', 'OTHER',
    name='normalized_txn_type', create_type=False
)
_nts_col = PG_ENUM(
    'DRAFT', 'AWAITING_APPROVAL', 'APPROVED', 'SENT', 'PAID', 'VOIDED', 'UNKNOWN',
    name='normalized_txn_status', create_type=False
)
_cb_col = PG_ENUM(
    'AR_CURRENT', 'AR_OVERDUE', 'AP_CURRENT', 'AP_OVERDUE',
    'CASH_IN', 'CASH_OUT', 'NON_CASH', 'IGNORE',
    name='cashflow_bucket', create_type=False
)
_ds_col = PG_ENUM(
    'DUE_DATE', 'TRANSACTION_DATE',
    name='date_source', create_type=False
)


def upgrade() -> None:
    # Create enums using raw SQL (avoids SQLAlchemy double-create issues)
    op.execute("CREATE TYPE normalized_txn_type AS ENUM ("
               "'SALES_INVOICE', 'PURCHASE_INVOICE', 'CREDIT_NOTE', "
               "'BANK_PAYMENT', 'BANK_RECEIPT', 'JOURNAL', 'TRANSFER', 'OTHER')")
    op.execute("CREATE TYPE normalized_txn_status AS ENUM ("
               "'DRAFT', 'AWAITING_APPROVAL', 'APPROVED', 'SENT', 'PAID', 'VOIDED', 'UNKNOWN')")
    op.execute("CREATE TYPE cashflow_bucket AS ENUM ("
               "'AR_CURRENT', 'AR_OVERDUE', 'AP_CURRENT', 'AP_OVERDUE', "
               "'CASH_IN', 'CASH_OUT', 'NON_CASH', 'IGNORE')")
    op.execute("CREATE TYPE date_source AS ENUM ('DUE_DATE', 'TRANSACTION_DATE')")

    # Create platform_transaction_mapping table
    op.create_table(
        'platform_transaction_mapping',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('platform_name', sa.String(50), nullable=False),
        sa.Column('source_type', sa.String(100), nullable=False),
        sa.Column('source_status', sa.String(100), nullable=False),
        sa.Column('normalized_type', _ntt_col, nullable=False),
        sa.Column('normalized_status', _nts_col, nullable=False),
        sa.Column('canonical_bucket', _cb_col, nullable=False),
        sa.Column('effective_date_source', _ds_col, nullable=False,
                  server_default='TRANSACTION_DATE'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Unique partial index: one active mapping per (platform, type, status)
    op.create_index(
        'ix_ptm_platform_type_status_active',
        'platform_transaction_mapping',
        ['platform_name', 'source_type', 'source_status'],
        unique=True,
        postgresql_where=sa.text('is_active = true')
    )

    # Index for lookups
    op.create_index(
        'ix_ptm_platform_name',
        'platform_transaction_mapping',
        ['platform_name']
    )


def downgrade() -> None:
    op.drop_index('ix_ptm_platform_name', 'platform_transaction_mapping')
    op.drop_index('ix_ptm_platform_type_status_active', 'platform_transaction_mapping')
    op.drop_table('platform_transaction_mapping')

    op.execute("DROP TYPE IF EXISTS date_source")
    op.execute("DROP TYPE IF EXISTS cashflow_bucket")
    op.execute("DROP TYPE IF EXISTS normalized_txn_status")
    op.execute("DROP TYPE IF EXISTS normalized_txn_type")
