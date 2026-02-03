BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'normalized_txn_type') THEN
    CREATE TYPE normalized_txn_type AS ENUM (
      'INVOICE',
      'BILL',
      'PAYMENT_RECEIPT',
      'PAYMENT_SENT',
      'BANK_RECEIPT',
      'BANK_PAYMENT',
      'JOURNAL',
      'ADJUSTMENT',
      'UNKNOWN'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'normalized_txn_status') THEN
    CREATE TYPE normalized_txn_status AS ENUM (
      'DRAFT',
      'SUBMITTED',
      'APPROVED',
      'OVERDUE',
      'PAID',
      'VOIDED',
      'DELETED',
      'UNKNOWN'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'cashflow_bucket') THEN
    CREATE TYPE cashflow_bucket AS ENUM (
      'AR_OPEN',
      'AP_OPEN',
      'CASH_IN_ASSUMED',
      'CASH_OUT_ASSUMED',
      'CASH_IN',
      'CASH_OUT',
      'IGNORE'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'date_source') THEN
    CREATE TYPE date_source AS ENUM (
      'DUE_DATE',
      'TRANSACTION_DATE'
    );
  END IF;
END$$;

COMMIT;
