BEGIN;

CREATE TABLE IF NOT EXISTS platform_transaction_mapping (
  id BIGSERIAL PRIMARY KEY,
  -- scope: global (NULL) or org-specific override
  organization_id UUID NULL,
  platform_name TEXT NULL,                 -- e.g. 'freeagent', 'xero', 'quickbooks'
  source_type TEXT NOT NULL,               -- e.g. 'Invoice', 'Bill', 'ACCREC'
  source_status TEXT NULL,                 -- e.g. 'approved', 'paid'; nullable to indicate "any status"
  normalized_type normalized_txn_type NOT NULL,
  normalized_status normalized_txn_status NOT NULL,
  canonical_bucket cashflow_bucket NOT NULL,
  effective_date_source date_source NOT NULL,
  priority INT NOT NULL DEFAULT 100,       -- higher wins
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  notes TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Prevent duplicate active mappings at the same specificity.
-- Note: This allows duplicates if you vary org/platform/priority, but discourages accidental collisions.
CREATE UNIQUE INDEX IF NOT EXISTS ux_mapping_unique
ON platform_transaction_mapping (
  COALESCE(organization_id::text, ''),
  COALESCE(platform_name, ''),
  source_type,
  COALESCE(source_status, ''),
  priority
);

CREATE INDEX IF NOT EXISTS ix_mapping_lookup
ON platform_transaction_mapping (
  COALESCE(organization_id, '00000000-0000-0000-0000-000000000000'::uuid),
  COALESCE(platform_name, ''),
  source_type,
  COALESCE(source_status, ''),
  is_active,
  priority
);

-- updated_at trigger
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'set_updated_at_mapping') THEN
    CREATE OR REPLACE FUNCTION set_updated_at_mapping()
    RETURNS trigger AS $fn$
    BEGIN
      NEW.updated_at = now();
      RETURN NEW;
    END;
    $fn$ LANGUAGE plpgsql;
  END IF;
END$$;

DROP TRIGGER IF EXISTS trg_mapping_updated_at ON platform_transaction_mapping;
CREATE TRIGGER trg_mapping_updated_at
BEFORE UPDATE ON platform_transaction_mapping
FOR EACH ROW EXECUTE FUNCTION set_updated_at_mapping();

COMMIT;
