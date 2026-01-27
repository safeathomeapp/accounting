# Platform Onboarding Guide

How to add a new accounting platform to the canonical data mapping layer.

**Applies to**: FreeAgent, ClearBooks, FreshBooks, Sage, and any future platform.

---

## Overview

When adding support for a new platform, you need to:
1. Build the platform adapter (existing pattern in `backend/accounting/<platform>/`)
2. Define how the platform's transaction types and statuses map to canonical buckets
3. Populate the mapping table
4. Generate facts and verify 100% coverage

The canonical layer ensures **all platforms produce identical normalized output** for reporting. Reports never query raw transactions directly - they read from `cashflow_facts_v1`.

---

## Architecture

```
Layer 1 (existing - DO NOT MODIFY):
  Platform APIs -> Platform Mapper -> transactions table (raw data)

Layer 2 (canonical mapping - this guide):
  transactions -> MappingEngine -> platform_transaction_mapping (lookup)
                                -> cashflow_facts_v1 (output)
                                -> ingestion_quarantine (unmappable)

Layer 3 (reporting - reads from Layer 2):
  cashflow_facts_v1 -> ReportGenerator -> P&L, Balance Sheet, Cash Flow
  cashflow_facts_v1 -> Analytics API -> Summary, Trends, By-Category
  cashflow_facts_v1 -> Data Quality API -> Coverage, Quarantine, Mappings
```

**Key files:**

| File | Purpose |
|------|---------|
| `backend/canonical/mapping_definitions.py` | Single source of truth for all mapping rows |
| `backend/canonical/engine.py` | MappingEngine - applies mappings, creates facts/quarantine |
| `backend/canonical/models.py` | ORM models: PlatformTransactionMapping, CashflowFact, IngestionQuarantine |
| `backend/canonical/queries.py` | Shared query helpers for reporting |
| `backend/canonical/listeners.py` | Auto-generates facts on transaction insert/update |
| `scripts/generate_facts.py` | CLI to batch-generate or rebuild facts |
| `scripts/seed_canonical_mappings.py` | CLI to seed/replace mapping data from definitions |
| `scripts/validate_platform_mappings.py` | CI-ready coverage validation (exit 1 = gaps) |

---

## Prerequisites

Before starting canonical mapping for a new platform, ensure:

- [ ] Platform adapter implemented in `backend/accounting/<platform>/`
- [ ] Mapper converting platform API responses to `StandardTransaction` objects
- [ ] Sync handler writing transactions to the `transactions` table
- [ ] At least one test sync completed so transactions exist in the DB

---

## Step-by-Step Checklist

### Step 1: Document Source Types and Statuses

Before creating mappings, catalogue **every** `(transaction_type, status)` combination the platform adapter can produce. Check the mapper file for the values it writes.

**How to find the values:**
- Read the platform mapper: `backend/accounting/<platform>/mapper.py`
- Look for status mapping dicts (e.g., `status_map = {...}`)
- Look for transaction type assignment (e.g., `transaction_type = "invoice"`)
- Check the platform's API docs for all possible statuses

**Existing platform references:**
- Xero mapper: `backend/accounting/xero/mapper.py`
- QuickBooks mapper: `backend/accounting/quickbooks/mapper.py`

**After first sync, verify against actual data:**
```sql
SELECT platform_name, transaction_type, status, COUNT(*)
FROM transactions
WHERE platform_name = '<platform>'
GROUP BY platform_name, transaction_type, status
ORDER BY count DESC;
```

Example documentation for a new platform:

| transaction_type | status | Description |
|---|---|---|
| invoice | draft | Unpublished sales invoice |
| invoice | approved | Approved, awaiting payment |
| invoice | paid | Fully paid invoice |
| invoice | overdue | Past due date |
| bill | draft | Unpublished purchase bill |
| bill | approved | Approved, awaiting payment |
| bill | paid | Fully paid bill |
| bill | overdue | Past due date |

---

### Step 2: Create Mapping Definitions

Add the platform's mappings to `backend/canonical/mapping_definitions.py`.

This is the **single source of truth** - both Alembic migrations and the seed script read from here.

