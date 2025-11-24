"""Tests for Xero accounting client.

Module: tests.test_accounting_xero
Purpose: Unit and integration tests for XeroClient adapter
Dependencies: pytest, unittest.mock, backend.accounting.xero

Test Coverage:
- Mapper transformations (invoice, contact, account)
- Authentication flow
- Transaction fetching and filtering
- Contact and account management
- Error handling and rate limiting
- Organization info retrieval

Run with:
    pytest tests/test_accounting_xero.py -v
    pytest tests/test_accounting_xero.py -v --cov=backend.accounting.xero

Author: Claude Code
Created: November 24, 2025
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date, datetime, timedelta
from decimal import Decimal

from backend.accounting import (
    TransactionType,
    ContactType,
    AccountType,
    StandardTransaction,
    StandardContact,
    StandardAccount,
    APIError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    SyncStatus,
)
from backend.accounting.xero.client import XeroClient
from backend.accounting.xero.mapper import XeroMapper
from backend.accounting.xero.auth import XeroAuth


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def mock_credentials():
    """Create mock Xero credentials."""
    return {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "redirect_uri": "http://localhost:8000/auth/xero/callback",
    }


@pytest.fixture
def xero_client(mock_credentials):
    """Create XeroClient instance for testing."""
    return XeroClient("org123", mock_credentials)


@pytest.fixture
def mock_xero_invoice():
    """Create a mock Xero invoice."""
    return {
        "InvoiceID": "12345678-1234-1234-1234-123456789012",
        "InvoiceNumber": "INV-001",
        "Type": "ACCREC",
        "Status": "AUTHORISED",
        "InvoiceDate": "2025-01-15T00:00:00Z",
        "DueDate": "2025-02-15T00:00:00Z",
        "Total": "1000.00",
        "TaxTotal": "200.00",
        "Description": "Service provided",
        "Contact": {"ContactID": "contact-123"},
        "LineItems": [
            {
                "Description": "Service",
                "Quantity": 1,
                "UnitAmount": "1000.00",
                "AccountCode": "4000",
                "TaxType": "Tax on Sales",
                "TaxAmount": "200.00",
                "LineAmount": "1000.00",
            }
        ],
        "LineAmountTypes": "Exclusive",
        "HasAttachments": False,
        "UpdatedDateUTC": "2025-01-15T10:30:00Z",
    }


@pytest.fixture
def mock_xero_contact():
    """Create a mock Xero contact."""
    return {
        "ContactID": "contact-123",
        "Name": "ACME Corp",
        "EmailAddress": "hello@acme.com",
        "Phones": [{"PhoneNumber": "01234567890"}],
        "ContactGroups": ["CUSTOMER"],
        "TaxNumber": "123456789",
        "ContactNumber": "CUST-001",
        "Website": "www.acme.com",
        "ContactStatus": "ACTIVE",
        "Addresses": [
            {
                "AddressType": "STREET",
                "AddressLine1": "123 Main St",
                "AddressLine2": "Suite 100",
                "City": "London",
                "PostalCode": "SW1A1AA",
                "PostalCodeCountry": "GB",
            }
        ],
        "UpdatedDateUTC": "2025-01-15T10:30:00Z",
    }


@pytest.fixture
def mock_xero_account():
    """Create a mock Xero account."""
    return {
        "AccountID": "acc-123",
        "Code": "4000",
        "Name": "Sales Income",
        "Type": "REVENUE",
        "Status": "ACTIVE",
        "TaxType": "Tax on Sales",
        "SystemAccount": False,
        "EnablePayments": True,
        "UpdatedDateUTC": "2025-01-15T10:30:00Z",
    }


# ============================================================================
# TESTS FOR XEROMAPPER
# ============================================================================


class TestXeroMapper:
    """Tests for XeroMapper data transformation."""

    def test_map_invoice_to_transaction_accrec(self, mock_xero_invoice):
        """Test mapping Xero ACCREC invoice to StandardTransaction."""
        mapper = XeroMapper()
        txn = mapper.map_invoice_to_transaction(mock_xero_invoice)

        assert txn.id == "12345678-1234-1234-1234-123456789012"
        assert txn.type == TransactionType.INVOICE
        assert txn.reference == "INV-001"
        assert txn.status == "approved"
        assert txn.amount == Decimal("1000.00")
        assert txn.tax_amount == Decimal("200.00")
        assert txn.contact_id == "contact-123"
        assert txn.account_id == "4000"
        assert txn.platform_name == "xero"
        assert txn.platform_id == "12345678-1234-1234-1234-123456789012"
        assert txn.sync_status == SyncStatus.SYNCED

    def test_map_invoice_to_transaction_accpay(self, mock_xero_invoice):
        """Test mapping Xero ACCPAY invoice (bill) to StandardTransaction."""
        mock_xero_invoice["Type"] = "ACCPAY"
        mock_xero_invoice["InvoiceNumber"] = "BILL-001"

        mapper = XeroMapper()
        txn = mapper.map_invoice_to_transaction(mock_xero_invoice)

        assert txn.type == TransactionType.BILL
        assert txn.reference == "BILL-001"

    def test_map_invoice_status_mapping(self):
        """Test all invoice status mappings."""
        mapper = XeroMapper()

        status_map = {
            "DRAFT": "draft",
            "SUBMITTED": "submitted",
            "AUTHORISED": "approved",
            "PAID": "paid",
            "AWAITING_PAYMENT": "awaiting_payment",
            "VOIDED": "cancelled",
            "DELETED": "deleted",
        }

        for xero_status, expected_status in status_map.items():
            assert mapper._map_invoice_status(xero_status) == expected_status

    def test_map_contact_to_standard(self, mock_xero_contact):
        """Test mapping Xero contact to StandardContact."""
        mapper = XeroMapper()
        contact = mapper.map_contact_to_standard(mock_xero_contact)

        assert contact.id == "contact-123"
        assert contact.name == "ACME Corp"
        assert contact.email == "hello@acme.com"
        assert contact.phone == "01234567890"
        assert contact.type == ContactType.CUSTOMER
        assert contact.tax_id == "123456789"
        assert contact.currency == "GBP"
        assert contact.platform_name == "xero"
        assert "123 Main St" in contact.address
        assert "London" in contact.address

    def test_map_contact_type_inference_supplier(self):
        """Test contact type inference for supplier."""
        mapper = XeroMapper()
        contact = {
            "ContactID": "sup-123",
            "Name": "Supplier Corp",
            "ContactGroups": ["SUPPLIER"],
            "Addresses": [],
            "Phones": [],
        }

        result = mapper.map_contact_to_standard(contact)
        assert result.type == ContactType.SUPPLIER

    def test_map_contact_type_inference_pobox(self):
        """Test contact type inference from PO BOX address."""
        mapper = XeroMapper()
        contact = {
            "ContactID": "sup-456",
            "Name": "PO Box Supplier",
            "ContactGroups": [],
            "Addresses": [
                {
                    "AddressType": "STREET",
                    "AddressLine1": "PO BOX 123",
                    "City": "London",
                }
            ],
            "Phones": [],
        }

        result = mapper.map_contact_to_standard(contact)
        assert result.type == ContactType.SUPPLIER

    def test_map_account_to_standard(self, mock_xero_account):
        """Test mapping Xero account to StandardAccount."""
        mapper = XeroMapper()
        account = mapper.map_account_to_standard(mock_xero_account)

        assert account.id == "acc-123"
        assert account.code == "4000"
        assert account.name == "Sales Income"
        assert account.type == AccountType.INCOME
        assert account.currency == "GBP"
        assert account.tax_type == "Tax on Sales"
        assert account.platform_name == "xero"
        assert account.platform_id == "acc-123"

    def test_map_account_type_mapping(self):
        """Test all account type mappings."""
        mapper = XeroMapper()

        type_map = {
            "ASSET": AccountType.ASSET,
            "BANK": AccountType.BANK,
            "EXPENSE": AccountType.EXPENSE,
            "REVENUE": AccountType.INCOME,
            "EQUITY": AccountType.EQUITY,
            "LIABILITY": AccountType.LIABILITY,
        }

        for xero_type, expected_type in type_map.items():
            assert mapper._map_account_type(xero_type) == expected_type

    def test_parse_xero_date(self):
        """Test parsing Xero ISO 8601 dates."""
        mapper = XeroMapper()

        result = mapper._parse_xero_date("2025-01-15T00:00:00Z")
        assert result == date(2025, 1, 15)

        result = mapper._parse_xero_date("")
        assert result is None

        result = mapper._parse_xero_date("invalid")
        assert result is None

    def test_map_line_items(self, mock_xero_invoice):
        """Test line item extraction and transformation."""
        mapper = XeroMapper()
        txn = mapper.map_invoice_to_transaction(mock_xero_invoice)

        assert len(txn.line_items) == 1
        line_item = txn.line_items[0]
        assert line_item["description"] == "Service"
        assert line_item["quantity"] == 1.0
        assert line_item["unit_amount"] == "1000.00"
        assert line_item["account_code"] == "4000"


# ============================================================================
# TESTS FOR XEROCLIENT AUTHENTICATION
# ============================================================================


class TestXeroClientAuthentication:
    """Tests for XeroClient authentication."""

    def test_client_initialization(self, mock_credentials):
        """Test XeroClient initialization."""
        client = XeroClient("org123", mock_credentials)

        assert client.organization_id == "org123"
        assert client.PLATFORM_NAME == "xero"
        assert isinstance(client.auth, XeroAuth)
        assert isinstance(client.mapper, XeroMapper)

    def test_validate_credentials_success(self, mock_credentials):
        """Test successful credentials validation."""
        client = XeroClient("org123", mock_credentials)
        # Should not raise
        client._validate_credentials()

    def test_validate_credentials_missing(self):
        """Test credentials validation with missing field."""
        credentials = {
            "client_id": "test_id",
            # Missing client_secret and redirect_uri
        }

        with pytest.raises(ValidationError):
            XeroClient("org123", credentials)

    def test_authenticate_not_authenticated(self, xero_client):
        """Test authenticate method when not authenticated."""
        assert xero_client.authenticate() is False

    @patch("backend.accounting.xero.auth.XeroAuth.get_access_token")
    def test_authenticate_success(self, mock_get_token, xero_client):
        """Test successful authentication."""
        mock_get_token.return_value = "test_token_123"

        assert xero_client.authenticate() is True

    @patch("backend.accounting.xero.auth.XeroAuth.get_access_token")
    def test_authenticate_exception_handling(self, mock_get_token, xero_client):
        """Test authentication with exception."""
        mock_get_token.side_effect = Exception("Token error")

        assert xero_client.authenticate() is False


# ============================================================================
# TESTS FOR XEROCLIENT TRANSACTIONS
# ============================================================================


class TestXeroClientTransactions:
    """Tests for transaction-related methods."""

    @patch("backend.accounting.xero.client.requests.request")
    def test_get_transactions(self, mock_request, xero_client, mock_xero_invoice):
        """Test getting transactions."""
        # Setup
        xero_client.auth.tokens = {
            "access_token": "test_token",
            "tenant_id": "test_tenant",
            "expires_at": datetime.now() + timedelta(hours=1),
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-Rate-Limit-Remaining-Minute": "59"}
        mock_response.json.return_value = {"Invoices": [mock_xero_invoice]}
        mock_request.return_value = mock_response

        # Test
        txns = xero_client.get_transactions(date(2025, 1, 1), date(2025, 1, 31))

        assert len(txns) > 0
        assert txns[0].type == TransactionType.INVOICE

    @patch("backend.accounting.xero.client.requests.request")
    def test_get_transaction_not_found(self, mock_request, xero_client):
        """Test getting single transaction not found."""
        xero_client.auth.tokens = {
            "access_token": "test_token",
            "tenant_id": "test_tenant",
            "expires_at": datetime.now() + timedelta(hours=1),
        }

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        result = xero_client.get_transaction("nonexistent-id")
        assert result is None

    def test_create_transaction_not_implemented(self, xero_client):
        """Test that create_transaction raises NotImplementedError."""
        txn = StandardTransaction(
            id="test",
            type=TransactionType.INVOICE,
            date=date(2025, 1, 1),
            description="Test",
            amount=Decimal("100"),
            tax_amount=Decimal("20"),
            account_id="4000",
        )

        with pytest.raises(NotImplementedError):
            xero_client.create_transaction(txn)

    def test_update_transaction_not_implemented(self, xero_client):
        """Test that update_transaction raises NotImplementedError."""
        txn = StandardTransaction(
            id="test",
            type=TransactionType.INVOICE,
            date=date(2025, 1, 1),
            description="Test",
            amount=Decimal("100"),
            tax_amount=Decimal("20"),
            account_id="4000",
        )

        with pytest.raises(NotImplementedError):
            xero_client.update_transaction("test-id", txn)


# ============================================================================
# TESTS FOR XEROCLIENT CONTACTS AND ACCOUNTS
# ============================================================================


class TestXeroClientContactsAndAccounts:
    """Tests for contact and account methods."""

    @patch("backend.accounting.xero.client.requests.request")
    def test_get_contacts(self, mock_request, xero_client, mock_xero_contact):
        """Test getting contacts."""
        xero_client.auth.tokens = {
            "access_token": "test_token",
            "tenant_id": "test_tenant",
            "expires_at": datetime.now() + timedelta(hours=1),
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {"Contacts": [mock_xero_contact]}
        mock_request.return_value = mock_response

        contacts = xero_client.get_contacts()

        assert len(contacts) > 0
        assert contacts[0].type == ContactType.CUSTOMER

    @patch("backend.accounting.xero.client.requests.request")
    def test_get_accounts(self, mock_request, xero_client, mock_xero_account):
        """Test getting accounts."""
        xero_client.auth.tokens = {
            "access_token": "test_token",
            "tenant_id": "test_tenant",
            "expires_at": datetime.now() + timedelta(hours=1),
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {"Accounts": [mock_xero_account]}
        mock_request.return_value = mock_response

        accounts = xero_client.get_accounts()

        assert len(accounts) > 0
        assert accounts[0].type == AccountType.INCOME

    def test_create_contact_not_implemented(self, xero_client):
        """Test that create_contact raises NotImplementedError."""
        contact = StandardContact(
            id="test",
            type=ContactType.CUSTOMER,
            name="Test Customer",
        )

        with pytest.raises(NotImplementedError):
            xero_client.create_contact(contact)

    def test_update_contact_not_implemented(self, xero_client):
        """Test that update_contact raises NotImplementedError."""
        contact = StandardContact(
            id="test",
            type=ContactType.CUSTOMER,
            name="Test Customer",
        )

        with pytest.raises(NotImplementedError):
            xero_client.update_contact("test-id", contact)


# ============================================================================
# TESTS FOR ERROR HANDLING
# ============================================================================


class TestXeroClientErrorHandling:
    """Tests for error handling."""

    @patch("backend.accounting.xero.client.requests.request")
    def test_authentication_error_401(self, mock_request, xero_client):
        """Test 401 raises AuthenticationError."""
        xero_client.auth.tokens = {
            "access_token": "test_token",
            "tenant_id": "test_tenant",
            "expires_at": datetime.now(),
        }

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response

        with pytest.raises(AuthenticationError):
            xero_client._make_request("GET", "https://api.xero.com/test")

    @patch("backend.accounting.xero.client.requests.request")
    def test_rate_limit_error_429(self, mock_request, xero_client):
        """Test 429 raises RateLimitError."""
        xero_client.auth.tokens = {
            "access_token": "test_token",
            "tenant_id": "test_tenant",
            "expires_at": datetime.now() + timedelta(hours=1),
        }

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_request.return_value = mock_response

        with pytest.raises(RateLimitError):
            xero_client._make_request("GET", "https://api.xero.com/test")

    @patch("backend.accounting.xero.client.requests.request")
    def test_not_found_error_404(self, mock_request, xero_client):
        """Test 404 raises NotFoundError."""
        xero_client.auth.tokens = {
            "access_token": "test_token",
            "tenant_id": "test_tenant",
            "expires_at": datetime.now() + timedelta(hours=1),
        }

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        with pytest.raises(NotFoundError):
            xero_client._make_request("GET", "https://api.xero.com/test")

    @patch("backend.accounting.xero.client.requests.request")
    def test_api_error_generic(self, mock_request, xero_client):
        """Test generic API error handling."""
        xero_client.auth.tokens = {
            "access_token": "test_token",
            "tenant_id": "test_tenant",
            "expires_at": datetime.now() + timedelta(hours=1),
        }

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_request.return_value = mock_response

        with pytest.raises(APIError):
            xero_client._make_request("GET", "https://api.xero.com/test")

    def test_not_authenticated_error(self, xero_client):
        """Test error when not authenticated."""
        with pytest.raises(AuthenticationError):
            xero_client._make_request("GET", "https://api.xero.com/test")


# ============================================================================
# TESTS FOR ORGANIZATION INFO
# ============================================================================


class TestXeroClientOrganization:
    """Tests for organization info methods."""

    @patch("backend.accounting.xero.client.requests.request")
    def test_get_organization_info(self, mock_request, xero_client):
        """Test getting organization information."""
        xero_client.auth.tokens = {
            "access_token": "test_token",
            "tenant_id": "test_tenant",
            "expires_at": datetime.now() + timedelta(hours=1),
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {
            "Organisations": [
                {
                    "OrganisationID": "org-123",
                    "Name": "Test Org",
                    "LegalName": "Test Org Ltd",
                    "CountryCode": "GB",
                    "TaxNumber": "123456789",
                    "RegistrationNumber": "12345678",
                    "BaseCurrency": "GBP",
                    "OrganisationStatus": "ACTIVE",
                }
            ]
        }
        mock_request.return_value = mock_response

        info = xero_client.get_organization_info()

        assert info["id"] == "org-123"
        assert info["name"] == "Test Org"
        assert info["country_code"] == "GB"

    def test_get_sync_status(self, xero_client):
        """Test getting sync status."""
        status = xero_client.get_sync_status()

        assert "last_sync" in status
        assert "next_sync" in status
        assert "rate_limit_remaining" in status
        assert "authenticated" in status


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestXeroClientIntegration:
    """Integration tests for XeroClient."""

    def test_client_extends_accounting_client(self, xero_client):
        """Test that XeroClient extends AccountingClient."""
        from backend.accounting import AccountingClient

        assert isinstance(xero_client, AccountingClient)

    def test_client_implements_all_abstract_methods(self, xero_client):
        """Test that XeroClient implements all abstract methods."""
        # Check that all abstract methods are implemented
        assert hasattr(xero_client, "authenticate")
        assert hasattr(xero_client, "get_transactions")
        assert hasattr(xero_client, "get_transaction")
        assert hasattr(xero_client, "create_transaction")
        assert hasattr(xero_client, "update_transaction")
        assert hasattr(xero_client, "get_accounts")
        assert hasattr(xero_client, "get_account")
        assert hasattr(xero_client, "get_contacts")
        assert hasattr(xero_client, "get_contact")
        assert hasattr(xero_client, "create_contact")
        assert hasattr(xero_client, "update_contact")
        assert hasattr(xero_client, "get_organization_info")
        assert hasattr(xero_client, "get_sync_status")

    def test_mapper_handles_missing_fields(self):
        """Test mapper gracefully handles missing fields."""
        mapper = XeroMapper()

        minimal_invoice = {
            "InvoiceID": "test-id",
            "Type": "ACCREC",
        }

        txn = mapper.map_invoice_to_transaction(minimal_invoice)
        assert txn.id == "test-id"
        assert txn.type == TransactionType.INVOICE

    def test_contact_filtering_by_type(self, xero_client):
        """Test that contact filtering works correctly."""
        # Create mock contacts of different types
        contacts_mock = [
            {
                "ContactID": "cust-1",
                "Name": "Customer",
                "ContactGroups": ["CUSTOMER"],
                "Addresses": [],
                "Phones": [],
            },
            {
                "ContactID": "supp-1",
                "Name": "Supplier",
                "ContactGroups": ["SUPPLIER"],
                "Addresses": [],
                "Phones": [],
            },
        ]

        mapper = XeroMapper()
        mapped = [mapper.map_contact_to_standard(c) for c in contacts_mock]

        customers = [c for c in mapped if c.type == ContactType.CUSTOMER]
        suppliers = [c for c in mapped if c.type == ContactType.SUPPLIER]

        assert len(customers) == 1
        assert len(suppliers) == 1
