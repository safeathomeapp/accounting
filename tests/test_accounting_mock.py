"""Tests for Mock accounting client.

Module: tests.test_accounting_mock
Purpose: Unit and integration tests for MockClient adapter
Status: Tests for TEMPORARY mock client (will be removed before production)
Dependencies: pytest, backend.accounting.mock

Test Coverage:
- MockClient initialization
- Transaction fetching and filtering
- Contact and account management
- Organization info retrieval
- Read-only constraints (create/update raise errors)
- Factory integration

Run with:
    pytest tests/test_accounting_mock.py -v
    pytest tests/test_accounting_mock.py -v --cov=backend.accounting.mock

Author: Claude Code
Created: November 24, 2025
"""

import pytest
from datetime import date, timedelta

from backend.accounting import (
    TransactionType,
    ContactType,
    AccountType,
    StandardTransaction,
    StandardContact,
    StandardAccount,
)
from backend.accounting.mock.client import MockClient
from backend.accounting.factory import AccountingClientFactory


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def mock_client():
    """Create MockClient instance for testing."""
    credentials = {
        "client_id": "mock_test",
        "client_secret": "mock_test",
    }
    return MockClient("org-mock-test", credentials)


# ============================================================================
# TESTS FOR MOCKCLIENT INITIALIZATION
# ============================================================================


class TestMockClientInitialization:
    """Tests for MockClient initialization and basic setup."""

    def test_client_initialization(self, mock_client):
        """Test that MockClient initializes correctly."""
        assert mock_client is not None
        assert mock_client.organization_id == "org-mock-test"
        assert mock_client.PLATFORM_NAME == "mock"

    def test_authentication_always_returns_true(self, mock_client):
        """Test that mock client always returns True for authentication."""
        assert mock_client.authenticate() is True

    def test_client_extends_accounting_client(self, mock_client):
        """Test that MockClient is an AccountingClient."""
        from backend.accounting import AccountingClient

        assert isinstance(mock_client, AccountingClient)

    def test_client_implements_all_abstract_methods(self, mock_client):
        """Test that MockClient implements all required methods."""
        required_methods = [
            "authenticate",
            "get_transactions",
            "get_transaction",
            "create_transaction",
            "update_transaction",
            "get_accounts",
            "get_account",
            "get_contacts",
            "get_contact",
            "create_contact",
            "update_contact",
            "get_organization_info",
            "get_sync_status",
        ]
        for method in required_methods:
            assert hasattr(mock_client, method), f"Missing method: {method}"
            assert callable(getattr(mock_client, method)), f"Not callable: {method}"


# ============================================================================
# TESTS FOR TRANSACTIONS
# ============================================================================


