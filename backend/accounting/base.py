"""
Module: accounting.base
Purpose: Abstract base class for accounting platform clients
Dependencies: Python ABC, typing, datetime
Platform: Universal (implemented by platform-specific adapters)

This module defines the AccountingClient abstract base class that ALL
platform-specific adapters (Xero, QuickBooks, Sage, etc.) must implement.

By using this abstraction, business logic never needs to know which
platform it's working with. Just call methods on the client and get
back standardized data.

Example:
    # Create a client (Xero or QB - doesn't matter)
    client = AccountingClientFactory.create(organization)

    # Same code works for ANY platform
    transactions = client.get_transactions(start_date, end_date)
    accounts = client.get_accounts()

    # Platform adapters handle the specifics
    # Business logic stays clean and simple

Extension Points:
    To add a new platform (e.g., Sage):
    1. Create sage/client.py
    2. Extend AccountingClient
    3. Implement all abstract methods
    4. Add mapper functions (Sage format → Standard format)
    5. Add to AccountingClientFactory
    6. That's it! No business logic changes needed.

Author: Claude Code
Created: November 24, 2025
Last Modified: November 24, 2025
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Dict, Optional, Any
from decimal import Decimal
from enum import Enum


# ============================================================================
# ENUMERATIONS - Standard values across all platforms
# ============================================================================


class TransactionType(str, Enum):
    """
    Standard transaction types across all platforms.

    Xero and QB might use different names, but we normalize to these.
    """
    INVOICE = "invoice"  # Customer invoices (income)
    BILL = "bill"  # Supplier bills (expense)
    BANK_TRANSFER = "bank_transfer"  # Between accounts
    CREDIT_NOTE = "credit_note"  # Credit (reversal)
    EXPENSE_CLAIM = "expense_claim"  # Employee expense
    DEPOSIT = "deposit"  # Bank deposit
    WITHDRAWAL = "withdrawal"  # Bank withdrawal


class ContactType(str, Enum):
    """Standard contact types across all platforms."""
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    EMPLOYEE = "employee"
    OTHER = "other"


class AccountType(str, Enum):
    """
    Standard chart of accounts types.

    Follows UK bookkeeping standards (most common in our market).
    """
    ASSET = "asset"  # Bank accounts, receivables, equipment
    LIABILITY = "liability"  # Payables, loans, credit cards
    EQUITY = "equity"  # Owner's equity, retained earnings
    INCOME = "income"  # Revenue from sales
    EXPENSE = "expense"  # Costs (salaries, supplies, etc.)
    BANK = "bank"  # Bank accounts (special category)


class SyncStatus(str, Enum):
    """Status of sync operations."""
    NOT_SYNCED = "not_synced"
    SYNCING = "syncing"
    SYNCED = "synced"
    ERROR = "error"


# ============================================================================
# STANDARD DATA MODELS
# ============================================================================


class StandardTransaction:
    """
    Normalized transaction across all platforms.

    Xero and QB represent transactions differently. This class provides
    a standard representation that works for any platform.

    Attributes:
        id (str): Unique ID from platform
        type (TransactionType): What kind of transaction
        date (date): Transaction date
        description (str): Transaction description/memo
        amount (Decimal): Transaction amount (absolute value)
        tax_amount (Decimal): Tax/VAT amount
        account_id (str): Account from chart of accounts
        contact_id (Optional[str]): Customer/supplier/employee
        reference (str): Reference number (invoice #, etc.)
        status (str): Draft, approved, submitted, etc.
        line_items (List[Dict]): Line-level details if applicable
        platform_id (str): ID in the original platform
        platform_name (str): Which platform (xero, quickbooks, etc.)
        metadata (Dict): Platform-specific data we preserve
        sync_status (SyncStatus): Whether synced to our database

    Example:
        >>> txn = StandardTransaction(
        ...     id="TXN001",
        ...     type=TransactionType.INVOICE,
        ...     date=date(2025, 1, 15),
        ...     description="Monthly consulting",
        ...     amount=Decimal("1500.00"),
        ...     tax_amount=Decimal("300.00"),
        ...     account_id="200",  # Income account
        ...     contact_id="CUST001",
        ...     reference="INV-2025-001",
        ... )
    """

    def __init__(
        self,
        id: str,
        type: TransactionType,
        date: date,
        description: str,
        amount: Decimal,
        tax_amount: Decimal,
        account_id: str,
        contact_id: Optional[str] = None,
        reference: str = "",
        status: str = "approved",
        line_items: Optional[List[Dict]] = None,
        platform_id: str = "",
        platform_name: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        sync_status: SyncStatus = SyncStatus.NOT_SYNCED,
    ):
        self.id = id
        self.type = type
        self.date = date
        self.description = description
        self.amount = amount
        self.tax_amount = tax_amount
        self.account_id = account_id
        self.contact_id = contact_id
        self.reference = reference
        self.status = status
        self.line_items = line_items or []
        self.platform_id = platform_id
        self.platform_name = platform_name
        self.metadata = metadata or {}
        self.sync_status = sync_status

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<StandardTransaction("
            f"id={self.id}, "
            f"type={self.type.value}, "
            f"amount={self.amount}, "
            f"date={self.date}"
            f")>"
        )


class StandardContact:
    """
    Normalized contact across all platforms.

    Attributes:
        id (str): Unique ID from platform
        type (ContactType): Customer, supplier, employee, etc.
        name (str): Contact name
        email (Optional[str]): Email address
        phone (Optional[str]): Phone number
        address (Optional[str]): Full address
        tax_id (Optional[str]): Tax ID (ABN, EIN, etc.)
        currency (str): Currency code (GBP, USD, etc.)
        platform_id (str): ID in original platform
        platform_name (str): Which platform
        metadata (Dict): Platform-specific data
    """

    def __init__(
        self,
        id: str,
        type: ContactType,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        tax_id: Optional[str] = None,
        currency: str = "GBP",
        platform_id: str = "",
        platform_name: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.type = type
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address
        self.tax_id = tax_id
        self.currency = currency
        self.platform_id = platform_id
        self.platform_name = platform_name
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<StandardContact("
            f"id={self.id}, "
            f"name={self.name}, "
            f"type={self.type.value}"
            f")>"
        )


class StandardAccount:
    """
    Normalized account (chart of accounts).

    Attributes:
        id (str): Account ID (e.g., "200" for income)
        code (str): Account code (may be different from ID)
        name (str): Account name (e.g., "Sales Income")
        type (AccountType): Asset, liability, income, etc.
        currency (str): Currency code
        tax_type (Optional[str]): Tax treatment (VATable, etc.)
        platform_id (str): ID in original platform
        platform_name (str): Which platform
        metadata (Dict): Platform-specific data
    """

    def __init__(
        self,
        id: str,
        code: str,
        name: str,
        type: AccountType,
        currency: str = "GBP",
        tax_type: Optional[str] = None,
        platform_id: str = "",
        platform_name: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.code = code
        self.name = name
        self.type = type
        self.currency = currency
        self.tax_type = tax_type
        self.platform_id = platform_id
        self.platform_name = platform_name
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<StandardAccount("
            f"id={self.id}, "
            f"code={self.code}, "
            f"type={self.type.value}"
            f")>"
        )


# ============================================================================
# ABSTRACT BASE CLASS - All platforms implement this
# ============================================================================


class AccountingClient(ABC):
    """
    Abstract base class for all accounting platform clients.

    This is the foundation of our multi-platform approach. Every platform
    adapter (Xero, QuickBooks, Sage, etc.) inherits from this class and
    implements these abstract methods.

    The beauty of this approach:
    - Business logic calls methods on AccountingClient
    - Doesn't care which platform is behind it
    - Platform-specific details hidden in adapters
    - Adding new platforms = just implement these methods

    Example:
        # Don't do this (platform-specific):
        if platform == 'xero':
            from backend.accounting.xero import XeroClient
            client = XeroClient(credentials)

        # Do this instead (platform-agnostic):
        client = AccountingClientFactory.create(organization)
        # Now use client without knowing what platform it is

    Thread Safety:
        Subclasses should NOT assume thread-safety. Create separate
        instances for concurrent operations.

    Error Handling:
        All methods may raise AccountingClientError subclasses:
        - AuthenticationError - Auth failed
        - APIError - API call failed
        - RateLimitError - Rate limit exceeded
        - NotFoundError - Resource not found
    """

    # Platform name (set by subclass)
    PLATFORM_NAME: str = "unknown"

    def __init__(self, organization_id: str, credentials: Dict[str, Any]):
        """
        Initialize accounting client.

        Args:
            organization_id: Our internal organization ID
            credentials: Platform-specific credentials (API key, OAuth token, etc.)

        Raises:
            ValueError: If credentials are invalid
        """
        self.organization_id = organization_id
        self.credentials = credentials
        self._validate_credentials()

    @abstractmethod
    def _validate_credentials(self) -> None:
        """
        Validate that credentials are valid for this platform.

        Should be called in __init__. Raises error if invalid.

        Raises:
            ValueError: If credentials are missing or invalid
        """
        pass

    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the platform.

        Should verify that our credentials are still valid and refresh
        if needed (e.g., OAuth tokens).

        Returns:
            True if authentication successful

        Raises:
            AuthenticationError: If authentication fails

        Example:
            >>> client = XeroClient(org_id, credentials)
            >>> if client.authenticate():
            ...     print("Connected to Xero!")
        """
        pass

    # ========================================================================
    # TRANSACTION METHODS
    # ========================================================================

    @abstractmethod
    def get_transactions(
        self,
        start_date: date,
        end_date: date,
        transaction_types: Optional[List[TransactionType]] = None,
        limit: int = 1000,
    ) -> List[StandardTransaction]:
        """
        Get transactions for a date range.

        Returns platform transactions normalized to StandardTransaction.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            transaction_types: Filter by type (optional)
            limit: Max transactions to return (default 1000)

        Returns:
            List of StandardTransaction objects

        Raises:
            APIError: If API call fails
            RateLimitError: If rate limit exceeded

        Example:
            >>> transactions = client.get_transactions(
            ...     start_date=date(2025, 1, 1),
            ...     end_date=date(2025, 1, 31)
            ... )
            >>> for txn in transactions:
            ...     print(f"{txn.date}: {txn.description} ({txn.amount})")
        """
        pass

    @abstractmethod
    def get_transaction(self, transaction_id: str) -> Optional[StandardTransaction]:
        """
        Get a single transaction by ID.

        Args:
            transaction_id: Transaction ID

        Returns:
            StandardTransaction or None if not found

        Raises:
            APIError: If API call fails
        """
        pass

    @abstractmethod
    def create_transaction(
        self,
        transaction: StandardTransaction,
    ) -> StandardTransaction:
        """
        Create a new transaction.

        Args:
            transaction: StandardTransaction with data to create

        Returns:
            StandardTransaction with platform_id populated

        Raises:
            ValidationError: If transaction data is invalid
            APIError: If API call fails
        """
        pass

    @abstractmethod
    def update_transaction(
        self,
        transaction_id: str,
        transaction: StandardTransaction,
    ) -> StandardTransaction:
        """
        Update an existing transaction.

        Args:
            transaction_id: ID of transaction to update
            transaction: StandardTransaction with updated data

        Returns:
            Updated StandardTransaction

        Raises:
            NotFoundError: If transaction not found
            APIError: If API call fails
        """
        pass

    # ========================================================================
    # ACCOUNT METHODS
    # ========================================================================

    @abstractmethod
    def get_accounts(self, account_types: Optional[List[AccountType]] = None) -> List[StandardAccount]:
        """
        Get all accounts (chart of accounts).

        Returns accounts normalized to StandardAccount.

        Args:
            account_types: Filter by type (optional)

        Returns:
            List of StandardAccount objects

        Raises:
            APIError: If API call fails

        Example:
            >>> accounts = client.get_accounts()
            >>> income_accounts = [a for a in accounts if a.type == AccountType.INCOME]
        """
        pass

    @abstractmethod
    def get_account(self, account_id: str) -> Optional[StandardAccount]:
        """
        Get a single account by ID.

        Args:
            account_id: Account ID

        Returns:
            StandardAccount or None if not found
        """
        pass

    # ========================================================================
    # CONTACT METHODS
    # ========================================================================

    @abstractmethod
    def get_contacts(
        self,
        contact_types: Optional[List[ContactType]] = None,
        limit: int = 1000,
    ) -> List[StandardContact]:
        """
        Get all contacts (customers, suppliers, employees).

        Returns contacts normalized to StandardContact.

        Args:
            contact_types: Filter by type (optional)
            limit: Max contacts to return

        Returns:
            List of StandardContact objects

        Raises:
            APIError: If API call fails
        """
        pass

    @abstractmethod
    def get_contact(self, contact_id: str) -> Optional[StandardContact]:
        """
        Get a single contact by ID.

        Args:
            contact_id: Contact ID

        Returns:
            StandardContact or None if not found
        """
        pass

    @abstractmethod
    def create_contact(self, contact: StandardContact) -> StandardContact:
        """
        Create a new contact.

        Args:
            contact: StandardContact with data to create

        Returns:
            StandardContact with platform_id populated

        Raises:
            ValidationError: If contact data is invalid
            APIError: If API call fails
        """
        pass

    @abstractmethod
    def update_contact(
        self,
        contact_id: str,
        contact: StandardContact,
    ) -> StandardContact:
        """
        Update an existing contact.

        Args:
            contact_id: ID of contact to update
            contact: StandardContact with updated data

        Returns:
            Updated StandardContact

        Raises:
            NotFoundError: If contact not found
            APIError: If API call fails
        """
        pass

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    @abstractmethod
    def get_organization_info(self) -> Dict[str, Any]:
        """
        Get organization/company information.

        Returns:
            Dict with organization details (name, tax ID, etc.)

        Raises:
            APIError: If API call fails
        """
        pass

    @abstractmethod
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get sync status information.

        Used to monitor health of connection and rate limits.

        Returns:
            Dict with:
            - last_sync: datetime of last sync
            - next_sync: estimated next sync
            - rate_limit_remaining: calls remaining
            - rate_limit_reset: when limit resets

        Raises:
            APIError: If API call fails
        """
        pass


# ============================================================================
# EXCEPTION CLASSES
# ============================================================================


class AccountingClientError(Exception):
    """Base exception for accounting client errors."""
    pass


class AuthenticationError(AccountingClientError):
    """Authentication with platform failed."""
    pass


class APIError(AccountingClientError):
    """General API error."""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded."""
    pass


class NotFoundError(APIError):
    """Resource not found."""
    pass


class ValidationError(AccountingClientError):
    """Data validation error."""
    pass
