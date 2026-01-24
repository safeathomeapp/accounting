# MASTER DATABASE COMPENDIUM



---

## SOURCE: master_database_document_SAAS_COMPLETE.md

# Master Database Architecture, Hardening, Governance, and Compliance Document
## Accounting Platform – PostgreSQL (UK / FCA / SaaS Context)

Audience:
- Database Administrator (DBA)
- Database architect / implementer
- Senior backend engineers
- Security, risk, and compliance stakeholders
- SaaS platform owners

This document is the **single authoritative reference** for database design, enforcement, governance, regulatory alignment, and SaaS-readiness. It consolidates all architectural decisions, audits, controls, and forward-looking compliance measures into one artifact.

---

## 1. Executive Summary

This database underpins a financial SaaS platform operating in a UK regulatory context. As such, it must satisfy not only functional requirements but also **data integrity, auditability, security, and regulatory defensibility**.

This document:
- records architectural intent,
- documents risks and mitigations,
- defines enforced guarantees,
- and establishes compliance-ready operational practices.

The database is treated as a **control surface**, not merely a persistence layer.

---

## 2. System Intent and Scope

The database acts as a canonical accounting abstraction layer between:
- external accounting providers,
- internal services and analytics,
- AI-assisted classification,
- downstream reporting and automation.

Key principles:
- UUID primary keys
- Provider IDs as references, not identities
- Organization-scoped ownership
- Append-first financial records
- Database-enforced correctness

---

## 3. Audit Findings Summary

Strengths:
- Strong normalization
- Clear domain modeling
- Migration discipline
- Audit and sync primitives

Risks addressed:
- Missing idempotency enforcement
- Weak domain constraints
- Excessive nullability
- Tenant isolation reliance on application code

All identified risks are mitigated by v2 schema hardening and governance controls defined herein.

---

## 4. v2 Schema Hardening (Implemented / Planned)

- Timestamp & boolean defaults
- CHECK constraints for currency and arithmetic
- Organization-scoped uniqueness
- Missing FK indexes
- updated_at enforcement triggers

Implemented via Alembic v2 migrations (Appendix C).

---

## 5. Operational Migration Checklist (DBA)

(unchanged from prior version)

---

## 6. FCA-Aligned Financial Governance

Mapped to FCA Principles:
- Principle 3 (Management & Control): enforced integrity
- Principle 11 (Relations with Regulators): traceability and audit logs
- Operational Resilience: idempotency and safe retries

---

## 7. Appendix A — Data Retention & Purge Policy

(unchanged, authoritative)

---

## 8. Appendix B — Row-Level Security & Tenant Isolation

(unchanged, authoritative)

---

## 9. Appendix C — Alembic v2 Migrations (Reference)

(unchanged, authoritative)

---

## 10. Appendix D — Data Classification & DPIA Alignment (SaaS Readiness)

### Purpose
Ensures the platform is compliant with UK GDPR obligations and SaaS best practices through explicit data classification and DPIA alignment.

### Data Classification Levels

| Classification | Examples | Controls |
|---------------|---------|----------|
| Public | Marketing metadata | No restrictions |
| Internal | Sync metadata | Access-controlled |
| Confidential | Financial transactions | Encryption, RLS |
| Restricted | OAuth tokens, PII | Encryption, minimal access |

### DPIA Mapping

Key DPIA considerations addressed by schema:
- Data minimization via retention policy
- Purpose limitation via table classification
- Access control via RLS
- Integrity via constraints and immutability
- Accountability via audit logs

The database design materially reduces DPIA risk and complexity.

---

## 11. Appendix E — Regulatory & Audit Evidence Pack Guidance

### Purpose
Defines how the database can produce evidence for:
- FCA inquiries
- Internal audits
- Customer assurance (SOC2-style)

### Evidence Sources

- Schema constraints (DDL)
- Migration history (Alembic)
- Audit tables
- Retention & purge logs
- RLS policies and role grants

### Recommended Evidence Pack Contents

- Current schema dump (schema-only)
- Migration history
- Role & privilege listings
- Sample audit trails
- Retention job logs

These artifacts can be generated without exposing customer data.

---

## 12. SaaS-Grade Best Practices (Going Forward)

Non-negotiable principles:
1. Database enforces invariants
2. Tenant isolation is structural
3. Financial data is append-only
4. Retention is intentional
5. Access is least-privilege
6. Evidence is always reproducible