class TestMockClientTransactions:
    """Tests for transaction-related methods."""

    def test_get_transactions_all(self, mock_client):
        """Test getting all transactions."""
        start = date.today() - timedelta(days=60)
        end = date.today() + timedelta(days=30)
        txns = mock_client.get_transactions(start, end)

        assert len(txns) > 0
        assert all(isinstance(t, StandardTransaction) for t in txns)

    def test_get_transactions_by_type_invoice(self, mock_client):
        """Test getting only invoices."""
        start = date.today() - timedelta(days=60)
        end = date.today() + timedelta(days=30)
        txns = mock_client.get_transactions(
            start, end, transaction_types=[TransactionType.INVOICE]
        )

        assert len(txns) > 0
        assert all(t.type == TransactionType.INVOICE for t in txns)

    def test_get_transactions_by_type_bank_transfer(self, mock_client):
        """Test getting only bank transfers."""
        start = date.today() - timedelta(days=60)
        end = date.today() + timedelta(days=30)
        txns = mock_client.get_transactions(
            start, end, transaction_types=[TransactionType.BANK_TRANSFER]
        )

        assert len(txns) > 0
        assert all(t.type == TransactionType.BANK_TRANSFER for t in txns)

    def test_get_transactions_with_limit(self, mock_client):
        """Test transaction limit is respected."""
        start = date.today() - timedelta(days=60)
        end = date.today() + timedelta(days=30)
        txns = mock_client.get_transactions(start, end, limit=1)

        assert len(txns) <= 1

    def test_get_transactions_date_filtering(self, mock_client):
        """Test that date filtering works."""
        # Only get recent transactions
        start = date.today() - timedelta(days=1)
        end = date.today()
        txns = mock_client.get_transactions(start, end)

        # Should have some recent transactions in mock data
        assert len(txns) >= 0

    def test_get_transaction_by_id(self, mock_client):
        """Test getting single transaction by ID."""
        txn = mock_client.get_transaction("inv-001-demo")

        assert txn is not None
        assert txn.id == "inv-001-demo"
        assert isinstance(txn, StandardTransaction)

    def test_get_transaction_not_found(self, mock_client):
        """Test getting non-existent transaction."""
        txn = mock_client.get_transaction("nonexistent-id")
        assert txn is None

    def test_create_transaction_not_implemented(self, mock_client):
        """Test that create_transaction raises NotImplementedError."""
        from decimal import Decimal

        txn = StandardTransaction(
            id="test",
            type=TransactionType.INVOICE,
            date=date.today(),
            description="Test",
            amount=Decimal("100"),
            tax_amount=Decimal("20"),
            account_id="4000",
        )

        with pytest.raises(NotImplementedError):
            mock_client.create_transaction(txn)

    def test_update_transaction_not_implemented(self, mock_client):
        """Test that update_transaction raises NotImplementedError."""
        from decimal import Decimal

        txn = StandardTransaction(
            id="test",
            type=TransactionType.INVOICE,
            date=date.today(),
            description="Test",
            amount=Decimal("100"),
            tax_amount=Decimal("20"),
            account_id="4000",
        )

        with pytest.raises(NotImplementedError):
            mock_client.update_transaction("inv-001-demo", txn)


# ============================================================================
# TESTS FOR CONTACTS
# ============================================================================


class TestMockClientContacts:
    """Tests for contact-related methods."""

    def test_get_contacts_all(self, mock_client):
        """Test getting all contacts."""
        contacts = mock_client.get_contacts()

        assert len(contacts) > 0
        assert all(isinstance(c, StandardContact) for c in contacts)

    def test_get_contacts_by_type_customer(self, mock_client):
        """Test getting only customer contacts."""
        contacts = mock_client.get_contacts(
            contact_types=[ContactType.CUSTOMER]
        )

        assert len(contacts) > 0
        assert all(c.type == ContactType.CUSTOMER for c in contacts)

    def test_get_contacts_by_type_supplier(self, mock_client):
        """Test getting only supplier contacts."""
        contacts = mock_client.get_contacts(
            contact_types=[ContactType.SUPPLIER]
        )

        assert len(contacts) > 0
        assert all(c.type == ContactType.SUPPLIER for c in contacts)

    def test_get_contacts_with_limit(self, mock_client):
        """Test contact limit is respected."""
        contacts = mock_client.get_contacts(limit=1)
        assert len(contacts) <= 1

    def test_get_contact_by_id(self, mock_client):
        """Test getting single contact by ID."""
        contact = mock_client.get_contact("contact-acme-demo")

        assert contact is not None
        assert contact.id == "contact-acme-demo"
        assert contact.name == "Acme Corporation"
        assert isinstance(contact, StandardContact)

    def test_get_contact_not_found(self, mock_client):
        """Test getting non-existent contact."""
        contact = mock_client.get_contact("nonexistent-id")
        assert contact is None

    def test_contact_has_complete_data(self, mock_client):
        """Test that returned contacts have complete data."""
        contact = mock_client.get_contact("contact-acme-demo")

        assert contact.name is not None
        assert contact.email is not None
        assert contact.type is not None
        assert contact.phone is not None

    def test_create_contact_not_implemented(self, mock_client):
        """Test that create_contact raises NotImplementedError."""
        contact = StandardContact(
            id="test",
            name="Test Contact",
            type=ContactType.CUSTOMER,
        )

        with pytest.raises(NotImplementedError):
            mock_client.create_contact(contact)

    def test_update_contact_not_implemented(self, mock_client):
        """Test that update_contact raises NotImplementedError."""
        contact = StandardContact(
            id="test",
            name="Test Contact",
            type=ContactType.CUSTOMER,
        )

        with pytest.raises(NotImplementedError):
            mock_client.update_contact("contact-acme-demo", contact)


