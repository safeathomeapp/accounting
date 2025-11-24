"""TEMPORARY: Mock fixture data for testing and development.

WARNING: This module contains DEMO/FAKE DATA ONLY.
         Remove entire backend/accounting/mock/ directory before going to production.

Module: backend.accounting.mock.fixtures
Purpose: Fixture data for MockClient adapter
Status: DEVELOPMENT ONLY - Will be removed before live deployment
Created: November 24, 2025

This file provides hardcoded fixture data that simulates real accounting platform responses.
It's useful for:
- Unit testing without API dependencies
- Demo purposes
- Development and CI/CD pipelines
- Testing error handling locally
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any

# ============================================================================
# DEMO DATA - REMOVE BEFORE PRODUCTION
# ============================================================================

# Sample transactions (invoices, bills, transfers)
MOCK_INVOICES: List[Dict[str, Any]] = [
    {
        "id": "inv-001-demo",
        "number": "INV-001",
        "type": "INVOICE",  # Customer invoice
        "status": "PAID",
        "date": date.today() - timedelta(days=30),
        "due_date": date.today() - timedelta(days=20),
        "description": "Professional services - Website redesign",
        "contact_id": "contact-acme-demo",
        "contact_name": "Acme Corporation",
        "amount": Decimal("5000.00"),
        "tax_amount": Decimal("1000.00"),
        "total": Decimal("6000.00"),
        "account_code": "4000",  # Revenue
    },
    {
        "id": "inv-002-demo",
        "number": "INV-002",
        "type": "BILL",  # Supplier bill
        "status": "AUTHORISED",
        "date": date.today() - timedelta(days=15),
        "due_date": date.today() + timedelta(days=15),
        "description": "Office supplies and equipment",
        "contact_id": "contact-supplier-demo",
        "contact_name": "Tech Supplies Inc",
        "amount": Decimal("2500.00"),
        "tax_amount": Decimal("500.00"),
        "total": Decimal("3000.00"),
        "account_code": "6000",  # Expense
    },
    {
        "id": "inv-003-demo",
        "number": "INV-003",
        "type": "INVOICE",
        "status": "DRAFT",
        "date": date.today() - timedelta(days=5),
        "due_date": date.today() + timedelta(days=25),
        "description": "Monthly retainer - Q4 2025",
        "contact_id": "contact-acme-demo",
        "contact_name": "Acme Corporation",
        "amount": Decimal("10000.00"),
        "tax_amount": Decimal("2000.00"),
        "total": Decimal("12000.00"),
        "account_code": "4000",
    },
]

# Sample bank transfers
MOCK_BANK_TRANSFERS: List[Dict[str, Any]] = [
    {
        "id": "transfer-001-demo",
        "type": "BANK_TRANSFER",
        "status": "AUTHORISED",
        "date": date.today() - timedelta(days=10),
        "description": "Transfer to savings account",
        "from_account": "Business Checking",
        "to_account": "Business Savings",
        "amount": Decimal("25000.00"),
    },
    {
        "id": "transfer-002-demo",
        "type": "BANK_TRANSFER",
        "status": "AUTHORISED",
        "date": date.today() - timedelta(days=5),
        "description": "Payroll transfer",
        "from_account": "Business Checking",
        "to_account": "Payroll Account",
        "amount": Decimal("15000.00"),
    },
]

# Sample contacts
MOCK_CONTACTS: List[Dict[str, Any]] = [
    {
        "id": "contact-acme-demo",
        "name": "Acme Corporation",
        "email": "accounts@acme.example.com",
        "phone": "+1-555-0101",
        "type": "CUSTOMER",
        "address": "123 Business Way, Tech City, TC 12345",
        "tax_number": "98-7654321",
        "is_archived": False,
    },
    {
        "id": "contact-supplier-demo",
        "name": "Tech Supplies Inc",
        "email": "sales@techsupplies.example.com",
        "phone": "+1-555-0102",
        "type": "SUPPLIER",
        "address": "456 Supply Street, Industrial City, IC 54321",
        "tax_number": "12-3456789",
        "is_archived": False,
    },
    {
        "id": "contact-freelancer-demo",
        "name": "Jane Developer",
        "email": "jane@freelance.example.com",
        "phone": "+1-555-0103",
        "type": "SUPPLIER",
        "address": "789 Code Lane, Dev City, DC 99999",
        "tax_number": None,
        "is_archived": False,
    },
]

# Sample accounts (chart of accounts)
MOCK_ACCOUNTS: List[Dict[str, Any]] = [
    {
        "id": "account-1000-demo",
        "code": "1000",
        "name": "Business Checking Account",
        "type": "BANK",
        "status": "ACTIVE",
        "tax_type": None,
    },
    {
        "id": "account-1100-demo",
        "code": "1100",
        "name": "Savings Account",
        "type": "BANK",
        "status": "ACTIVE",
        "tax_type": None,
    },
    {
        "id": "account-1200-demo",
        "code": "1200",
        "name": "Accounts Receivable",
        "type": "ASSET",
        "status": "ACTIVE",
        "tax_type": None,
    },
    {
        "id": "account-2000-demo",
        "code": "2000",
        "name": "Accounts Payable",
        "type": "LIABILITY",
        "status": "ACTIVE",
        "tax_type": None,
    },
    {
        "id": "account-3000-demo",
        "code": "3000",
        "name": "Retained Earnings",
        "type": "EQUITY",
        "status": "ACTIVE",
        "tax_type": None,
    },
    {
        "id": "account-4000-demo",
        "code": "4000",
        "name": "Product Sales Income",
        "type": "INCOME",
        "status": "ACTIVE",
        "tax_type": "Tax on Sales",
    },
    {
        "id": "account-4100-demo",
        "code": "4100",
        "name": "Service Income",
        "type": "INCOME",
        "status": "ACTIVE",
        "tax_type": "Tax on Sales",
    },
    {
        "id": "account-5000-demo",
        "code": "5000",
        "name": "Cost of Goods Sold",
        "type": "EXPENSE",
        "status": "ACTIVE",
        "tax_type": None,
    },
    {
        "id": "account-6000-demo",
        "code": "6000",
        "name": "Office Supplies",
        "type": "EXPENSE",
        "status": "ACTIVE",
        "tax_type": None,
    },
    {
        "id": "account-6100-demo",
        "code": "6100",
        "name": "Rent Expense",
        "type": "EXPENSE",
        "status": "ACTIVE",
        "tax_type": None,
    },
]

# Organization info
MOCK_ORGANIZATION_INFO: Dict[str, Any] = {
    "id": "org-demo-12345",
    "name": "Demo Company Inc",
    "legal_name": "Demo Company Incorporated",
    "country_code": "US",
    "tax_number": "45-6789012",
    "registration_number": "12345678",
    "base_currency": "USD",
    "status": "ACTIVE",
    "platform": "MOCK",
    "created_at": date.today() - timedelta(days=365),
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_mock_transactions(
    start_date: date, end_date: date, transaction_type: str = None
) -> List[Dict[str, Any]]:
    """Get mock transactions within date range.

    DEMO DATA ONLY - Will be removed before production.
    """
    all_txns = MOCK_INVOICES + MOCK_BANK_TRANSFERS
    filtered = [
        t for t in all_txns
        if start_date <= t["date"] <= end_date
    ]
    if transaction_type:
        filtered = [t for t in filtered if t["type"] == transaction_type]
    return filtered


def get_mock_transaction(transaction_id: str) -> Dict[str, Any]:
    """Get single mock transaction by ID.

    DEMO DATA ONLY - Will be removed before production.
    """
    all_txns = MOCK_INVOICES + MOCK_BANK_TRANSFERS
    for txn in all_txns:
        if txn["id"] == transaction_id:
            return txn
    return None


def get_mock_contact(contact_id: str) -> Dict[str, Any]:
    """Get single mock contact by ID.

    DEMO DATA ONLY - Will be removed before production.
    """
    for contact in MOCK_CONTACTS:
        if contact["id"] == contact_id:
            return contact
    return None


def get_mock_account(account_id: str) -> Dict[str, Any]:
    """Get single mock account by ID.

    DEMO DATA ONLY - Will be removed before production.
    """
    for account in MOCK_ACCOUNTS:
        if account["id"] == account_id:
            return account
    return None
