"""v2_010_defaults_and_updated_at_triggers

Revision ID: v2_010_defaults_and_updated_at_triggers
Revises: 11da10f67c9e
Create Date: 2026-01-24

Adds:
- Defaults for timestamps and booleans (less brittle inserts)
- A generic set_updated_at() trigger function and triggers on selected tables
"""

from alembic import op
import sqlalchemy as sa

revision = "v2_010_defaults_and_updated_at_triggers"
down_revision = "11da10f67c9e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Timestamp defaults
    for table in ["organizations", "accounting_platforms", "accounts", "clients", "transactions", "ai_analysis_results"]:
        op.alter_column(table, "created_at", server_default=sa.text("now()"))
        # Some tables may not have updated_at (e.g., audit_log, oauth_tokens, sync_history)
        try:
            op.alter_column(table, "updated_at", server_default=sa.text("now()"))
        except Exception:
            pass

    # Boolean defaults (adjust if your domain differs)
    op.alter_column("organizations", "is_active", server_default=sa.text("true"))
    op.alter_column("accounting_platforms", "is_active", server_default=sa.text("true"))
    op.alter_column("accounts", "is_active", server_default=sa.text("true"))
    op.alter_column("clients", "is_active", server_default=sa.text("true"))
    op.alter_column("transactions", "is_reconciled", server_default=sa.text("false"))
    op.alter_column("ai_analysis_results", "is_approved", server_default=sa.text("false"))
    op.alter_column("ai_analysis_results", "was_used", server_default=sa.text("false"))

    # updated_at enforcement trigger function
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.set_updated_at()
        RETURNS trigger AS $$
        BEGIN
          NEW.updated_at = now();
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # Triggers for tables that have updated_at
    for table in ["organizations", "accounting_platforms", "accounts", "clients", "transactions", "ai_analysis_results"]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_set_updated_at ON public.{table};")
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_set_updated_at
            BEFORE UPDATE ON public.{table}
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
            """
        )


def downgrade() -> None:
    # Drop triggers first
    for table in ["organizations", "accounting_platforms", "accounts", "clients", "transactions", "ai_analysis_results"]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_set_updated_at ON public.{table};")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS public.set_updated_at();")

    # Remove defaults (best-effort)
    for table in ["organizations", "accounting_platforms", "accounts", "clients", "transactions", "ai_analysis_results"]:
        try:
            op.alter_column(table, "created_at", server_default=None)
        except Exception:
            pass
        try:
            op.alter_column(table, "updated_at", server_default=None)
        except Exception:
            pass

    for (table, col) in [
        ("organizations","is_active"),
        ("accounting_platforms","is_active"),
        ("accounts","is_active"),
        ("clients","is_active"),
        ("transactions","is_reconciled"),
        ("ai_analysis_results","is_approved"),
        ("ai_analysis_results","was_used"),
    ]:
        try:
            op.alter_column(table, col, server_default=None)
        except Exception:
            pass
