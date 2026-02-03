BEGIN;

-- Seed mappings for your CURRENT MOCK DATA ONLY:
-- source_type: 'Invoice' / 'Bill'
-- source_status: draft/submitted/approved/overdue/paid
-- platform_name left NULL => applies to all platforms until overridden.

-- Drafts => IGNORE
INSERT INTO platform_transaction_mapping
  (organization_id, platform_name, source_type, source_status, normalized_type, normalized_status, canonical_bucket, effective_date_source, priority, notes)
VALUES
  (NULL, NULL, 'Invoice', 'draft', 'INVOICE', 'DRAFT', 'IGNORE', 'DUE_DATE', 1000, 'Mock: drafts excluded'),
  (NULL, NULL, 'Bill',    'draft', 'BILL',    'DRAFT', 'IGNORE', 'DUE_DATE', 1000, 'Mock: drafts excluded')
ON CONFLICT DO NOTHING;

-- Invoices open => AR_OPEN, due date schedule
INSERT INTO platform_transaction_mapping
  (organization_id, platform_name, source_type, source_status, normalized_type, normalized_status, canonical_bucket, effective_date_source, priority, notes)
VALUES
  (NULL, NULL, 'Invoice', 'submitted', 'INVOICE', 'SUBMITTED', 'AR_OPEN', 'DUE_DATE', 900, 'Mock: AR open'),
  (NULL, NULL, 'Invoice', 'approved',  'INVOICE', 'APPROVED',  'AR_OPEN', 'DUE_DATE', 900, 'Mock: AR open'),
  (NULL, NULL, 'Invoice', 'overdue',   'INVOICE', 'OVERDUE',   'AR_OPEN', 'DUE_DATE', 900, 'Mock: AR open')
ON CONFLICT DO NOTHING;

-- Bills open => AP_OPEN, due date schedule
INSERT INTO platform_transaction_mapping
  (organization_id, platform_name, source_type, source_status, normalized_type, normalized_status, canonical_bucket, effective_date_source, priority, notes)
VALUES
  (NULL, NULL, 'Bill', 'approved', 'BILL', 'APPROVED', 'AP_OPEN', 'DUE_DATE', 900, 'Mock: AP open'),
  (NULL, NULL, 'Bill', 'overdue',  'BILL', 'OVERDUE',  'AP_OPEN', 'DUE_DATE', 900, 'Mock: AP open')
ON CONFLICT DO NOTHING;

-- Paid items => assumed cash moved in v1 (transaction date)
INSERT INTO platform_transaction_mapping
  (organization_id, platform_name, source_type, source_status, normalized_type, normalized_status, canonical_bucket, effective_date_source, priority, notes)
VALUES
  (NULL, NULL, 'Invoice', 'paid', 'INVOICE', 'PAID', 'CASH_IN_ASSUMED', 'TRANSACTION_DATE', 800, 'Mock: paid assumed cash-in'),
  (NULL, NULL, 'Bill',    'paid', 'BILL',    'PAID', 'CASH_OUT_ASSUMED','TRANSACTION_DATE', 800, 'Mock: paid assumed cash-out')
ON CONFLICT DO NOTHING;

COMMIT;