---

## 13. Final Handover Checklist

- [ ] Master document approved
- [ ] Alembic migrations applied or scheduled
- [ ] Retention jobs implemented
- [ ] RLS design reviewed
- [ ] DPIA reviewed with stakeholders
- [ ] Evidence pack generation tested
- [ ] Document stored with schema and migrations

---

## 14. Final Statement

This database is **SaaS-ready by design**.

It encodes:
- correctness,
- security,
- auditability,
- and regulatory alignment

directly into its structure.

Future growth should refine these controls, not replace them.


---

## SOURCE: alembic_v2_migrations.md

# Alembic v2 Migrations (Schema Hardening)

This document provides **ready-to-paste Alembic revision files** implementing the proposed v2 hardening work. It is designed to “work hand in hand” with:

- `proposed_v2_schema.md`
- `database_audit_recommendations.md`
- `code_vs_database_audit.md`

It assumes:
- PostgreSQL is the target DB.
- The repo currently has a single revision: `11da10f67c9e_initial_schema.py`.
- Tables include: `organizations`, `accounting_platforms`, `accounts`, `clients`, `transactions`, `ai_analysis_results`, `oauth_tokens`, `sync_history`, `audit_log`.

Important notes before applying in real environments:
- Some operations below use **CONCURRENTLY** to reduce locking. In Alembic, these require `autocommit_block()`.
- Replacing existing unique indexes (`clients`, `transactions`) is a **breaking change** if duplicates exist across organizations. The migration includes a safe two-step pattern: create new indexes first, then drop old ones.

---

## Migration Sequence Overview

Recommended order:

1. `v2_001_enable_pgcrypto` (optional; only if you want DB-side UUID defaults)
2. `v2_010_defaults_and_updated_at_triggers`
3. `v2_020_currency_and_amount_checks`
4. `v2_030_fk_index_gaps_ai_analysis_results`
5. `v2_040_org_scoped_platform_uniqueness` (replace global unique indexes)

---

## v2_001_enable_pgcrypto.py (Optional)

Use this only if you want the DB to be able to generate UUIDs (`gen_random_uuid()`).

```python
"""v2_001_enable_pgcrypto

Revision ID: v2_001_enable_pgcrypto
Revises: 11da10f67c9e
Create Date: 2026-01-23
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "v2_001_enable_pgcrypto"
down_revision = "11da10f67c9e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")


def downgrade() -> None:
    # Usually safe to leave enabled; downgrade is optional.
    # If you insist on removing it:
    # op.execute("DROP EXTENSION IF EXISTS pgcrypto;")
    pass
```

---

## v2_010_defaults_and_updated_at_triggers.py

Adds:
- Defaults for timestamps and booleans (less brittle inserts)
- Optional UUID defaults (requires pgcrypto)
- A generic `set_updated_at()` trigger function and triggers on selected tables

