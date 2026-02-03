BEGIN;

-- Canonical facts table for cashflow reporting.
-- This is the only table reports should read (for cashflow v1).
CREATE TABLE IF NOT EXISTS cashflow_facts_v1 (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL,
  transaction_id UUID NOT NULL,                 -- references raw transaction row id (FK optional)
  client_id UUID NULL,
  platform_name TEXT NULL,

  normalized_type normalized_txn_type NOT NULL,
  normalized_status normalized_txn_status NOT NULL,
  bucket cashflow_bucket NOT NULL,

  effective_date DATE NOT NULL,
  signed_amount NUMERIC(14,2) NOT NULL,

  mapping_id BIGINT NULL,                        -- optional provenance
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Optional FK if your `transactions` table exists and uses UUID PK.
-- Comment out if it doesn't match your schema.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='transactions') THEN
    BEGIN
      ALTER TABLE cashflow_facts_v1
        ADD CONSTRAINT fk_cashflow_facts_txn
        FOREIGN KEY (transaction_id) REFERENCES transactions(id)
        ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN
      -- ignore
    END;
  END IF;
END$$;

-- One fact row per transaction for v1 (adjust if you later split payments etc.)
CREATE UNIQUE INDEX IF NOT EXISTS ux_cashflow_facts_txn
ON cashflow_facts_v1 (transaction_id);

-- Query performance
CREATE INDEX IF NOT EXISTS ix_cashflow_facts_org_date
ON cashflow_facts_v1 (organization_id, effective_date);

CREATE INDEX IF NOT EXISTS ix_cashflow_facts_bucket
ON cashflow_facts_v1 (organization_id, bucket, effective_date);

-- Conformity constraints (facts-only; do NOT put these on raw data initially)

-- Drafts must never be reportable.
ALTER TABLE cashflow_facts_v1
  DROP CONSTRAINT IF EXISTS ck_cashflow_draft_not_reportable;
ALTER TABLE cashflow_facts_v1
  ADD CONSTRAINT ck_cashflow_draft_not_reportable
  CHECK (NOT (normalized_status = 'DRAFT' AND bucket <> 'IGNORE'));

-- Sign alignment by bucket (assumed and actual)
ALTER TABLE cashflow_facts_v1
  DROP CONSTRAINT IF EXISTS ck_cashflow_sign_alignment;
ALTER TABLE cashflow_facts_v1
  ADD CONSTRAINT ck_cashflow_sign_alignment
  CHECK (
    (bucket IN ('AR_OPEN','CASH_IN_ASSUMED','CASH_IN') AND signed_amount >= 0)
    OR
    (bucket IN ('AP_OPEN','CASH_OUT_ASSUMED','CASH_OUT') AND signed_amount <= 0)
    OR
    (bucket = 'IGNORE')
  );

-- Effective date required for reportable buckets (IGNORE allowed but still must have effective_date due to NOT NULL)
-- (Already enforced by NOT NULL; keep this note for clarity.)

COMMIT;
