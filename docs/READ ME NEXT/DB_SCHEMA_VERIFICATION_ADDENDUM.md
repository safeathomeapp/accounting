# Addendum: Domain Clarification, Naming Canon, and Verification Guidance
## To be read in conjunction with DB_SCHEMA_VERIFICATION_REPORT.md

Audience:
- Lead Programmer
- Senior Backend Engineers
- Database Owner

This addendum exists to remove ambiguity, eliminate false positives during verification, and **canonise domain language** so future schema and code decisions are internally consistent.

The tone is intentionally direct. Ambiguity is the enemy of correctness in financial systems.

---

## 1. Canonical Domain Definitions (Non‑Negotiable)

The following definitions are now **canonical**. All schema, code, migrations, and documentation must align with them.

### Organization
- Represents the **tenant / firm using the software**.
- This is the SaaS account holder.
- All data isolation, RLS policies, and access control are scoped to `organization_id`.

There is no global chart of accounts at the organization level.

---

### Client
- Represents a **customer / counterparty of an organization**.
- Clients belong to exactly one organization.
- Clients may be legal entities, individuals, or other accounting counterparties.

---

### Accounts
- Represents **client‑scoped chart‑of‑accounts entries**.
- Each client may have:
  - a bespoke chart of accounts,
  - provider‑specific account identifiers,
  - mappings that differ from other clients, even within the same organization.

This is intentional and correct.

There is **no single organization‑level CoA**.

---

### Accounting Platform
- Represents an external provider connection (e.g. Xero, QuickBooks).
- Always scoped to an organization.

---

### Platform ID
- Represents a **stable external provider object identifier**.
- If a column named `platform_id` is used for sync, it **must be idempotency‑safe**.

If a value is not stable across syncs, it must not be called `platform_id`.

---

## 2. Impact of Domain Model on Verification Findings

This clarification materially affects how certain findings should be interpreted.

---

### 2.1 Account Code Uniqueness — RESOLVED AS INTENTIONAL

Earlier verification flagged uniqueness on `(client_id, code)` as potentially incorrect.

Given the clarified domain model:
- Each client has its own chart of accounts
- Account codes are meaningful only within the context of a client

Therefore:
- `(client_id, code)` uniqueness is **correct**
- `(organization_id, code)` uniqueness would be **wrong**

**Action**
- Retain `(client_id, code)` uniqueness
- Explicitly document this in schema comments and architecture docs

This resolves that item as **PASS**, not PARTIAL.

---

### 2.2 Accounts Provider Idempotency — STILL REQUIRED

Even with client‑scoped charts, the following remains true:

If an account row includes:
- organization_id
- platform_name
- platform_id

Then **idempotency requires uniqueness** across those fields.

This is independent of chart‑of‑accounts scope.

**Required constraint**
```sql
CREATE UNIQUE INDEX CONCURRENTLY ux_accounts_org_platform
ON public.accounts (organization_id, platform_name, platform_id);
```

Failure to enforce this will result in duplicate accounts on retry.

This item remains **FAIL until fixed**.

---

## 3. Naming Conventions and Schema Hygiene

Because this platform deliberately deviates from “standard” accounting assumptions, naming must be explicit.

### Required practices

- Column names must reflect domain truth, not convenience
- Any overloaded term must be documented in the schema
- Ambiguous names (e.g. `account`, `ledger`, `entity`) must have comments

Example:
```sql
COMMENT ON TABLE public.accounts IS
'Client‑scoped chart‑of‑accounts entries. Each client maintains an independent CoA.';
```

This is not optional. It prevents future engineers from breaking invariants.

---

## 4. RLS and Tenant Safety (Reaffirmed)

The clarified domain does **not** change RLS requirements.

- organization_id remains the tenant boundary
- FORCE RLS should be applied to all tenant‑scoped tables, including:
  - organizations
  - users

Unless there is a documented and reviewed exception, FORCE is the default.

---

## 5. How the Team Should Respond to the Verification Report

When responding to `DB_SCHEMA_VERIFICATION_REPORT.md`, please:

1. Annotate each FAIL / PARTIAL item with:
   - AGREE / DISAGREE / CLARIFIED
2. Where CLARIFIED:
   - reference this addendum explicitly
3. Where AGREE:
   - provide the Alembic revision ID and SQL
4. Where DISAGREE:
   - state the counter‑control and why it is sufficient

Silence is not acceptance.

---

## 6. Required Final Actions (Updated)

After incorporating this addendum, the remaining mandatory actions are:

1. Add accounts provider idempotency uniqueness
2. FORCE RLS on `organizations` and `users`
3. Explicitly manage pgcrypto extension
4. Add schema comments clarifying client‑scoped CoA

Once these are done, the database can be signed off as compliant with the agreed architecture.

---

## 7. Closing Statement

The clarified model is valid and well‑reasoned.

However, because it is **non‑standard**, it must be:
- enforced structurally,
- documented explicitly,
- and protected from future misinterpretation.

This addendum exists to make sure that happens.
