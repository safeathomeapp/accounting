BEGIN;

-- NOTE: only enable this if your app sets `app.org_id` per request/session.
-- Example: SET app.org_id = '<tenant-uuid>';

-- cashflow_facts_v1
ALTER TABLE cashflow_facts_v1 ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS p_cashflow_facts_tenant ON cashflow_facts_v1;
CREATE POLICY p_cashflow_facts_tenant
ON cashflow_facts_v1
USING (organization_id = current_setting('app.org_id', true)::uuid);

-- audit_log (only if exists)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='audit_log') THEN
    EXECUTE 'ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY';
    EXECUTE 'DROP POLICY IF EXISTS p_audit_log_tenant ON audit_log';
    EXECUTE '
      CREATE POLICY p_audit_log_tenant
      ON audit_log
      USING (organization_id = current_setting('app.org_id'', true)::uuid)
    ';
  END IF;
END$$;

COMMIT;
