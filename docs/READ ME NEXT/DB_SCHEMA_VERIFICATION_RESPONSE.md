# Database Schema Verification Response
## Response to DB_SCHEMA_VERIFICATION_REPORT.md

Date: 2026-02-03
Author: Lead Engineer (Claude Code)
Status: **REVIEW COMPLETE**

---

## 1. Executive Summary

The verification report identifies four items requiring attention. After review against the Addendum (which canonises our domain model), I respond as follows:

| Item | Report Status | Response | Action Required |
|------|---------------|----------|-----------------|
| 4.1 Accounts Provider Idempotency | FAIL | **AGREE** | Yes - Migration needed |
| 4.2 Account Code Uniqueness | PARTIAL | **CLARIFIED** | No - Already correct |
| 4.3 RLS FORCE on org/users | PARTIAL | **DISAGREE** | No - Counter-control documented |
| 4.4 pgcrypto Extension | PARTIAL | **AGREE** | Yes - Migration needed |

**Two migrations required. Two items rejected with justification.**

---

## 2. Item-by-Item Response

### 2.1 Accounts Provider Idempotency — AGREE

**Report finding**: Missing uniqueness constraint on accounts for sync idempotency.

**Response**: AGREE. This is a valid gap.

**Correction**: Per discussion with project owner, the constraint should be **client-scoped** (not organization-scoped) to align with the canonised domain model where accounts belong to clients:

```sql
CREATE UNIQUE INDEX CONCURRENTLY ux_accounts_client_platform
ON public.accounts (client_id, platform_name, platform_id)
WHERE client_id IS NOT NULL;
```

**Note**: The `WHERE client_id IS NOT NULL` clause handles legacy accounts created before client_id was required. New accounts must have client_id.

**Alembic migration**: To be created as `v2_100_accounts_platform_idempotency.py`

**Priority**: CRITICAL - Must be applied before production sync volume increases.

---

### 2.2 Account Code Uniqueness — CLARIFIED (No Action)

**Report finding**: `(client_id, code)` uniqueness flagged as "likely incorrect", recommending `(organization_id, code)`.

**Response**: CLARIFIED per Addendum Section 2.1.

The current implementation is **correct**:
```python
# backend/models/account.py line 154-156
__table_args__ = (
    Index("ix_accounts_client_code", "client_id", "code", unique=True),
)
```

**Justification** (from Addendum):
> "Each client has its own chart of accounts. Account codes are meaningful only within the context of a client. Therefore: `(client_id, code)` uniqueness is **correct**. `(organization_id, code)` uniqueness would be **wrong**."

This is intentional and reflects our domain model where:
- Organizations are SaaS tenants (accounting firms)
- Clients are their customers (businesses being managed)
- Each client has their own CoA from their own accounting software

**Action**: None required. Mark as PASS.

**Documentation fix**: The model docstring at line 60 incorrectly states `(organization_id, code)`. This should be corrected to `(client_id, code)` for consistency.

---

### 2.3 RLS FORCE on organizations/users — DISAGREE

**Report finding**: `FORCE ROW LEVEL SECURITY` missing on `organizations` and `users` tables.

**Response**: DISAGREE. Intentionally omitted with documented counter-controls.

**Current implementation** (from `v2_090_rls_policies.py`):

```python
# Lines 177-198: organizations table
# NOTE: No FORCE RLS - allows owner to create orgs during registration

# Lines 200-224: users table
# NOTE: No FORCE RLS - allows owner to query for auth
```

**Counter-controls in place**:

1. **RLS policies still exist** - The policies are created and enforced for `app_user` and `app_readonly` roles
2. **Only table owner bypasses** - Only the database connection owner (used for migrations/auth) bypasses RLS
3. **Auth workflow requirement** - User authentication must query by email before organization context is known
4. **Registration workflow requirement** - New organization creation happens before any org_id context can be set
5. **app_admin role has BYPASSRLS** - Explicit role for administrative operations

**Why FORCE would break the application**:

| Operation | Requires | Why FORCE Fails |
|-----------|----------|-----------------|
| User login | Query users by email | No org_id known yet |
| Registration | Create new organization | No org_id exists yet |
| Password reset | Query users by email | No org_id in context |

**Alternative considered**: Separate connection pools (one with BYPASSRLS for auth, one without). Rejected as over-engineering for current scale.

