"""
Tests for Row-Level Security (RLS) policies.

These tests verify that the tenant context setting mechanism works correctly.
The actual RLS policy enforcement is tested indirectly - full RLS enforcement
testing requires running as the app_user role which may not be available in
all test environments.
"""

import uuid
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import SessionLocal, set_tenant_context, clear_tenant_context


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


class TestSetTenantContext:
    """Tests for the set_tenant_context helper function."""

    def test_set_tenant_context_sets_session_variable(self, db_session: Session):
        """Test that set_tenant_context properly sets the app.org_id variable."""
        org_id = uuid.uuid4()

        set_tenant_context(db_session, org_id)

        # Check the session variable was set
        result = db_session.execute(
            text("SELECT current_setting('app.org_id', true)")
        ).scalar()
        assert result == str(org_id)

    def test_clear_tenant_context_resets_variable(self, db_session: Session):
        """Test that clear_tenant_context resets the app.org_id variable."""
        org_id = uuid.uuid4()
        set_tenant_context(db_session, org_id)

        clear_tenant_context(db_session)

        # Variable should be empty/null after reset
        result = db_session.execute(
            text("SELECT current_setting('app.org_id', true)")
        ).scalar()
        assert result == "" or result is None

    def test_set_tenant_context_with_none_clears_context(self, db_session: Session):
        """Test that set_tenant_context(None) clears the context."""
        org_id = uuid.uuid4()
        set_tenant_context(db_session, org_id)

        set_tenant_context(db_session, None)

        result = db_session.execute(
            text("SELECT current_setting('app.org_id', true)")
        ).scalar()
        assert result == "" or result is None

    def test_multiple_context_switches(self, db_session: Session):
        """Test that tenant context can be switched multiple times."""
        org_id1 = uuid.uuid4()
        org_id2 = uuid.uuid4()

        # Set first context
        set_tenant_context(db_session, org_id1)
        result1 = db_session.execute(
            text("SELECT current_setting('app.org_id', true)")
        ).scalar()
        assert result1 == str(org_id1)

        # Switch to second context
        set_tenant_context(db_session, org_id2)
        result2 = db_session.execute(
            text("SELECT current_setting('app.org_id', true)")
        ).scalar()
        assert result2 == str(org_id2)

        # Clear context
        clear_tenant_context(db_session)
        result3 = db_session.execute(
            text("SELECT current_setting('app.org_id', true)")
        ).scalar()
        assert result3 == "" or result3 is None


class TestRLSPoliciesExist:
    """Tests to verify RLS policies were created correctly."""

    def test_rls_enabled_on_tenant_tables(self, db_session: Session):
        """Verify RLS is enabled on key tenant-scoped tables."""
        # Query pg_class to check if RLS is enabled
        result = db_session.execute(text("""
            SELECT relname, relrowsecurity, relforcerowsecurity
            FROM pg_class
            WHERE relname IN ('clients', 'transactions', 'accounts', 'cashflow_facts_v1')
            AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        """)).fetchall()

        # Convert to dict for easier checking
        tables = {row[0]: {'rls': row[1], 'force': row[2]} for row in result}

        # All these tables should have RLS enabled
        for table_name in ['clients', 'transactions', 'accounts']:
            if table_name in tables:
                assert tables[table_name]['rls'] is True, f"RLS not enabled on {table_name}"

    def test_rls_policies_created(self, db_session: Session):
        """Verify RLS policies exist on tenant-scoped tables."""
        result = db_session.execute(text("""
            SELECT schemaname, tablename, policyname
            FROM pg_policies
            WHERE schemaname = 'public'
            AND policyname LIKE 'p_%_tenant_isolation'
        """)).fetchall()

        # Should have policies for main tables
        policy_tables = [row[1] for row in result]

        # Check some key tables have policies
        expected_tables = ['clients', 'transactions', 'accounts']
        for table in expected_tables:
            assert table in policy_tables, f"Missing RLS policy for {table}"

    def test_database_roles_exist(self, db_session: Session):
        """Verify the database roles were created."""
        result = db_session.execute(text("""
            SELECT rolname FROM pg_roles
            WHERE rolname IN ('app_user', 'app_readonly', 'app_admin')
        """)).fetchall()

        role_names = [row[0] for row in result]

        assert 'app_user' in role_names, "app_user role not created"
        assert 'app_readonly' in role_names, "app_readonly role not created"
        assert 'app_admin' in role_names, "app_admin role not created"


class TestRLSWithExistingData:
    """
    Tests that verify RLS behavior with existing data.

    These tests query existing data in the database rather than creating
    new test data, to avoid permission issues in environments where
    FORCE RLS is enabled.
    """

    def test_context_affects_query_filter(self, db_session: Session):
        """
        Test that setting context changes the effective filter.

        This is a basic sanity check that the context-setting SQL runs
        without error. Actual row filtering depends on connecting as
        a non-owner role.
        """
        # Get an existing organization ID if any
        result = db_session.execute(
            text("SELECT id FROM organizations LIMIT 1")
        ).fetchone()

        if result:
            org_id = result[0]

            # Set context to this org
            set_tenant_context(db_session, uuid.UUID(str(org_id)))

            # Verify context is set
            context_result = db_session.execute(
                text("SELECT current_setting('app.org_id', true)")
            ).scalar()
            assert context_result == str(org_id)

            # Query should work (whether RLS filters or not depends on role)
            # This just verifies no SQL errors
            db_session.execute(text("SELECT COUNT(*) FROM clients"))
        else:
            pytest.skip("No existing organizations in database")

    def test_invalid_org_id_returns_no_rows_as_app_user(self, db_session: Session):
        """
        Test that an invalid org_id context returns no rows.

        This test attempts to switch to app_user role. If that fails
        (e.g., permission not granted), the test is skipped.
        """
        try:
            # Try to switch to app_user role
            db_session.execute(text("SET ROLE app_user"))

            # Set context to a random UUID that shouldn't exist
            fake_org_id = uuid.uuid4()
            set_tenant_context(db_session, fake_org_id)

            # Query should return 0 rows due to RLS
            result = db_session.execute(
                text("SELECT COUNT(*) FROM clients")
            ).scalar()
            assert result == 0, "Expected 0 rows with invalid org_id context"

        except Exception as e:
            if "permission denied" in str(e).lower() or "must be member" in str(e).lower():
                pytest.skip("Cannot switch to app_user role - insufficient privileges")
            raise
        finally:
            # Reset role
            try:
                db_session.execute(text("RESET ROLE"))
            except Exception:
                pass
