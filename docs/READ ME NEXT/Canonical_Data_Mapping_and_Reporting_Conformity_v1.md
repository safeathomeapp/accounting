# Canonical Data Mapping & Reporting Conformity – Revised Guidance (v1)

Date: 2026-01-26  
Audience: Engineering, Data, Product, Security  
Context: Multi-platform accounting ingestion (FreeAgent, Xero, QuickBooks, Sage, FreshBooks, ClearBooks) with AR/AP-driven cashflow reporting v1.

---

## 1. Short answer: does mapping between different software/APIs change the earlier recommendations?

**No – it strengthens them.**  
The introduction of multiple upstream accounting platforms does *not* invalidate any of the previous database recommendations. It makes them **mandatory**.

What *does* change is **where responsibility sits**:

- Without mapping: application code must guess intent repeatedly.
- With mapping: the database becomes the contract enforcer, and reporting becomes deterministic.

The correct architecture is:

> **Raw source data → Platform mapping → Canonical facts → Reports**

The mapping layer does not replace the canonical reporting structures. It feeds them.

---

## 2. Re-affirmed architecture (authoritative)

### 2.1 Three-layer data model (must be explicit)

#### Layer 1: Raw ingestion (unchanged)
- Stores upstream payloads faithfully.
- No assumptions about sign, timing, or semantics.
- Purpose: traceability, reprocessing, audits.

Examples:
- `transactions` (raw)
- `source_payload JSONB`
- `source_type`, `source_status`

#### Layer 2: Mapping & normalisation (new emphasis)
- Translates *platform-specific meaning* into *system meaning*.
- Enforced by database tables, not ad-hoc code.

This is where:
- `Invoice` vs `SalesInvoice` vs `ACCREC`
- `Authorised` vs `Approved`
- `Paid` semantics
are unified.

#### Layer 3: Canonical facts (reporting truth)
- Single, stable interpretation for reports and AI.
- No platform logic allowed here.

Examples:
- `cashflow_facts_v1`
- `financial_metric_facts`
- `forecast_inputs`

---

## 3. Mapping layer – what must exist (revised emphasis)

### 3.1 Platform mapping table (non-optional)

**This table becomes the keystone of the system.**

```text
platform_transaction_mapping
```

Required columns:
- `platform_name TEXT NOT NULL`
- `source_type TEXT NOT NULL`
- `source_status TEXT NULL`
- `normalized_type normalized_txn_type NOT NULL`
- `normalized_status normalized_txn_status NOT NULL`
- `canonical_bucket cashflow_bucket NOT NULL`
- `effective_date_source date_source NOT NULL`  -- DUE_DATE | TRANSACTION_DATE
- `priority INT NOT NULL`
- `is_active BOOLEAN NOT NULL DEFAULT TRUE`

Key points:
- This table is data, not configuration.
- Changes here are auditable and reversible.
- No connector is “hardcoded” with meaning.

### 3.2 What mapping does *not* do
Mapping:
- Does **not** decide report inclusion.
- Does **not** compute forecasts.
- Does **not** bypass validation.

It only answers:
> “What does this upstream row *mean* in our system?”

---

## 4. Canonical reporting structures (unchanged, but now justified)

The earlier recommendations remain correct and are now formally required.

### 4.1 Canonical classification outputs (must be stored)

Add or derive:
- `normalized_type`
- `normalized_status`
- `canonical_bucket`
- `effective_date`
- `signed_amount`

These must exist **before** data reaches reports.

### 4.2 Derived facts table (strongly recommended)

```text
cashflow_facts_v1
```

Purpose:
- Freeze interpretation at a point in time.
- Remove platform variability from reporting.
- Make AI and forecasts reproducible.

Mapping feeds this table. Reports read *only* from this table.

---

## 5. Database failsafes (revised with mapping in mind)

### 5.1 “No mapping, no report” rule
If a transaction cannot be mapped:
- `normalized_type = UNKNOWN`
- `canonical_bucket = IGNORE`
- Row is excluded from facts generation.
- Row is written to `ingestion_quarantine`.

This prevents silent contamination of reports.

### 5.2 CHECK constraints now become meaningful
Because mapping has happened, the DB can enforce truth.

Examples:
- Drafts can never be reportable.
- AR/AP rows must have effective dates.
- Signed amounts must align with buckets.

These constraints **cannot** be enforced reliably without mapping.

### 5.3 Platform drift detection
Because mapping is explicit:
- A new upstream `source_status` immediately shows up as unmapped.
- Coverage metrics can alert:
  - “Xero returned a new status we don’t recognise.”

This is critical at scale.

---

## 6. What changes compared to the earlier document?

### 6.1 What does NOT change
- Need for canonical enums
- Need for derived facts tables
- Need for CHECK constraints
- Need for quarantine
- Need for RLS

### 6.2 What IS clarified
- Mapping is a **database concern**, not just an ingestion concern.
- Reports must never read raw tables.
- AI must never read raw tables.
- Facts tables are the contract boundary.

---

## 7. Revised minimal v1 change set (with mapping)

If you want the *smallest* correct system that supports:
- multiple platforms
- consistent cashflow reports
- future AI

You need:

1. Enums:
   - `normalized_txn_type`
   - `normalized_txn_status`
   - `cashflow_bucket`
   - `date_source`

2. Mapping table:
   - `platform_transaction_mapping`

3. Canonical facts table:
   - `cashflow_facts_v1`

4. Quarantine table:
   - `ingestion_quarantine`

5. RLS on:
   - `cashflow_facts_v1`
   - `audit_log`

Nothing less will scale safely.

---

## 8. Design guidance for your team (plain English)

You should tell your design/dev team:

- “We are not building reports on accounting software data.”
- “We are building reports on *our interpretation* of accounting software data.”
- “That interpretation is enforced by the database, not developers’ memory.”
- “If data cannot be interpreted safely, it is excluded by default.”

This mindset is what separates a tool accountants trust from one they constantly sanity-check in Excel.

---

## 9. Forward compatibility (AI agents)

Because:
- facts are canonical
- interpretation is explicit
- provenance is stored

AI agents can later:
- explain *why* a forecast looks the way it does
- simulate changes without mutating raw data
- be audited (“what inputs produced this suggestion?”)

Without this structure, AI output will never be defensible.

---

## 10. Final recommendation (unchanged, now reinforced)

**Proceed exactly as previously advised**, but treat the mapping layer as:
- mandatory
- first-class
- database-enforced

This is not extra complexity; it is the cost of correctness in a multi-platform accounting system.
