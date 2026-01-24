"""v2_020_currency_and_amount_checks

Revision ID: v2_020_currency_and_amount_checks
Revises: v2_010_defaults_and_updated_at_triggers
Create Date: 2026-01-24

Adds CHECK constraints that enforce basic correctness:
- ISO-like currency code format (^[A-Z]{3}$) for organizations.currency and transactions.currency
- Non-negative tax amount
- Total amount arithmetic consistency (total_amount = amount + tax_amount)

Uses NOT VALID then validates, to reduce immediate failure risk on existing data.
"""

from alembic import op

revision = "v2_020_currency_and_amount_checks"
down_revision = "v2_010_defaults_and_updated_at_triggers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Currency ISO format checks
    op.execute("""
        ALTER TABLE public.organizations
          ADD CONSTRAINT ck_organizations_currency_iso
          CHECK (currency ~ '^[A-Z]{3}$') NOT VALID;
    """)
    op.execute("""
        ALTER TABLE public.transactions
          ADD CONSTRAINT ck_transactions_currency_iso
          CHECK (currency ~ '^[A-Z]{3}$') NOT VALID;
    """)

    # Amount arithmetic checks
    op.execute("""
        ALTER TABLE public.transactions
          ADD CONSTRAINT ck_transactions_tax_nonnegative
          CHECK (tax_amount >= 0) NOT VALID;
    """)
    op.execute("""
        ALTER TABLE public.transactions
          ADD CONSTRAINT ck_transactions_total_matches
          CHECK (total_amount = amount + tax_amount) NOT VALID;
    """)

    # Validate constraints (will scan table)
    op.execute("ALTER TABLE public.organizations VALIDATE CONSTRAINT ck_organizations_currency_iso;")
    op.execute("ALTER TABLE public.transactions VALIDATE CONSTRAINT ck_transactions_currency_iso;")
    op.execute("ALTER TABLE public.transactions VALIDATE CONSTRAINT ck_transactions_tax_nonnegative;")
    op.execute("ALTER TABLE public.transactions VALIDATE CONSTRAINT ck_transactions_total_matches;")


def downgrade() -> None:
    op.execute("ALTER TABLE public.transactions DROP CONSTRAINT IF EXISTS ck_transactions_total_matches;")
    op.execute("ALTER TABLE public.transactions DROP CONSTRAINT IF EXISTS ck_transactions_tax_nonnegative;")
    op.execute("ALTER TABLE public.transactions DROP CONSTRAINT IF EXISTS ck_transactions_currency_iso;")
    op.execute("ALTER TABLE public.organizations DROP CONSTRAINT IF EXISTS ck_organizations_currency_iso;")