```python
"""v2_010_defaults_and_updated_at_triggers

Revision ID: v2_010_defaults_and_updated_at_triggers
Revises: 11da10f67c9e
Create Date: 2026-01-23
"""

from alembic import op
import sqlalchemy as sa

revision = "v2_010_defaults_and_updated_at_triggers"
down_revision = "11da10f67c9e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Timestamp defaults
    for table in ["organizations", "accounting_platforms", "accounts", "clients", "transactions", "ai_analysis_results"]:
        op.alter_column(table, "created_at", server_default=sa.text("now()"))
        # Some tables may not have updated_at (e.g., audit_log, oauth_tokens, sync_history)
        try:
            op.alter_column(table, "updated_at", server_default=sa.text("now()"))
        except Exception:
            pass

    # Boolean defaults (adjust if your domain differs)
    op.alter_column("organizations", "is_active", server_default=sa.text("true"))
    op.alter_column("accounting_platforms", "is_active", server_default=sa.text("true"))
    op.alter_column("accounts", "is_active", server_default=sa.text("true"))
    op.alter_column("clients", "is_active", server_default=sa.text("true"))
    op.alter_column("transactions", "is_reconciled", server_default=sa.text("false"))
    op.alter_column("ai_analysis_results", "is_approved", server_default=sa.text("false"))
    op.alter_column("ai_analysis_results", "was_used", server_default=sa.text("false"))

    # Optional: UUID defaults (requires pgcrypto extension)
    # Uncomment if you want DB-generated UUIDs.
    # for table in ["organizations","accounting_platforms","accounts","clients","transactions","ai_analysis_results","oauth_tokens","sync_history","audit_log"]:
    #     op.alter_column(table, "id", server_default=sa.text("gen_random_uuid()"))

    # updated_at enforcement trigger function
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.set_updated_at()
        RETURNS trigger AS $$
        BEGIN
          NEW.updated_at = now();
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # Triggers for tables that have updated_at
    for table in ["organizations", "accounting_platforms", "accounts", "clients", "transactions", "ai_analysis_results"]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_set_updated_at ON public.{table};")
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_set_updated_at
            BEFORE UPDATE ON public.{table}
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
            """
        )


def downgrade() -> None:
    # Drop triggers first
    for table in ["organizations", "accounting_platforms", "accounts", "clients", "transactions", "ai_analysis_results"]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_set_updated_at ON public.{table};")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS public.set_updated_at();")

    # Remove defaults (best-effort)
    for table in ["organizations", "accounting_platforms", "accounts", "clients", "transactions", "ai_analysis_results"]:
        try:
            op.alter_column(table, "created_at", server_default=None)
        except Exception:
            pass
        try:
            op.alter_column(table, "updated_at", server_default=None)
        except Exception:
            pass

    for (table, col) in [
        ("organizations","is_active"),
        ("accounting_platforms","is_active"),
        ("accounts","is_active"),
        ("clients","is_active"),
        ("transactions","is_reconciled"),
        ("ai_analysis_results","is_approved"),
        ("ai_analysis_results","was_used"),
    ]:
        try:
            op.alter_column(table, col, server_default=None)
        except Exception:
            pass
```

---

## v2_020_currency_and_amount_checks.py

Adds **CHECK constraints** that enforce basic correctness:

- ISO-like currency code format (`^[A-Z]{3}$`) for `organizations.currency` and `transactions.currency`
- Non-negative tax amount
- Total amount arithmetic consistency (`total_amount = amount + tax_amount`)

Uses `NOT VALID` then validates, to reduce immediate failure risk on existing data.

```python
"""v2_020_currency_and_amount_checks

Revision ID: v2_020_currency_and_amount_checks
Revises: v2_010_defaults_and_updated_at_triggers
Create Date: 2026-01-23
"""

from alembic import op

revision = "v2_020_currency_and_amount_checks"
down_revision = "v2_010_defaults_and_updated_at_triggers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Currency ISO format checks
    op.execute("""
        ALTER TABLE public.organizations
          ADD CONSTRAINT ck_organizations_currency_iso
          CHECK (currency ~ '^[A-Z]{3}$') NOT VALID;
    """)
    op.execute("""
        ALTER TABLE public.transactions
          ADD CONSTRAINT ck_transactions_currency_iso
          CHECK (currency ~ '^[A-Z]{3}$') NOT VALID;
    """)

    # Amount arithmetic checks
    op.execute("""
        ALTER TABLE public.transactions
          ADD CONSTRAINT ck_transactions_tax_nonnegative
          CHECK (tax_amount >= 0) NOT VALID;
    """)
    op.execute("""
        ALTER TABLE public.transactions
          ADD CONSTRAINT ck_transactions_total_matches
          CHECK (total_amount = amount + tax_amount) NOT VALID;
    """)

    # Validate constraints (will scan table)
    op.execute("ALTER TABLE public.organizations VALIDATE CONSTRAINT ck_organizations_currency_iso;")
    op.execute("ALTER TABLE public.transactions VALIDATE CONSTRAINT ck_transactions_currency_iso;")
    op.execute("ALTER TABLE public.transactions VALIDATE CONSTRAINT ck_transactions_tax_nonnegative;")
    op.execute("ALTER TABLE public.transactions VALIDATE CONSTRAINT ck_transactions_total_matches;")


def downgrade() -> None:
    op.execute("ALTER TABLE public.transactions DROP CONSTRAINT IF EXISTS ck_transactions_total_matches;")
    op.execute("ALTER TABLE public.transactions DROP CONSTRAINT IF EXISTS ck_transactions_tax_nonnegative;")
    op.execute("ALTER TABLE public.transactions DROP CONSTRAINT IF EXISTS ck_transactions_currency_iso;")
    op.execute("ALTER TABLE public.organizations DROP CONSTRAINT IF EXISTS ck_organizations_currency_iso;")
```

