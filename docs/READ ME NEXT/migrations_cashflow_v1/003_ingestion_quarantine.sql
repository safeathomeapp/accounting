BEGIN;

CREATE TABLE IF NOT EXISTS ingestion_quarantine (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL,
  client_id UUID NULL,
  source_table TEXT NOT NULL,           -- e.g. 'transactions'
  source_identifier TEXT NULL,          -- upstream id/reference
  reason_code TEXT NOT NULL,            -- e.g. 'UNMAPPED_TYPE', 'MISSING_DUE_DATE'
  reason_detail TEXT NULL,
  raw_payload JSONB NULL,               -- optional; omit if you don't want payload storage
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_quarantine_org_created
ON ingestion_quarantine (organization_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_quarantine_reason
ON ingestion_quarantine (reason_code, created_at DESC);

COMMIT;
