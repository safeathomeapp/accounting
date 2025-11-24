# Xero Implementation Blueprint

**Status:** Ready for Implementation (Week 3)
**Date:** November 24, 2025
**Purpose:** Step-by-step guide to implementing XeroClient adapter

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture & File Structure](#architecture--file-structure)
3. [Implementation Steps](#implementation-steps)
4. [Detailed Code Walkthroughs](#detailed-code-walkthroughs)
5. [Testing Strategy](#testing-strategy)
6. [Troubleshooting](#troubleshooting)
7. [Completion Checklist](#completion-checklist)

---

## 🎯 Overview

This blueprint guides you through implementing the **XeroClient** - an adapter that bridges Xero API and our abstraction layer.

**What You'll Build:**
- `XeroClient` - Main adapter class extending `AccountingClient`
- `XeroAuth` - OAuth 2.0 authentication handler
- `XeroMapper` - Data transformation from Xero format to standard models
- `test_accounting_xero.py` - Comprehensive test suite (80%+ coverage)

**Time Estimate:** 4-6 hours of focused implementation
**Difficulty:** Medium (lots of boilerplate, but straightforward logic)

**Golden Rule:** Don't add features beyond the abstraction layer contract. Keep it simple.

---

## 🏗️ Architecture & File Structure

### Directory Structure to Create

```
backend/accounting/xero/
├── __init__.py           # Exports (minimal)
├── client.py             # XeroClient main class (300-400 LOC)
├── auth.py               # OAuth authentication (150-200 LOC)
└── mapper.py             # Data transformation (200-300 LOC)
```

### File Dependencies

```
XeroClient (client.py)
  ├── imports AccountingClient, Standard models
  ├── imports XeroAuth for authentication
  ├── imports XeroMapper for data transformation
  ├── makes HTTP requests via requests library
  └── uses environment variables for credentials

XeroAuth (auth.py)
  ├── imports OAuth utilities
  ├── handles token storage/retrieval
  └── manages token refresh

XeroMapper (mapper.py)
  ├── imports Standard models
  ├── imports enumerations
  └── contains pure translation functions (no external calls)
```

### Class Hierarchy

```
                 AccountingClient (ABC)
                        ▲
                        │
                        │ extends
                        │
                    XeroClient
                        │
                        ├─ uses ─> XeroAuth
                        └─ uses ─> XeroMapper
```

---

## 🚀 Implementation Steps

### Step 1: Create Package Structure (5 minutes)

#### 1.1: Create directory
```bash
mkdir -p backend/accounting/xero
```

#### 1.2: Create `backend/accounting/xero/__init__.py`
```python
"""Xero accounting adapter."""

from .client import XeroClient

__all__ = ["XeroClient"]
```

### Step 2: Implement XeroAuth (40 minutes)

Create `backend/accounting/xero/auth.py` - OAuth 2.0 handler

**Key Responsibilities:**
- Generate authorization URL for user login
- Exchange authorization code for access token
- Refresh expired tokens
- Store/retrieve tokens securely

See detailed walkthrough: [Step 2 Walkthrough](#step-2-walkthrough-xerauth)

### Step 3: Implement XeroMapper (60 minutes)

Create `backend/accounting/xero/mapper.py` - Data transformation

**Key Responsibilities:**
- Map Xero Invoice → StandardTransaction
- Map Xero Contact → StandardContact
- Map Xero Account → StandardAccount
- Handle all special cases from DATA_MAPPING_SPEC.md

See detailed walkthrough: [Step 3 Walkthrough](#step-3-walkthrough-xeromapper)

### Step 4: Implement XeroClient (90 minutes)

Create `backend/accounting/xero/client.py` - Main adapter class

**Key Responsibilities:**
- Extend AccountingClient with all abstract methods
- Implement OAuth flow
- Fetch data from Xero API endpoints
- Transform and return data using mapper
- Handle errors and rate limiting

See detailed walkthrough: [Step 4 Walkthrough](#step-4-walkthrough-xeroclient)

### Step 5: Write Tests (60 minutes)

Create `tests/test_accounting_xero.py` - Comprehensive test suite

**Coverage Areas:**
- OAuth flow (mocked)
- API calls (mocked)
- Data mapping (real - test every mapping)
- Error handling
- Rate limiting
- Integration workflows

See testing strategy: [Testing Strategy](#testing-strategy)

### Step 6: Integration Testing (30 minutes)

Test with actual Xero demo company if credentials available.

---

## 📝 Detailed Code Walkthroughs

### Step 2 Walkthrough: XeroAuth

**File:** `backend/accounting/xero/auth.py`

```python
"""OAuth 2.0 authentication for Xero."""

import os
import secrets
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import base64
import requests
from urllib.parse import urlencode

# ============================================================================
# CONFIGURATION
# ============================================================================

# Xero OAuth endpoints
XERO_AUTH_URL = "https://login.xero.com/identity/connect/authorize"
XERO_TOKEN_URL = "https://identity.xero.com/connect/token"
XERO_REVOKE_URL = "https://identity.xero.com/connect/revoke"

# Scopes we need
XERO_SCOPES = [
    "offline_access",                    # Long-lived refresh tokens
    "accounting.transactions",           # Read invoices, bills
    "accounting.contacts",               # Read contacts
    "accounting.settings",               # Read organization info
]


# ============================================================================
# PKCE HELPER FUNCTIONS
# ============================================================================

def generate_pkce_pair() -> Tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge.

    Returns:
        Tuple of (code_verifier, code_challenge)
    """
    # Generate random string (43-128 chars)
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode("utf-8").rstrip("=")

    # Create challenge from verifier
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode("utf-8").rstrip("=")

    return code_verifier, challenge


def generate_state() -> str:
    """Generate random state parameter for OAuth."""
    return secrets.token_urlsafe(32)


# ============================================================================
# XERAUTH CLASS
# ============================================================================

class XeroAuth:
    """Handles OAuth 2.0 authentication with Xero."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """Initialize authentication handler.

        Args:
            client_id: Xero application client ID
            client_secret: Xero application client secret
            redirect_uri: Callback URL (e.g., http://localhost:8000/auth/xero/callback)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        # Token storage (in production, use database)
        self.tokens = {}
        self.pkce_state = {}  # Store PKCE pairs during auth flow

    def get_authorization_url(self, state: Optional[str] = None) -> Tuple[str, str]:
        """Generate authorization URL for user to visit.

        Args:
            state: Optional state parameter for security

        Returns:
            Tuple of (authorization_url, state) where state should be stored
        """
        if state is None:
            state = generate_state()

        # Generate PKCE pair
        code_verifier, code_challenge = generate_pkce_pair()

        # Store PKCE verifier for later token exchange
        self.pkce_state[state] = {
            "code_verifier": code_verifier,
            "created_at": datetime.now(),
        }

        # Build authorization URL
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(XERO_SCOPES),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        auth_url = f"{XERO_AUTH_URL}?{urlencode(params)}"
        return auth_url, state

    def exchange_code_for_token(self, code: str, state: str) -> Dict:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from Xero callback
            state: State parameter from authorization URL

        Returns:
            Dict with access_token, refresh_token, expires_in, Xero-tenant-id

        Raises:
            ValueError: If state is invalid or PKCE verifier not found
        """
        if state not in self.pkce_state:
            raise ValueError(f"Invalid state parameter: {state}")

        pkce_data = self.pkce_state[state]
        code_verifier = pkce_data["code_verifier"]

        # Check if PKCE is too old (>10 minutes)
        if datetime.now() - pkce_data["created_at"] > timedelta(minutes=10):
            del self.pkce_state[state]
            raise ValueError("Authorization request expired")

        # Exchange code for token
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code_verifier": code_verifier,
        }

        response = requests.post(XERO_TOKEN_URL, data=data)
        response.raise_for_status()

        token_data = response.json()

        # Clean up PKCE state
        del self.pkce_state[state]

        # Store token with expiration
        self.tokens = {
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "expires_at": datetime.now() + timedelta(seconds=token_data["expires_in"]),
            "tenant_id": token_data.get("Xero-tenant-id"),
        }

        return token_data

    def get_access_token(self) -> Optional[str]:
        """Get current access token, refreshing if needed.

        Returns:
            Access token string or None if not authenticated
        """
        if not self.tokens:
            return None

        # Check if token expired
        if datetime.now() >= self.tokens["expires_at"]:
            self.refresh_access_token()

        return self.tokens.get("access_token")

    def refresh_access_token(self) -> Dict:
        """Refresh the access token using refresh token.

        Returns:
            Dict with new token data

        Raises:
            ValueError: If no refresh token available
        """
        if not self.tokens.get("refresh_token"):
            raise ValueError("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.tokens["refresh_token"],
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = requests.post(XERO_TOKEN_URL, data=data)
        response.raise_for_status()

        token_data = response.json()

        # Update stored tokens
        self.tokens["access_token"] = token_data["access_token"]
        self.tokens["refresh_token"] = token_data.get(
            "refresh_token",
            self.tokens["refresh_token"]
        )
        self.tokens["expires_at"] = datetime.now() + timedelta(
            seconds=token_data["expires_in"]
        )

        return token_data

    def get_tenant_id(self) -> Optional[str]:
        """Get Xero tenant ID.

        Returns:
            Tenant ID string or None
        """
        return self.tokens.get("tenant_id")

    def is_authenticated(self) -> bool:
        """Check if currently authenticated.

        Returns:
            True if has valid token, False otherwise
        """
        return bool(self.get_access_token())

    def revoke_token(self) -> bool:
        """Revoke the refresh token (logout).

        Returns:
            True if successful
        """
        if not self.tokens.get("refresh_token"):
            return False

        data = {
            "token": self.tokens["refresh_token"],
            "client_id": self.client_id,
        }

        try:
            response = requests.post(XERO_REVOKE_URL, data=data)
            response.raise_for_status()
            self.tokens = {}
            return True
        except requests.exceptions.RequestException:
            return False
```

**Key Points:**
- ✅ PKCE support (required by Xero)
- ✅ State parameter for security
- ✅ Token refresh handling
- ✅ Token expiration tracking
- ✅ Clean separation of concerns

---

### Step 3 Walkthrough: XeroMapper

**File:** `backend/accounting/xero/mapper.py`

```python
"""Xero data transformation to standard models."""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List

from backend.accounting import (
    StandardTransaction,
    StandardContact,
    StandardAccount,
    TransactionType,
    ContactType,
    AccountType,
    SyncStatus,
)


# ============================================================================
# TRANSACTION MAPPING
# ============================================================================

class XeroMapper:
    """Maps Xero API responses to standard models."""

    @staticmethod
    def map_invoice_to_transaction(invoice: Dict[str, Any]) -> StandardTransaction:
        """Convert Xero Invoice (ACCREC or ACCPAY) to StandardTransaction.

        Args:
            invoice: Raw Xero invoice dict from API

        Returns:
            StandardTransaction object
        """
        # Determine type based on invoice type
        xero_type = invoice.get("Type", "ACCREC")
        if xero_type == "ACCREC":
            txn_type = TransactionType.INVOICE
        elif xero_type == "ACCPAY":
            txn_type = TransactionType.BILL
        else:
            txn_type = TransactionType.INVOICE  # Default

        # Parse dates
        date_obj = XeroMapper._parse_xero_date(
            invoice.get("InvoiceDate", "")
        )

        due_date = XeroMapper._parse_xero_date(
            invoice.get("DueDate", "")
        )

        # Extract contact ID
        contact_id = None
        if invoice.get("Contact"):
            contact_id = invoice["Contact"].get("ContactID")

        # Get first line item for account code
        account_id = ""
        line_items_list = invoice.get("LineItems", [])
        if line_items_list:
            account_id = line_items_list[0].get("AccountCode", "")

        # Map status
        status = XeroMapper._map_invoice_status(
            invoice.get("Status", "DRAFT")
        )

        # Build metadata
        metadata = {
            "xero_type": xero_type,
            "tax_type": line_items_list[0].get("TaxType") if line_items_list else None,
            "due_date": due_date.isoformat() if due_date else None,
            "line_amount_types": invoice.get("LineAmountTypes", "Exclusive"),
            "has_attachments": invoice.get("HasAttachments", False),
            "updated_utc": invoice.get("UpdatedDateUTC"),
        }

        # Convert line items to list of dicts
        line_items = []
        for item in line_items_list:
            line_items.append({
                "description": item.get("Description", ""),
                "quantity": float(item.get("Quantity", 0)),
                "unit_amount": str(item.get("UnitAmount", "0")),
                "account_code": item.get("AccountCode", ""),
                "tax_type": item.get("TaxType"),
                "tax_amount": str(item.get("TaxAmount", "0")),
                "line_amount": str(item.get("LineAmount", "0")),
            })

        # Create transaction
        transaction = StandardTransaction(
            id=invoice.get("InvoiceID", ""),
            type=txn_type,
            date=date_obj,
            description=invoice.get("Description", ""),
            amount=Decimal(str(invoice.get("Total", "0"))),
            tax_amount=Decimal(str(invoice.get("TaxTotal", "0"))),
            account_id=account_id,
            contact_id=contact_id,
            reference=invoice.get("InvoiceNumber", ""),
            status=status,
            line_items=line_items,
            platform_id=invoice.get("InvoiceID", ""),
            platform_name="xero",
            metadata=metadata,
            sync_status=SyncStatus.SYNCED,
        )

        return transaction

    @staticmethod
    def map_bank_transfer_to_transaction(
        transfer: Dict[str, Any]
    ) -> StandardTransaction:
        """Convert Xero BankTransfer to StandardTransaction.

        Args:
            transfer: Raw Xero bank transfer dict

        Returns:
            StandardTransaction object
        """
        # Get amount from line items
        amount = Decimal("0")
        line_items_list = transfer.get("LineItems", [])
        if line_items_list:
            amount = Decimal(str(line_items_list[0].get("UnitAmount", "0")))

        # Get from/to accounts
        from_account = transfer.get("FromBankAccount", {})
        to_account = transfer.get("ToBankAccount", {})

        metadata = {
            "from_account": from_account.get("Code"),
            "to_account": to_account.get("Code"),
            "has_attachments": transfer.get("HasAttachments", False),
        }

        transaction = StandardTransaction(
            id=transfer.get("BankTransferID", ""),
            type=TransactionType.BANK_TRANSFER,
            date=XeroMapper._parse_xero_date(
                transfer.get("DateString", "")
            ),
            description="Bank Transfer",
            amount=amount,
            tax_amount=Decimal("0"),
            account_id=from_account.get("Code", ""),
            contact_id=None,
            reference=f"TRANSFER-{transfer.get('BankTransferID', '')}",
            status="approved",
            line_items=[],
            platform_id=transfer.get("BankTransferID", ""),
            platform_name="xero",
            metadata=metadata,
            sync_status=SyncStatus.SYNCED,
        )

        return transaction

    @staticmethod
    def map_credit_note_to_transaction(
        credit_note: Dict[str, Any]
    ) -> StandardTransaction:
        """Convert Xero CreditNote to StandardTransaction.

        Args:
            credit_note: Raw Xero credit note dict

        Returns:
            StandardTransaction object
        """
        date_obj = XeroMapper._parse_xero_date(
            credit_note.get("DateString", "")
        )

        contact_id = None
        if credit_note.get("Contact"):
            contact_id = credit_note["Contact"].get("ContactID")

        # Get first line item for account
        account_id = ""
        line_items_list = credit_note.get("LineItems", [])
        if line_items_list:
            account_id = line_items_list[0].get("AccountCode", "")

        # Credit notes have negative amounts
        amount = Decimal(str(credit_note.get("Total", "0")))
        tax_amount = Decimal(str(credit_note.get("TaxTotal", "0")))

        transaction = StandardTransaction(
            id=credit_note.get("CreditNoteID", ""),
            type=TransactionType.CREDIT_NOTE,
            date=date_obj,
            description=credit_note.get("Description", ""),
            amount=amount,
            tax_amount=tax_amount,
            account_id=account_id,
            contact_id=contact_id,
            reference=credit_note.get("CreditNoteNumber", ""),
            status=XeroMapper._map_invoice_status(
                credit_note.get("Status", "DRAFT")
            ),
            line_items=[],
            platform_id=credit_note.get("CreditNoteID", ""),
            platform_name="xero",
            metadata={},
            sync_status=SyncStatus.SYNCED,
        )

        return transaction


# ============================================================================
# CONTACT MAPPING
# ============================================================================

    @staticmethod
    def map_contact_to_standard(contact: Dict[str, Any]) -> StandardContact:
        """Convert Xero Contact to StandardContact.

        Args:
            contact: Raw Xero contact dict

        Returns:
            StandardContact object
        """
        # Infer contact type
        contact_type = XeroMapper._infer_contact_type(contact)

        # Parse address
        addresses = contact.get("Addresses", [])
        address_str = XeroMapper._build_address(addresses)

        # Get first phone
        phone = None
        phones = contact.get("Phones", [])
        if phones:
            phone = phones[0].get("PhoneNumber")

        # Build metadata
        metadata = {
            "contact_number": contact.get("ContactNumber"),
            "website": contact.get("Website"),
            "contact_status": contact.get("ContactStatus"),
            "addresses": addresses,
            "phones": phones,
            "xero_updated_utc": contact.get("UpdatedDateUTC"),
        }

        contact_obj = StandardContact(
            id=contact.get("ContactID", ""),
            type=contact_type,
            name=contact.get("Name", ""),
            email=contact.get("EmailAddress"),
            phone=phone,
            address=address_str,
            tax_id=contact.get("TaxNumber"),
            currency="GBP",  # Default for UK
            platform_id=contact.get("ContactID", ""),
            platform_name="xero",
            metadata=metadata,
        )

        return contact_obj


# ============================================================================
# ACCOUNT MAPPING
# ============================================================================

    @staticmethod
    def map_account_to_standard(account: Dict[str, Any]) -> StandardAccount:
        """Convert Xero Account to StandardAccount.

        Args:
            account: Raw Xero account dict

        Returns:
            StandardAccount object
        """
        # Map account type
        account_type = XeroMapper._map_account_type(
            account.get("Type", "EXPENSE")
        )

        metadata = {
            "xero_status": account.get("Status"),
            "system_account": account.get("SystemAccount", False),
            "enable_payments": account.get("EnablePayments", False),
            "xero_updated_utc": account.get("UpdatedDateUTC"),
        }

        account_obj = StandardAccount(
            id=account.get("AccountID", ""),
            code=account.get("Code", ""),
            name=account.get("Name", ""),
            type=account_type,
            currency="GBP",
            tax_type=account.get("TaxType"),
            platform_id=account.get("AccountID", ""),
            platform_name="xero",
            metadata=metadata,
        )

        return account_obj


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

    @staticmethod
    def _parse_xero_date(date_string: str) -> Optional[datetime]:
        """Parse Xero ISO 8601 date string.

        Args:
            date_string: ISO 8601 date (e.g., "2025-01-15T00:00:00Z")

        Returns:
            datetime object or None if invalid
        """
        if not date_string:
            return None

        try:
            # Xero returns dates with Z timezone
            dt = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
            return dt.date()
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _map_invoice_status(xero_status: str) -> str:
        """Map Xero invoice status to standard status.

        Args:
            xero_status: Xero status (DRAFT, AUTHORISED, PAID, etc.)

        Returns:
            Standard status string
        """
        status_map = {
            "DRAFT": "draft",
            "SUBMITTED": "submitted",
            "AUTHORISED": "approved",
            "PAID": "paid",
            "AWAITING_PAYMENT": "awaiting_payment",
            "VOIDED": "cancelled",
            "DELETED": "deleted",
        }

        return status_map.get(xero_status, "approved")

    @staticmethod
    def _infer_contact_type(contact: Dict[str, Any]) -> ContactType:
        """Infer contact type from Xero contact data.

        Args:
            contact: Raw Xero contact dict

        Returns:
            ContactType enum value
        """
        # Check contact groups
        groups = contact.get("ContactGroups", [])
        if any("SUPPLIER" in str(g) for g in groups):
            return ContactType.SUPPLIER
        if any("CUSTOMER" in str(g) for g in groups):
            return ContactType.CUSTOMER

        # Check for PO Box (supplier indicator)
        addresses = contact.get("Addresses", [])
        for addr in addresses:
            if "PO BOX" in str(addr.get("AddressLine1", "")).upper():
                return ContactType.SUPPLIER

        # Default to customer
        return ContactType.CUSTOMER

    @staticmethod
    def _build_address(addresses: List[Dict]) -> str:
        """Build single address string from Xero address array.

        Args:
            addresses: Xero Addresses array

        Returns:
            Formatted address string
        """
        if not addresses:
            return ""

        # Prefer STREET type
        address = next(
            (a for a in addresses if a.get("AddressType") == "STREET"),
            addresses[0]
        )

        # Build address from components
        parts = [
            address.get("AddressLine1"),
            address.get("AddressLine2"),
            address.get("City"),
            address.get("PostalCode"),
            address.get("PostalCodeCountry"),
        ]

        return ", ".join(filter(None, parts))

    @staticmethod
    def _map_account_type(xero_type: str) -> AccountType:
        """Map Xero account type to standard type.

        Args:
            xero_type: Xero Type (ASSET, EXPENSE, REVENUE, etc.)

        Returns:
            AccountType enum value
        """
        type_map = {
            "ASSET": AccountType.ASSET,
            "BANK": AccountType.BANK,
            "CURRENT": AccountType.ASSET,
            "FIXED": AccountType.ASSET,
            "EQUITY": AccountType.EQUITY,
            "EXPENSE": AccountType.EXPENSE,
            "LIABILITY": AccountType.LIABILITY,
            "OASSET": AccountType.ASSET,
            "PAYROLL": AccountType.EXPENSE,
            "REVENUE": AccountType.INCOME,
            "SALES": AccountType.INCOME,
        }

        return type_map.get(xero_type, AccountType.EXPENSE)
```

**Key Points:**
- ✅ Pure functions (no side effects)
- ✅ Handles all transaction types
- ✅ Proper error handling
- ✅ Metadata storage for extra Xero fields
- ✅ Status mapping
- ✅ Type inference for contacts

---

### Step 4 Walkthrough: XeroClient

**File:** `backend/accounting/xero/client.py`

```python
"""Xero accounting adapter implementation."""

import os
from typing import List, Optional, Dict, Any
from datetime import date, timedelta

import requests

from backend.accounting import (
    AccountingClient,
    StandardTransaction,
    StandardContact,
    StandardAccount,
    TransactionType,
    ContactType,
    APIError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
)

from .auth import XeroAuth
from .mapper import XeroMapper


# ============================================================================
# XEROCLIENT CLASS
# ============================================================================

class XeroClient(AccountingClient):
    """Xero adapter implementing AccountingClient interface."""

    PLATFORM_NAME = "xero"

    # Xero API configuration
    XERO_BASE_URL = "https://api.xero.com/api.xro/2.0"
    XERO_TENANT_HEADER = "Xero-tenant-id"

    def __init__(self, organization_id: str, credentials: Dict[str, Any]):
        """Initialize XeroClient.

        Args:
            organization_id: Organization ID from database
            credentials: Dict with keys:
                - client_id: Xero app client ID
                - client_secret: Xero app client secret
                - redirect_uri: OAuth callback URL
                - access_token: (optional) Existing access token
                - refresh_token: (optional) Existing refresh token
                - tenant_id: (optional) Xero tenant ID

        Raises:
            ValidationError: If credentials invalid
        """
        super().__init__(organization_id, credentials)

        # Initialize auth
        self.auth = XeroAuth(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            redirect_uri=credentials.get(
                "redirect_uri",
                "http://localhost:8000/auth/xero/callback"
            ),
        )

        # Restore tokens if provided
        if credentials.get("access_token"):
            self.auth.tokens = {
                "access_token": credentials["access_token"],
                "refresh_token": credentials.get("refresh_token"),
                "tenant_id": credentials.get("tenant_id"),
                "expires_at": None,  # Assume valid
            }

        # Initialize mapper
        self.mapper = XeroMapper()

    def _validate_credentials(self) -> None:
        """Validate that required credentials are present.

        Raises:
            ValidationError: If credentials missing or invalid
        """
        required = ["client_id", "client_secret", "redirect_uri"]
        for key in required:
            if key not in self.credentials:
                raise ValidationError(f"Missing credential: {key}")

    def authenticate(self) -> bool:
        """Check if currently authenticated.

        Returns:
            True if has valid access token
        """
        try:
            token = self.auth.get_access_token()
            return token is not None
        except Exception:
            return False

    def get_transactions(
        self,
        start_date: date,
        end_date: date,
        transaction_types: Optional[List[TransactionType]] = None,
        limit: int = 1000,
    ) -> List[StandardTransaction]:
        """Get transactions from Xero.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            transaction_types: Optional list of types to include
            limit: Maximum transactions to return

        Returns:
            List of StandardTransaction objects
        """
        transactions = []

        # Fetch invoices (ACCREC = customer invoices)
        if self._should_fetch_type(transaction_types, TransactionType.INVOICE):
            invoices = self._get_invoices(
                start_date, end_date, "ACCREC", limit
            )
            transactions.extend(invoices)

        # Fetch bills (ACCPAY = supplier invoices)
        if self._should_fetch_type(transaction_types, TransactionType.BILL):
            bills = self._get_invoices(
                start_date, end_date, "ACCPAY", limit
            )
            transactions.extend(bills)

        # Fetch bank transfers
        if self._should_fetch_type(transaction_types, TransactionType.BANK_TRANSFER):
            transfers = self._get_bank_transfers(start_date, end_date, limit)
            transactions.extend(transfers)

        return transactions[:limit]

    def get_transaction(self, transaction_id: str) -> Optional[StandardTransaction]:
        """Get single transaction by ID.

        Args:
            transaction_id: Transaction ID

        Returns:
            StandardTransaction or None if not found
        """
        try:
            # Try to find in invoices (we don't know the type)
            for invoice_type in ["ACCREC", "ACCPAY"]:
                url = f"{self.XERO_BASE_URL}/Invoices/{transaction_id}"
                response = self._make_request("GET", url)

                if response.get("Invoices"):
                    return self.mapper.map_invoice_to_transaction(
                        response["Invoices"][0]
                    )
        except NotFoundError:
            pass

        # Try bank transfers
        try:
            url = f"{self.XERO_BASE_URL}/BankTransfers/{transaction_id}"
            response = self._make_request("GET", url)
            if response.get("BankTransfers"):
                return self.mapper.map_bank_transfer_to_transaction(
                    response["BankTransfers"][0]
                )
        except NotFoundError:
            pass

        return None

    def create_transaction(self, transaction: StandardTransaction) -> StandardTransaction:
        """Create transaction in Xero.

        Note: Not implemented in Phase 1 (read-only access).

        Args:
            transaction: StandardTransaction to create

        Returns:
            Created transaction with platform_id

        Raises:
            NotImplementedError: Phase 1 is read-only
        """
        raise NotImplementedError("Phase 1: Read-only access to Xero")

    def update_transaction(
        self,
        transaction_id: str,
        transaction: StandardTransaction
    ) -> StandardTransaction:
        """Update transaction in Xero.

        Note: Not implemented in Phase 1 (read-only access).

        Args:
            transaction_id: ID of transaction to update
            transaction: Updated transaction data

        Returns:
            Updated transaction

        Raises:
            NotImplementedError: Phase 1 is read-only
        """
        raise NotImplementedError("Phase 1: Read-only access to Xero")

    def get_accounts(
        self,
        account_types: Optional[List[str]] = None
    ) -> List[StandardAccount]:
        """Get chart of accounts from Xero.

        Args:
            account_types: Optional list of types to filter

        Returns:
            List of StandardAccount objects
        """
        url = f"{self.XERO_BASE_URL}/Accounts"
        response = self._make_request("GET", url)

        accounts = []
        for account_data in response.get("Accounts", []):
            # Filter by type if specified
            if account_types and account_data.get("Type") not in account_types:
                continue

            account = self.mapper.map_account_to_standard(account_data)
            accounts.append(account)

        return accounts

    def get_account(self, account_id: str) -> Optional[StandardAccount]:
        """Get single account by ID.

        Args:
            account_id: Account ID

        Returns:
            StandardAccount or None if not found
        """
        try:
            url = f"{self.XERO_BASE_URL}/Accounts/{account_id}"
            response = self._make_request("GET", url)

            if response.get("Accounts"):
                return self.mapper.map_account_to_standard(
                    response["Accounts"][0]
                )
        except NotFoundError:
            pass

        return None

    def get_contacts(
        self,
        contact_types: Optional[List[ContactType]] = None,
        limit: int = 1000
    ) -> List[StandardContact]:
        """Get contacts from Xero.

        Args:
            contact_types: Optional list of types to filter
            limit: Maximum contacts to return

        Returns:
            List of StandardContact objects
        """
        contacts = []
        page = 1

        while len(contacts) < limit:
            url = f"{self.XERO_BASE_URL}/Contacts"
            params = {"page": page}
            response = self._make_request("GET", url, params=params)

            page_contacts = response.get("Contacts", [])
            if not page_contacts:
                break

            for contact_data in page_contacts:
                if len(contacts) >= limit:
                    break

                contact = self.mapper.map_contact_to_standard(contact_data)

                # Filter by type if specified
                if contact_types and contact.type not in contact_types:
                    continue

                contacts.append(contact)

            page += 1

        return contacts[:limit]

    def get_contact(self, contact_id: str) -> Optional[StandardContact]:
        """Get single contact by ID.

        Args:
            contact_id: Contact ID

        Returns:
            StandardContact or None if not found
        """
        try:
            url = f"{self.XERO_BASE_URL}/Contacts/{contact_id}"
            response = self._make_request("GET", url)

            if response.get("Contacts"):
                return self.mapper.map_contact_to_standard(
                    response["Contacts"][0]
                )
        except NotFoundError:
            pass

        return None

    def create_contact(self, contact: StandardContact) -> StandardContact:
        """Create contact in Xero.

        Note: Not implemented in Phase 1 (read-only access).

        Args:
            contact: StandardContact to create

        Returns:
            Created contact with platform_id

        Raises:
            NotImplementedError: Phase 1 is read-only
        """
        raise NotImplementedError("Phase 1: Read-only access to Xero")

    def update_contact(
        self,
        contact_id: str,
        contact: StandardContact
    ) -> StandardContact:
        """Update contact in Xero.

        Note: Not implemented in Phase 1 (read-only access).

        Args:
            contact_id: ID of contact to update
            contact: Updated contact data

        Returns:
            Updated contact

        Raises:
            NotImplementedError: Phase 1 is read-only
        """
        raise NotImplementedError("Phase 1: Read-only access to Xero")

    def get_organization_info(self) -> Dict[str, Any]:
        """Get organization information from Xero.

        Returns:
            Dict with organization details
        """
        url = f"{self.XERO_BASE_URL}/Organisation"
        response = self._make_request("GET", url)

        org_data = response.get("Organisations", [{}])[0]

        return {
            "id": org_data.get("OrganisationID"),
            "name": org_data.get("Name"),
            "legal_name": org_data.get("LegalName"),
            "country_code": org_data.get("CountryCode"),
            "tax_number": org_data.get("TaxNumber"),
            "registration_number": org_data.get("RegistrationNumber"),
            "base_currency": org_data.get("BaseCurrency"),
            "status": org_data.get("OrganisationStatus"),
        }

    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status information.

        Returns:
            Dict with sync status
        """
        return {
            "last_sync": None,  # Would track in database
            "next_sync": None,
            "rate_limit_remaining": self._rate_limit_remaining,
            "authenticated": self.authenticate(),
        }

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _get_invoices(
        self,
        start_date: date,
        end_date: date,
        invoice_type: str,
        limit: int
    ) -> List[StandardTransaction]:
        """Fetch invoices from Xero API.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            invoice_type: "ACCREC" or "ACCPAY"
            limit: Maximum to fetch

        Returns:
            List of StandardTransaction objects
        """
        invoices = []
        page = 1

        while len(invoices) < limit:
            # Build where clause for date filtering
            where = f"Type==\"{invoice_type}\" AND InvoiceDate>DateTime({start_date.year},{start_date.month},{start_date.day}) AND InvoiceDate<DateTime({end_date.year},{end_date.month},{end_date.day})"

            url = f"{self.XERO_BASE_URL}/Invoices"
            params = {
                "where": where,
                "page": page,
            }

            response = self._make_request("GET", url, params=params)

            page_invoices = response.get("Invoices", [])
            if not page_invoices:
                break

            for invoice_data in page_invoices:
                if len(invoices) >= limit:
                    break

                txn = self.mapper.map_invoice_to_transaction(invoice_data)
                invoices.append(txn)

            page += 1

        return invoices[:limit]

    def _get_bank_transfers(
        self,
        start_date: date,
        end_date: date,
        limit: int
    ) -> List[StandardTransaction]:
        """Fetch bank transfers from Xero API.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum to fetch

        Returns:
            List of StandardTransaction objects
        """
        transfers = []
        page = 1

        while len(transfers) < limit:
            url = f"{self.XERO_BASE_URL}/BankTransfers"
            params = {"page": page}

            response = self._make_request("GET", url, params=params)

            page_transfers = response.get("BankTransfers", [])
            if not page_transfers:
                break

            for transfer_data in page_transfers:
                if len(transfers) >= limit:
                    break

                txn = self.mapper.map_bank_transfer_to_transaction(transfer_data)
                transfers.append(txn)

            page += 1

        return transfers[:limit]

    def _should_fetch_type(
        self,
        requested_types: Optional[List[TransactionType]],
        check_type: TransactionType
    ) -> bool:
        """Determine if should fetch a transaction type.

        Args:
            requested_types: List of types requested, or None for all
            check_type: Type to check

        Returns:
            True if should fetch this type
        """
        if requested_types is None:
            return True
        return check_type in requested_types

    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Xero API.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to call
            params: Optional query parameters
            data: Optional body data

        Returns:
            Parsed JSON response

        Raises:
            AuthenticationError: If token invalid
            RateLimitError: If rate limited
            APIError: For other API errors
        """
        # Get access token
        access_token = self.auth.get_access_token()
        if not access_token:
            raise AuthenticationError("Not authenticated with Xero")

        # Build headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            self.XERO_TENANT_HEADER: self.auth.get_tenant_id() or "",
            "Accept": "application/json",
        }

        if method in ["POST", "PUT"]:
            headers["Content-Type"] = "application/json"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=30,
            )

            # Track rate limits
            if "X-Rate-Limit-Remaining-Minute" in response.headers:
                self._rate_limit_remaining = int(
                    response.headers["X-Rate-Limit-Remaining-Minute"]
                )

            # Handle HTTP errors
            if response.status_code == 401:
                raise AuthenticationError("Xero authentication failed")
            elif response.status_code == 404:
                raise NotFoundError("Resource not found")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code >= 400:
                # Try to parse Xero error
                try:
                    error_data = response.json()
                    if "ApiException" in error_data:
                        msg = error_data["ApiException"].get("Message", "Unknown error")
                        raise APIError(f"Xero API error: {msg}")
                except:
                    pass

                raise APIError(f"HTTP {response.status_code}: {response.text}")

            return response.json()

        except requests.exceptions.Timeout:
            raise APIError("Request to Xero timed out")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}")
```

**Key Points:**
- ✅ Implements all abstract methods
- ✅ Proper error handling and mapping
- ✅ Rate limit tracking
- ✅ Pagination support
- ✅ Helper methods for code reuse
- ✅ Phase 1 read-only (create/update raise NotImplementedError)

---

## 🧪 Testing Strategy

### Test File Structure

Create `tests/test_accounting_xero.py` with these test classes:

```python
"""Tests for Xero accounting client."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date
from decimal import Decimal

from backend.accounting import (
    TransactionType, ContactType, AccountType,
    StandardTransaction, StandardContact, StandardAccount,
    APIError, AuthenticationError, RateLimitError,
)
from backend.accounting.xero.client import XeroClient
from backend.accounting.xero.mapper import XeroMapper


# Test fixtures for mock data
@pytest.fixture
def mock_credentials():
    """Mock Xero credentials."""
    return {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "redirect_uri": "http://localhost:8000/auth/xero/callback",
    }


@pytest.fixture
def xero_client(mock_credentials):
    """Create XeroClient instance for testing."""
    return XeroClient("org123", mock_credentials)


# Test mapper functions
class TestXeroMapper:
    """Tests for XeroMapper."""

    def test_map_invoice_to_transaction(self):
        """Test mapping Xero invoice to StandardTransaction."""
        # Mock Xero invoice
        xero_invoice = {
            "InvoiceID": "12345678-1234-1234-1234-123456789012",
            "InvoiceNumber": "INV-001",
            "Type": "ACCREC",
            "Status": "AUTHORISED",
            "InvoiceDate": "2025-01-15T00:00:00Z",
            "Total": "1000.00",
            "TaxTotal": "200.00",
            "Contact": {"ContactID": "contact-123"},
            "LineItems": [
                {
                    "Description": "Service",
                    "Quantity": 1,
                    "UnitAmount": "1000.00",
                    "AccountCode": "4000",
                    "TaxType": "Tax on Sales",
                }
            ],
        }

        # Map
        mapper = XeroMapper()
        txn = mapper.map_invoice_to_transaction(xero_invoice)

        # Assertions
        assert txn.id == "12345678-1234-1234-1234-123456789012"
        assert txn.type == TransactionType.INVOICE
        assert txn.reference == "INV-001"
        assert txn.status == "approved"
        assert txn.amount == Decimal("1000.00")
        assert txn.tax_amount == Decimal("200.00")
        assert txn.contact_id == "contact-123"
        assert txn.account_id == "4000"
        assert txn.platform_name == "xero"

    def test_map_contact_to_standard(self):
        """Test mapping Xero contact to StandardContact."""
        xero_contact = {
            "ContactID": "contact-123",
            "Name": "ACME Corp",
            "EmailAddress": "hello@acme.com",
            "Phones": [{"PhoneNumber": "01234567890"}],
            "ContactGroups": ["SUPPLIER"],
            "TaxNumber": "123456789",
            "Addresses": [
                {
                    "AddressType": "STREET",
                    "AddressLine1": "123 Main St",
                    "City": "London",
                    "PostalCode": "SW1A1AA",
                }
            ],
        }

        mapper = XeroMapper()
        contact = mapper.map_contact_to_standard(xero_contact)

        assert contact.id == "contact-123"
        assert contact.name == "ACME Corp"
        assert contact.email == "hello@acme.com"
        assert contact.phone == "01234567890"
        assert contact.type == ContactType.SUPPLIER
        assert contact.tax_id == "123456789"

    def test_map_account_to_standard(self):
        """Test mapping Xero account to StandardAccount."""
        xero_account = {
            "AccountID": "acc-123",
            "Code": "4000",
            "Name": "Sales Income",
            "Type": "REVENUE",
            "TaxType": "Tax on Sales",
        }

        mapper = XeroMapper()
        account = mapper.map_account_to_standard(xero_account)

        assert account.id == "acc-123"
        assert account.code == "4000"
        assert account.name == "Sales Income"
        assert account.type == AccountType.INCOME
        assert account.tax_type == "Tax on Sales"


# Test XeroClient methods
class TestXeroClientAuthentication:
    """Tests for authentication."""

    @patch("backend.accounting.xero.client.requests.post")
    def test_authenticate_success(self, mock_post, xero_client):
        """Test successful authentication."""
        # Mock token response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "token123",
            "refresh_token": "refresh123",
            "expires_in": 1800,
            "Xero-tenant-id": "tenant123",
        }
        mock_post.return_value = mock_response

        # Set up auth with token
        xero_client.auth.tokens = {
            "access_token": "token123",
            "expires_at": datetime.now() + timedelta(hours=1),
        }

        # Test
        assert xero_client.authenticate() is True

    def test_authenticate_not_authenticated(self, xero_client):
        """Test when not authenticated."""
        assert xero_client.authenticate() is False


class TestXeroClientTransactions:
    """Tests for transaction methods."""

    @patch("backend.accounting.xero.client.XeroClient._make_request")
    def test_get_transactions(self, mock_request, xero_client):
        """Test getting transactions."""
        # Set up auth
        xero_client.auth.tokens = {
            "access_token": "token123",
            "tenant_id": "tenant123",
            "expires_at": None,
        }

        # Mock API response
        mock_request.return_value = {
            "Invoices": [
                {
                    "InvoiceID": "inv-123",
                    "InvoiceNumber": "INV-001",
                    "Type": "ACCREC",
                    "Status": "AUTHORISED",
                    "InvoiceDate": "2025-01-15T00:00:00Z",
                    "Total": "1000.00",
                    "TaxTotal": "200.00",
                    "LineItems": [{"AccountCode": "4000"}],
                }
            ]
        }

        # Test
        txns = xero_client.get_transactions(
            date(2025, 1, 1),
            date(2025, 1, 31)
        )

        assert len(txns) > 0
        assert txns[0].type == TransactionType.INVOICE


class TestXeroClientErrors:
    """Tests for error handling."""

    @patch("backend.accounting.xero.client.XeroClient._make_request")
    def test_authentication_error(self, mock_request, xero_client):
        """Test AuthenticationError on 401."""
        mock_request.side_effect = AuthenticationError("Token invalid")

        with pytest.raises(AuthenticationError):
            xero_client._make_request("GET", "https://api.xero.com/...")

    @patch("backend.accounting.xero.client.XeroClient._make_request")
    def test_rate_limit_error(self, mock_request, xero_client):
        """Test RateLimitError on 429."""
        mock_request.side_effect = RateLimitError("Rate limit exceeded")

        with pytest.raises(RateLimitError):
            xero_client._make_request("GET", "https://api.xero.com/...")
```

**Coverage Goals:**
- ✅ 80%+ coverage minimum
- ✅ Test every mapper function
- ✅ Test all error cases
- ✅ Test pagination
- ✅ Test optional field handling

---

## 🆘 Troubleshooting

### Issue: OAuth Token Expired

**Symptom:** `AuthenticationError: Xero authentication failed`

**Solution:** Implement token refresh in `_make_request()`:
```python
try:
    # First attempt
    response = requests.get(...)
except HTTPError as e:
    if e.response.status_code == 401:
        # Token expired, refresh it
        self.auth.refresh_access_token()
        # Retry with new token
        # (in production, limit retries to 1 to avoid infinite loop)
```

### Issue: Rate Limiting

**Symptom:** `RateLimitError: Rate limit exceeded` (status 429)

**Solution:** Implement exponential backoff:
```python
import time

def _make_request_with_backoff(self, ...):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return self._make_request(...)
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_seconds = 2 ** attempt  # 1, 2, 4 seconds
            time.sleep(wait_seconds)
```

### Issue: Pagination Not Working

**Symptom:** Only getting first page of results

**Solution:** Ensure loop continues until no more pages:
```python
page = 1
while True:
    response = self._make_request(
        "GET",
        f"{url}",
        params={"page": page}
    )

    items = response.get("Invoices", [])
    if not items:
        break  # No more pages

    # Process items...
    page += 1
```

### Issue: Missing Fields in Mapping

**Symptom:** `KeyError` when accessing field from response

**Solution:** Always use `.get()` with defaults:
```python
# ❌ Wrong
account_code = invoice["LineItems"][0]["AccountCode"]

# ✅ Correct
line_items = invoice.get("LineItems", [])
account_code = line_items[0].get("AccountCode", "") if line_items else ""
```

---

## ✅ Completion Checklist

### Code Implementation

- [ ] Created `backend/accounting/xero/` directory
- [ ] Created `__init__.py` with exports
- [ ] Implemented `auth.py` (XeroAuth class, ~200 LOC)
- [ ] Implemented `mapper.py` (XeroMapper class, ~300 LOC)
- [ ] Implemented `client.py` (XeroClient class, ~400 LOC)
- [ ] All abstract methods implemented
- [ ] Error handling in place
- [ ] Rate limiting handled
- [ ] Pagination supported

### Testing

- [ ] Created `tests/test_accounting_xero.py`
- [ ] Mapper tests (transaction, contact, account)
- [ ] Client tests (get methods)
- [ ] Error handling tests
- [ ] All tests passing
- [ ] Coverage >= 80%

### Integration

- [ ] XeroClient can be instantiated via factory
- [ ] Works with abstraction layer
- [ ] Compatible with existing database models
- [ ] Can authenticate with demo company (if credentials available)
- [ ] Can fetch transactions, contacts, accounts

### Documentation

- [ ] Code has docstrings
- [ ] Error messages are clear
- [ ] Examples in docstrings
- [ ] Updated project documentation if needed

---

## 🎯 Success Criteria

When complete, you should be able to:

✅ Create XeroClient from factory
```python
from backend.accounting import AccountingClientFactory
client = AccountingClientFactory.create_from_platform(
    platform="xero",
    organization_id="123",
    credentials={...}
)
```

✅ Authenticate with Xero
```python
auth_url, state = client.auth.get_authorization_url()
# User visits auth_url, logs in
# Xero redirects to callback with code
client.auth.exchange_code_for_token(code, state)
assert client.authenticate() is True
```

✅ Fetch transactions
```python
transactions = client.get_transactions(
    date(2025, 1, 1),
    date(2025, 1, 31)
)
assert len(transactions) > 0
assert all(isinstance(t, StandardTransaction) for t in transactions)
```

✅ Fetch contacts and accounts
```python
contacts = client.get_contacts()
accounts = client.get_accounts()
assert len(contacts) > 0
assert len(accounts) > 0
```

✅ Tests passing
```bash
pytest tests/test_accounting_xero.py -v --cov=backend.accounting.xero
# Coverage >= 80%
# All tests passing
```

---

## 📚 Related Documentation

- [XERO_API_GUIDE.md](XERO_API_GUIDE.md) - API reference
- [DATA_MAPPING_SPEC.md](DATA_MAPPING_SPEC.md) - Field mappings
- [ABSTRACTION_LAYER.md](ABSTRACTION_LAYER.md) - Standard models

---

## 🚀 Next Steps (After Week 3)

1. **Week 4:** Implement first mock accounting client
2. **Month 2:** Add QuickBooks adapter
3. **Month 3-4:** Build API endpoints for web frontend
4. **Month 5-6:** AI analysis features

---

**Status:** Ready for Implementation
**Estimated Time:** 4-6 hours
**Difficulty:** Medium (straightforward, lots of boilerplate)

Begin with Step 1: Create package structure!

---