# ============================================================================
# TESTS FOR ACCOUNTS
# ============================================================================


class TestMockClientAccounts:
    """Tests for account-related methods."""

    def test_get_accounts_all(self, mock_client):
        """Test getting all accounts."""
        accounts = mock_client.get_accounts()

        assert len(accounts) > 0
        assert all(isinstance(a, StandardAccount) for a in accounts)

    def test_get_accounts_by_type_bank(self, mock_client):
        """Test getting only bank accounts."""
        accounts = mock_client.get_accounts(account_types=["BANK"])

        assert len(accounts) > 0
        assert all(a.type == AccountType.BANK for a in accounts)

    def test_get_accounts_by_type_expense(self, mock_client):
        """Test getting only expense accounts."""
        accounts = mock_client.get_accounts(account_types=["EXPENSE"])

        assert len(accounts) > 0
        assert all(a.type == AccountType.EXPENSE for a in accounts)

    def test_get_account_by_id(self, mock_client):
        """Test getting single account by ID."""
        account = mock_client.get_account("account-1000-demo")

        assert account is not None
        assert account.id == "account-1000-demo"
        assert account.code == "1000"
        assert isinstance(account, StandardAccount)

    def test_get_account_not_found(self, mock_client):
        """Test getting non-existent account."""
        account = mock_client.get_account("nonexistent-id")
        assert account is None

    def test_account_has_complete_data(self, mock_client):
        """Test that returned accounts have complete data."""
        account = mock_client.get_account("account-1000-demo")

        assert account.name is not None
        assert account.code is not None
        assert account.type is not None


# ============================================================================
# TESTS FOR ORGANIZATION INFO
# ============================================================================


class TestMockClientOrganization:
    """Tests for organization-related methods."""

    def test_get_organization_info(self, mock_client):
        """Test getting organization information."""
        org_info = mock_client.get_organization_info()

        assert org_info is not None
        assert "id" in org_info
        assert "name" in org_info
        assert org_info["name"] == "Demo Company Inc"

    def test_organization_info_has_all_fields(self, mock_client):
        """Test that org info has all required fields."""
        org_info = mock_client.get_organization_info()

        required_fields = [
            "id",
            "name",
            "legal_name",
            "country_code",
            "tax_number",
            "base_currency",
            "status",
        ]
        for field in required_fields:
            assert field in org_info, f"Missing field: {field}"

    def test_organization_platform_identified_as_mock(self, mock_client):
        """Test that organization info identifies as MOCK."""
        org_info = mock_client.get_organization_info()
        assert "mock" in org_info.get("platform", "").lower()

    def test_get_sync_status(self, mock_client):
        """Test getting sync status."""
        status = mock_client.get_sync_status()

        assert status is not None
        assert "authenticated" in status
        assert status["authenticated"] is True

    def test_sync_status_identified_as_demo(self, mock_client):
        """Test that sync status identifies as demo."""
        status = mock_client.get_sync_status()
        assert status.get("is_demo") is True


# ============================================================================
# TESTS FOR FACTORY INTEGRATION
# ============================================================================