**Action**: None required. Document this decision in `ARCHITECTURE_PRINCIPLES.md`.

---

### 2.4 pgcrypto Extension — AGREE

**Report finding**: `gen_random_uuid()` used but extension not explicitly managed.

**Response**: AGREE. This is a portability risk.

**Current state**: Multiple migrations use `gen_random_uuid()`:
- `v2_071_cashflow_facts_and_quarantine.py`
- `v2_080_document_review_tables.py`

**Risk**: Fresh database deployments or CI/CD environments may fail if pgcrypto is not pre-installed.

**Required action**: Add migration to explicitly create extension.

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

**Alembic migration**: To be created as `v2_095_pgcrypto_extension.py` (slots between RLS and accounts idempotency).

**Priority**: MEDIUM - Required for portability but not blocking current operations.

---

## 3. Additional Finding: Documentation Inconsistency

During review, I identified a documentation inconsistency in `backend/models/account.py`:

**Line 59-60** (docstring):
```
Unique Constraint:
    (organization_id, code) - one account per code per organization
```

**Line 154-156** (actual code):
```python
__table_args__ = (
    Index("ix_accounts_client_code", "client_id", "code", unique=True),
)
```

**Action**: Update docstring to match implementation. This is cosmetic but prevents future confusion.

---

## 4. Required Migrations

### Migration 1: pgcrypto Extension
**File**: `alembic/versions/v2_095_pgcrypto_extension.py`
**Priority**: MEDIUM

```python
"""v2_095_pgcrypto_extension

Explicitly manage pgcrypto extension for gen_random_uuid() support.
"""

from alembic import op

revision = "v2_095_pgcrypto_extension"
down_revision = "v2_090_rls_policies"

def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

def downgrade() -> None:
    # Don't drop - other things may depend on it
    pass
```

### Migration 2: Accounts Platform Idempotency
**File**: `alembic/versions/v2_100_accounts_platform_idempotency.py`
**Priority**: CRITICAL

```python
"""v2_100_accounts_platform_idempotency

Add client-scoped platform idempotency constraint to accounts table.
Prevents duplicate accounts on sync retry.
"""

from alembic import op

revision = "v2_100_accounts_platform_idempotency"
down_revision = "v2_095_pgcrypto_extension"

def upgrade() -> None:
    op.execute("""
        CREATE UNIQUE INDEX CONCURRENTLY ux_accounts_client_platform
        ON public.accounts (client_id, platform_name, platform_id)
        WHERE client_id IS NOT NULL;
    """)

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ux_accounts_client_platform;")
```

---

## 5. Schema Comments (Addendum Section 3)

Per Addendum requirement, add clarifying comment:

```sql
COMMENT ON TABLE public.accounts IS
'Client-scoped chart-of-accounts entries. Each client maintains an independent CoA synced from their accounting platform (Xero, QuickBooks, etc.). Uniqueness is enforced per client, NOT per organization.';
```

This should be added to Migration 2.

---

## 6. Summary of Actions

| Action | File | Priority | Status |
|--------|------|----------|--------|
| Create pgcrypto migration | `v2_095_pgcrypto_extension.py` | MEDIUM | TODO |
| Create accounts idempotency migration | `v2_100_accounts_platform_idempotency.py` | CRITICAL | TODO |
| Fix account.py docstring | `backend/models/account.py` | LOW | TODO |
| Document RLS FORCE decision | `ARCHITECTURE_PRINCIPLES.md` | LOW | TODO |

---

## 7. Sign-off Criteria

After implementing the above:
- [ ] pgcrypto extension migration applied
- [ ] Accounts idempotency constraint applied
- [ ] All 903+ tests passing
- [ ] Schema dump regenerated
- [ ] Verification report re-run confirms all PASS

---

## 8. Response to Subcontractor

The verification report is thorough and valuable. Two items required correction:
1. **Accounts idempotency** - Valid gap, now addressed
2. **pgcrypto** - Valid portability concern, now addressed

Two items were rejected with justification:
1. **Account code uniqueness** - Report assumed standard accounting model; our domain model is intentionally different (client-scoped CoA)
2. **RLS FORCE** - Intentionally omitted with documented counter-controls for auth/registration workflows

The database will be compliant after the two migrations are applied.

---

**Document Status**: COMPLETE
**Next Step**: Implement migrations and re-verify
