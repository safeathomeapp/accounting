# Session Notes - February 3, 2026

## Session Overview
**Focus**: Database Hardening - FINAL_NON_NEGOTIABLE_DB_STANCE implementation
**Branch**: `feat/doc-review-ui`
**Database**: Advanced from `v2_090_rls_policies` to `v2_114_auth_security_definer`

---

## Completed

### 1. Created Database Hardening Migrations (v2_095, v2_110-v2_114)

Implemented all requirements from `FINAL_NON_NEGOTIABLE_DB_STANCE.md`:

| Migration | Description | Key Changes |
|-----------|-------------|-------------|
| **v2_095** | client_assignments | Composite FKs to clients and users, CHECK on assignment_role |
| **v2_110** | accounts client enforcement | `client_id NOT NULL`, composite FK `(org_id, client_id) → clients`, idempotency index |
| **v2_111** | accounting_platforms client scope | Renamed `client_id → oauth_client_id`, added `managed_client_id` with composite FK |
| **v2_112** | users pending invariant | Added `status` column, CHECK constraint `(pending AND org NULL) OR (not pending AND org NOT NULL)` |
| **v2_113** | email uniqueness | Case-insensitive unique index on `lower(email)` |
| **v2_114** | SECURITY DEFINER auth | `auth_definer` role, 4 auth functions, FORCE RLS on users/organizations |

### 2. Fixed Migration Issues During Execution

- **v2_095**: Changed partial unique INDEX to proper UNIQUE CONSTRAINT on `users(organization_id, id)` - PostgreSQL requires constraints (not indexes) for FK references
- **v2_110 & v2_113**: Removed `CONCURRENTLY` from index creation - cannot run inside Alembic transactions

### 3. Updated ORM Models

- **User model**: Added `status` column for pending state tracking
- **AccountingPlatform model**: Added `managed_client_id`, renamed `client_id → oauth_client_id`

### 4. Generated Schema Dump for DBA Sign-off

- Created `/docs/schema_dump_v2_114.sql` (3,151 lines)
- Verified all required constraints present in dump
- Pushed to GitHub for DBA review

### 5. Updated Documentation

- **README.md**: Updated session instructions, current state, completed features, Phase 4A/5 status
- **DATABASE_SCHEMA.md**: Updated to v2.0, added new constraints, SECURITY DEFINER section
- **GLOSSARY.md**: Added SECURITY DEFINER, auth_definer role, updated migration sequences

---

## Key Decisions Made

### 1. Composite FKs for Cross-Org Integrity
All foreign keys that could allow cross-organization references now use composite FKs:
- `accounts(organization_id, client_id) → clients(organization_id, id)`
- `accounting_platforms(organization_id, managed_client_id) → clients(organization_id, id)`
- `client_assignments(organization_id, client_id) → clients(organization_id, id)`
- `client_assignments(organization_id, user_id) → users(organization_id, id)`

### 2. SECURITY DEFINER vs Table Owner Bypass
Chose SECURITY DEFINER functions for auth bypass instead of table owner bypass because:
- Explicit and auditable
- Single entry point for RLS bypass
- Function ownership by dedicated `auth_definer` role
- Hardened with strict `search_path`

### 3. Users Pending State Invariant
Implemented CHECK constraint ensuring:
- `status = 'pending'` → `organization_id IS NULL`
- `status != 'pending'` → `organization_id IS NOT NULL`

This prevents "active users without tenant context" bug class.

---

## In Progress

- Awaiting DBA sign-off on schema dump
- Servers running for manual testing (backend :8000, frontend :3000)

---

## Blockers

None currently. Awaiting DBA review.

---

## Next Session Priorities

1. **Receive DBA sign-off** on FINAL_NON_NEGOTIABLE requirements
2. **Run acceptance tests** from Section 4 of FINAL_NON_NEGOTIABLE_DB_STANCE.md
3. **Merge to master** or continue with real OAuth implementation
4. **Test Claude OCR** with real invoices/receipts

---

## Technical Notes

### SECURITY DEFINER Functions Created

```sql
-- Login lookup
auth_lookup_user_by_email(lookup_email TEXT)
  → (user_id, password_hash, user_status, organization_id, user_role, is_active)

-- Org lookup for registration
auth_lookup_org_by_id(lookup_id UUID)
  → (org_id, org_name, org_status)

-- Create pending user
auth_create_pending_user(p_email, p_password_hash, p_name)
  → UUID

-- Activate user with org
auth_activate_user(p_user_id, p_organization_id)
  → BOOLEAN
```

### Database Roles

| Role | Purpose |
|------|---------|
| app_user | Normal app queries with RLS |
| app_readonly | Reporting with RLS |
| app_admin | Admin operations with RLS |
| auth_definer | Owns SECURITY DEFINER functions, NOLOGIN |

---

## Files Modified

| File | Changes |
|------|---------|
| `alembic/versions/v2_095_client_assignments.py` | Fixed unique constraint (INDEX → CONSTRAINT) |
| `alembic/versions/v2_110_accounts_client_enforcement.py` | Created + fixed CONCURRENTLY issue |
| `alembic/versions/v2_111_accounting_platforms_client_scope.py` | Created |
| `alembic/versions/v2_112_users_pending_invariant.py` | Created |
| `alembic/versions/v2_113_email_uniqueness.py` | Created + fixed CONCURRENTLY issue |
| `alembic/versions/v2_114_auth_security_definer.py` | Created |
| `backend/models/user.py` | Added `status` column |
| `backend/models/accounting_platform.py` | Added `managed_client_id`, renamed `oauth_client_id` |
| `docs/schema_dump_v2_114.sql` | Created for DBA review |
| `README.md` | Updated current state and session instructions |
| `docs/ARCHITECTURE/DATABASE_SCHEMA.md` | Updated to v2.0 with new constraints |
| `docs/GLOSSARY.md` | Added auth terms and migration sequences |

---

## Git Commits

1. `eda215d` - feat(db): Implement database hardening per FINAL_NON_NEGOTIABLE_DB_STANCE
2. `cd85350` - fix(migrations): Fix FK constraint and CONCURRENTLY issues
3. `e6f6530` - docs: Add schema dump v2_114 for DB review sign-off

---

**Session End**: February 3, 2026
**Next Session**: Await DBA sign-off, then proceed with merge or OAuth
