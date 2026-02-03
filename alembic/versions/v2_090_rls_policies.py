"""v2_090_rls_policies

Revision ID: v2_090_rls_policies
Revises: v2_080_document_review_tables
Create Date: 2026-02-02

Implements Row-Level Security (RLS) for multi-tenant isolation.

This migration:
1. Creates database roles (app_user, app_readonly, app_admin)
2. Enables RLS on all tenant-scoped tables
3. Creates RLS policies using app.org_id session variable
4. Grants appropriate permissions to roles

IMPORTANT: After applying this migration, the application MUST set
the session variable `app.org_id` before querying tenant-scoped tables:

    SET app.org_id = '<organization-uuid>';

Without this, queries will return no rows (RLS default-deny behavior).

The application should connect as `app_user` role for normal operations.
"""

from alembic import op

revision = "v2_090_rls_policies"
down_revision = "v2_080_document_review_tables"
branch_labels = None
depends_on = None

# Tables that have organization_id column
# NOTE: oauth_tokens does NOT have organization_id directly - it's linked via platform_id
# to accounting_platforms which has organization_id. We skip it here.
TABLES_WITH_ORG_ID = [
    "clients",
    "transactions",
    "accounts",
    "accounting_platforms",
    # "oauth_tokens" - excluded: linked via platform_id, not organization_id
    "ai_analysis_results",
    "sync_history",
    "audit_log",
    "cashflow_facts_v1",
    "ingestion_quarantine",
]

# Document tables use org_id instead of organization_id
DOCUMENT_TABLES = [
    "document_inbox_item",
    "document_ocr_result",
    "document_draft",
    "document_draft_line",
]


