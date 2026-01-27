"""v2_071_cashflow_facts_and_quarantine

Revision ID: v2_071_cashflow_facts_and_quarantine
Revises: v2_070_canonical_enums_and_mapping_table
Create Date: 2026-01-27

Creates the canonical facts table and ingestion quarantine table.

cashflow_facts_v1: The single source of truth for all reporting and analytics.
Each row is one transaction mapped to its canonical bucket with signed amount.

ingestion_quarantine: Holds transactions that couldn't be mapped. These need
a new mapping row added before they can be processed into facts.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM as PG_ENUM

revision = "v2_071_cashflow_facts_and_quarantine"
down_revision = "v2_070_canonical_enums_and_mapping_table"
branch_labels = None
depends_on = None

# Reference existing enums (already created in v2_070) - PG_ENUM with create_type=False
normalized_txn_type = PG_ENUM(
    'SALES_INVOICE', 'PURCHASE_INVOICE', 'CREDIT_NOTE',
    'BANK_PAYMENT', 'BANK_RECEIPT', 'JOURNAL', 'TRANSFER', 'OTHER',
    name='normalized_txn_type', create_type=False
)

normalized_txn_status = PG_ENUM(
    'DRAFT', 'AWAITING_APPROVAL', 'APPROVED', 'SENT', 'PAID', 'VOIDED', 'UNKNOWN',
    name='normalized_txn_status', create_type=False
)

cashflow_bucket = PG_ENUM(
    'AR_CURRENT', 'AR_OVERDUE', 'AP_CURRENT', 'AP_OVERDUE',
    'CASH_IN', 'CASH_OUT', 'NON_CASH', 'IGNORE',
    name='cashflow_bucket', create_type=False
)


def upgrade() -> None:
    # Create cashflow_facts_v1 table
    op.create_table(
        'cashflow_facts_v1',
        sa.Column('id', UUID(as_uuid=True), nullable=False,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('transaction_id', UUID(as_uuid=True), nullable=False),
        sa.Column('mapping_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', UUID(as_uuid=True), nullable=True),
        sa.Column('normalized_type', normalized_txn_type, nullable=False),
        sa.Column('normalized_status', normalized_txn_status, nullable=False),
        sa.Column('canonical_bucket', cashflow_bucket, nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('signed_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='GBP'),
        sa.Column('snapshot_date', sa.Date(), nullable=False,
                  server_default=sa.text('CURRENT_DATE')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mapping_id'], ['platform_transaction_mapping.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='SET NULL'),
    )

    # One fact per transaction
    op.create_index('ix_cf_facts_transaction_id', 'cashflow_facts_v1',
                    ['transaction_id'], unique=True)

    # Query indexes for reporting
    op.create_index('ix_cf_facts_org_effective_date', 'cashflow_facts_v1',
                    ['organization_id', 'effective_date'])
    op.create_index('ix_cf_facts_org_bucket_date', 'cashflow_facts_v1',
                    ['organization_id', 'canonical_bucket', 'effective_date'])
    op.create_index('ix_cf_facts_client_date', 'cashflow_facts_v1',
                    ['client_id', 'effective_date'])

    # Create ingestion_quarantine table
    op.create_table(
        'ingestion_quarantine',
        sa.Column('id', UUID(as_uuid=True), nullable=False,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('transaction_id', UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', UUID(as_uuid=True), nullable=False),
        sa.Column('platform_name', sa.String(50), nullable=False),
        sa.Column('source_type', sa.String(100), nullable=False),
        sa.Column('source_status', sa.String(100), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('quarantined_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )

    # One unresolved quarantine entry per transaction
    op.create_index(
        'ix_quarantine_txn_unresolved',
        'ingestion_quarantine',
        ['transaction_id'],
        unique=True,
        postgresql_where=sa.text('resolved_at IS NULL')
    )

    op.create_index('ix_quarantine_org_id', 'ingestion_quarantine', ['organization_id'])


def downgrade() -> None:
    op.drop_index('ix_quarantine_org_id', 'ingestion_quarantine')
    op.drop_index('ix_quarantine_txn_unresolved', 'ingestion_quarantine')
    op.drop_table('ingestion_quarantine')

    op.drop_index('ix_cf_facts_client_date', 'cashflow_facts_v1')
    op.drop_index('ix_cf_facts_org_bucket_date', 'cashflow_facts_v1')
    op.drop_index('ix_cf_facts_org_effective_date', 'cashflow_facts_v1')
    op.drop_index('ix_cf_facts_transaction_id', 'cashflow_facts_v1')
    op.drop_table('cashflow_facts_v1')
