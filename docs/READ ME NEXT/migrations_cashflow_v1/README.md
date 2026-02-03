# Cashflow v1 Migration Pack (Postgres)
Generated: 2026-01-29

This pack introduces a database contract for multi-platform ingestion → mapping → canonical facts, focused on **Cashflow Forecast v1 (AR/AP-driven)**.

It is designed to be **additive** and to work even if you keep your existing raw `transactions` table. Where the existing schema differs (PK types, column names), adjust the referenced columns accordingly.

## What this adds
1. Enums:
   - `normalized_txn_type`
   - `normalized_txn_status`
   - `cashflow_bucket`
   - `date_source`

2. Tables:
   - `platform_transaction_mapping`
   - `ingestion_quarantine`
   - `cashflow_facts_v1`
   - `data_quality_events` (optional but recommended)

3. Views:
   - `v_mapping_coverage` (optional)

4. RLS policies (optional but recommended):
   - for `cashflow_facts_v1` and `audit_log` (if present)

## Assumptions (edit if needed)
- Tenant key column is `organization_id` of type UUID on the relevant tables.
- Raw source table is named `transactions` and has:
  - `id` (UUID)
  - `organization_id` (UUID)
  - `client_id` (UUID, optional)
  - `transaction_type` (TEXT)  -- raw/source type
  - `status` (TEXT)            -- raw/source status
  - `transaction_date` (DATE or TIMESTAMP)
  - `due_date` (DATE or TIMESTAMP, nullable)
  - `total_amount` (NUMERIC)   -- magnitude or signed; we normalise later

If your schema differs, keep the migration pack but adjust:
- referenced table/column names in `004_cashflow_facts_v1.sql`
- join keys in `007_views.sql`
- seed mapping in `006_seed_mock_mapping.sql`

## How to apply
Run in order:
- 001_create_enums.sql
- 002_platform_transaction_mapping.sql
- 003_ingestion_quarantine.sql
- 004_cashflow_facts_v1.sql
- 005_data_quality_events.sql (optional)
- 006_seed_mock_mapping.sql (optional, for your current mock)
- 007_views.sql (optional)
- 008_rls_policies.sql (optional; requires app to set `app.org_id`)

## App requirement for RLS
If you enable RLS, the application must set tenant context per session:
- `SET app.org_id = '<uuid>'`
