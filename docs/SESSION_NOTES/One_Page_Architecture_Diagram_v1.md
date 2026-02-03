# One-Page Architecture Diagram (v1) — Multi-Platform Ingestion → Reporting → AI
Date: 2026-01-26  
Purpose: A single-page diagram and narrative your team can align on.  
Core rule: **Raw → Mapping → Canonical Facts → Reports/AI** (reports/AI never read raw).

---

## 1) System diagram (conceptual)

```
                ┌──────────────────────────────────────────────────┐
                │                External Platforms                │
                │  FreeAgent | Xero | QuickBooks | Sage | etc.      │
                └───────────────┬──────────────────────────────────┘
                                │  OAuth / API pull (scheduled)
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         Ingestion & Sync Layer                            │
│  - Connector per platform                                                  │
│  - Pull raw objects (invoices, bills, payments, bank feed when available)  │
│  - Write Sync History + Errors                                              │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │  (No semantics assumed here)
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                              RAW STORAGE (DB)                              │
│  Postgres tables:                                                          │
│   - raw_transactions / raw_invoices / raw_bills (or `transactions` raw)     │
│   - source_type, source_status, source_payload (JSONB)                      │
│   - sync_history                                                            │
│  Rule: Raw is traceable, not reportable                                     │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │  interpret via mapping (DB contract)
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                           MAPPING / NORMALISATION                          │
│  Postgres tables:                                                          │
│   - platform_transaction_mapping                                            │
│   - (optional) mapping coverage views                                       │
│  Output fields:                                                            │
│   - normalized_type (INVOICE/BILL/...)                                      │
│   - normalized_status (SUBMITTED/APPROVED/...)                              │
│   - canonical_bucket (AR_OPEN/AP_OPEN/CASH_*/IGNORE)                        │
│   - effective_date_source (DUE_DATE/TRANSACTION_DATE)                       │
│  Rule: if unmapped/invalid → default-deny                                  │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │  deterministic derivation
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                           CANONICAL FACTS (DB)                              │
│  Postgres tables:                                                          │
│   - cashflow_facts_v1  (report truth for v1)                                │
│   - audit_log                                                              │
│   - ingestion_quarantine (unmapped/bad rows)                                │
│  Facts are: tenant-scoped, constrained, indexable                           │
│  Rule: Reports & AI read facts only                                         │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │
               ┌────────────────┴────────────────┐
               │                                 │
               ▼                                 ▼
┌───────────────────────────────┐   ┌───────────────────────────────────────┐
│        REPORTING (SSR)         │   │                 AI LAYER              │
│  FastAPI + Jinja2              │   │  Agents operate on facts/aggregates   │
│  - /portal/reports/cashflow    │   │  - suggestions stored separately       │
│  - server-side charts (PNG/SVG)│   │  - always link back to facts used      │
│  - Cache-Control: no-store     │   │  - never mutate facts                  │
└───────────────┬───────────────┘   └───────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                              CLIENT ACCESS                                 │
│  Web + Mobile:                                                             │
│   - Auth (OIDC+MFA later; JWT in dev)                                       │
│   - Tenant isolation (RLS + app org context)                                │
│  Optional channels: WhatsApp/email triggers → “report ready” link           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2) Data “truth boundaries” (what is allowed to read what)

- Ingestion connectors can write RAW and sync metadata.
- Mapping jobs read RAW and mapping tables, write FACTS or quarantine.
- Reports read FACTS only.
- AI reads FACTS (or aggregates derived from FACTS) only.
- Clients never read RAW and never provide `org_id` as a trust input.

---

## 3) v1 cashflow slice (what ships first)

Input (current mock reality):
- Invoices + Bills with status, due date, amount.

Mapping output (v1 rules):
- drafts excluded
- submitted/approved/overdue included
- paid treated as assumed cash moved (until bank feed exists)

Facts table:
- `cashflow_facts_v1(organization_id, transaction_id, bucket, effective_date, signed_amount, normalized_type, normalized_status, created_at)`

Report:
- `GET /portal/reports/cashflow` SSR page
- weekly buckets, 12-month horizon
- base + conservative scenario

---

## 4) Security controls (where they live)

Database:
- RLS on facts (and audit_log)
- CHECK constraints on facts (bucket/sign/date rules)
- quarantine table for non-conforming records

Application:
- Auth required for all report routes
- Tenant context derived from user session (not URL)
- No-store headers on all private HTML
- Audit log entry on every report view

---

## 5) Platform expansion playbook (repeatable)
For each new platform:
1. Ingest raw data (no semantics)
2. Observe source_type/source_status values
3. Add mapping rows until coverage ≥ 95%
4. Run facts generator (verify minimal quarantine)
5. Enable reports for tenants on that platform

---

## 6) Why this design scales
- Adding a platform mostly changes mapping rows, not report logic.
- Report logic remains stable because it reads canonical facts.
- AI remains defensible because it references canonical facts and provenance.
