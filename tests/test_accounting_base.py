"""
Module: tests.test_accounting_base
Purpose: Unit tests for accounting abstraction layer
Dependencies: pytest, backend.accounting

Test Coverage:
- Standard data models (Transaction, Contact, Account)
- Enumerations (TransactionType, ContactType, etc.)
- Exception classes
- Abstract base class interface

Run with:
    pytest tests/test_accounting_base.py -v
    pytest tests/test_accounting_base.py -v --cov=backend.accounting

Author: Claude Code
Created: November 24, 2025
"""

import pytest
from datetime import date
from decimal import Decimal
from abc import ABC, abstractmethod

from backend.accounting import (
    # Standard models
    StandardTransaction,
    StandardContact,
    StandardAccount,
    # Enumerations
    TransactionType,
    ContactType,
    AccountType,
    SyncStatus,
    # Base class
    AccountingClient,
    # Exceptions
    AccountingClientError,
    AuthenticationError,
    APIError,
    RateLimitError,
    NotFoundError,
    ValidationError,
)


# ============================================================================
# TESTS FOR STANDARD DATA MODELS
# ============================================================================


class TestStandardTransaction:
    """Tests for StandardTransaction model."""

    def test_create_transaction_minimal(self):
        """Test creating transaction with required fields only."""
        txn = StandardTransaction(
            id="TXN001",
            type=TransactionType.INVOICE,
            date=date(2025, 1, 15),
            description="Test invoice",
            amount=Decimal("100.00"),
            tax_amount=Decimal("20.00"),
            account_id="200",
        )

        assert txn.id == "TXN001"
        assert txn.type == TransactionType.INVOICE
        assert txn.date == date(2025, 1, 15)
        assert txn.description == "Test invoice"
        assert txn.amount == Decimal("100.00")
        assert txn.tax_amount == Decimal("20.00")
        assert txn.account_id == "200"
        assert txn.contact_id is None
        assert txn.status == "approved"
        assert txn.sync_status == SyncStatus.NOT_SYNCED

    def test_create_transaction_complete(self):
        """Test creating transaction with all fields."""
        txn = StandardTransaction(
            id="TXN001",
            type=TransactionType.INVOICE,
            date=date(2025, 1, 15),
            description="Test invoice",
            amount=Decimal("1000.00"),
            tax_amount=Decimal("200.00"),
            account_id="200",
            contact_id="CUST001",
            reference="INV-2025-001",
            status="draft",
            line_items=[{"description": "Item 1", "amount": "500.00"}],
            platform_id="XER123456",
            platform_name="xero",
            metadata={"custom_field": "value"},
            sync_status=SyncStatus.SYNCED,
        )

        assert txn.id == "TXN001"
        assert txn.contact_id == "CUST001"
        assert txn.reference == "INV-2025-001"
        assert txn.status == "draft"
        assert len(txn.line_items) == 1
        assert txn.platform_id == "XER123456"
        assert txn.platform_name == "xero"
        assert txn.metadata["custom_field"] == "value"
        assert txn.sync_status == SyncStatus.SYNCED

    def test_transaction_repr(self):
        """Test string representation of transaction."""
        txn = StandardTransaction(
            id="TXN001",
            type=TransactionType.BILL,
            date=date(2025, 1, 15),
            description="Test bill",
            amount=Decimal("500.00"),
            tax_amount=Decimal("100.00"),
            account_id="300",
        )

        repr_str = repr(txn)
        assert "StandardTransaction" in repr_str
        assert "TXN001" in repr_str
        assert "bill" in repr_str
        assert "500.00" in repr_str

    def test_transaction_type_enum(self):
        """Test TransactionType enumeration."""
        assert TransactionType.INVOICE.value == "invoice"
        assert TransactionType.BILL.value == "bill"
        assert TransactionType.BANK_TRANSFER.value == "bank_transfer"
        assert TransactionType.CREDIT_NOTE.value == "credit_note"
        assert TransactionType.EXPENSE_CLAIM.value == "expense_claim"
        assert TransactionType.DEPOSIT.value == "deposit"
        assert TransactionType.WITHDRAWAL.value == "withdrawal"


class TestStandardContact:
    """Tests for StandardContact model."""

    def test_create_contact_minimal(self):
        """Test creating contact with required fields only."""
        contact = StandardContact(
            id="CUST001",
            type=ContactType.CUSTOMER,
            name="John Smith",
        )

        assert contact.id == "CUST001"
        assert contact.type == ContactType.CUSTOMER
        assert contact.name == "John Smith"
        assert contact.email is None
        assert contact.phone is None
        assert contact.currency == "GBP"
        assert contact.metadata == {}

    def test_create_contact_complete(self):
        """Test creating contact with all fields."""
        contact = StandardContact(
            id="CUST001",
            type=ContactType.CUSTOMER,
            name="John Smith",
            email="john@example.com",
            phone="01234567890",
            address="123 Main St, London",
            tax_id="12345678",
            currency="GBP",
            platform_id="XER789",
            platform_name="xero",
            metadata={"account_manager": "Jane"},
        )

        assert contact.email == "john@example.com"
        assert contact.phone == "01234567890"
        assert contact.address == "123 Main St, London"
        assert contact.tax_id == "12345678"
        assert contact.platform_id == "XER789"
        assert contact.metadata["account_manager"] == "Jane"

    def test_contact_type_enum(self):
        """Test ContactType enumeration."""
        assert ContactType.CUSTOMER.value == "customer"
        assert ContactType.SUPPLIER.value == "supplier"
        assert ContactType.EMPLOYEE.value == "employee"
        assert ContactType.OTHER.value == "other"


