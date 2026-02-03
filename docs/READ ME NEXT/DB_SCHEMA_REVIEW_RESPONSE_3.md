# Response to Schema Review - Finding Common Ground

**Date**: February 3, 2026
**Reviewer**: Subcontractor
**Respondent**: Lead Engineer
**Status**: Revised position with concessions

---

## Summary of Revised Position

| Point | Original Position | Revised Position |
|-------|-------------------|------------------|
| A) accounts.client_id + idempotency | Agreed NOT NULL | **AGREE + add idempotency uniqueness** |
| B) accounting_platforms | Defer full refactor | **AGREE to "stop the bleeding" now** |
| C.2) users.org_id nullable | Defended as-is | **CONCEDE - add pending user invariant** |
| C.3) FORCE RLS bypass | Defended table-owner | **CONCEDE - implement SECURITY DEFINER** |
| D) Assignment-based RLS | Deferred | **MAINTAIN - document as product decision** |

---

## Point-by-Point Revised Response

### A) accounts.client_id — AGREE, Including Idempotency

**Original position**: Add NOT NULL + composite FK.

**Reviewer's addition**: Idempotency uniqueness must be scoped correctly.

**Revised position**: Agree. Without idempotency uniqueness, sync retries create duplicates.

**Implementation**:
```sql
-- Step 1: Composite unique on clients (already done in v2_095)
-- UNIQUE (organization_id, id) on clients

-- Step 2: accounts.client_id NOT NULL
ALTER TABLE accounts ALTER COLUMN client_id SET NOT NULL;

-- Step 3: Composite FK
ALTER TABLE accounts
ADD CONSTRAINT fk_accounts_client
FOREIGN KEY (organization_id, client_id)
REFERENCES clients(organization_id, id)
ON DELETE CASCADE;

-- Step 4: Idempotency uniqueness (minimum acceptable)
CREATE UNIQUE INDEX CONCURRENTLY ux_accounts_client_platform_idempotency
ON accounts (client_id, platform_name, platform_id);
```

**Note on "best" option**: The reviewer suggests `UNIQUE(accounting_platform_id, platform_id)` as best practice. This requires the accounting_platforms refactor in (B). We will implement the minimum acceptable now and upgrade when accounting_platforms is client-scoped.

**Migration**: v2_110_accounts_client_enforcement

---

### B) accounting_platforms — AGREE to "Stop the Bleeding" Now

**Original position**: Document target architecture, defer refactor.

**Reviewer's point**: Documentation alone allows schema drift. Must implement hard constraints now.

**Revised position**: Agree. Implement "stop the bleeding" changes immediately.

**Implementation**:
```sql
-- Step 1: Rename misleading column
ALTER TABLE accounting_platforms
RENAME COLUMN client_id TO oauth_client_id;

-- Step 2: Add managed_client_id
ALTER TABLE accounting_platforms
ADD COLUMN managed_client_id UUID NULL
REFERENCES clients(id) ON DELETE SET NULL;

-- Step 3: Add composite FK for org consistency
-- (requires uq_clients_org_id which we already have)
-- First add org-scoped unique on accounting_platforms
ALTER TABLE accounting_platforms
ADD CONSTRAINT uq_accounting_platforms_org_id
UNIQUE (organization_id, id);

-- Then we can add composite FK when managed_client_id is set
-- For now, add a trigger to enforce org match on INSERT/UPDATE
CREATE OR REPLACE FUNCTION check_accounting_platform_client_org()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.managed_client_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM clients
            WHERE id = NEW.managed_client_id
            AND organization_id = NEW.organization_id
        ) THEN
            RAISE EXCEPTION 'managed_client_id must belong to same organization';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_accounting_platforms_client_org
BEFORE INSERT OR UPDATE ON accounting_platforms
FOR EACH ROW
EXECUTE FUNCTION check_accounting_platform_client_org();

-- Step 4: Add comment documenting target state
COMMENT ON COLUMN accounting_platforms.managed_client_id IS
'The client whose external accounting system this connection represents.
Currently nullable during transition. Target: NOT NULL for all new connections.';
```

