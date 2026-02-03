# Response to Schema Review (February 3, 2026)

**Reviewer**: Subcontractor
**Respondent**: Lead Engineer
**Status**: Response with partial agreement and pushback

---

## Executive Summary

| Point | Verdict | Action |
|-------|---------|--------|
| A) accounts.client_id nullable | **AGREE** | Migration to NOT NULL needed |
| B) accounting_platforms per-client | **AGREE IN PRINCIPLE** | Major refactor - needs scoping |
| C) Users defaults missing | **AGREE** | Add defaults |
| C) Users org_id NOT NULL | **DISAGREE** | Registration flow requires nullable |
| C) FORCE RLS on users/orgs | **DISAGREE** | Auth flow requires table-owner bypass |
| D) Assignment-based RLS | **DISAGREE** | Intentionally deferred - workflow not access |

---

## Detailed Response

### A) accounts.client_id Nullable — AGREE

**Current state**: `client_id` is nullable with comment "Nullable during migration, should be required for new accounts"

**Reviewer is correct**: This is a correctness hole. Orphaned accounts will accumulate.

**Action**:
1. Backfill existing accounts to appropriate clients
2. Add NOT NULL constraint
3. Add composite FK `(organization_id, client_id) → clients(organization_id, id)`

**Migration sequence**:
```sql
-- Step 1: Identify orphans
SELECT id, code, name FROM accounts WHERE client_id IS NULL;

-- Step 2: Backfill (requires business logic decision)
-- Step 3: Add NOT NULL
ALTER TABLE accounts ALTER COLUMN client_id SET NOT NULL;

-- Step 4: Add composite FK (requires uq_clients_org_id first)
ALTER TABLE accounts
ADD CONSTRAINT fk_accounts_client
FOREIGN KEY (organization_id, client_id)
REFERENCES clients(organization_id, id);
```

**Timeline**: Next migration batch.

---

### B) accounting_platforms Per-Client — AGREE IN PRINCIPLE, SCOPE CONCERN

**Reviewer's point**: The current schema models "organization has platforms" but the domain model requires "client has platforms".

**This is architecturally correct.** In the UK practice model:
- Each client business has their own Xero/QBO account
- The practice is invited as an "advisor" to each client's account
- Therefore: one platform connection per client, not per organization

**However**, this is a **significant refactor**:

| Current | Required |
|---------|----------|
| `accounting_platforms.organization_id` | Keep (for RLS) |
| `accounting_platforms.client_id` (OAuth) | Rename to `oauth_client_id` |
| (missing) | Add `managed_client_id → clients(id)` |
| Uniqueness on org+platform | Uniqueness on client+platform+realm |

**Downstream impact**:
- Sync engine assumes org-level connections
- OAuth flow stores tokens at org level
- All platform adapters need updates
- Test suite needs updates

**My recommendation**:
1. **Agree** this is the correct target architecture
2. **Defer** to a dedicated refactor phase (not a drive-by fix)
3. **Document** the target schema now so new code doesn't make it worse

**Proposed compromise**:
- Add `managed_client_id` column now (nullable)
- Rename `client_id` → `oauth_client_id` now (breaking change, but clean)
- Backfill and enforce NOT NULL in subsequent phase
- Update sync engine to be client-aware in subsequent phase

**Timeline**: Phase 6 or dedicated sprint. Not blocking current work.

---

### C) Users Table — PARTIAL AGREE

#### C.1) Missing defaults — AGREE

**Current**:
```sql
created_at timestamp with time zone NOT NULL,  -- no default
updated_at timestamp with time zone NOT NULL,  -- no default
is_active boolean NOT NULL,                    -- no default
is_admin boolean NOT NULL,                     -- no default
```

**Required**:
```sql
created_at timestamp with time zone NOT NULL DEFAULT now(),
updated_at timestamp with time zone NOT NULL DEFAULT now(),
is_active boolean NOT NULL DEFAULT true,
is_admin boolean NOT NULL DEFAULT false,
```

**Action**: Add defaults in next migration.

---

#### C.2) organization_id NOT NULL — DISAGREE

**Reviewer suggests**: Make `users.organization_id` NOT NULL unless "global/system user" is documented.

**Our position**: Nullable is **intentional** for registration flow.

**Registration sequence**:
1. User submits email + password
2. User record created (org_id = NULL)
3. User creates or joins organization
4. User record updated (org_id = <uuid>)

