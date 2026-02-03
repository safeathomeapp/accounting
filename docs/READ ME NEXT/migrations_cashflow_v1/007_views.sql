BEGIN;

-- Mapping coverage view to surface drift.
-- Adjust table/column names if your raw schema differs.

CREATE OR REPLACE VIEW v_mapping_coverage AS
WITH raw AS (
  SELECT
    t.organization_id,
    COALESCE(c.platform_name, NULL) AS platform_name,
    t.transaction_type AS source_type,
    t.status AS source_status,
    count(*) AS row_count
  FROM transactions t
  LEFT JOIN clients c ON c.id = t.client_id
  GROUP BY 1,2,3,4
),
mapped AS (
  SELECT
    r.*,
    m.id AS mapping_id
  FROM raw r
  LEFT JOIN LATERAL (
    SELECT id
    FROM platform_transaction_mapping m
    WHERE m.is_active = true
      AND (m.organization_id IS NULL OR m.organization_id = r.organization_id)
      AND (m.platform_name IS NULL OR m.platform_name = r.platform_name)
      AND m.source_type = r.source_type
      AND (m.source_status IS NULL OR m.source_status = r.source_status)
    ORDER BY m.priority DESC
    LIMIT 1
  ) m ON true
)
SELECT
  organization_id,
  platform_name,
  source_type,
  source_status,
  row_count,
  (mapping_id IS NOT NULL) AS is_mapped
FROM mapped;

COMMIT;
