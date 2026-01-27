"""
Single source of truth for all platform transaction mapping definitions.

Both the Alembic seed migration and the standalone seed script import from here.
To add a new platform, add its mappings to PLATFORM_MAPPINGS below.

Each mapping entry is a dict with:
  platform_name  - lowercase platform identifier (e.g. "xero", "quickbooks")
  source_type    - the transaction_type value stored in the transactions table
  source_status  - the status value stored in the transactions table
  normalized_type   - NormalizedTxnType enum value
  normalized_status - NormalizedTxnStatus enum value
  canonical_bucket  - CashflowBucket enum value
  effective_date_source - DateSource enum value (default: TRANSACTION_DATE)
"""

# Using string values that match the enum names
# This keeps the definitions serializable and importable from migrations

PLATFORM_MAPPINGS = [
    # =========================================================================
    # XERO MAPPINGS
    # =========================================================================

    # --- Xero Invoices (Sales - ACCREC type) ---
    {
        "platform_name": "xero",
        "source_type": "invoice",
        "source_status": "draft",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "DRAFT",
        "canonical_bucket": "IGNORE",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "xero",
        "source_type": "invoice",
        "source_status": "submitted",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "AWAITING_APPROVAL",
        "canonical_bucket": "AR_CURRENT",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "xero",
        "source_type": "invoice",
        "source_status": "approved",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "APPROVED",
        "canonical_bucket": "AR_CURRENT",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "xero",
        "source_type": "invoice",
        "source_status": "awaiting_payment",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "SENT",
        "canonical_bucket": "AR_CURRENT",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "xero",
        "source_type": "invoice",
        "source_status": "paid",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "PAID",
        "canonical_bucket": "CASH_IN",
        "effective_date_source": "TRANSACTION_DATE",
    },
    {
        "platform_name": "xero",
        "source_type": "invoice",
        "source_status": "cancelled",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "VOIDED",
        "canonical_bucket": "IGNORE",
        "effective_date_source": "TRANSACTION_DATE",
    },
    {
        "platform_name": "xero",
        "source_type": "invoice",
        "source_status": "deleted",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "VOIDED",
        "canonical_bucket": "IGNORE",
        "effective_date_source": "TRANSACTION_DATE",
    },
    {
        "platform_name": "xero",
        "source_type": "invoice",
        "source_status": "overdue",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "SENT",
        "canonical_bucket": "AR_OVERDUE",
        "effective_date_source": "DUE_DATE",
    },

    # --- Xero Bills (Purchases - ACCPAY type) ---
    {
        "platform_name": "xero",
        "source_type": "bill",
        "source_status": "draft",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "DRAFT",
        "canonical_bucket": "IGNORE",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "xero",
        "source_type": "bill",
        "source_status": "submitted",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "AWAITING_APPROVAL",
        "canonical_bucket": "AP_CURRENT",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "xero",
        "source_type": "bill",
        "source_status": "approved",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "APPROVED",
        "canonical_bucket": "AP_CURRENT",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "xero",
        "source_type": "bill",
        "source_status": "awaiting_payment",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "APPROVED",
        "canonical_bucket": "AP_CURRENT",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "xero",
        "source_type": "bill",
        "source_status": "paid",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "PAID",
        "canonical_bucket": "CASH_OUT",
        "effective_date_source": "TRANSACTION_DATE",
    },
    {
        "platform_name": "xero",
        "source_type": "bill",
        "source_status": "cancelled",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "VOIDED",
        "canonical_bucket": "IGNORE",
        "effective_date_source": "TRANSACTION_DATE",
    },

    # --- Xero Bank Transactions ---
    {
        "platform_name": "xero",
        "source_type": "bank_transaction",
        "source_status": "approved",
        "normalized_type": "BANK_RECEIPT",
        "normalized_status": "APPROVED",
        "canonical_bucket": "CASH_IN",
        "effective_date_source": "TRANSACTION_DATE",
    },

    # --- Xero Credit Notes ---
    {
        "platform_name": "xero",
        "source_type": "credit_note",
        "source_status": "approved",
        "normalized_type": "CREDIT_NOTE",
        "normalized_status": "APPROVED",
        "canonical_bucket": "NON_CASH",
        "effective_date_source": "TRANSACTION_DATE",
    },

    # =========================================================================
    # MOCK PLATFORM MAPPINGS (development/test data)
    # Same patterns as Xero - invoice and bill with common statuses
    # =========================================================================

    # --- Mock Invoices (Sales) ---
    {
        "platform_name": "mock",
        "source_type": "invoice",
        "source_status": "draft",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "DRAFT",
        "canonical_bucket": "IGNORE",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "mock",
        "source_type": "invoice",
        "source_status": "submitted",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "AWAITING_APPROVAL",
        "canonical_bucket": "AR_CURRENT",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "mock",
        "source_type": "invoice",
        "source_status": "approved",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "APPROVED",
        "canonical_bucket": "AR_CURRENT",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "mock",
        "source_type": "invoice",
        "source_status": "paid",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "PAID",
        "canonical_bucket": "CASH_IN",
        "effective_date_source": "TRANSACTION_DATE",
    },
    {
        "platform_name": "mock",
        "source_type": "invoice",
        "source_status": "overdue",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "SENT",
        "canonical_bucket": "AR_OVERDUE",
        "effective_date_source": "DUE_DATE",
    },

    # --- Mock Bills (Purchases) ---
    {
        "platform_name": "mock",
        "source_type": "bill",
        "source_status": "draft",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "DRAFT",
        "canonical_bucket": "IGNORE",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "mock",
        "source_type": "bill",
        "source_status": "submitted",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "AWAITING_APPROVAL",
        "canonical_bucket": "AP_CURRENT",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "mock",
        "source_type": "bill",
        "source_status": "approved",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "APPROVED",
        "canonical_bucket": "AP_CURRENT",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "mock",
        "source_type": "bill",
        "source_status": "paid",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "PAID",
        "canonical_bucket": "CASH_OUT",
        "effective_date_source": "TRANSACTION_DATE",
    },
    {
        "platform_name": "mock",
        "source_type": "bill",
        "source_status": "overdue",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "APPROVED",
        "canonical_bucket": "AP_OVERDUE",
        "effective_date_source": "DUE_DATE",
    },

    # =========================================================================
    # QUICKBOOKS MAPPINGS
    # =========================================================================

    # --- QuickBooks Invoices ---
    {
        "platform_name": "quickbooks",
        "source_type": "invoice",
        "source_status": "draft",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "DRAFT",
        "canonical_bucket": "IGNORE",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "quickbooks",
        "source_type": "invoice",
        "source_status": "approved",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "APPROVED",
        "canonical_bucket": "AR_CURRENT",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "quickbooks",
        "source_type": "invoice",
        "source_status": "paid",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "PAID",
        "canonical_bucket": "CASH_IN",
        "effective_date_source": "TRANSACTION_DATE",
    },
    {
        "platform_name": "quickbooks",
        "source_type": "invoice",
        "source_status": "voided",
        "normalized_type": "SALES_INVOICE",
        "normalized_status": "VOIDED",
        "canonical_bucket": "IGNORE",
        "effective_date_source": "TRANSACTION_DATE",
    },

    # --- QuickBooks Bills ---
    {
        "platform_name": "quickbooks",
        "source_type": "bill",
        "source_status": "draft",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "DRAFT",
        "canonical_bucket": "IGNORE",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "quickbooks",
        "source_type": "bill",
        "source_status": "approved",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "APPROVED",
        "canonical_bucket": "AP_CURRENT",
        "effective_date_source": "DUE_DATE",
    },
    {
        "platform_name": "quickbooks",
        "source_type": "bill",
        "source_status": "paid",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "PAID",
        "canonical_bucket": "CASH_OUT",
        "effective_date_source": "TRANSACTION_DATE",
    },
    {
        "platform_name": "quickbooks",
        "source_type": "bill",
        "source_status": "voided",
        "normalized_type": "PURCHASE_INVOICE",
        "normalized_status": "VOIDED",
        "canonical_bucket": "IGNORE",
        "effective_date_source": "TRANSACTION_DATE",
    },
]