class TestStandardAccount:
    """Tests for StandardAccount model."""

    def test_create_account_minimal(self):
        """Test creating account with required fields."""
        account = StandardAccount(
            id="200",
            code="4000",
            name="Sales Income",
            type=AccountType.INCOME,
        )

        assert account.id == "200"
        assert account.code == "4000"
        assert account.name == "Sales Income"
        assert account.type == AccountType.INCOME
        assert account.currency == "GBP"
        assert account.tax_type is None

    def test_create_account_complete(self):
        """Test creating account with all fields."""
        account = StandardAccount(
            id="200",
            code="4000",
            name="Sales Income",
            type=AccountType.INCOME,
            currency="GBP",
            tax_type="VATable",
            platform_id="XER123",
            platform_name="xero",
            metadata={"vat_code": "Tax on Sales"},
        )

        assert account.tax_type == "VATable"
        assert account.platform_id == "XER123"
        assert account.metadata["vat_code"] == "Tax on Sales"

    def test_account_type_enum(self):
        """Test AccountType enumeration."""
        assert AccountType.ASSET.value == "asset"
        assert AccountType.LIABILITY.value == "liability"
        assert AccountType.EQUITY.value == "equity"
        assert AccountType.INCOME.value == "income"
        assert AccountType.EXPENSE.value == "expense"
        assert AccountType.BANK.value == "bank"


# ============================================================================
# TESTS FOR SYNC STATUS ENUM
# ============================================================================


class TestSyncStatus:
    """Tests for SyncStatus enumeration."""

    def test_sync_status_values(self):
        """Test SyncStatus enum values."""
        assert SyncStatus.NOT_SYNCED.value == "not_synced"
        assert SyncStatus.SYNCING.value == "syncing"
        assert SyncStatus.SYNCED.value == "synced"
        assert SyncStatus.ERROR.value == "error"


# ============================================================================
# TESTS FOR EXCEPTION CLASSES
# ============================================================================


class TestExceptionClasses:
    """Tests for exception hierarchy."""

    def test_accounting_client_error_base(self):
        """Test AccountingClientError is base exception."""
        with pytest.raises(AccountingClientError):
            raise AccountingClientError("Test error")

    def test_authentication_error(self):
        """Test AuthenticationError is subclass of AccountingClientError."""
        with pytest.raises(AccountingClientError):
            raise AuthenticationError("Auth failed")

    def test_api_error(self):
        """Test APIError is subclass of AccountingClientError."""
        with pytest.raises(AccountingClientError):
            raise APIError("API failed")

    def test_rate_limit_error(self):
        """Test RateLimitError is subclass of APIError."""
        with pytest.raises(APIError):
            raise RateLimitError("Rate limit exceeded")

    def test_not_found_error(self):
        """Test NotFoundError is subclass of APIError."""
        with pytest.raises(APIError):
            raise NotFoundError("Resource not found")

    def test_validation_error(self):
        """Test ValidationError is subclass of AccountingClientError."""
        with pytest.raises(AccountingClientError):
            raise ValidationError("Invalid data")


# ============================================================================
# TESTS FOR ABSTRACT BASE CLASS
# ============================================================================


class MockAccountingClient(AccountingClient):
    """
    Mock implementation of AccountingClient for testing.

    This is a complete implementation used to test the abstract base class
    interface without testing platform-specific logic.
    """

    PLATFORM_NAME = "mock"

    def _validate_credentials(self) -> None:
        """Mock: Just check credentials dict exists."""
        if not isinstance(self.credentials, dict):
            raise ValueError("Credentials must be a dict")

    def authenticate(self) -> bool:
        """Mock: Always succeeds."""
        return True

    def get_transactions(self, start_date, end_date, transaction_types=None, limit=1000):
        """Mock: Return empty list."""
        return []

    def get_transaction(self, transaction_id):
        """Mock: Return None (not found)."""
        return None

    def create_transaction(self, transaction):
        """Mock: Return same transaction."""
        transaction.platform_id = "MOCK123"
        return transaction

    def update_transaction(self, transaction_id, transaction):
        """Mock: Return updated transaction."""
        return transaction

    def get_accounts(self, account_types=None):
        """Mock: Return empty list."""
        return []

    def get_account(self, account_id):
        """Mock: Return None."""
        return None

    def get_contacts(self, contact_types=None, limit=1000):
        """Mock: Return empty list."""
        return []

    def get_contact(self, contact_id):
        """Mock: Return None."""
        return None

    def create_contact(self, contact):
        """Mock: Return contact with ID."""
        contact.platform_id = "MOCK456"
        return contact

    def update_contact(self, contact_id, contact):
        """Mock: Return updated contact."""
        return contact

    def get_organization_info(self):
        """Mock: Return org info."""
        return {"name": "Mock Org", "id": "ORG123"}

    def get_sync_status(self):
        """Mock: Return sync status."""
        return {
            "last_sync": None,
            "next_sync": None,
            "rate_limit_remaining": 100,
        }