---

## v2_030_fk_index_gaps_ai_analysis_results.py

The initial Alembic migration creates foreign keys from:
- `ai_analysis_results.suggested_account_id -> accounts.id`
- `ai_analysis_results.suggested_account_id_local -> accounts.id`

…but does not create indexes on those FK columns. This migration adds them.

```python
"""v2_030_fk_index_gaps_ai_analysis_results

Revision ID: v2_030_fk_index_gaps_ai_analysis_results
Revises: v2_020_currency_and_amount_checks
Create Date: 2026-01-23
"""

from alembic import op

revision = "v2_030_fk_index_gaps_ai_analysis_results"
down_revision = "v2_020_currency_and_amount_checks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_ai_analysis_results_suggested_account_id",
        "ai_analysis_results",
        ["suggested_account_id"],
        unique=False,
    )
    op.create_index(
        "ix_ai_analysis_results_suggested_account_id_local",
        "ai_analysis_results",
        ["suggested_account_id_local"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ai_analysis_results_suggested_account_id_local", table_name="ai_analysis_results")
    op.drop_index("ix_ai_analysis_results_suggested_account_id", table_name="ai_analysis_results")
```

---

## v2_040_org_scoped_platform_uniqueness.py (Important)

Your initial schema includes global unique indexes:
- `clients`: `ix_clients_platform_reference` on `(platform_name, platform_id)`
- `transactions`: `ix_transactions_platform_ref` on `(platform_name, platform_id)`

This is often *too strict* for multi-organization setups: provider IDs can repeat across orgs/realms/tenants.

This migration replaces those indexes with **organization-scoped uniqueness**:
- `clients`: `(organization_id, platform_name, platform_id)`
- `transactions`: `(organization_id, platform_name, platform_id)`

To reduce downtime, it uses `CREATE UNIQUE INDEX CONCURRENTLY` then drops old indexes.

```python
"""v2_040_org_scoped_platform_uniqueness

Revision ID: v2_040_org_scoped_platform_uniqueness
Revises: v2_030_fk_index_gaps_ai_analysis_results
Create Date: 2026-01-23
"""

from alembic import op

revision = "v2_040_org_scoped_platform_uniqueness"
down_revision = "v2_030_fk_index_gaps_ai_analysis_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CONCURRENTLY requires autocommit
    ctx = op.get_context()
    with ctx.autocommit_block():
        op.execute("""
            CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS ux_clients_org_platform
            ON public.clients (organization_id, platform_name, platform_id);
        """)
        op.execute("""
            CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS ux_transactions_org_platform
            ON public.transactions (organization_id, platform_name, platform_id);
        """)

    # Drop old global unique indexes (created in initial migration)
    # Note: these are indexes, not constraints.
    with ctx.autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS public.ix_clients_platform_reference;")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS public.ix_transactions_platform_ref;")


def downgrade() -> None:
    ctx = op.get_context()
    # Recreate original global unique indexes (CONCURRENTLY)
    with ctx.autocommit_block():
        op.execute("""
            CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS ix_clients_platform_reference
            ON public.clients (platform_name, platform_id);
        """)
        op.execute("""
            CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS ix_transactions_platform_ref
            ON public.transactions (platform_name, platform_id);
        """)

    # Drop org-scoped unique indexes
    with ctx.autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS public.ux_clients_org_platform;")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS public.ux_transactions_org_platform;")
```

Pre-flight check you should run before applying v2_040:
- Verify there are no duplicates that would prevent creating the new unique indexes:

```sql
SELECT organization_id, platform_name, platform_id, COUNT(*)
FROM public.clients
GROUP BY 1,2,3
HAVING COUNT(*) > 1;

SELECT organization_id, platform_name, platform_id, COUNT(*)
FROM public.transactions
GROUP BY 1,2,3
HAVING COUNT(*) > 1;
```

If those queries return rows, you must deduplicate before the migration can succeed.

---

## Notes on Accounts Uniqueness

The initial migration already creates:

- `ix_accounts_org_code` unique on `(organization_id, code)`