If we make org_id NOT NULL, we must either:
- Create a dummy org during registration (bad: orphan orgs)
- Require org to exist before user (bad: chicken-egg)
- Use a separate "pending_users" table (over-engineering)

**Counter-control**: Application code enforces org_id is set before any data access. RLS returns no rows if org context not set.

**Action**: Document this decision. No schema change.

---

#### C.3) FORCE RLS on users/organizations — DISAGREE

**Reviewer suggests**: `ALTER TABLE users FORCE ROW LEVEL SECURITY`

**Our position**: Intentionally omitted. Documented in migration comments.

**Why FORCE breaks auth**:

| Operation | Requires | Why FORCE Fails |
|-----------|----------|-----------------|
| Login | Query user by email | No org_id known yet |
| Password reset | Query user by email | No org_id in context |
| Registration | Create organization | No org_id exists yet |

**Current mitigation**:
- RLS policies exist and are enforced for `app_user` and `app_readonly` roles
- Only table owner (connection user) bypasses RLS
- Table owner is only used for auth operations
- All data access uses `app_user` role with org context set

**Alternative considered**: Separate connection pool with BYPASSRLS for auth. Rejected as over-engineering for current scale.

**Action**: Document decision in GLOSSARY.md and architecture docs. No schema change.

---

### D) Assignment-Based RLS — DISAGREE (INTENTIONAL DEFERRAL)

**Reviewer suggests**: RLS policies should incorporate user assignments:
```sql
organization_id = app.org_id
AND (EXISTS active assignment OR user is admin)
```

**Our explicit design decision**: Assignments are for **workflow**, not **access control**.

**Rationale**:
1. All staff in a practice can access all clients (cover for sick, handoffs)
2. Assignments track **responsibility**, not **permission**
3. Assignment-based RLS adds complexity with limited benefit at current scale
4. "Who can see what" is org-level; "who should work on what" is assignment-level

**If we wanted assignment-based access control**, we would need:
- `app.user_id` session variable in addition to `app.org_id`
- Policy joins to `client_assignments` on every client-scoped query
- Admin bypass logic in every policy
- Significantly more complex testing

**This is a product decision, not a technical oversight.**

**When to revisit**:
- If a customer explicitly requires "accountant A cannot see client X"
- If we expand to enterprise with strict data segregation requirements
- Not before beta launch

**Action**: Document this as intentional in architecture docs. No implementation.

---

## Summary of Actions

### Immediate (Next Migration Batch)

| Item | Migration | Priority |
|------|-----------|----------|
| accounts.client_id NOT NULL | v2_105 | HIGH |
| accounts composite FK to clients | v2_105 | HIGH |
| users defaults (created_at, is_active, etc.) | v2_106 | MEDIUM |
| Rename accounting_platforms.client_id → oauth_client_id | v2_107 | MEDIUM |
| Add accounting_platforms.managed_client_id (nullable) | v2_107 | MEDIUM |

### Deferred (Phase 6 / Dedicated Sprint)

| Item | Reason |
|------|--------|
| accounting_platforms client-scoping enforcement | Major refactor, needs sync engine updates |
| Assignment-based RLS | Product decision: not required for beta |
| FORCE RLS on users/organizations | Auth flow requires current design |

### Documentation Only (No Code Change)

| Item | Document |
|------|----------|
| users.organization_id nullable rationale | GLOSSARY.md, migration comments |
| FORCE RLS omission rationale | GLOSSARY.md, RLS migration comments |
| Assignment = workflow, not access | GLOSSARY.md, client_assignments comments |
| Target architecture for accounting_platforms | New ARCHITECTURE doc section |

---

## Closing

The review is valuable and identifies real gaps. However:

1. **accounts.client_id**: Agree, will fix.
2. **accounting_platforms refactor**: Agree it's correct, but it's a major change that needs proper scoping. Partial fix now, full fix later.
3. **Users table**: Defaults yes, org_id nullable and no FORCE RLS are intentional with documented rationale.
4. **Assignment-based RLS**: Intentionally deferred. This is a product decision. Our current model is "all staff see all clients, assignments track responsibility."

We should not let perfect be the enemy of good. The current schema is safe for beta with the agreed fixes. The larger refactors are Phase 6+ work.

---

**Response Status**: COMPLETE
**Next Step**: Kev to review and confirm scope decisions before implementation