```python
# Add a new section in PLATFORM_MAPPINGS list:

    # =========================================================================
    # FREEAGENT MAPPINGS
    # =========================================================================

    # --- FreeAgent Invoices (Sales) ---
    {
        "platform_name": "freeagent",       # lowercase, must match transactions.platform_name
        "source_type": "invoice",           # must match transactions.transaction_type
        "source_status": "approved",        # must match transactions.status
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "APPROVED",
        "canonical_bucket": "AR_CURRENT",
        "effective_date_source": "DUE_DATE",
    },
```

#### Canonical Bucket Selection Guide

| Bucket | Use when... | signed_amount |
|---|---|---|
| `AR_CURRENT` | Sales invoice outstanding, not overdue | **+positive** |
| `AR_OVERDUE` | Sales invoice past due date | **+positive** |
| `AP_CURRENT` | Purchase bill outstanding, not overdue | **-negative** |
| `AP_OVERDUE` | Purchase bill past due date | **-negative** |
| `CASH_IN` | Payment received (invoice paid, bank receipt) | **+positive** |
| `CASH_OUT` | Payment made (bill paid, bank payment) | **-negative** |
| `NON_CASH` | Journal entries, credit notes, adjustments | **zero** |
| `IGNORE` | Drafts, voided, deleted - exclude from reporting | **zero** |

**The signed_amount is computed automatically by the MappingEngine based on the bucket.** You do not need to specify signs - just pick the right bucket.

#### Normalized Type Mapping

| Type | Use for... |
|---|---|
| `SALES_INVOICE` | Customer invoices (accounts receivable) |
| `PURCHASE_INVOICE` | Supplier bills (accounts payable) |
| `CREDIT_NOTE` | Credit notes and refunds |
| `BANK_PAYMENT` | Outgoing bank payments |
| `BANK_RECEIPT` | Incoming bank receipts |
| `JOURNAL` | Journal entries |
| `TRANSFER` | Inter-account transfers |
| `OTHER` | Anything that doesn't fit above |

#### Effective Date Source

| Value | Use when... |
|---|---|
| `DUE_DATE` | Outstanding AR/AP items - use the due date for cash flow timing |
| `TRANSACTION_DATE` | Payments, journals, completed items - use the transaction date |

**Rule of thumb**: If the transaction is about *future* money movement (outstanding invoice/bill), use `DUE_DATE`. If the money has already moved (paid, received), use `TRANSACTION_DATE`.

---

### Step 3: Insert Mappings into Database

**Option A: Via seed script** (recommended for development)

```bash
# Replace all mappings with current definitions (idempotent)
python scripts/seed_canonical_mappings.py --replace

# Preview without changing anything
python scripts/seed_canonical_mappings.py --dry-run
```

**Option B: Via Alembic migration** (production deployments)

Create a new migration that imports from `mapping_definitions.py`. Follow the pattern in `alembic/versions/v2_073_seed_mapping_data.py`.

**Important**: Update the downgrade function to include the new platform name in the DELETE statement.

**Option C: Via API** (runtime, one-off additions)

```bash
curl -X POST "http://localhost:8000/api/data-quality/mappings" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "platform_name=freeagent&source_type=invoice&source_status=approved&normalized_type=SALES_INVOICE&normalized_status=APPROVED&canonical_bucket=AR_CURRENT&effective_date_source=DUE_DATE"
```

---

### Step 4: Generate Facts

Process all transactions for the new platform into `cashflow_facts_v1`:

```bash
# Process only unmapped transactions (incremental)
python scripts/generate_facts.py

# Rebuild all facts from scratch (use after mapping changes)
python scripts/generate_facts.py --rebuild

# Preview only (no changes)
python scripts/generate_facts.py --dry-run

# Filter to specific org
python scripts/generate_facts.py --org-id <uuid>
```

---

### Step 5: Verify Coverage

**Must achieve 100% coverage before considering the platform complete.**

```bash
# CLI validation (exit code 0 = all mapped, 1 = gaps found)
python scripts/validate_platform_mappings.py

# Filter to specific platform
python scripts/validate_platform_mappings.py --platform freeagent
```

**Also verify via SQL:**

```sql
-- Coverage stats view (per org per platform)
SELECT * FROM mapping_coverage_stats
WHERE platform_name = 'freeagent';

-- Should show: coverage_pct = 100.00, quarantined_count = 0

-- Check quarantine is empty
SELECT COUNT(*) FROM ingestion_quarantine
WHERE platform_name = 'freeagent' AND resolved_at IS NULL;
-- Should return 0
```

