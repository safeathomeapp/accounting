"""v2_040_org_scoped_platform_uniqueness

Revision ID: v2_040_org_scoped_platform_uniqueness
Revises: v2_030_fk_index_gaps_ai_analysis_results
Create Date: 2026-01-24

CRITICAL MIGRATION - Fixes multi-tenancy issue.

Your initial schema includes global unique indexes:
- clients: ix_clients_platform_reference on (platform_name, platform_id)
- transactions: ix_transactions_platform_ref on (platform_name, platform_id)

This is often *too strict* for multi-organization setups: provider IDs can repeat across orgs/realms/tenants.

This migration replaces those indexes with **organization-scoped uniqueness**:
- clients: (organization_id, platform_name, platform_id)
- transactions: (organization_id, platform_name, platform_id)

To reduce downtime, it uses CREATE UNIQUE INDEX CONCURRENTLY then drops old indexes.
"""

from alembic import op

revision = "v2_040_org_scoped_platform_uniqueness"
down_revision = "v2_030_fk_index_gaps_ai_analysis_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CONCURRENTLY requires autocommit
    ctx = op.get_context()
    with ctx.autocommit_block():
        op.execute("""
            CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS ux_clients_org_platform
            ON public.clients (organization_id, platform_name, platform_id);
        """)
        op.execute("""
            CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS ux_transactions_org_platform
            ON public.transactions (organization_id, platform_name, platform_id);
        """)

    # Drop old global unique indexes (created in initial migration)
    # Note: these are indexes, not constraints.
    with ctx.autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS public.ix_clients_platform_reference;")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS public.ix_transactions_platform_ref;")


def downgrade() -> None:
    ctx = op.get_context()
    # Recreate original global unique indexes (CONCURRENTLY)
    with ctx.autocommit_block():
        op.execute("""
            CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS ix_clients_platform_reference
            ON public.clients (platform_name, platform_id);
        """)
        op.execute("""
            CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS ix_transactions_platform_ref
            ON public.transactions (platform_name, platform_id);
        """)

    # Drop org-scoped unique indexes
    with ctx.autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS public.ux_clients_org_platform;")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS public.ux_transactions_org_platform;")
