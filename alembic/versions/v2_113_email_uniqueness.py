"""v2_113_email_uniqueness

Enforce case-insensitive email uniqueness.

Requirements (from FINAL_NON_NEGOTIABLE_DB_STANCE.md):
1. Email identity must be unambiguous
2. Case-insensitive uniqueness via lower(email) index

Revision ID: v2_113_email_uniqueness
Revises: v2_112_users_pending_invariant
Create Date: 2026-02-03
"""

from alembic import op

revision = "v2_113_email_uniqueness"
down_revision = "v2_112_users_pending_invariant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # PRE-FLIGHT: Check for case-insensitive duplicates
    # =========================================================================

    op.execute("""
        DO $$
        DECLARE
            dup_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO dup_count
            FROM (
                SELECT lower(email), COUNT(*)
                FROM users
                GROUP BY lower(email)
                HAVING COUNT(*) > 1
            ) AS dups;

            IF dup_count > 0 THEN
                RAISE EXCEPTION 'Cannot proceed: % case-insensitive email duplicates exist. Manual resolution required.', dup_count;
            END IF;
        END$$;
    """)

    # =========================================================================
    # Step 1: Create case-insensitive unique index
    # =========================================================================

    op.execute("""
        CREATE UNIQUE INDEX CONCURRENTLY ux_users_email_lower
        ON users (lower(email));
    """)

    # =========================================================================
    # Step 2: Documentation
    # =========================================================================

    op.execute("""
        COMMENT ON INDEX ux_users_email_lower IS
        'Case-insensitive email uniqueness. Prevents duplicate identities differing only by case. Auth lookup must use lower(email).';
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ux_users_email_lower;")