**Phase 2** (when ready for full refactor):
- Backfill `managed_client_id` for existing connections
- Add NOT NULL constraint
- Update sync engine to be client-aware
- Add proper uniqueness: `UNIQUE(managed_client_id, platform_name, tenant_id)`

**Migration**: v2_111_accounting_platforms_client_scope

---

### C.2) users.organization_id — CONCEDE, Add Pending User Invariant

**Original position**: Nullable is intentional for registration, app enforces completion.

**Reviewer's point**: "App enforces it" is not a DB control. Add a DB-level invariant.

**Revised position**: Concede. The "pending user" pattern with CHECK constraint is clean and doesn't complicate registration.

**Implementation** (Pattern 1 from reviewer):
```sql
-- Step 1: Add status column if not exists
-- (Check: we already have is_active, but that's different from pending/active/disabled)
ALTER TABLE users
ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending'
CHECK (status IN ('pending', 'active', 'suspended', 'disabled'));

-- Step 2: Add the invariant
ALTER TABLE users
ADD CONSTRAINT ck_users_org_status
CHECK (
    (status = 'pending' AND organization_id IS NULL)
    OR
    (status != 'pending' AND organization_id IS NOT NULL)
);

-- Step 3: Backfill existing users
UPDATE users SET status = 'active' WHERE organization_id IS NOT NULL;
UPDATE users SET status = 'pending' WHERE organization_id IS NULL;

-- Step 4: Add defaults
ALTER TABLE users
ALTER COLUMN created_at SET DEFAULT now(),
ALTER COLUMN updated_at SET DEFAULT now(),
ALTER COLUMN is_active SET DEFAULT true,
ALTER COLUMN is_admin SET DEFAULT false;
```

**Application change required**:
- Registration creates user with `status = 'pending'`
- After org creation/join, update to `status = 'active'`
- Login rejects `status = 'pending'` users (or prompts to complete setup)

**Migration**: v2_112_users_pending_invariant

---

### C.3) FORCE RLS — CONCEDE, Implement SECURITY DEFINER Pattern

**Original position**: Table-owner bypass is acceptable for auth flow.

**Reviewer's point**: "Table-owner bypass" is not auditable, creates implicit god-mode, undermines DB-enforced tenancy claim.

**Revised position**: Concede. The reviewer is correct. I will implement **Solution B: SECURITY DEFINER functions**.

**Why Solution B**:
- Solution A (separate auth schema) requires schema restructure
- Solution C (dedicated BYPASSRLS role) requires connection pool changes
- Solution B is surgical: one function, explicit bypass surface, auditable

**Implementation**:
```sql
-- Step 1: Create auth lookup function with SECURITY DEFINER
-- This runs with the privileges of the function owner (who can bypass RLS)
-- but only exposes the minimum needed for authentication

CREATE OR REPLACE FUNCTION auth_lookup_user_by_email(lookup_email TEXT)
RETURNS TABLE (
    user_id UUID,
    password_hash VARCHAR(255),
    user_status VARCHAR(20),
    organization_id UUID,
    user_role VARCHAR(50),
    is_active BOOLEAN
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.password_hash,
        u.status,
        u.organization_id,
        u.role,
        u.is_active
    FROM users u
    WHERE u.email = lookup_email;
END;
$$;

-- Step 2: Restrict execution to app roles only
REVOKE ALL ON FUNCTION auth_lookup_user_by_email(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_lookup_user_by_email(TEXT) TO app_user;
GRANT EXECUTE ON FUNCTION auth_lookup_user_by_email(TEXT) TO app_admin;

-- Step 3: Add similar function for organization lookup during registration
CREATE OR REPLACE FUNCTION auth_lookup_org_by_id(lookup_id UUID)
RETURNS TABLE (
    org_id UUID,
    org_name VARCHAR(255)
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id,
        o.name
    FROM organizations o
    WHERE o.id = lookup_id;
END;
$$;

REVOKE ALL ON FUNCTION auth_lookup_org_by_id(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_lookup_org_by_id(UUID) TO app_user;
GRANT EXECUTE ON FUNCTION auth_lookup_org_by_id(UUID) TO app_admin;

-- Step 4: Now we can FORCE RLS on both tables
ALTER TABLE users FORCE ROW LEVEL SECURITY;
ALTER TABLE organizations FORCE ROW LEVEL SECURITY;

-- Step 5: Add audit comment
COMMENT ON FUNCTION auth_lookup_user_by_email(TEXT) IS
'SECURITY DEFINER function for auth. This is the ONLY approved bypass of users RLS.
Returns minimal fields needed for authentication. Auditable entry point.';
```

