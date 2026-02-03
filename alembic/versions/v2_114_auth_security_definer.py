"""v2_114_auth_security_definer

Implement hardened SECURITY DEFINER auth functions and FORCE RLS.

Requirements (from FINAL_NON_NEGOTIABLE_DB_STANCE.md):
1. FORCE RLS on users and organizations
2. Single explicit bypass surface via SECURITY DEFINER functions
3. Hardened: strict search_path, minimal return fields
4. Dedicated auth_definer role owns functions
5. App roles cannot directly SELECT for login flows

Revision ID: v2_114_auth_security_definer
Revises: v2_113_email_uniqueness
Create Date: 2026-02-03
"""

from alembic import op

revision = "v2_114_auth_security_definer"
down_revision = "v2_113_email_uniqueness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # Step 1: Create dedicated auth_definer role
    # This role owns SECURITY DEFINER functions
    # It is NOT used for normal app queries
    # =========================================================================

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'auth_definer') THEN
                CREATE ROLE auth_definer NOLOGIN;
            END IF;
        END$$;
    """)

    # Grant minimal permissions needed for auth functions
    op.execute("GRANT SELECT ON users TO auth_definer;")
    op.execute("GRANT SELECT ON organizations TO auth_definer;")

    # =========================================================================
    # Step 2: Create SECURITY DEFINER function for user auth lookup
    # Hardened: strict search_path, minimal fields, owned by auth_definer
    # =========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION auth_lookup_user_by_email(lookup_email TEXT)
        RETURNS TABLE (
            user_id UUID,
            password_hash TEXT,
            user_status VARCHAR(20),
            organization_id UUID,
            user_role VARCHAR(50),
            is_active BOOLEAN
        )
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                u.id,
                u.password_hash::TEXT,
                u.status,
                u.organization_id,
                u.role,
                u.is_active
            FROM public.users u
            WHERE lower(u.email) = lower(lookup_email)
            LIMIT 1;
        END;
        $$;
    """)

    # Transfer ownership to auth_definer
    op.execute("ALTER FUNCTION auth_lookup_user_by_email(TEXT) OWNER TO auth_definer;")

    # Restrict execution
    op.execute("REVOKE ALL ON FUNCTION auth_lookup_user_by_email(TEXT) FROM PUBLIC;")
    op.execute("GRANT EXECUTE ON FUNCTION auth_lookup_user_by_email(TEXT) TO app_user;")
    op.execute("GRANT EXECUTE ON FUNCTION auth_lookup_user_by_email(TEXT) TO app_admin;")

    # =========================================================================
    # Step 3: Create SECURITY DEFINER function for organization lookup
    # Used during registration flow
    # =========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION auth_lookup_org_by_id(lookup_id UUID)
        RETURNS TABLE (
            org_id UUID,
            org_name VARCHAR(255),
            org_status VARCHAR(50)
        )
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                o.id,
                o.name,
                o.status
            FROM public.organizations o
            WHERE o.id = lookup_id
            LIMIT 1;
        END;
        $$;
    """)

    # Transfer ownership to auth_definer
    op.execute("ALTER FUNCTION auth_lookup_org_by_id(UUID) OWNER TO auth_definer;")

    # Restrict execution
    op.execute("REVOKE ALL ON FUNCTION auth_lookup_org_by_id(UUID) FROM PUBLIC;")
    op.execute("GRANT EXECUTE ON FUNCTION auth_lookup_org_by_id(UUID) TO app_user;")
    op.execute("GRANT EXECUTE ON FUNCTION auth_lookup_org_by_id(UUID) TO app_admin;")

    # =========================================================================
    # Step 4: Create SECURITY DEFINER function for user creation (registration)
    # Allows creating pending user without org context
    # =========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION auth_create_pending_user(
            p_email TEXT,
            p_password_hash TEXT,
            p_name TEXT
        )
        RETURNS UUID
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE
            new_id UUID;
        BEGIN
            INSERT INTO public.users (email, password_hash, name, status, is_active, is_admin)
            VALUES (p_email, p_password_hash, p_name, 'pending', true, false)
            RETURNING id INTO new_id;
            RETURN new_id;
        END;
        $$;
    """)

    op.execute("ALTER FUNCTION auth_create_pending_user(TEXT, TEXT, TEXT) OWNER TO auth_definer;")
    op.execute("REVOKE ALL ON FUNCTION auth_create_pending_user(TEXT, TEXT, TEXT) FROM PUBLIC;")
    op.execute("GRANT EXECUTE ON FUNCTION auth_create_pending_user(TEXT, TEXT, TEXT) TO app_user;")
    op.execute("GRANT EXECUTE ON FUNCTION auth_create_pending_user(TEXT, TEXT, TEXT) TO app_admin;")

    # =========================================================================
    # Step 5: Create SECURITY DEFINER function for activating user with org
    # =========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION auth_activate_user(
            p_user_id UUID,
            p_organization_id UUID
        )
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE
            rows_updated INTEGER;
        BEGIN
            UPDATE public.users
            SET
                organization_id = p_organization_id,
                status = 'active',
                updated_at = now()
            WHERE id = p_user_id AND status = 'pending';
            GET DIAGNOSTICS rows_updated = ROW_COUNT;
            RETURN rows_updated > 0;
        END;
        $$;
    """)

    op.execute("ALTER FUNCTION auth_activate_user(UUID, UUID) OWNER TO auth_definer;")
    op.execute("REVOKE ALL ON FUNCTION auth_activate_user(UUID, UUID) FROM PUBLIC;")
    op.execute("GRANT EXECUTE ON FUNCTION auth_activate_user(UUID, UUID) TO app_user;")
    op.execute("GRANT EXECUTE ON FUNCTION auth_activate_user(UUID, UUID) TO app_admin;")

    # =========================================================================
    # Step 6: FORCE RLS on users and organizations
    # Now safe because auth bypass is via SECURITY DEFINER functions
    # =========================================================================

    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE organizations FORCE ROW LEVEL SECURITY;")

    # =========================================================================
    # Step 7: Documentation
    # =========================================================================

    op.execute("""
        COMMENT ON FUNCTION auth_lookup_user_by_email(TEXT) IS
        'SECURITY DEFINER function for auth lookup. This is the ONLY approved RLS bypass for user queries during login. Owned by auth_definer role. Returns minimal fields. Hardened search_path.';
    """)

    op.execute("""
        COMMENT ON FUNCTION auth_lookup_org_by_id(UUID) IS
        'SECURITY DEFINER function for org lookup during registration. RLS bypass via auth_definer role.';
    """)

    op.execute("""
        COMMENT ON FUNCTION auth_create_pending_user(TEXT, TEXT, TEXT) IS
        'SECURITY DEFINER function for creating pending users during registration. Bypasses RLS. Returns new user UUID.';
    """)

    op.execute("""
        COMMENT ON FUNCTION auth_activate_user(UUID, UUID) IS
        'SECURITY DEFINER function for activating pending user with organization. Bypasses RLS. Returns success boolean.';
    """)

    op.execute("""
        COMMENT ON ROLE auth_definer IS
        'Dedicated role for SECURITY DEFINER auth functions. NOT for normal app queries. Owns auth_* functions.';
    """)


def downgrade() -> None:
    # Remove FORCE RLS
    op.execute("""
        DO $$
        BEGIN
            EXECUTE 'ALTER TABLE users NO FORCE ROW LEVEL SECURITY';
            EXECUTE 'ALTER TABLE organizations NO FORCE ROW LEVEL SECURITY';
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END$$;
    """)

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS auth_activate_user(UUID, UUID);")
    op.execute("DROP FUNCTION IF EXISTS auth_create_pending_user(TEXT, TEXT, TEXT);")
    op.execute("DROP FUNCTION IF EXISTS auth_lookup_org_by_id(UUID);")
    op.execute("DROP FUNCTION IF EXISTS auth_lookup_user_by_email(TEXT);")

    # Revoke grants from auth_definer
    op.execute("""
        DO $$
        BEGIN
            REVOKE SELECT ON users FROM auth_definer;
            REVOKE SELECT ON organizations FROM auth_definer;
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END$$;
    """)

    # Drop role
    op.execute("DROP ROLE IF EXISTS auth_definer;")
