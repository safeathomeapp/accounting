# FreeAgent Implementation Blueprint

**Status:** Ready for Implementation
**Date:** January 24, 2026
**Purpose:** Step-by-step guide to implementing FreeAgentClient adapter

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & File Structure](#architecture--file-structure)
3. [Implementation Steps](#implementation-steps)
4. [Detailed Code Walkthroughs](#detailed-code-walkthroughs)
5. [Testing Strategy](#testing-strategy)
6. [Troubleshooting](#troubleshooting)
7. [Completion Checklist](#completion-checklist)

---

## Overview

This blueprint guides you through implementing the **FreeAgentClient** - an adapter that bridges FreeAgent API and our abstraction layer.

**What You'll Build:**
- `FreeAgentClient` - Main adapter class extending `AccountingClient`
- `FreeAgentAuth` - OAuth 2.0 authentication handler
- `FreeAgentMapper` - Data transformation from FreeAgent format to standard models
- `test_accounting_freeagent.py` - Comprehensive test suite (80%+ coverage)

**Time Estimate:** 4-6 hours of focused implementation
**Difficulty:** Medium (similar to Xero, with some FreeAgent-specific patterns)

**Golden Rule:** Don't add features beyond the abstraction layer contract. Keep it simple.

---

## Architecture & File Structure

### Directory Structure to Create

```
backend/accounting/freeagent/
├── __init__.py           # Exports (minimal)
├── client.py             # FreeAgentClient main class (~350 LOC)
├── auth.py               # OAuth authentication (~150 LOC)
└── mapper.py             # Data transformation (~250 LOC)
```

### File Dependencies

```
FreeAgentClient (client.py)
  ├── imports AccountingClient, Standard models
  ├── imports FreeAgentAuth for authentication
  ├── imports FreeAgentMapper for data transformation
  ├── makes HTTP requests via requests library
  └── uses environment variables for credentials

FreeAgentAuth (auth.py)
  ├── imports base64 for Basic Auth
  ├── handles token storage/retrieval
  └── manages token refresh

FreeAgentMapper (mapper.py)
  ├── imports Standard models
  ├── imports enumerations
  └── contains pure translation functions (no external calls)
```

### Class Hierarchy

```
                 AccountingClient (ABC)
                        ^
                        |
                        | extends
                        |
                   FreeAgentClient
                        |
                        ├─ uses ─> FreeAgentAuth
                        └─ uses ─> FreeAgentMapper
```

---

## Implementation Steps

### Step 1: Create Package Structure (5 minutes)

#### 1.1: Create directory
```bash
mkdir -p backend/accounting/freeagent
```

#### 1.2: Create `backend/accounting/freeagent/__init__.py`
```python
"""FreeAgent accounting adapter."""

from .client import FreeAgentClient

__all__ = ["FreeAgentClient"]
```

### Step 2: Implement FreeAgentAuth (40 minutes)

Create `backend/accounting/freeagent/auth.py` - OAuth 2.0 handler

**Key Responsibilities:**
- Generate authorization URL for user login
- Exchange authorization code for access token (with Basic Auth)
- Refresh expired tokens
- Store/retrieve tokens securely

See detailed walkthrough: [Step 2 Walkthrough](#step-2-walkthrough-freeagentauth)

### Step 3: Implement FreeAgentMapper (60 minutes)

Create `backend/accounting/freeagent/mapper.py` - Data transformation

**Key Responsibilities:**
- Map FreeAgent Invoice → StandardTransaction
- Map FreeAgent Bill → StandardTransaction
- Map FreeAgent Credit Note → StandardTransaction
- Map FreeAgent Contact → StandardContact
- Map FreeAgent Category → StandardAccount
- Extract IDs from FreeAgent URLs
- Handle all special cases

See detailed walkthrough: [Step 3 Walkthrough](#step-3-walkthrough-freeagentmapper)

### Step 4: Implement FreeAgentClient (90 minutes)

Create `backend/accounting/freeagent/client.py` - Main adapter class

**Key Responsibilities:**
- Extend AccountingClient with all abstract methods
- Implement OAuth flow
- Fetch data from FreeAgent API endpoints
- Transform and return data using mapper
- Handle errors and rate limiting

See detailed walkthrough: [Step 4 Walkthrough](#step-4-walkthrough-freeagentclient)

### Step 5: Write Tests (60 minutes)

Create `tests/test_accounting_freeagent.py` - Comprehensive test suite

**Coverage Areas:**
- OAuth flow (mocked)
- API calls (mocked)
- Data mapping (real - test every mapping)
- Error handling
- Rate limiting
- Integration workflows

See testing strategy: [Testing Strategy](#testing-strategy)

### Step 6: Integration Testing (30 minutes)

Test with actual FreeAgent sandbox if credentials available.

---

## Detailed Code Walkthroughs

### Step 2 Walkthrough: FreeAgentAuth

**File:** `backend/accounting/freeagent/auth.py`

```python
"""OAuth 2.0 authentication for FreeAgent."""

import os
import base64
import secrets
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import requests


# ============================================================================
# CONFIGURATION
# ============================================================================

# FreeAgent OAuth endpoints (Production)
FREEAGENT_AUTH_URL = "https://api.freeagent.com/v2/approve_app"
FREEAGENT_TOKEN_URL = "https://api.freeagent.com/v2/token_endpoint"

# Sandbox endpoints
FREEAGENT_SANDBOX_AUTH_URL = "https://api.sandbox.freeagent.com/v2/approve_app"
FREEAGENT_SANDBOX_TOKEN_URL = "https://api.sandbox.freeagent.com/v2/token_endpoint"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_state() -> str:
    """Generate random state parameter for OAuth."""
    return secrets.token_urlsafe(32)


def encode_basic_auth(client_id: str, client_secret: str) -> str:
    """Encode client credentials for HTTP Basic Auth.

    Args:
        client_id: OAuth client ID
        client_secret: OAuth client secret

    Returns:
        Base64 encoded credentials string
    """
    credentials = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return encoded


# ============================================================================
# FREEAGENTAUTH CLASS
# ============================================================================

class FreeAgentAuth:
    """Handles OAuth 2.0 authentication with FreeAgent."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        use_sandbox: bool = False
    ):
        """Initialize authentication handler.

        Args:
            client_id: FreeAgent OAuth identifier
            client_secret: FreeAgent OAuth secret
            redirect_uri: Callback URL (e.g., http://localhost:8000/auth/freeagent/callback)
            use_sandbox: If True, use sandbox endpoints
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.use_sandbox = use_sandbox

        # Set endpoints based on environment
        if use_sandbox:
            self.auth_url = FREEAGENT_SANDBOX_AUTH_URL
            self.token_url = FREEAGENT_SANDBOX_TOKEN_URL
        else:
            self.auth_url = FREEAGENT_AUTH_URL
            self.token_url = FREEAGENT_TOKEN_URL

        # Token storage (in production, use database)
        self.tokens = {}
        self.state_storage = {}  # Store state during auth flow

    def get_authorization_url(self, state: Optional[str] = None) -> Tuple[str, str]:
        """Generate authorization URL for user to visit.

        Args:
            state: Optional state parameter for security

        Returns:
            Tuple of (authorization_url, state) where state should be stored
        """
        if state is None:
            state = generate_state()

        # Store state for validation
        self.state_storage[state] = {
            "created_at": datetime.now(),
        }

        # Build authorization URL
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "state": state,
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        auth_url = f"{self.auth_url}?{query_string}"

        return auth_url, state

    def exchange_code_for_token(self, code: str, state: str) -> Dict:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from FreeAgent callback
            state: State parameter from authorization URL

        Returns:
            Dict with access_token, refresh_token, expires_in

        Raises:
            ValueError: If state is invalid
        """
        # Validate state
        if state not in self.state_storage:
            raise ValueError(f"Invalid state parameter: {state}")

        state_data = self.state_storage[state]

        # Check if state is too old (>15 minutes - FreeAgent's auth code expiry)
        if datetime.now() - state_data["created_at"] > timedelta(minutes=15):
            del self.state_storage[state]
            raise ValueError("Authorization request expired")

        # Build Basic Auth header
        basic_auth = encode_basic_auth(self.client_id, self.client_secret)

        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        response = requests.post(self.token_url, headers=headers, data=data)
        response.raise_for_status()

        token_data = response.json()

        # Clean up state
        del self.state_storage[state]

        # Store tokens with expiration
        self.tokens = {
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "expires_at": datetime.now() + timedelta(seconds=token_data["expires_in"]),
        }

        return token_data

    def get_access_token(self) -> Optional[str]:
        """Get current access token, refreshing if needed.

        Returns:
            Access token string or None if not authenticated
        """
        if not self.tokens:
            return None

        # Check if token expired (with 5 minute buffer)
        if self.tokens.get("expires_at"):
            if datetime.now() >= self.tokens["expires_at"] - timedelta(minutes=5):
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

        # Build Basic Auth header
        basic_auth = encode_basic_auth(self.client_id, self.client_secret)

        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.tokens["refresh_token"],
        }

        response = requests.post(self.token_url, headers=headers, data=data)
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

    def is_authenticated(self) -> bool:
        """Check if currently authenticated.

        Returns:
            True if has valid token, False otherwise
        """
        return bool(self.get_access_token())

    def revoke_token(self) -> bool:
        """Clear stored tokens (logout).

        Note: FreeAgent doesn't have a revoke endpoint, so we just clear locally.

        Returns:
            True if successful
        """
        self.tokens = {}
        return True
```

**Key Points:**
- HTTP Basic Auth for token requests (different from Xero)
- No PKCE required
- State parameter for security
- Token refresh handling
- Sandbox support

---

### Step 3 Walkthrough: FreeAgentMapper

**File:** `backend/accounting/freeagent/mapper.py`

```python
"""FreeAgent data transformation to standard models."""

from datetime import datetime, date
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
# HELPER FUNCTIONS
# ============================================================================

def extract_id_from_url(url: str) -> str:
    """Extract numeric ID from FreeAgent URL.

    Args:
        url: FreeAgent URL (e.g., "https://api.freeagent.com/v2/invoices/12345")

    Returns:
        ID string (e.g., "12345")
    """
    if not url:
        return ""
    return url.rstrip('/').split('/')[-1]


def parse_freeagent_date(date_string: str) -> Optional[date]:
    """Parse FreeAgent date string.

    Args:
        date_string: Date in YYYY-MM-DD format

    Returns:
        date object or None if invalid
    """
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def parse_freeagent_datetime(datetime_string: str) -> Optional[datetime]:
    """Parse FreeAgent ISO 8601 datetime string.

    Args:
        datetime_string: ISO 8601 datetime (e.g., "2026-01-15T10:30:00Z")

    Returns:
        datetime object or None if invalid
    """
    if not datetime_string:
        return None
    try:
        return datetime.fromisoformat(datetime_string.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


# ============================================================================
# FREEAGENTMAPPER CLASS
# ============================================================================

class FreeAgentMapper:
    """Maps FreeAgent API responses to standard models."""

    # ========================================================================
    # TRANSACTION MAPPING
    # ========================================================================

    @staticmethod
    def map_invoice_to_transaction(invoice: Dict[str, Any]) -> StandardTransaction:
        """Convert FreeAgent Invoice to StandardTransaction.

        Args:
            invoice: Raw FreeAgent invoice dict from API

        Returns:
            StandardTransaction object
        """
        # Extract ID from URL
        invoice_id = extract_id_from_url(invoice.get("url", ""))

        # Parse date
        date_obj = parse_freeagent_date(invoice.get("dated_on", ""))

        # Extract contact ID from URL
        contact_id = None
        if invoice.get("contact"):
            contact_id = extract_id_from_url(invoice["contact"])

        # Get description from first invoice item or reference
        description = invoice.get("reference", "")
        invoice_items = invoice.get("invoice_items", [])
        if invoice_items:
            description = invoice_items[0].get("description", description)

        # Get account from first item's category
        account_id = ""
        if invoice_items:
            category = invoice_items[0].get("category")
            if category:
                account_id = extract_id_from_url(category)

        # Map status
        status = FreeAgentMapper._map_invoice_status(
            invoice.get("status", "Draft")
        )

        # Build metadata
        metadata = {
            "due_on": invoice.get("due_on"),
            "currency": invoice.get("currency", "GBP"),
            "exchange_rate": invoice.get("exchange_rate"),
            "paid_value": invoice.get("paid_value"),
            "due_value": invoice.get("due_value"),
            "ec_status": invoice.get("ec_status"),
            "created_at": invoice.get("created_at"),
            "updated_at": invoice.get("updated_at"),
        }

        # Convert line items
        line_items = []
        for item in invoice_items:
            line_items.append({
                "description": item.get("description", ""),
                "quantity": float(item.get("quantity", 1)),
                "unit_amount": str(item.get("price", "0")),
                "category": extract_id_from_url(item.get("category", "")),
                "sales_tax_rate": item.get("sales_tax_rate"),
            })

        # Create transaction
        transaction = StandardTransaction(
            id=invoice_id,
            type=TransactionType.INVOICE,
            date=date_obj,
            description=description,
            amount=Decimal(str(invoice.get("total_value", "0"))),
            tax_amount=Decimal(str(invoice.get("sales_tax_value", "0"))),
            account_id=account_id,
            contact_id=contact_id,
            reference=invoice.get("reference", ""),
            status=status,
            line_items=line_items,
            platform_id=invoice_id,
            platform_name="freeagent",
            metadata=metadata,
            sync_status=SyncStatus.SYNCED,
        )

        return transaction

    @staticmethod
    def map_bill_to_transaction(bill: Dict[str, Any]) -> StandardTransaction:
        """Convert FreeAgent Bill to StandardTransaction.

        Args:
            bill: Raw FreeAgent bill dict from API

        Returns:
            StandardTransaction object
        """
        # Extract ID from URL
        bill_id = extract_id_from_url(bill.get("url", ""))

        # Parse date
        date_obj = parse_freeagent_date(bill.get("dated_on", ""))

        # Extract contact ID from URL
        contact_id = None
        if bill.get("contact"):
            contact_id = extract_id_from_url(bill["contact"])

        # Get description from first bill item or reference
        description = bill.get("reference", "")
        bill_items = bill.get("bill_items", [])
        if bill_items:
            description = bill_items[0].get("description", description)

        # Get account from first item's category
        account_id = ""
        if bill_items:
            category = bill_items[0].get("category")
            if category:
                account_id = extract_id_from_url(category)

        # Map status
        status = FreeAgentMapper._map_bill_status(
            bill.get("status", "Open")
        )

        # Build metadata
        metadata = {
            "due_on": bill.get("due_on"),
            "currency": bill.get("currency", "GBP"),
            "exchange_rate": bill.get("exchange_rate"),
            "paid_value": bill.get("paid_value"),
            "due_value": bill.get("due_value"),
            "ec_status": bill.get("ec_status"),
            "recurring": bill.get("recurring"),
            "created_at": bill.get("created_at"),
            "updated_at": bill.get("updated_at"),
        }

        # Convert line items
        line_items = []
        for item in bill_items:
            line_items.append({
                "description": item.get("description", ""),
                "quantity": float(item.get("quantity", 1)),
                "unit_amount": str(item.get("total_value", "0")),
                "category": extract_id_from_url(item.get("category", "")),
                "sales_tax_rate": item.get("sales_tax_rate"),
            })

        # Create transaction
        transaction = StandardTransaction(
            id=bill_id,
            type=TransactionType.BILL,
            date=date_obj,
            description=description,
            amount=Decimal(str(bill.get("total_value", "0"))),
            tax_amount=Decimal(str(bill.get("sales_tax_value", "0"))),
            account_id=account_id,
            contact_id=contact_id,
            reference=bill.get("reference", ""),
            status=status,
            line_items=line_items,
            platform_id=bill_id,
            platform_name="freeagent",
            metadata=metadata,
            sync_status=SyncStatus.SYNCED,
        )

        return transaction

    @staticmethod
    def map_credit_note_to_transaction(
        credit_note: Dict[str, Any]
    ) -> StandardTransaction:
        """Convert FreeAgent Credit Note to StandardTransaction.

        Args:
            credit_note: Raw FreeAgent credit note dict from API

        Returns:
            StandardTransaction object
        """
        # Extract ID from URL
        cn_id = extract_id_from_url(credit_note.get("url", ""))

        # Parse date
        date_obj = parse_freeagent_date(credit_note.get("dated_on", ""))

        # Extract contact ID from URL
        contact_id = None
        if credit_note.get("contact"):
            contact_id = extract_id_from_url(credit_note["contact"])

        # Get account from first item's category
        account_id = ""
        cn_items = credit_note.get("credit_note_items", [])
        if cn_items:
            category = cn_items[0].get("category")
            if category:
                account_id = extract_id_from_url(category)

        # Map status
        status = FreeAgentMapper._map_credit_note_status(
            credit_note.get("status", "Draft")
        )

        # Create transaction (amounts already negative in FreeAgent)
        transaction = StandardTransaction(
            id=cn_id,
            type=TransactionType.CREDIT_NOTE,
            date=date_obj,
            description=credit_note.get("reference", "Credit Note"),
            amount=Decimal(str(credit_note.get("total_value", "0"))),
            tax_amount=Decimal(str(credit_note.get("sales_tax_value", "0"))),
            account_id=account_id,
            contact_id=contact_id,
            reference=credit_note.get("reference", ""),
            status=status,
            line_items=[],
            platform_id=cn_id,
            platform_name="freeagent",
            metadata={},
            sync_status=SyncStatus.SYNCED,
        )

        return transaction

    # ========================================================================
    # CONTACT MAPPING
    # ========================================================================

    @staticmethod
    def map_contact_to_standard(
        contact: Dict[str, Any],
        contact_type: Optional[ContactType] = None
    ) -> StandardContact:
        """Convert FreeAgent Contact to StandardContact.

        Args:
            contact: Raw FreeAgent contact dict from API
            contact_type: Optional type override (CUSTOMER or SUPPLIER)

        Returns:
            StandardContact object
        """
        # Extract ID from URL
        contact_id = extract_id_from_url(contact.get("url", ""))

        # Build name from organisation or first/last name
        name = contact.get("organisation_name", "")
        if not name:
            first_name = contact.get("first_name", "")
            last_name = contact.get("last_name", "")
            name = f"{first_name} {last_name}".strip()

        # Build address string
        address_parts = [
            contact.get("address1"),
            contact.get("address2"),
            contact.get("address3"),
            contact.get("town"),
            contact.get("region"),
            contact.get("postcode"),
            contact.get("country"),
        ]
        address = ", ".join(filter(None, address_parts))

        # Determine contact type if not provided
        if contact_type is None:
            # Default to CUSTOMER - FreeAgent doesn't have explicit types
            # Caller should use view=clients or view=suppliers to filter
            contact_type = ContactType.CUSTOMER

        # Build metadata
        metadata = {
            "organisation_name": contact.get("organisation_name"),
            "first_name": contact.get("first_name"),
            "last_name": contact.get("last_name"),
            "mobile": contact.get("mobile"),
            "locale": contact.get("locale"),
            "account_balance": contact.get("account_balance"),
            "status": contact.get("status"),
            "active_projects_count": contact.get("active_projects_count"),
            "created_at": contact.get("created_at"),
            "updated_at": contact.get("updated_at"),
        }

        contact_obj = StandardContact(
            id=contact_id,
            type=contact_type,
            name=name,
            email=contact.get("email"),
            phone=contact.get("phone_number"),
            address=address,
            tax_id=contact.get("sales_tax_registration_number"),
            currency="GBP",  # Default for UK
            platform_id=contact_id,
            platform_name="freeagent",
            metadata=metadata,
        )

        return contact_obj

    # ========================================================================
    # ACCOUNT MAPPING (Categories)
    # ========================================================================

    @staticmethod
    def map_category_to_account(category: Dict[str, Any]) -> StandardAccount:
        """Convert FreeAgent Category to StandardAccount.

        Args:
            category: Raw FreeAgent category dict from API

        Returns:
            StandardAccount object
        """
        nominal_code = category.get("nominal_code", "")

        # Map account type from nominal code range
        account_type = FreeAgentMapper._map_category_type(nominal_code)

        # Build metadata
        metadata = {
            "group_description": category.get("group_description"),
            "allowable_for_tax": category.get("allowable_for_tax"),
            "tax_reporting_name": category.get("tax_reporting_name"),
        }

        account_obj = StandardAccount(
            id=nominal_code,
            code=nominal_code,
            name=category.get("description", ""),
            type=account_type,
            currency="GBP",
            tax_type=category.get("auto_sales_tax_rate"),
            platform_id=nominal_code,
            platform_name="freeagent",
            metadata=metadata,
        )

        return account_obj

    # ========================================================================
    # HELPER FUNCTIONS
    # ========================================================================

    @staticmethod
    def _map_invoice_status(freeagent_status: str) -> str:
        """Map FreeAgent invoice status to standard status.

        Args:
            freeagent_status: FreeAgent status string

        Returns:
            Standard status string
        """
        status_map = {
            "Draft": "draft",
            "Scheduled To Email": "scheduled",
            "Open": "approved",
            "Zero Value": "approved",
            "Overdue": "overdue",
            "Paid": "paid",
            "Overpaid": "paid",
            "Refunded": "refunded",
            "Written-off": "written_off",
            "Part written-off": "partial_written_off",
        }
        return status_map.get(freeagent_status, "approved")

    @staticmethod
    def _map_bill_status(freeagent_status: str) -> str:
        """Map FreeAgent bill status to standard status.

        Args:
            freeagent_status: FreeAgent status string

        Returns:
            Standard status string
        """
        status_map = {
            "Zero Value": "approved",
            "Open": "approved",
            "Paid": "paid",
            "Overdue": "overdue",
            "Refunded": "refunded",
        }
        return status_map.get(freeagent_status, "approved")

    @staticmethod
    def _map_credit_note_status(freeagent_status: str) -> str:
        """Map FreeAgent credit note status to standard status.

        Args:
            freeagent_status: FreeAgent status string

        Returns:
            Standard status string
        """
        status_map = {
            "Draft": "draft",
            "Open": "approved",
            "Overdue": "overdue",
            "Refunded": "refunded",
            "Written-off": "written_off",
        }
        return status_map.get(freeagent_status, "approved")

    @staticmethod
    def _map_category_type(nominal_code: str) -> AccountType:
        """Map FreeAgent nominal code to account type.

        Args:
            nominal_code: FreeAgent nominal code string

        Returns:
            AccountType enum value
        """
        try:
            code = int(nominal_code)
        except (ValueError, TypeError):
            return AccountType.EXPENSE  # Default

        # FreeAgent nominal code ranges
        if 1 <= code <= 49:
            return AccountType.INCOME
        elif 96 <= code <= 199:
            return AccountType.EXPENSE  # Cost of Sales
        elif 200 <= code <= 399:
            return AccountType.EXPENSE  # Admin Expenses
        elif 671 <= code <= 720:
            return AccountType.ASSET  # Current Assets
        elif 731 <= code <= 780:
            return AccountType.LIABILITY
        elif 921 <= code <= 960:
            return AccountType.EQUITY
        else:
            return AccountType.EXPENSE  # Default
```

**Key Points:**
- URL ID extraction helper
- Date parsing for FreeAgent formats
- Nominal code range mapping for account types
- Contact type inference (uses caller context)
- Status mapping for all transaction types

---

### Step 4 Walkthrough: FreeAgentClient

**File:** `backend/accounting/freeagent/client.py`

```python
"""FreeAgent accounting adapter implementation."""

import os
from typing import List, Optional, Dict, Any
from datetime import date
from urllib.parse import urlencode

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

from .auth import FreeAgentAuth
from .mapper import FreeAgentMapper, extract_id_from_url


# ============================================================================
# FREEAGENTCLIENT CLASS
# ============================================================================

class FreeAgentClient(AccountingClient):
    """FreeAgent adapter implementing AccountingClient interface."""

    PLATFORM_NAME = "freeagent"

    # FreeAgent API configuration
    FREEAGENT_BASE_URL = "https://api.freeagent.com/v2"
    FREEAGENT_SANDBOX_URL = "https://api.sandbox.freeagent.com/v2"

    def __init__(self, organization_id: str, credentials: Dict[str, Any]):
        """Initialize FreeAgentClient.

        Args:
            organization_id: Organization ID from database
            credentials: Dict with keys:
                - client_id: FreeAgent OAuth identifier
                - client_secret: FreeAgent OAuth secret
                - redirect_uri: OAuth callback URL
                - access_token: (optional) Existing access token
                - refresh_token: (optional) Existing refresh token
                - use_sandbox: (optional) Use sandbox environment

        Raises:
            ValidationError: If credentials invalid
        """
        super().__init__(organization_id, credentials)

        # Determine environment
        self.use_sandbox = credentials.get("use_sandbox", False)
        self.base_url = (
            self.FREEAGENT_SANDBOX_URL if self.use_sandbox
            else self.FREEAGENT_BASE_URL
        )

        # Initialize auth
        self.auth = FreeAgentAuth(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            redirect_uri=credentials.get(
                "redirect_uri",
                "http://localhost:8000/auth/freeagent/callback"
            ),
            use_sandbox=self.use_sandbox,
        )

        # Restore tokens if provided
        if credentials.get("access_token"):
            self.auth.tokens = {
                "access_token": credentials["access_token"],
                "refresh_token": credentials.get("refresh_token"),
                "expires_at": None,  # Assume valid
            }

        # Initialize mapper
        self.mapper = FreeAgentMapper()

        # Rate limit tracking
        self._rate_limit_remaining = 120

    def _validate_credentials(self) -> None:
        """Validate that required credentials are present.

        Raises:
            ValidationError: If credentials missing or invalid
        """
        required = ["client_id", "client_secret"]
        for key in required:
            if key not in self.credentials:
                raise ValidationError(f"Missing credential: {key}")

    def authenticate(self) -> bool:
        """Check if currently authenticated.

        Returns:
            True if has valid access token
        """
        try:
            return self.auth.is_authenticated()
        except Exception:
            return False

    # ========================================================================
    # TRANSACTION METHODS
    # ========================================================================

    def get_transactions(
        self,
        start_date: date,
        end_date: date,
        transaction_types: Optional[List[TransactionType]] = None,
        limit: int = 1000,
    ) -> List[StandardTransaction]:
        """Get transactions from FreeAgent.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            transaction_types: Optional list of types to include
            limit: Maximum transactions to return

        Returns:
            List of StandardTransaction objects
        """
        transactions = []

        # Fetch invoices
        if self._should_fetch_type(transaction_types, TransactionType.INVOICE):
            invoices = self._get_invoices(start_date, end_date, limit)
            transactions.extend(invoices)

        # Fetch bills
        if self._should_fetch_type(transaction_types, TransactionType.BILL):
            bills = self._get_bills(start_date, end_date, limit)
            transactions.extend(bills)

        # Fetch credit notes
        if self._should_fetch_type(transaction_types, TransactionType.CREDIT_NOTE):
            credit_notes = self._get_credit_notes(start_date, end_date, limit)
            transactions.extend(credit_notes)

        return transactions[:limit]

    def get_transaction(self, transaction_id: str) -> Optional[StandardTransaction]:
        """Get single transaction by ID.

        Args:
            transaction_id: Transaction ID

        Returns:
            StandardTransaction or None if not found
        """
        # Try invoices first
        try:
            url = f"{self.base_url}/invoices/{transaction_id}"
            response = self._make_request("GET", url)
            if response.get("invoice"):
                return self.mapper.map_invoice_to_transaction(response["invoice"])
        except NotFoundError:
            pass

        # Try bills
        try:
            url = f"{self.base_url}/bills/{transaction_id}"
            response = self._make_request("GET", url)
            if response.get("bill"):
                return self.mapper.map_bill_to_transaction(response["bill"])
        except NotFoundError:
            pass

        # Try credit notes
        try:
            url = f"{self.base_url}/credit_notes/{transaction_id}"
            response = self._make_request("GET", url)
            if response.get("credit_note"):
                return self.mapper.map_credit_note_to_transaction(
                    response["credit_note"]
                )
        except NotFoundError:
            pass

        return None

    def create_transaction(
        self,
        transaction: StandardTransaction
    ) -> StandardTransaction:
        """Create transaction in FreeAgent.

        Note: Not implemented in Phase 1 (read-only access).

        Raises:
            NotImplementedError: Phase 1 is read-only
        """
        raise NotImplementedError("Phase 1: Read-only access to FreeAgent")

    def update_transaction(
        self,
        transaction_id: str,
        transaction: StandardTransaction
    ) -> StandardTransaction:
        """Update transaction in FreeAgent.

        Note: Not implemented in Phase 1 (read-only access).

        Raises:
            NotImplementedError: Phase 1 is read-only
        """
        raise NotImplementedError("Phase 1: Read-only access to FreeAgent")

    # ========================================================================
    # ACCOUNT METHODS
    # ========================================================================

    def get_accounts(
        self,
        account_types: Optional[List[str]] = None
    ) -> List[StandardAccount]:
        """Get categories (accounts) from FreeAgent.

        Args:
            account_types: Optional list of types to filter

        Returns:
            List of StandardAccount objects
        """
        url = f"{self.base_url}/categories"
        response = self._make_request("GET", url)

        accounts = []
        for category_data in response.get("categories", []):
            account = self.mapper.map_category_to_account(category_data)

            # Filter by type if specified
            if account_types and account.type.value not in account_types:
                continue

            accounts.append(account)

        return accounts

    def get_account(self, account_id: str) -> Optional[StandardAccount]:
        """Get single account by ID (nominal code).

        Args:
            account_id: Account ID (nominal code)

        Returns:
            StandardAccount or None if not found
        """
        try:
            url = f"{self.base_url}/categories/{account_id}"
            response = self._make_request("GET", url)

            if response.get("category"):
                return self.mapper.map_category_to_account(response["category"])
        except NotFoundError:
            pass

        return None

    # ========================================================================
    # CONTACT METHODS
    # ========================================================================

    def get_contacts(
        self,
        contact_types: Optional[List[ContactType]] = None,
        limit: int = 1000
    ) -> List[StandardContact]:
        """Get contacts from FreeAgent.

        Args:
            contact_types: Optional list of types to filter
            limit: Maximum contacts to return

        Returns:
            List of StandardContact objects
        """
        contacts = []

        # Determine which views to fetch
        views_to_fetch = []
        if contact_types is None:
            views_to_fetch = [("clients", ContactType.CUSTOMER)]
        else:
            if ContactType.CUSTOMER in contact_types:
                views_to_fetch.append(("clients", ContactType.CUSTOMER))
            if ContactType.SUPPLIER in contact_types:
                views_to_fetch.append(("suppliers", ContactType.SUPPLIER))

        for view, contact_type in views_to_fetch:
            if len(contacts) >= limit:
                break

            page = 1
            while len(contacts) < limit:
                url = f"{self.base_url}/contacts"
                params = {
                    "view": view,
                    "page": page,
                    "per_page": min(100, limit - len(contacts)),
                }

                response = self._make_request("GET", url, params=params)

                page_contacts = response.get("contacts", [])
                if not page_contacts:
                    break

                for contact_data in page_contacts:
                    if len(contacts) >= limit:
                        break

                    contact = self.mapper.map_contact_to_standard(
                        contact_data,
                        contact_type=contact_type
                    )
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
            url = f"{self.base_url}/contacts/{contact_id}"
            response = self._make_request("GET", url)

            if response.get("contact"):
                return self.mapper.map_contact_to_standard(response["contact"])
        except NotFoundError:
            pass

        return None

    def create_contact(self, contact: StandardContact) -> StandardContact:
        """Create contact in FreeAgent.

        Note: Not implemented in Phase 1 (read-only access).

        Raises:
            NotImplementedError: Phase 1 is read-only
        """
        raise NotImplementedError("Phase 1: Read-only access to FreeAgent")

    def update_contact(
        self,
        contact_id: str,
        contact: StandardContact
    ) -> StandardContact:
        """Update contact in FreeAgent.

        Note: Not implemented in Phase 1 (read-only access).

        Raises:
            NotImplementedError: Phase 1 is read-only
        """
        raise NotImplementedError("Phase 1: Read-only access to FreeAgent")

    # ========================================================================
    # ORGANIZATION METHODS
    # ========================================================================

    def get_organization_info(self) -> Dict[str, Any]:
        """Get company information from FreeAgent.

        Returns:
            Dict with organization details
        """
        url = f"{self.base_url}/company"
        response = self._make_request("GET", url)

        company = response.get("company", {})

        return {
            "id": extract_id_from_url(company.get("url", "")),
            "name": company.get("name"),
            "subdomain": company.get("subdomain"),
            "type": company.get("type"),
            "country_code": "GB",  # FreeAgent is UK-only
            "currency": company.get("currency", "GBP"),
            "tax_number": company.get("sales_tax_registration_number"),
            "registration_number": company.get("company_registration_number"),
            "start_date": company.get("company_start_date"),
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
        limit: int
    ) -> List[StandardTransaction]:
        """Fetch invoices from FreeAgent API.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum to fetch

        Returns:
            List of StandardTransaction objects
        """
        invoices = []
        page = 1

        while len(invoices) < limit:
            url = f"{self.base_url}/invoices"
            params = {
                "view": "all",
                "nested_invoice_items": "true",
                "updated_since": f"{start_date}T00:00:00Z",
                "page": page,
                "per_page": min(100, limit - len(invoices)),
            }

            response = self._make_request("GET", url, params=params)

            page_invoices = response.get("invoices", [])
            if not page_invoices:
                break

            for invoice_data in page_invoices:
                if len(invoices) >= limit:
                    break

                # Filter by date range
                invoice_date = invoice_data.get("dated_on", "")
                if invoice_date:
                    inv_date = date.fromisoformat(invoice_date)
                    if inv_date < start_date or inv_date > end_date:
                        continue

                txn = self.mapper.map_invoice_to_transaction(invoice_data)
                invoices.append(txn)

            page += 1

        return invoices[:limit]

    def _get_bills(
        self,
        start_date: date,
        end_date: date,
        limit: int
    ) -> List[StandardTransaction]:
        """Fetch bills from FreeAgent API.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum to fetch

        Returns:
            List of StandardTransaction objects
        """
        bills = []
        page = 1

        while len(bills) < limit:
            url = f"{self.base_url}/bills"
            params = {
                "from_date": start_date.isoformat(),
                "to_date": end_date.isoformat(),
                "nested_bill_items": "true",
                "page": page,
                "per_page": min(100, limit - len(bills)),
            }

            response = self._make_request("GET", url, params=params)

            page_bills = response.get("bills", [])
            if not page_bills:
                break

            for bill_data in page_bills:
                if len(bills) >= limit:
                    break

                txn = self.mapper.map_bill_to_transaction(bill_data)
                bills.append(txn)

            page += 1

        return bills[:limit]

    def _get_credit_notes(
        self,
        start_date: date,
        end_date: date,
        limit: int
    ) -> List[StandardTransaction]:
        """Fetch credit notes from FreeAgent API.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum to fetch

        Returns:
            List of StandardTransaction objects
        """
        credit_notes = []
        page = 1

        while len(credit_notes) < limit:
            url = f"{self.base_url}/credit_notes"
            params = {
                "updated_since": f"{start_date}T00:00:00Z",
                "nested_credit_note_items": "true",
                "page": page,
                "per_page": min(100, limit - len(credit_notes)),
            }

            response = self._make_request("GET", url, params=params)

            page_notes = response.get("credit_notes", [])
            if not page_notes:
                break

            for cn_data in page_notes:
                if len(credit_notes) >= limit:
                    break

                # Filter by date range
                cn_date = cn_data.get("dated_on", "")
                if cn_date:
                    note_date = date.fromisoformat(cn_date)
                    if note_date < start_date or note_date > end_date:
                        continue

                txn = self.mapper.map_credit_note_to_transaction(cn_data)
                credit_notes.append(txn)

            page += 1

        return credit_notes[:limit]

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
        """Make HTTP request to FreeAgent API.

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
            NotFoundError: If resource not found
            APIError: For other API errors
        """
        # Get access token
        access_token = self.auth.get_access_token()
        if not access_token:
            raise AuthenticationError("Not authenticated with FreeAgent")

        # Build headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "User-Agent": "AccountingPlatform/1.0",
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

            # Handle HTTP errors
            if response.status_code == 401:
                raise AuthenticationError("FreeAgent authentication failed")
            elif response.status_code == 404:
                raise NotFoundError("Resource not found")
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise RateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds"
                )
            elif response.status_code >= 400:
                # Try to parse FreeAgent error
                try:
                    error_data = response.json()
                    errors = error_data.get("errors", [])
                    if errors:
                        msg = errors[0].get("message", "Unknown error")
                        raise APIError(f"FreeAgent API error: {msg}")
                except Exception:
                    pass

                raise APIError(f"HTTP {response.status_code}: {response.text}")

            return response.json()

        except requests.exceptions.Timeout:
            raise APIError("Request to FreeAgent timed out")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}")
```

**Key Points:**
- Implements all abstract methods
- Sandbox support via `use_sandbox` credential
- User-Agent header included
- Pagination handling
- Rate limit error handling with Retry-After
- Contact type inference via view parameter

---

## Testing Strategy

### Test File Structure

Create `tests/test_accounting_freeagent.py`:

```python
"""Tests for FreeAgent accounting client."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date, datetime, timedelta
from decimal import Decimal

from backend.accounting import (
    TransactionType, ContactType, AccountType,
    StandardTransaction, StandardContact, StandardAccount,
    APIError, AuthenticationError, RateLimitError,
)
from backend.accounting.freeagent.client import FreeAgentClient
from backend.accounting.freeagent.mapper import FreeAgentMapper, extract_id_from_url
from backend.accounting.freeagent.auth import FreeAgentAuth, encode_basic_auth


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_credentials():
    """Mock FreeAgent credentials."""
    return {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "redirect_uri": "http://localhost:8000/auth/freeagent/callback",
        "use_sandbox": True,
    }


@pytest.fixture
def freeagent_client(mock_credentials):
    """Create FreeAgentClient instance for testing."""
    return FreeAgentClient("org123", mock_credentials)


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestHelperFunctions:
    """Tests for helper functions."""

    def test_extract_id_from_url(self):
        """Test URL ID extraction."""
        url = "https://api.freeagent.com/v2/invoices/12345"
        assert extract_id_from_url(url) == "12345"

    def test_extract_id_from_url_trailing_slash(self):
        """Test URL ID extraction with trailing slash."""
        url = "https://api.freeagent.com/v2/invoices/12345/"
        assert extract_id_from_url(url) == "12345"

    def test_extract_id_from_empty_url(self):
        """Test URL ID extraction with empty string."""
        assert extract_id_from_url("") == ""

    def test_encode_basic_auth(self):
        """Test Basic Auth encoding."""
        encoded = encode_basic_auth("client_id", "client_secret")
        assert encoded == "Y2xpZW50X2lkOmNsaWVudF9zZWNyZXQ="


# ============================================================================
# MAPPER TESTS
# ============================================================================

class TestFreeAgentMapper:
    """Tests for FreeAgentMapper."""

    def test_map_invoice_to_transaction(self):
        """Test mapping FreeAgent invoice to StandardTransaction."""
        freeagent_invoice = {
            "url": "https://api.freeagent.com/v2/invoices/12345",
            "contact": "https://api.freeagent.com/v2/contacts/67890",
            "dated_on": "2026-01-15",
            "due_on": "2026-02-15",
            "reference": "INV-001",
            "currency": "GBP",
            "net_value": "1000.00",
            "sales_tax_value": "200.00",
            "total_value": "1200.00",
            "status": "Open",
            "invoice_items": [
                {
                    "description": "Consulting services",
                    "quantity": "10",
                    "price": "100.00",
                    "category": "https://api.freeagent.com/v2/categories/001",
                }
            ],
        }

        mapper = FreeAgentMapper()
        txn = mapper.map_invoice_to_transaction(freeagent_invoice)

        assert txn.id == "12345"
        assert txn.type == TransactionType.INVOICE
        assert txn.reference == "INV-001"
        assert txn.status == "approved"
        assert txn.amount == Decimal("1200.00")
        assert txn.tax_amount == Decimal("200.00")
        assert txn.contact_id == "67890"
        assert txn.account_id == "001"
        assert txn.platform_name == "freeagent"

    def test_map_bill_to_transaction(self):
        """Test mapping FreeAgent bill to StandardTransaction."""
        freeagent_bill = {
            "url": "https://api.freeagent.com/v2/bills/54321",
            "contact": "https://api.freeagent.com/v2/contacts/11111",
            "dated_on": "2026-01-10",
            "due_on": "2026-02-10",
            "reference": "BILL-001",
            "total_value": "500.00",
            "sales_tax_value": "100.00",
            "status": "Open",
            "bill_items": [],
        }

        mapper = FreeAgentMapper()
        txn = mapper.map_bill_to_transaction(freeagent_bill)

        assert txn.id == "54321"
        assert txn.type == TransactionType.BILL
        assert txn.amount == Decimal("500.00")
        assert txn.contact_id == "11111"

    def test_map_contact_to_standard_organisation(self):
        """Test mapping contact with organisation name."""
        freeagent_contact = {
            "url": "https://api.freeagent.com/v2/contacts/12345",
            "organisation_name": "ACME Corp",
            "email": "hello@acme.com",
            "phone_number": "020 1234 5678",
            "address1": "123 Main Street",
            "town": "London",
            "postcode": "SW1A 1AA",
            "country": "United Kingdom",
            "sales_tax_registration_number": "GB123456789",
        }

        mapper = FreeAgentMapper()
        contact = mapper.map_contact_to_standard(
            freeagent_contact,
            contact_type=ContactType.CUSTOMER
        )

        assert contact.id == "12345"
        assert contact.name == "ACME Corp"
        assert contact.email == "hello@acme.com"
        assert contact.type == ContactType.CUSTOMER
        assert contact.tax_id == "GB123456789"

    def test_map_contact_to_standard_individual(self):
        """Test mapping contact with first/last name."""
        freeagent_contact = {
            "url": "https://api.freeagent.com/v2/contacts/12345",
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
        }

        mapper = FreeAgentMapper()
        contact = mapper.map_contact_to_standard(freeagent_contact)

        assert contact.name == "John Smith"

    def test_map_category_to_account_income(self):
        """Test mapping income category."""
        freeagent_category = {
            "url": "https://api.freeagent.com/v2/categories/001",
            "description": "Sales",
            "nominal_code": "001",
            "group_description": "Income",
            "auto_sales_tax_rate": "Standard Rate",
        }

        mapper = FreeAgentMapper()
        account = mapper.map_category_to_account(freeagent_category)

        assert account.id == "001"
        assert account.code == "001"
        assert account.name == "Sales"
        assert account.type == AccountType.INCOME

    def test_map_category_to_account_expense(self):
        """Test mapping expense category."""
        freeagent_category = {
            "url": "https://api.freeagent.com/v2/categories/200",
            "description": "Office Supplies",
            "nominal_code": "200",
        }

        mapper = FreeAgentMapper()
        account = mapper.map_category_to_account(freeagent_category)

        assert account.type == AccountType.EXPENSE


# ============================================================================
# AUTH TESTS
# ============================================================================

class TestFreeAgentAuth:
    """Tests for FreeAgentAuth."""

    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        auth = FreeAgentAuth(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        url, state = auth.get_authorization_url()

        assert "approve_app" in url
        assert "client_id=test_id" in url
        assert "response_type=code" in url
        assert state in url

    def test_get_authorization_url_sandbox(self):
        """Test sandbox authorization URL."""
        auth = FreeAgentAuth(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
            use_sandbox=True,
        )

        url, _ = auth.get_authorization_url()

        assert "sandbox.freeagent.com" in url

    @patch("backend.accounting.freeagent.auth.requests.post")
    def test_exchange_code_for_token(self, mock_post):
        """Test token exchange."""
        auth = FreeAgentAuth(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        # Generate state first
        _, state = auth.get_authorization_url()

        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "token123",
            "refresh_token": "refresh123",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        # Exchange
        result = auth.exchange_code_for_token("code123", state)

        assert result["access_token"] == "token123"
        assert auth.tokens["access_token"] == "token123"


# ============================================================================
# CLIENT TESTS
# ============================================================================

class TestFreeAgentClientAuthentication:
    """Tests for client authentication."""

    def test_authenticate_not_authenticated(self, freeagent_client):
        """Test when not authenticated."""
        assert freeagent_client.authenticate() is False

    def test_authenticate_with_token(self, mock_credentials):
        """Test when token provided."""
        mock_credentials["access_token"] = "token123"
        client = FreeAgentClient("org123", mock_credentials)

        assert client.authenticate() is True


class TestFreeAgentClientTransactions:
    """Tests for transaction methods."""

    @patch("backend.accounting.freeagent.client.FreeAgentClient._make_request")
    def test_get_transactions(self, mock_request, freeagent_client):
        """Test getting transactions."""
        # Set up auth
        freeagent_client.auth.tokens = {
            "access_token": "token123",
            "expires_at": datetime.now() + timedelta(hours=1),
        }

        # Mock API responses
        mock_request.side_effect = [
            # Invoices response
            {
                "invoices": [
                    {
                        "url": "https://api.freeagent.com/v2/invoices/123",
                        "dated_on": "2026-01-15",
                        "total_value": "1000.00",
                        "sales_tax_value": "200.00",
                        "status": "Open",
                        "invoice_items": [],
                    }
                ]
            },
            # Empty second page
            {"invoices": []},
            # Bills response
            {"bills": []},
            # Credit notes response
            {"credit_notes": []},
        ]

        txns = freeagent_client.get_transactions(
            date(2026, 1, 1),
            date(2026, 1, 31)
        )

        assert len(txns) >= 1
        assert txns[0].type == TransactionType.INVOICE


class TestFreeAgentClientErrors:
    """Tests for error handling."""

    def test_make_request_not_authenticated(self, freeagent_client):
        """Test request without authentication."""
        with pytest.raises(AuthenticationError):
            freeagent_client._make_request("GET", "https://api.freeagent.com/v2/invoices")

    @patch("backend.accounting.freeagent.client.requests.request")
    def test_rate_limit_error(self, mock_request, freeagent_client):
        """Test rate limit handling."""
        freeagent_client.auth.tokens = {
            "access_token": "token123",
            "expires_at": datetime.now() + timedelta(hours=1),
        }

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_request.return_value = mock_response

        with pytest.raises(RateLimitError):
            freeagent_client._make_request(
                "GET",
                "https://api.freeagent.com/v2/invoices"
            )
```

**Coverage Goals:**
- 80%+ coverage minimum
- Test every mapper function
- Test all error cases
- Test pagination
- Test optional field handling

---

## Troubleshooting

### Issue: Basic Auth Not Working

**Symptom:** `401 Unauthorized` on token exchange

**Solution:** Ensure correct encoding:
```python
import base64
credentials = f"{client_id}:{client_secret}"
encoded = base64.b64encode(credentials.encode()).decode()
headers = {"Authorization": f"Basic {encoded}"}
```

### Issue: Rate Limiting

**Symptom:** `429 Too Many Requests`

**Solution:** Check `Retry-After` header and implement backoff:
```python
if response.status_code == 429:
    retry_after = int(response.headers.get("Retry-After", 60))
    time.sleep(retry_after)
    # Retry request
```

### Issue: Pagination Not Working

**Symptom:** Only getting 25 items

**Solution:** Use `page` and `per_page` parameters:
```python
params = {
    "page": 1,
    "per_page": 100,  # Max 100
}
```

### Issue: Missing Line Items

**Symptom:** Invoice items not included

**Solution:** Add `nested_invoice_items=true`:
```python
params = {
    "nested_invoice_items": "true",
}
```

### Issue: URL ID Extraction Failing

**Symptom:** Empty or incorrect IDs

**Solution:** Handle trailing slashes and empty strings:
```python
def extract_id_from_url(url: str) -> str:
    if not url:
        return ""
    return url.rstrip('/').split('/')[-1]
```

---

## Completion Checklist

### Code Implementation

- [ ] Created `backend/accounting/freeagent/` directory
- [ ] Created `__init__.py` with exports
- [ ] Implemented `auth.py` (FreeAgentAuth class, ~150 LOC)
- [ ] Implemented `mapper.py` (FreeAgentMapper class, ~250 LOC)
- [ ] Implemented `client.py` (FreeAgentClient class, ~350 LOC)
- [ ] All abstract methods implemented
- [ ] Error handling in place
- [ ] Rate limiting handled
- [ ] Pagination supported
- [ ] Sandbox support included

### Testing

- [ ] Created `tests/test_accounting_freeagent.py`
- [ ] Mapper tests (invoice, bill, credit note, contact, category)
- [ ] Auth tests (URL generation, token exchange)
- [ ] Client tests (get methods)
- [ ] Error handling tests
- [ ] All tests passing
- [ ] Coverage >= 80%

### Integration

- [ ] FreeAgentClient can be instantiated via factory
- [ ] Works with abstraction layer
- [ ] Compatible with existing database models
- [ ] Can authenticate with sandbox (when available)
- [ ] Can fetch transactions, contacts, accounts

### Documentation

- [ ] Code has docstrings
- [ ] Error messages are clear
- [ ] Examples in docstrings
- [ ] Updated project documentation if needed

---

## Success Criteria

When complete, you should be able to:

**Create FreeAgentClient from factory**
```python
from backend.accounting import AccountingClientFactory
client = AccountingClientFactory.create_from_platform(
    platform="freeagent",
    organization_id="123",
    credentials={
        "client_id": "...",
        "client_secret": "...",
        "use_sandbox": True,
    }
)
```

**Authenticate with FreeAgent**
```python
auth_url, state = client.auth.get_authorization_url()
# User visits auth_url, logs in
# FreeAgent redirects to callback with code
client.auth.exchange_code_for_token(code, state)
assert client.authenticate() is True
```

**Fetch transactions**
```python
transactions = client.get_transactions(
    date(2026, 1, 1),
    date(2026, 1, 31)
)
assert len(transactions) > 0
assert all(isinstance(t, StandardTransaction) for t in transactions)
```

**Fetch contacts and accounts**
```python
contacts = client.get_contacts()
accounts = client.get_accounts()
assert len(contacts) > 0
assert len(accounts) > 0
```

**Tests passing**
```bash
pytest tests/test_accounting_freeagent.py -v --cov=backend.accounting.freeagent
# Coverage >= 80%
# All tests passing
```

---

## Factory Integration

Add one line to `backend/accounting/factory.py`:

```python
PLATFORM_CLIENTS = {
    "xero": "backend.accounting.xero.client.XeroClient",
    "quickbooks": "backend.accounting.quickbooks.client.QuickBooksClient",
    "freeagent": "backend.accounting.freeagent.client.FreeAgentClient",
    "mock": "backend.accounting.mock.client.MockClient",
}
```

---

## Related Documentation

- [FREEAGENT_API_GUIDE.md](FREEAGENT_API_GUIDE.md) - API reference
- [DATA_MAPPING_SPEC.md](DATA_MAPPING_SPEC.md) - Field mappings
- [ABSTRACTION_LAYER.md](../architecture/abstraction_layer.md) - Standard models

---

**Status:** Ready for Implementation (pending sandbox credentials)
**Estimated Time:** 4-6 hours
**Difficulty:** Medium

Begin with Step 1: Create package structure!

---