class TestAccountingClientBase:
    """Tests for AccountingClient abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that AccountingClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AccountingClient("org123", {})

    def test_can_instantiate_concrete_implementation(self):
        """Test that concrete implementation can be instantiated."""
        client = MockAccountingClient("org123", {"api_key": "test"})
        assert client.organization_id == "org123"
        assert client.credentials == {"api_key": "test"}

    def test_invalid_credentials_raises_error(self):
        """Test that invalid credentials raise ValueError."""
        with pytest.raises(ValueError):
            MockAccountingClient("org123", "not a dict")

    def test_authenticate_method(self):
        """Test authenticate method."""
        client = MockAccountingClient("org123", {"api_key": "test"})
        assert client.authenticate() is True

    def test_get_transactions(self):
        """Test get_transactions method."""
        client = MockAccountingClient("org123", {"api_key": "test"})
        transactions = client.get_transactions(
            date(2025, 1, 1), date(2025, 1, 31)
        )
        assert isinstance(transactions, list)
        assert len(transactions) == 0

    def test_get_accounts(self):
        """Test get_accounts method."""
        client = MockAccountingClient("org123", {"api_key": "test"})
        accounts = client.get_accounts()
        assert isinstance(accounts, list)
        assert len(accounts) == 0

    def test_get_contacts(self):
        """Test get_contacts method."""
        client = MockAccountingClient("org123", {"api_key": "test"})
        contacts = client.get_contacts()
        assert isinstance(contacts, list)
        assert len(contacts) == 0

    def test_get_organization_info(self):
        """Test get_organization_info method."""
        client = MockAccountingClient("org123", {"api_key": "test"})
        info = client.get_organization_info()
        assert isinstance(info, dict)
        assert "name" in info

    def test_get_sync_status(self):
        """Test get_sync_status method."""
        client = MockAccountingClient("org123", {"api_key": "test"})
        status = client.get_sync_status()
        assert isinstance(status, dict)
        assert "rate_limit_remaining" in status

    def test_create_transaction(self):
        """Test create_transaction method."""
        client = MockAccountingClient("org123", {"api_key": "test"})
        txn = StandardTransaction(
            id="NEW001",
            type=TransactionType.INVOICE,
            date=date(2025, 1, 15),
            description="Test",
            amount=Decimal("100.00"),
            tax_amount=Decimal("20.00"),
            account_id="200",
        )
        result = client.create_transaction(txn)
        assert result.platform_id == "MOCK123"

    def test_create_contact(self):
        """Test create_contact method."""
        client = MockAccountingClient("org123", {"api_key": "test"})
        contact = StandardContact(
            id="NEW001",
            type=ContactType.CUSTOMER,
            name="Test Customer",
        )
        result = client.create_contact(contact)
        assert result.platform_id == "MOCK456"

    def test_platform_name(self):
        """Test PLATFORM_NAME class attribute."""
        client = MockAccountingClient("org123", {"api_key": "test"})
        assert client.PLATFORM_NAME == "mock"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestAbstractionLayerIntegration:
    """Integration tests for abstraction layer."""

    def test_client_with_standard_models(self):
        """Test that client works with standard models."""
        client = MockAccountingClient("org123", {"api_key": "test"})

        # Create transaction
        txn = StandardTransaction(
            id="TXN001",
            type=TransactionType.INVOICE,
            date=date(2025, 1, 15),
            description="Monthly service",
            amount=Decimal("1500.00"),
            tax_amount=Decimal("300.00"),
            account_id="200",
            contact_id="CUST001",
        )

        # Create contact
        contact = StandardContact(
            id="CUST001",
            type=ContactType.CUSTOMER,
            name="Test Customer",
            email="test@example.com",
        )

        # Create account
        account = StandardAccount(
            id="200",
            code="4000",
            name="Sales Income",
            type=AccountType.INCOME,
        )

        # All operations should work
        assert client.create_transaction(txn).platform_id == "MOCK123"
        assert client.create_contact(contact).platform_id == "MOCK456"
        assert account.type == AccountType.INCOME

    def test_multiple_transaction_types(self):
        """Test creating different transaction types."""
        client = MockAccountingClient("org123", {"api_key": "test"})

        types_to_test = [
            TransactionType.INVOICE,
            TransactionType.BILL,
            TransactionType.BANK_TRANSFER,
            TransactionType.CREDIT_NOTE,
        ]

        for txn_type in types_to_test:
            txn = StandardTransaction(
                id=f"TXN_{txn_type.value}",
                type=txn_type,
                date=date(2025, 1, 15),
                description="Test",
                amount=Decimal("100.00"),
                tax_amount=Decimal("20.00"),
                account_id="200",
            )
            result = client.create_transaction(txn)
            assert result.type == txn_type