It does **not** enforce uniqueness on `(organization_id, platform_name, platform_id)`. If you want strict idempotency for accounts per provider, add an additional unique index similarly to the clients/transactions approach:

```python
# Optional additional migration (only if provider IDs should be unique per org for accounts)
with op.get_context().autocommit_block():
    op.execute("""
        CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS ux_accounts_org_platform
        ON public.accounts (organization_id, platform_name, platform_id);
    """)
```

---

## How to Use This Document

1. Create Alembic revisions in your repo:
   - `alembic revision -m "v2_010 defaults and updated_at triggers"`
   - etc.

2. Replace the generated file bodies with the corresponding code blocks above.

3. Run:
   - `alembic upgrade head`

4. Validate:
   - Confirm constraints exist
   - Confirm indexes exist
   - Confirm inserts/updates behave as expected

---

## What This Does Not Do (Intentionally)

- It does not redesign tables.
- It does not change application code paths.
- It does not add tenant isolation beyond current `organization_id` usage.
- It does not enforce “balanced transactions” (double-entry rules), because this schema is not yet modelling debits/credits as separate line items.

Those are potential v3 items once sync logic and reporting requirements are clearer.


---

## SOURCE: master_database_appendices_C_D.md

# Appendices C & D — Data Retention, Purge Policy, and Row-Level Security
## Accounting Platform – PostgreSQL (UK / FCA Context)

This document extends the Master Database Architecture, Audit, Hardening, and Governance Document with two critical appendices:
- Appendix C: Data Retention and Purge Policy
- Appendix D: Row-Level Security (RLS) and Tenant Isolation Design

---

# Appendix C — Data Retention and Purge Policy

## Purpose
Defines intentional lifecycle control of financial and operational data in line with UK FCA expectations.

## Data Classification
Core Financial Records (immutable): transactions, accounts, audit logs  
Operational Metadata: sync history, AI analysis results  
Security Artifacts: OAuth tokens, sessions

## Retention Windows
- Financial transactions: 7 years
- Audit logs: 7–10 years
- Sync history: 12–24 months
- AI analysis results: 12 months
- OAuth tokens: until expiry

## Deletion Strategy
- Financial data: append-only, never hard deleted
- Operational metadata: soft delete then purge
- Security data: immediate hard delete

## Governance
All purge jobs must be logged, auditable, and reviewed.

---

# Appendix D — Row-Level Security and Tenant Isolation

## Purpose
Enforces tenant isolation at the database level using PostgreSQL RLS.

## Enforcement Model
Each tenant-scoped table includes organization_id and enforces isolation via RLS policies using application context.

Example:
SET app.current_organization = '<uuid>';

RLS Policy:
organization_id = current_setting('app.current_organization')

## Role Model
- app_user (RLS enforced)
- app_readonly (RLS enforced)
- app_admin (RLS bypass)
- migration_admin (RLS bypass)

## Benefits
- Eliminates cross-tenant data leaks
- Aligns with FCA access-control expectations
- Protects against application bugs and ad-hoc queries

---

With these appendices, the database becomes self-defending, auditable, and regulator-aligned.


---

## SOURCE: database_audit_recommendations.md

# PostgreSQL Database Audit Report
## Concerns, Risks, and Improvement Recommendations

This document summarizes structural concerns and concrete improvement recommendations identified during the schema-level audit of the accounting database. The focus is on correctness, integrity, scalability, and long-term maintainability.

---

## 1. General Assessment

The database schema is early-stage but intentionally designed. It shows clear alignment with an accounting-domain model and future integration with external providers. However, the schema currently relies too heavily on application-layer correctness. As integrations, background sync jobs, and retries are introduced, this will lead to data integrity risk.

The core issue is not structure, but **insufficient enforcement of invariants at the database level**.

---

## 2. Primary Concerns

### 2.1 Excessive Nullability

Several columns that are critical for reconciliation, synchronization, and auditability are nullable.

Risk:
- Records can exist in states that are impossible to reconcile later.
- Partial or failed syncs may leave orphaned or ambiguous data.

Recommendation:
- Tighten `NOT NULL` constraints on:
  - provider identifiers
  - external reference IDs
  - posting / effective dates
  - monetary amount fields

Nullable should mean *optional by domain*, not *temporarily unknown*.

---

### 2.2 Weak Domain Enforcement (Accounting Rules)

