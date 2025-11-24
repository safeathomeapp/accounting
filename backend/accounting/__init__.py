"""
Module: accounting
Purpose: Multi-platform accounting system abstraction
Platform: Universal

This package provides a unified interface to multiple accounting platforms
(Xero, QuickBooks, Sage, etc.) through the adapter pattern.

Key Classes:
- AccountingClient: Abstract base class for all platform adapters
- StandardTransaction: Normalized transaction data
- StandardContact: Normalized contact data
- StandardAccount: Normalized account data
- AccountingClientFactory: Creates platform-specific clients

Usage:
    from backend.accounting import AccountingClientFactory

    # Create client for any platform (Xero, QB, etc.)
    client = AccountingClientFactory.create(organization)

    # Use standard methods (works with any platform)
    transactions = client.get_transactions(start_date, end_date)
    accounts = client.get_accounts()
    contacts = client.get_contacts()

Extension Points:
    To add a new platform:
    1. Create platform package (e.g., backend/accounting/sage/)
    2. Create client.py with YourPlatformClient(AccountingClient)
    3. Implement all abstract methods
    4. Add to AccountingClientFactory.PLATFORM_CLIENTS
    5. Done!

Author: Claude Code
Created: November 24, 2025
"""

from backend.accounting.base import (
    # Abstract base class
    AccountingClient,
    # Standard data models
    StandardTransaction,
    StandardContact,
    StandardAccount,
    # Enumerations
    TransactionType,
    ContactType,
    AccountType,
    SyncStatus,
    # Exception classes
    AccountingClientError,
    AuthenticationError,
    APIError,
    RateLimitError,
    NotFoundError,
    ValidationError,
)

from backend.accounting.factory import AccountingClientFactory

__all__ = [
    # Base class
    "AccountingClient",
    # Standard models
    "StandardTransaction",
    "StandardContact",
    "StandardAccount",
    # Enumerations
    "TransactionType",
    "ContactType",
    "AccountType",
    "SyncStatus",
    # Factory
    "AccountingClientFactory",
    # Exceptions
    "AccountingClientError",
    "AuthenticationError",
    "APIError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
]