def upgrade() -> None:
    # =========================================================================
    # 1. Create database roles (if they don't exist)
    # =========================================================================

    # app_user: Normal application role with RLS enforced
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
                CREATE ROLE app_user NOLOGIN;
            END IF;
        END$$;
    """)

    # app_readonly: Read-only role with RLS enforced
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_readonly') THEN
                CREATE ROLE app_readonly NOLOGIN;
            END IF;
        END$$;
    """)

    # app_admin: Admin role that bypasses RLS (for migrations, maintenance)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_admin') THEN
                CREATE ROLE app_admin NOLOGIN BYPASSRLS;
            END IF;
        END$$;
    """)

    # =========================================================================
    # 2. Enable RLS and create policies for tables with organization_id
    # =========================================================================

    for table in TABLES_WITH_ORG_ID:
        # Check if table exists before enabling RLS
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table}') THEN
                    -- Enable RLS on the table
                    EXECUTE 'ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY';

                    -- Force RLS even for table owner (important for security)
                    EXECUTE 'ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY';

                    -- Drop existing policy if present
                    EXECUTE 'DROP POLICY IF EXISTS p_{table}_tenant_isolation ON public.{table}';

                    -- Create tenant isolation policy
                    -- Uses current_setting with missing_ok=true to return NULL if not set
                    -- This means: if app.org_id is not set, no rows are visible (safe default)
                    EXECUTE '
                        CREATE POLICY p_{table}_tenant_isolation
                        ON public.{table}
                        FOR ALL
                        TO PUBLIC
                        USING (organization_id = current_setting(''app.org_id'', true)::uuid)
                        WITH CHECK (organization_id = current_setting(''app.org_id'', true)::uuid)
                    ';

                    -- Grant permissions to app_user
                    EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON public.{table} TO app_user';

                    -- Grant read-only permissions to app_readonly
                    EXECUTE 'GRANT SELECT ON public.{table} TO app_readonly';

                    -- Grant full permissions to app_admin
                    EXECUTE 'GRANT ALL ON public.{table} TO app_admin';
                END IF;
            END$$;
        """)

    # =========================================================================
    # 3. Enable RLS for document tables (use org_id instead of organization_id)
    # =========================================================================

    for table in DOCUMENT_TABLES:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table}') THEN
                    -- Enable RLS on the table
                    EXECUTE 'ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY';

                    -- Force RLS even for table owner
                    EXECUTE 'ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY';

                    -- Drop existing policy if present
                    EXECUTE 'DROP POLICY IF EXISTS p_{table}_tenant_isolation ON public.{table}';

                    -- Create tenant isolation policy (using org_id column)
                    EXECUTE '
                        CREATE POLICY p_{table}_tenant_isolation
                        ON public.{table}
                        FOR ALL
                        TO PUBLIC
                        USING (org_id = current_setting(''app.org_id'', true)::uuid)
                        WITH CHECK (org_id = current_setting(''app.org_id'', true)::uuid)
                    ';

                    -- Grant permissions
                    EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON public.{table} TO app_user';
                    EXECUTE 'GRANT SELECT ON public.{table} TO app_readonly';
                    EXECUTE 'GRANT ALL ON public.{table} TO app_admin';
                END IF;
            END$$;
        """)

    # =========================================================================
    # 4. Grant permissions on non-tenant tables
    # =========================================================================

    # Organizations table - users can only see their own org
    # NOTE: We do NOT use FORCE ROW LEVEL SECURITY because registration
    # needs to create a new organization before the org_id context is set.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'organizations') THEN
                EXECUTE 'ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY';
                -- NOTE: No FORCE RLS - allows owner to create orgs during registration
                EXECUTE 'DROP POLICY IF EXISTS p_organizations_own_org ON public.organizations';
                EXECUTE '
                    CREATE POLICY p_organizations_own_org
                    ON public.organizations
                    FOR ALL
                    TO app_user, app_readonly
                    USING (id = current_setting(''app.org_id'', true)::uuid)
                    WITH CHECK (id = current_setting(''app.org_id'', true)::uuid)
                ';
                EXECUTE 'GRANT SELECT, UPDATE ON public.organizations TO app_user';
                EXECUTE 'GRANT SELECT ON public.organizations TO app_readonly';
                EXECUTE 'GRANT ALL ON public.organizations TO app_admin';
            END IF;
        END$$;
    """)

    # Users table - users can see users in their own org
    # NOTE: We do NOT use FORCE ROW LEVEL SECURITY on users table
    # because auth lookup needs to query by email before we know the org_id.
    # The table owner (connection user) can bypass RLS for auth.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
                EXECUTE 'ALTER TABLE public.users ENABLE ROW LEVEL SECURITY';
                -- NOTE: No FORCE RLS - allows owner to query for auth
                EXECUTE 'DROP POLICY IF EXISTS p_users_same_org ON public.users';
                EXECUTE '
                    CREATE POLICY p_users_same_org
                    ON public.users
                    FOR ALL
                    TO app_user, app_readonly
                    USING (organization_id = current_setting(''app.org_id'', true)::uuid)
                    WITH CHECK (organization_id = current_setting(''app.org_id'', true)::uuid)
                ';
                EXECUTE 'GRANT SELECT, INSERT, UPDATE ON public.users TO app_user';
                EXECUTE 'GRANT SELECT ON public.users TO app_readonly';
                EXECUTE 'GRANT ALL ON public.users TO app_admin';
            END IF;
        END$$;
    """)

    # Platform transaction mapping - global config, read-only for app_user
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'platform_transaction_mapping') THEN
                -- No RLS on this table - it's global config
                EXECUTE 'GRANT SELECT ON public.platform_transaction_mapping TO app_user';
                EXECUTE 'GRANT SELECT ON public.platform_transaction_mapping TO app_readonly';
                EXECUTE 'GRANT ALL ON public.platform_transaction_mapping TO app_admin';
            END IF;
        END$$;
    """)

    # OAuth tokens - linked via platform_id to accounting_platforms (which has RLS)
    # We enable RLS here using a subquery to accounting_platforms
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'oauth_tokens') THEN
                EXECUTE 'ALTER TABLE public.oauth_tokens ENABLE ROW LEVEL SECURITY';
                EXECUTE 'ALTER TABLE public.oauth_tokens FORCE ROW LEVEL SECURITY';
                EXECUTE 'DROP POLICY IF EXISTS p_oauth_tokens_tenant_isolation ON public.oauth_tokens';
                -- Policy uses a subquery to check the platform's organization_id
                EXECUTE '
                    CREATE POLICY p_oauth_tokens_tenant_isolation
                    ON public.oauth_tokens
                    FOR ALL
                    TO PUBLIC
                    USING (
                        platform_id IN (
                            SELECT id FROM public.accounting_platforms
                            WHERE organization_id = current_setting(''app.org_id'', true)::uuid
                        )
                    )
                    WITH CHECK (
                        platform_id IN (
                            SELECT id FROM public.accounting_platforms
                            WHERE organization_id = current_setting(''app.org_id'', true)::uuid
                        )
                    )
                ';
                EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON public.oauth_tokens TO app_user';
                EXECUTE 'GRANT SELECT ON public.oauth_tokens TO app_readonly';
                EXECUTE 'GRANT ALL ON public.oauth_tokens TO app_admin';
            END IF;
        END$$;
    """)

    # =========================================================================
    # 5. Grant sequence permissions (needed for INSERTs)
    # =========================================================================

    op.execute("""
        DO $$
        DECLARE
            seq_name TEXT;
        BEGIN
            FOR seq_name IN
                SELECT sequence_name
                FROM information_schema.sequences
                WHERE sequence_schema = 'public'
            LOOP
                EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE public.%I TO app_user', seq_name);
                EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE public.%I TO app_readonly', seq_name);
                EXECUTE format('GRANT ALL ON SEQUENCE public.%I TO app_admin', seq_name);
            END LOOP;
        END$$;
    """)

    # Grant usage on any serial/bigserial columns (platform_transaction_mapping.id is serial)
    op.execute("""
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_readonly;
        GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO app_admin;
    """)


def downgrade() -> None:
    # =========================================================================
    # Remove RLS policies and disable RLS
    # =========================================================================

    all_tables = TABLES_WITH_ORG_ID + DOCUMENT_TABLES + ["organizations", "users", "oauth_tokens"]

    for table in all_tables:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table}') THEN
                    EXECUTE 'DROP POLICY IF EXISTS p_{table}_tenant_isolation ON public.{table}';
                    EXECUTE 'DROP POLICY IF EXISTS p_{table}_own_org ON public.{table}';
                    EXECUTE 'DROP POLICY IF EXISTS p_{table}_same_org ON public.{table}';
                    EXECUTE 'ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY';
                END IF;
            END$$;
        """)

    # Revoke permissions (optional - roles will be dropped)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
                EXECUTE 'REVOKE ALL ON ALL TABLES IN SCHEMA public FROM app_user';
                EXECUTE 'REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM app_user';
            END IF;
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_readonly') THEN
                EXECUTE 'REVOKE ALL ON ALL TABLES IN SCHEMA public FROM app_readonly';
                EXECUTE 'REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM app_readonly';
            END IF;
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_admin') THEN
                EXECUTE 'REVOKE ALL ON ALL TABLES IN SCHEMA public FROM app_admin';
                EXECUTE 'REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM app_admin';
            END IF;
        END$$;
    """)

    # Drop roles
    op.execute("""
        DROP ROLE IF EXISTS app_user;
        DROP ROLE IF EXISTS app_readonly;
        DROP ROLE IF EXISTS app_admin;
    """)