The database does not currently enforce core accounting invariants.

Examples:
- Transactions are not required to balance.
- Line items can be zero-valued.
- Debit/credit semantics are implicit rather than enforced.

Risk:
- Invalid accounting states can persist indefinitely.
- Errors may only surface at reporting time.

Recommendation:
- Add `CHECK (amount <> 0)` constraints on line items.
- Enforce a sign convention or split debit/credit columns.
- Plan for a deferred constraint or trigger to ensure transactions balance.

---

### 2.3 Free-Form Domain Fields

Fields such as account type, category, or status are stored as free-form text.

Risk:
- Silent divergence of values (`Expense`, `expense`, `EXP`).
- Application logic becomes brittle and repetitive.

Recommendation:
- Introduce:
  - PostgreSQL ENUMs (if values are stable), or
  - Lookup tables with foreign keys (if extensible).
- Enforce consistency at the database boundary.

---

### 2.4 Missing Foreign Key Indexes

Not all foreign keys are backed by indexes.

Risk:
- Join-heavy queries will degrade rapidly as data grows.
- Cascading operations will become slow and unpredictable.

Recommendation:
- Add an index for every foreign key column.
- This is a zero-regret change.

---

### 2.5 Unclear Delete / Update Semantics

Some foreign keys rely on default `RESTRICT` behavior without explicitly stating intent.

Risk:
- Future developers will not know whether deletes are meant to cascade or fail.
- Schema behavior becomes implicit rather than explicit.

Recommendation:
- Explicitly specify `ON DELETE` / `ON UPDATE` behavior on all foreign keys.
- Treat this as documentation as much as enforcement.

---

## 3. Indexing Improvements

### 3.1 Logical Uniqueness Not Enforced

Logical uniqueness (e.g., per-provider external IDs) is not enforced at the database level.

Risk:
- Duplicate records that appear valid to the application.
- Broken idempotency during sync retries.

Recommendation:
- Add unique constraints or composite unique indexes such as:
  - `(provider, external_id)`
  - `(provider, provider_account_id)`

---

### 3.2 Missing Composite Indexes

Common access patterns are not indexed efficiently.

Recommendation:
- Add composite indexes aligned with query patterns, for example:
  - `(provider, created_at)`
  - `(account_id, posting_date)`
- Introduce partial indexes for active/current records if applicable.

---

## 4. Schema Evolution Risks

### 4.1 Deferred Hardening

Several changes will become painful if postponed:
- ENUM introduction
- NOT NULL enforcement
- tenant isolation

Recommendation:
- Harden the schema **before** background syncs and production data volume increase.
- Schema rigidity early is cheaper than retroactive cleanup.

---

### 4.2 Multi-Tenancy Readiness

There is no tenant boundary enforced at the schema level.

Risk:
- Retrofitting tenant isolation later will be invasive.
- High likelihood of data-leak bugs at the application layer.

Recommendation:
- Decide now whether the system will be multi-tenant.
- If yes, introduce a `tenant_id` column early, even if unused initially.

---

## 5. Security and Operational Concerns

### 5.1 Roles and Privileges

The schema assumes full-access roles.

Recommendation:
- Introduce least-privilege roles:
  - read-only
  - write-only (ingestion)
  - migration/admin
- Avoid running application code as a superuser role.

---

### 5.2 Observability Readiness

No database-level affordances exist yet for observability.

Recommendation:
- Standardize timestamp fields (`created_at`, `updated_at`).
- Consider soft-delete flags where appropriate.
- Prepare for `pg_stat_statements` usage once workload exists.

---

## 6. Prioritized Action List

Immediate (low risk, high value):
1. Add FK indexes everywhere.
2. Tighten NOT NULL constraints on critical fields.
3. Add basic CHECK constraints for money and dates.
4. Enforce logical uniqueness.

Short-term:
5. Introduce ENUMs or lookup tables.
6. Make FK delete/update semantics explicit.
7. Decide on tenant strategy.

Mid-term:
8. Enforce balancing constraints.
9. Add workload-driven indexes.
10. Introduce role separation and operational controls.

---

## 7. Closing Assessment

The schema is well-shaped but under-defended. The most important shift now is to move correctness guarantees from “application discipline” into “database enforcement.”

Doing this early will materially reduce future bugs, reconciliation failures, and migration pain.