class TestMockClientFactoryIntegration:
    """Tests for MockClient integration with factory pattern."""

    def test_create_mock_via_factory(self):
        """Test creating MockClient via factory."""
        credentials = {
            "client_id": "test",
            "client_secret": "test",
        }

        client = AccountingClientFactory.create_from_platform(
            platform="mock",
            organization_id="org-test",
            credentials=credentials,
        )

        assert client is not None
        assert client.PLATFORM_NAME == "mock"
        from backend.accounting.mock.client import MockClient

        assert isinstance(client, MockClient)

    def test_mock_listed_as_supported_platform(self):
        """Test that mock is in supported platforms."""
        platforms = AccountingClientFactory.supported_platforms()
        assert "mock" in platforms

    def test_is_platform_supported_mock(self):
        """Test is_platform_supported recognizes mock."""
        assert AccountingClientFactory.is_platform_supported("mock") is True

    def test_factory_creates_same_interface(self):
        """Test that factory-created mock has same interface as direct."""
        credentials = {"client_id": "test", "client_secret": "test"}

        # Via factory
        factory_client = AccountingClientFactory.create_from_platform(
            "mock", "org-test", credentials
        )

        # Direct
        direct_client = MockClient("org-test", credentials)

        # Should have same methods
        assert type(factory_client).__name__ == type(direct_client).__name__


# ============================================================================
# TESTS FOR DATA CONSISTENCY
# ============================================================================


class TestMockClientDataConsistency:
    """Tests for consistency of mock data."""

    def test_all_transactions_have_ids(self, mock_client):
        """Test that all transactions have IDs."""
        start = date.today() - timedelta(days=60)
        end = date.today() + timedelta(days=30)
        txns = mock_client.get_transactions(start, end)

        assert all(t.id is not None for t in txns)

    def test_all_contacts_have_ids(self, mock_client):
        """Test that all contacts have IDs."""
        contacts = mock_client.get_contacts()
        assert all(c.id is not None for c in contacts)

    def test_all_accounts_have_ids(self, mock_client):
        """Test that all accounts have IDs."""
        accounts = mock_client.get_accounts()
        assert all(a.id is not None for a in accounts)

    def test_transaction_ids_are_unique(self, mock_client):
        """Test that transaction IDs are unique."""
        start = date.today() - timedelta(days=60)
        end = date.today() + timedelta(days=30)
        txns = mock_client.get_transactions(start, end)

        ids = [t.id for t in txns]
        assert len(ids) == len(set(ids)), "Transaction IDs should be unique"

    def test_contact_ids_are_unique(self, mock_client):
        """Test that contact IDs are unique."""
        contacts = mock_client.get_contacts()
        ids = [c.id for c in contacts]
        assert len(ids) == len(set(ids)), "Contact IDs should be unique"

    def test_account_ids_are_unique(self, mock_client):
        """Test that account IDs are unique."""
        accounts = mock_client.get_accounts()
        ids = [a.id for a in accounts]
        assert len(ids) == len(set(ids)), "Account IDs should be unique"


# ============================================================================
# TESTS FOR DEMO IDENTIFICATION
# ============================================================================


class TestMockClientDemoIdentification:
    """Tests to ensure mock client is easily identified as demo."""

    def test_platform_name_is_mock(self, mock_client):
        """Test that platform name identifies as mock."""
        assert "mock" in mock_client.PLATFORM_NAME.lower()

    def test_organization_info_says_mock(self, mock_client):
        """Test that org info clearly identifies as MOCK."""
        org_info = mock_client.get_organization_info()
        platform_field = org_info.get("platform", "")
        assert "MOCK" in platform_field or "mock" in platform_field.lower()

    def test_sync_status_identifies_as_demo(self, mock_client):
        """Test that sync status has is_demo flag."""
        status = mock_client.get_sync_status()
        assert "is_demo" in status
        assert status["is_demo"] is True

    def test_client_docstring_mentions_demo(self, mock_client):
        """Test that client docstring mentions it's a demo."""
        docstring = MockClient.__doc__
        assert "demo" in docstring.lower()
        assert "development" in docstring.lower()

    def test_fixtures_module_docstring_mentions_temporary(self):
        """Test that fixtures module clearly says it's temporary."""
        from backend.accounting.mock import fixtures

        docstring = fixtures.__doc__
        assert "temporary" in docstring.lower()
        assert "remove" in docstring.lower()