**Also check the data quality dashboard:**
- Navigate to `/data-quality` in the frontend
- Verify the new platform shows 100% coverage bar
- Check the quarantine queue is empty for the new platform

---

### Step 6: Test Reporting

Verify reports produce correct output with the new platform's data:

```bash
# P&L report - should include new platform transactions
curl "http://localhost:8000/api/analytics/reports/profit-loss?start_date=2025-01-01&end_date=2025-12-31"

# Transaction summary - check data_source says "canonical_facts_v1"
curl "http://localhost:8000/api/analytics/transactions/summary?start_date=2025-01-01&end_date=2025-12-31"
```

**Verify signed amounts make sense:**

```sql
SELECT canonical_bucket, COUNT(*), SUM(signed_amount) AS total
FROM cashflow_facts_v1 f
JOIN transactions t ON t.id = f.transaction_id
WHERE t.platform_name = 'freeagent'
GROUP BY canonical_bucket;
```

- AR buckets should be positive
- AP buckets should be negative
- CASH_IN should be positive
- CASH_OUT should be negative
- IGNORE/NON_CASH should be zero

---

## Alembic Migration Gotchas

If you need to create new migrations for canonical tables, be aware of this critical issue:

**PostgreSQL enum types in Alembic**: When referencing existing PostgreSQL enum types inside `op.create_table()`, you **must** use `sqlalchemy.dialects.postgresql.ENUM` (imported as `PG_ENUM`) with `create_type=False`. Using `sa.Enum(..., create_type=False)` does **NOT** work - SQLAlchemy ignores that flag inside `create_table()` and will attempt to create the type again, causing a `DuplicateObject` error.

```python
# WRONG - will fail with "type already exists"
sa.Column('bucket', sa.Enum('AR_CURRENT', 'AP_CURRENT', ..., name='cashflow_bucket', create_type=False))

# CORRECT - references existing type without creating it
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
bucket_type = PG_ENUM('AR_CURRENT', 'AP_CURRENT', ..., name='cashflow_bucket', create_type=False)
sa.Column('bucket', bucket_type)
```

See `alembic/versions/v2_070_canonical_enums_and_mapping_table.py` and `v2_071_cashflow_facts_and_quarantine.py` for working examples.

---

## Currently Mapped Platforms

| Platform | Mappings | Status | Notes |
|----------|----------|--------|-------|
| **Xero** | 16 rows | Complete | invoice (8 statuses), bill (6), bank_transaction (1), credit_note (1) |
| **QuickBooks** | 8 rows | Complete | invoice (4 statuses), bill (4) |
| **Mock** | 10 rows | Complete | Development/test data: invoice (5 statuses), bill (5) |
| **FreeAgent** | - | Pending | Awaiting API sandbox access |
| **ClearBooks** | - | Pending | Awaiting API documentation |
| **FreshBooks** | - | Pending | Awaiting API documentation |
| **Sage** | - | Planned | Future platform |

---

## Platform Onboarding Checklist Template

Copy this for each new platform:

```
### <Platform Name> Canonical Mapping Checklist

- [ ] Platform adapter implemented (`backend/accounting/<platform>/`)
- [ ] Mapper writing transactions to DB
- [ ] All (transaction_type, status) combinations documented
- [ ] Mapping definitions added to `backend/canonical/mapping_definitions.py`
- [ ] Mappings seeded to database (`python scripts/seed_canonical_mappings.py --replace`)
- [ ] Facts generated (`python scripts/generate_facts.py --rebuild`)
- [ ] Coverage validated at 100% (`python scripts/validate_platform_mappings.py --platform <name>`)
- [ ] Quarantine queue empty for this platform
- [ ] Signed amounts verified (AR/CASH_IN positive, AP/CASH_OUT negative)
- [ ] Reports tested with new platform data
- [ ] Data quality dashboard shows 100% coverage
- [ ] Alembic seed migration updated (v2_073 downgrade includes platform name)
```

---

## Troubleshooting