**Application change required**:
- Replace direct `SELECT * FROM users WHERE email = ?` with function call
- `SELECT * FROM auth_lookup_user_by_email(?)`

**Audit surface**: The function is now the explicit, documented, single bypass point. Any other attempt to query users without org context will return zero rows.

**Migration**: v2_113_auth_security_definer

---

### D) Assignment-Based RLS — MAINTAIN Deferral, Document as Product Decision

**Original position**: Assignments are workflow, not access control.

**Reviewer's position**: Acceptable if documented as product decision, not technical decision.

**Revised position**: Maintain deferral. Add explicit documentation.

**Documentation to add** (in GLOSSARY.md and README):

```markdown
## Access Control Model (Product Decision)

**Current model**: Organization-level access.
- All users in an organization can view all clients in that organization.
- ClientAssignments track workflow responsibility, not access permissions.
- This is intentional for small/medium accounting practices where coverage is essential.

**What this means**:
- "Accountant A" can see "Client X" even if not assigned.
- Assignments determine "who should work on this," not "who can see this."
- Managers/admins can see who is responsible but don't need to manage view permissions.

**When we would revisit**:
- Enterprise customer requires per-user client segregation.
- Regulatory requirement for data partitioning within tenant.
- Not planned for beta launch.

**Cross-org integrity is still enforced**:
- User from Org A cannot be assigned to Client from Org B (composite FK).
- This is a data integrity control, not an access control.
```

**No schema change for D. Documentation only.**

---

## Migration Sequence

| Order | Migration | Content | Priority |
|-------|-----------|---------|----------|
| 1 | v2_110_accounts_client_enforcement | NOT NULL, composite FK, idempotency | HIGH |
| 2 | v2_111_accounting_platforms_client_scope | Rename oauth_client_id, add managed_client_id, trigger | HIGH |
| 3 | v2_112_users_pending_invariant | Status column, CHECK constraint, defaults | HIGH |
| 4 | v2_113_auth_security_definer | Auth functions, FORCE RLS on users/orgs | HIGH |

**All four migrations are required before sign-off.**

---

## What We're Agreeing To

| Control | Implementation |
|---------|----------------|
| accounts must belong to client | NOT NULL + composite FK |
| accounts sync idempotency | UNIQUE(client_id, platform_name, platform_id) |
| accounting_platforms client linkage | managed_client_id + org-match trigger |
| users pending state invariant | status + CHECK constraint |
| auth bypass is explicit and auditable | SECURITY DEFINER functions |
| FORCE RLS on users/organizations | Yes, after auth functions exist |
| Assignment-based access control | Deferred (documented product decision) |

---

## What We're NOT Doing (Explicitly Deferred)

| Item | Reason | When to Revisit |
|------|--------|-----------------|
| Full accounting_platforms refactor | Major sync engine changes | Phase 6 |
| Assignment-based RLS policies | Product decision: org-level access | Enterprise customer request |
| Separate auth schema | SECURITY DEFINER is sufficient | If audit requires stricter separation |

---

## Request for Sign-Off

With these four migrations implemented:
1. DB enforces accounts belong to clients (not orphans)
2. DB enforces sync idempotency (no retry duplicates)
3. DB enforces user pending state (no "active user without org")
4. Auth bypass is explicit via SECURITY DEFINER (auditable, not implicit)
5. FORCE RLS applies to all tenant tables including users/organizations

Is this sufficient for sign-off, or are there remaining concerns?

---

**Response Status**: REVISED - SEEKING AGREEMENT
**Next Step**: Await reviewer confirmation, then implement migrations
