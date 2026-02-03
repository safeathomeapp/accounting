# Database Hardening Verification Report
## Post-Implementation Review — Action Required

Audience:
- Lead Engineer
- Senior Backend Engineers
- Database Owner

Tone:
Direct, factual, and professional. This document is not advisory fluff. It is a **verification report with explicit corrective actions**.

Scope:
This review validates whether the implemented PostgreSQL schema meets the hardening, governance, and SaaS-readiness standards previously agreed. The review is based on the supplied SQL schema dump and compares **intended controls vs. actual enforcement**.

---

## 1. Executive Summary (Read This First)

The database is **materially improved** and significantly closer to a production-grade financial SaaS standard.

However, it is **not yet complete**.

Three critical controls are either missing or partially implemented. These are not stylistic issues. They are correctness, safety, and portability gaps that *will* surface under retries, scale, or environment replication.

Bottom line:
- Most of the work is correct.
- The remaining gaps must be closed before calling this “done.”

---

## 2. Verification Results Overview

| Control Area | Status | Notes |
|-------------|--------|-------|
| Timestamp & boolean defaults | PASS | Correctly enforced |
| updated_at triggers | PASS | Correct and consistent |
| Transaction arithmetic checks | PASS | Correct |
| Org-scoped provider uniqueness (clients, transactions) | PASS | Correct |
| FK index gaps (AI analysis) | PASS | Correct |
| Row-Level Security (RLS) | PARTIAL | FORCE missing on 2 tables |
| Account idempotency uniqueness | FAIL | Missing constraint |
| Account code uniqueness model | PARTIAL | Likely incorrect |
| pgcrypto extension management | PARTIAL | Portability risk |
| Retention & purge ops | OUT OF SCOPE | Not verifiable from schema |

Anything marked FAIL or PARTIAL requires action.

---

## 3. Confirmed Passes (No Action Required)

The following controls are correctly implemented and should not be revisited unless requirements change.

### 3.1 Defaults and Nullability
- created_at / updated_at defaults present
- boolean defaults present
- NOT NULL enforced where expected

### 3.2 updated_at Enforcement
- `public.set_updated_at()` function exists
- BEFORE UPDATE triggers exist on all relevant tables

### 3.3 Financial Correctness
- ISO currency format enforced
- tax_amount non-negative
- total_amount arithmetic enforced

### 3.4 Idempotency (Partial)
- Clients and transactions correctly enforce:
  `(organization_id, platform_name, platform_id)` uniqueness

### 3.5 FK Indexing
- Missing FK indexes for `ai_analysis_results` are present

These are correctly done. Do not regress them.

---

## 4. Failures and Required Corrections

### 4.1 FAIL — Accounts Provider Idempotency Not Enforced

**Current state**
- accounts.platform_id and platform_name are NOT NULL
- There is NO uniqueness constraint tying them together per organization

**Impact**
- Sync retries can create duplicate accounts
- Idempotency guarantees are broken
- Downstream reporting and mappings will drift silently

**This is not theoretical. This will happen.**

**Required action**
Add the following constraint:

```sql
CREATE UNIQUE INDEX CONCURRENTLY ux_accounts_org_platform
ON public.accounts (organization_id, platform_name, platform_id);
```

**Priority**
CRITICAL. This must be fixed before production sync workloads increase.

---

### 4.2 PARTIAL — Account Code Uniqueness Is Likely Wrong

**Current state**
- Unique index exists on `(client_id, code)`

**Problem**
- Chart-of-accounts codes are almost always organization-scoped, not client-scoped.
- This model is unusual and high-risk unless explicitly intended.

**Risk**
- Duplicate codes across the same organization
- Confusing financial reporting
- Hard-to-explain accounting behaviour

**Required action**
One of the following must happen — explicitly:

Option A (recommended):
```sql
CREATE UNIQUE INDEX CONCURRENTLY ux_accounts_org_code
ON public.accounts (organization_id, code);
```

Option B:
- Document clearly (in code and schema docs) that accounts are client-scoped
- Accept that this deviates from standard accounting models

**Priority**
HIGH. Resolve intentionally; do not leave ambiguous.

---

### 4.3 PARTIAL — Row-Level Security FORCE Missing

**Current state**
- RLS enabled on all tenant tables
- `FORCE ROW LEVEL SECURITY` missing on:
  - organizations
  - users

**Impact**
- Table owners or privileged roles can bypass RLS unintentionally
- This undermines tenant isolation guarantees

**Required action**
Execute:

```sql
ALTER TABLE public.organizations FORCE ROW LEVEL SECURITY;
ALTER TABLE public.users FORCE ROW LEVEL SECURITY;
```

Ensure admin/migration roles explicitly use BYPASSRLS.

**Priority**
HIGH for SaaS environments.

---

### 4.4 PARTIAL — pgcrypto Extension Not Explicitly Managed

**Current state**
- `gen_random_uuid()` is used in defaults
- No `CREATE EXTENSION pgcrypto` present in schema

**Impact**
- Fresh environments may fail
- CI/CD or customer-hosted deployments may break
- “Works on this DB” risk

**Required action**
Add pgcrypto via Alembic migration:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

**Priority**
MEDIUM, but must be resolved for portability.

---

## 5. Items Not Verifiable from Schema

The following are expected to exist operationally but cannot be verified from DDL:

- Retention / purge jobs
- Retention execution logs
- Archive strategy

If these are implemented outside the database:
- ensure they are documented,
- ensure execution is logged,
- ensure logs are retained.

This is governance, not optional polish.

---

## 6. Required Next Steps (Non-Negotiable)

Before declaring database hardening “complete”:

1. Add accounts provider-id uniqueness
2. Resolve account code uniqueness model explicitly
3. FORCE RLS on all tenant-scoped tables
4. Manage pgcrypto via migration or infra
5. Re-run schema verification after changes

Only after these are done should this be signed off.

---

## 7. Final Assessment

This is **good work** — but incomplete.

The remaining issues are:
- small in effort,
- large in impact,
- and entirely fixable now.

Leaving them unresolved would be a conscious acceptance of avoidable risk.

This report should be treated as an action list, not a discussion starter.