### Transactions stuck in quarantine
- Check `GET /api/data-quality/orgs/{org_id}/quarantine` for the reason
- Usually means a missing mapping for a specific type/status combo
- Add the missing mapping to `mapping_definitions.py`
- Re-seed: `python scripts/seed_canonical_mappings.py --replace`
- Resolve quarantine: `POST /api/data-quality/orgs/{org_id}/quarantine/resolve-all`
- Or rebuild: `python scripts/generate_facts.py --rebuild`

### Coverage below 100%
- Run `GET /api/data-quality/orgs/{org_id}/unmapped-types` to see gaps
- Or use SQL: `SELECT platform_name, transaction_type, status, COUNT(*) FROM transactions WHERE id NOT IN (SELECT transaction_id FROM cashflow_facts_v1) GROUP BY 1,2,3;`
- Each gap needs a mapping row in `mapping_definitions.py`
- After adding, re-seed and rebuild facts

### Facts not matching expected totals
- Rebuild facts: `python scripts/generate_facts.py --rebuild`
- Check signed_amount logic against the bucket table above
- Verify the correct `effective_date_source` is set (DUE_DATE vs TRANSACTION_DATE)
- If a mapper writes unexpected values for `transaction_type` or `status`, the transactions will land in quarantine instead of facts

### Circular import errors
- Canonical models import `Base` from `backend.models`
- Do **NOT** re-export canonical models from `backend/models/__init__.py`
- Import canonical models directly: `from backend.canonical.models import CashflowFact`

### New status/type appears after platform API update
- Platform APIs occasionally add new transaction types or statuses
- These will land in quarantine automatically
- Check quarantine regularly, add new mapping rows as needed
- The data quality dashboard surfaces these gaps

---

## Database Tables Reference

### `platform_transaction_mapping`
Lookup table linking platform-specific (type, status) to canonical classification.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | Auto-increment |
| platform_name | VARCHAR(50) | Lowercase: "xero", "quickbooks", "freeagent" |
| source_type | VARCHAR(100) | Matches `transactions.transaction_type` |
| source_status | VARCHAR(100) | Matches `transactions.status` |
| normalized_type | normalized_txn_type ENUM | See type mapping table |
| normalized_status | normalized_txn_status ENUM | See status mapping table |
| canonical_bucket | cashflow_bucket ENUM | See bucket selection guide |
| effective_date_source | date_source ENUM | DUE_DATE or TRANSACTION_DATE |
| priority | INTEGER | Default 0, higher = preferred |
| is_active | BOOLEAN | Soft delete support |
| created_at | TIMESTAMPTZ | Auto-set |
| updated_at | TIMESTAMPTZ | Auto-updated |

**Unique constraint**: `(platform_name, source_type, source_status)` WHERE `is_active = TRUE`

### `cashflow_facts_v1`
One row per transaction - the canonical truth for all reporting.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | Auto-generated |
| transaction_id | UUID FK UNIQUE | Links to transactions.id |
| mapping_id | INTEGER FK | Links to platform_transaction_mapping.id |
| organization_id | UUID FK | Org scoping |
| client_id | UUID FK nullable | Client association |
| normalized_type | ENUM | From mapping |
| normalized_status | ENUM | From mapping |
| canonical_bucket | ENUM | From mapping |
| effective_date | DATE | Computed from date_source |
| signed_amount | NUMERIC(15,2) | +positive or -negative per bucket rules |
| currency | VARCHAR(3) | Default GBP |
| snapshot_date | DATE | Default CURRENT_DATE |
| created_at | TIMESTAMPTZ | Auto-set |

### `ingestion_quarantine`
Holds transactions that couldn't be mapped. Needs a new mapping row before resolution.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | Auto-generated |
| transaction_id | UUID FK | Links to transactions.id |
| organization_id | UUID FK | Org scoping |
| platform_name | VARCHAR(50) | For quick filtering |
| source_type | VARCHAR(100) | The unmapped type |
| source_status | VARCHAR(100) | The unmapped status |
| reason | TEXT | Human-readable explanation |
| quarantined_at | TIMESTAMPTZ | When it was quarantined |
| resolved_at | TIMESTAMPTZ nullable | When it was resolved |
| resolved_by | VARCHAR(255) nullable | Who/what resolved it |

**Unique constraint**: `(transaction_id)` WHERE `resolved_at IS NULL` - one unresolved entry per transaction.
