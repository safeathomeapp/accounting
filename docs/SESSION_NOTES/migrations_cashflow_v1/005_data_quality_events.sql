BEGIN;

CREATE TABLE IF NOT EXISTS data_quality_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL,
  event_type TEXT NOT NULL,                 -- e.g. 'MAPPING_COVERAGE', 'QUARANTINE_SPIKE'
  severity TEXT NOT NULL DEFAULT 'WARN',    -- INFO/WARN/ERROR
  details JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_dq_org_created
ON data_quality_events (organization_id, created_at DESC);

COMMIT;
