"""Comprehensive tests for QuickBooks Online adapter."""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from backend.accounting.quickbooks.client import QuickBooksClient
from backend.accounting.quickbooks.mapper import QuickBooksMapper
from backend.accounting.quickbooks.auth import QuickBooksAuth
from backend.accounting import (
    StandardTransaction,
    StandardContact,
    StandardAccount,
    TransactionType,
    ContactType,
    AccountType,
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)


class TestQuickBooksMapper:
    """Tests for QuickBooks data mapping."""

    def test_map_invoice_to_transaction(self):
        """Test invoice mapping to standard transaction."""
        invoice = {
            "Id": "123",
            "DocNumber": "INV-001",
            "TxnDate": "2025-01-15",
            "TotalAmt": 1200.00,
            "TxnTaxDetail": {"TotalTax": 200.00},
            "DocStatus": "Posted",
            "CustomerRef": {"value": "cust-1"},
        }
        txn = QuickBooksMapper.map_invoice_to_transaction(invoice)

        assert txn.id == "123"
        assert txn.type == TransactionType.INVOICE
        assert txn.amount == Decimal("1200.00")
        assert txn.tax_amount == Decimal("200.00")
        assert txn.contact_id == "cust-1"
        assert txn.status == "approved"

    def test_map_bill_to_transaction(self):
        """Test bill mapping to standard transaction."""
        bill = {
            "Id": "456",
            "DocNumber": "BILL-001",
            "TxnDate": "2025-01-20",
            "TotalAmt": 500.00,
            "TxnTaxDetail": {"TotalTax": 50.00},
            "DocStatus": "Processed",
            "VendorRef": {"value": "vendor-1"},
        }
        txn = QuickBooksMapper.map_bill_to_transaction(bill)

        assert txn.id == "456"
        assert txn.type == TransactionType.BILL
        assert txn.amount == Decimal("500.00")
        assert txn.tax_amount == Decimal("50.00")
        assert txn.contact_id == "vendor-1"
        assert txn.status == "approved"

    def test_map_customer_to_standard_contact(self):
        """Test customer mapping to standard contact."""
        customer = {
            "Id": "cust-1",
            "DisplayName": "Acme Corp",
            "BillAddr": {
                "Line1": "123 Main St",
                "City": "Springfield",
                "PostalCode": "12345",
            },
            "PrimaryEmailAddr": [{"Address": "contact@acme.com"}],
            "PrimaryPhone": [{"FreeFormNumber": "555-1234"}],
            "ResaleNum": "TAX-123",
        }
        contact = QuickBooksMapper.map_customer_to_standard(customer)

        assert contact.id == "cust-1"
        assert contact.name == "Acme Corp"
        assert contact.type == ContactType.CUSTOMER
        assert contact.email == "contact@acme.com"
        assert contact.phone == "555-1234"
        assert contact.tax_id == "TAX-123"
        assert "123 Main St" in contact.address

    def test_map_vendor_to_standard_contact(self):
        """Test vendor mapping to standard contact."""
        vendor = {
            "Id": "vendor-1",
            "DisplayName": "Office Supplies Inc",
            "BillAddr": {
                "Line1": "456 Oak Ave",
                "City": "Shelbyville",
            },
            "PrimaryEmailAddr": [{"Address": "sales@office.com"}],
            "PrimaryPhone": [{"FreeFormNumber": "555-5678"}],
            "TaxId": "TAX-456",
        }
        contact = QuickBooksMapper.map_vendor_to_standard(vendor)

        assert contact.id == "vendor-1"
        assert contact.name == "Office Supplies Inc"
        assert contact.type == ContactType.SUPPLIER
        assert contact.email == "sales@office.com"
        assert contact.phone == "555-5678"
        assert contact.tax_id == "TAX-456"

    def test_map_account_to_standard(self):
        """Test account mapping to standard format."""
        account = {
            "Id": "acct-1",
            "Name": "Cash",
            "AcctNum": "1000",
            "AccountType": "Bank",
            "TaxAccount": False,
        }
        acc = QuickBooksMapper.map_account_to_standard(account)

        assert acc.id == "acct-1"
        assert acc.code == "1000"
        assert acc.name == "Cash"
        assert acc.type == AccountType.BANK

    def test_map_invoice_status_all_values(self):
        """Test all QB invoice status mappings."""
        assert QuickBooksMapper._map_invoice_status("Draft") == "draft"
        assert QuickBooksMapper._map_invoice_status("Posted") == "approved"
        assert QuickBooksMapper._map_invoice_status("Paid") == "paid"
        assert QuickBooksMapper._map_invoice_status("Voided") == "voided"
        assert QuickBooksMapper._map_invoice_status("Unknown") == "approved"

    def test_map_bill_status_all_values(self):
        """Test all QB bill status mappings."""
        assert QuickBooksMapper._map_bill_status("Draft") == "draft"
        assert QuickBooksMapper._map_bill_status("Voided") == "voided"
        assert QuickBooksMapper._map_bill_status("Processed") == "approved"
        assert QuickBooksMapper._map_bill_status("Unknown") == "draft"

    def test_parse_qbo_date(self):
        """Test QB date parsing."""
        date_str = "2025-01-15T10:00:00Z"
        parsed = QuickBooksMapper._parse_qbo_date(date_str)
        assert parsed == date(2025, 1, 15)

    def test_parse_invalid_date_returns_today(self):
        """Test invalid date returns today."""
        parsed = QuickBooksMapper._parse_qbo_date("invalid")
        assert parsed == date.today()

    def test_map_account_type_all_types(self):
        """Test all QB account type mappings."""
        assert QuickBooksMapper._map_account_type("Asset") == AccountType.ASSET
        assert QuickBooksMapper._map_account_type("Bank") == AccountType.BANK
        assert QuickBooksMapper._map_account_type("Credit Card") == AccountType.LIABILITY
        assert QuickBooksMapper._map_account_type("Expense") == AccountType.EXPENSE
        assert QuickBooksMapper._map_account_type("Income") == AccountType.INCOME
        assert QuickBooksMapper._map_account_type("Equity") == AccountType.EQUITY
        assert QuickBooksMapper._map_account_type("Unknown") == AccountType.ASSET


class TestQuickBooksClientAuthentication:
    """Tests for QuickBooks authentication."""

    def test_client_initialization(self):
        """Test QuickBooks client initialization."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost/callback",
        }
        client = QuickBooksClient("org-123", creds)

        assert client.organization_id == "org-123"
        assert client.PLATFORM_NAME == "quickbooks"

    def test_client_with_existing_tokens(self):
        """Test client initialization with existing tokens."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost/callback",
            "access_token": "existing-token",
            "refresh_token": "refresh-token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        assert client.auth.tokens["access_token"] == "existing-token"
        assert client.auth.tokens["realm_id"] == "realm-123"

    def test_validate_credentials_missing_client_id(self):
        """Test validation with missing client_id."""
        from backend.accounting import ValidationError

        creds = {
            "client_secret": "secret",
            "redirect_uri": "http://localhost",
        }

        with pytest.raises(ValidationError):
            client = QuickBooksClient("org-123", creds)

    def test_authenticate_with_valid_token(self):
        """Test authentication check."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost/callback",
            "access_token": "valid-token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        assert client.authenticate() is True

    def test_authenticate_without_token(self):
        """Test authentication check without token."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost/callback",
        }
        client = QuickBooksClient("org-123", creds)

        assert client.authenticate() is False

    def test_auth_generates_proper_url(self):
        """Test authorization URL generation."""
        auth = QuickBooksAuth("client-id", "client-secret", "http://localhost")
        auth_url, state = auth.get_authorization_url()

        assert "appcenter.intuit.com" in auth_url
        assert "client_id=client-id" in auth_url
        assert state is not None


class TestQuickBooksClientTransactions:
    """Tests for transaction operations."""

    @patch('backend.accounting.quickbooks.client.requests.request')
    def test_get_transactions_invoices_and_bills(self, mock_request):
        """Test getting transactions (invoices and bills)."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
            "access_token": "token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        invoice_response = {
            "QueryResponse": {
                "Invoice": [
                    {
                        "Id": "inv-1",
                        "DocNumber": "INV-001",
                        "TxnDate": "2025-01-15",
                        "TotalAmt": 1000.00,
                        "TxnTaxDetail": {"TotalTax": 100.00},
                        "DocStatus": "Posted",
                        "CustomerRef": {"value": "cust-1"},
                    }
                ]
            }
        }

        bill_response = {
            "QueryResponse": {
                "Bill": [
                    {
                        "Id": "bill-1",
                        "DocNumber": "BILL-001",
                        "TxnDate": "2025-01-20",
                        "TotalAmt": 500.00,
                        "TxnTaxDetail": {"TotalTax": 50.00},
                        "DocStatus": "Processed",
                        "VendorRef": {"value": "vendor-1"},
                    }
                ]
            }
        }

        mock_request.side_effect = [
            Mock(status_code=200, json=Mock(return_value=invoice_response)),
            Mock(status_code=200, json=Mock(return_value=bill_response)),
        ]

        txns = client.get_transactions(
            date(2025, 1, 1),
            date(2025, 1, 31),
            limit=100
        )

        assert len(txns) == 2
        assert txns[0].type == TransactionType.INVOICE
        assert txns[1].type == TransactionType.BILL

    @patch('backend.accounting.quickbooks.client.requests.request')
    def test_get_transaction_by_id_invoice(self, mock_request):
        """Test getting single transaction by ID."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
            "access_token": "token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        response = {
            "QueryResponse": {
                "Invoice": [
                    {
                        "Id": "inv-1",
                        "DocNumber": "INV-001",
                        "TxnDate": "2025-01-15",
                        "TotalAmt": 1000.00,
                        "TxnTaxDetail": {"TotalTax": 100.00},
                        "DocStatus": "Posted",
                        "CustomerRef": {"value": "cust-1"},
                    }
                ]
            }
        }

        mock_request.return_value = Mock(
            status_code=200,
            json=Mock(return_value=response)
        )

        txn = client.get_transaction("inv-1")

        assert txn is not None
        assert txn.id == "inv-1"
        assert txn.type == TransactionType.INVOICE

    def test_create_transaction_not_implemented(self):
        """Test that create_transaction raises NotImplementedError."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
        }
        client = QuickBooksClient("org-123", creds)

        txn = StandardTransaction(
            id="test",
            type=TransactionType.INVOICE,
            date=date.today(),
            description="Test",
            amount=Decimal("100"),
            tax_amount=Decimal("10"),
            account_id="1000",
        )

        with pytest.raises(NotImplementedError):
            client.create_transaction(txn)

    def test_update_transaction_not_implemented(self):
        """Test that update_transaction raises NotImplementedError."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
        }
        client = QuickBooksClient("org-123", creds)

        txn = StandardTransaction(
            id="test",
            type=TransactionType.INVOICE,
            date=date.today(),
            description="Test",
            amount=Decimal("100"),
            tax_amount=Decimal("10"),
            account_id="1000",
        )

        with pytest.raises(NotImplementedError):
            client.update_transaction("test", txn)

    @patch('backend.accounting.quickbooks.client.requests.request')
    def test_get_transaction_not_found(self, mock_request):
        """Test getting non-existent transaction."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
            "access_token": "token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        mock_request.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"QueryResponse": {"Invoice": []}})
        )

        txn = client.get_transaction("nonexistent")

        assert txn is None


class TestQuickBooksClientContactsAndAccounts:
    """Tests for contacts and accounts operations."""

    @patch('backend.accounting.quickbooks.client.requests.request')
    def test_get_contacts_customers_and_vendors(self, mock_request):
        """Test getting both customers and vendors."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
            "access_token": "token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        customer_response = {
            "QueryResponse": {
                "Customer": [
                    {
                        "Id": "cust-1",
                        "DisplayName": "Acme Corp",
                        "BillAddr": {"Line1": "123 Main St"},
                        "PrimaryEmailAddr": [{"Address": "contact@acme.com"}],
                        "ResaleNum": "TAX-123",
                    }
                ]
            }
        }

        vendor_response = {
            "QueryResponse": {
                "Vendor": [
                    {
                        "Id": "vendor-1",
                        "DisplayName": "Supplies Inc",
                        "BillAddr": {"Line1": "456 Oak Ave"},
                        "PrimaryEmailAddr": [{"Address": "sales@supplies.com"}],
                        "TaxId": "TAX-456",
                    }
                ]
            }
        }

        mock_request.side_effect = [
            Mock(status_code=200, json=Mock(return_value=customer_response)),
            Mock(status_code=200, json=Mock(return_value=vendor_response)),
        ]

        contacts = client.get_contacts(limit=100)

        assert len(contacts) == 2
        assert contacts[0].type == ContactType.CUSTOMER
        assert contacts[1].type == ContactType.SUPPLIER

    @patch('backend.accounting.quickbooks.client.requests.request')
    def test_get_contact_by_id(self, mock_request):
        """Test getting single contact by ID."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
            "access_token": "token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        response = {
            "QueryResponse": {
                "Customer": [
                    {
                        "Id": "cust-1",
                        "DisplayName": "Acme Corp",
                        "BillAddr": {},
                        "ResaleNum": "TAX-123",
                    }
                ]
            }
        }

        mock_request.return_value = Mock(
            status_code=200,
            json=Mock(return_value=response)
        )

        contact = client.get_contact("cust-1")

        assert contact is not None
        assert contact.id == "cust-1"
        assert contact.type == ContactType.CUSTOMER

    def test_create_contact_not_implemented(self):
        """Test that create_contact raises NotImplementedError."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
        }
        client = QuickBooksClient("org-123", creds)

        contact = StandardContact(
            id="test",
            name="Test Contact",
            type=ContactType.CUSTOMER,
        )

        with pytest.raises(NotImplementedError):
            client.create_contact(contact)

    def test_update_contact_not_implemented(self):
        """Test that update_contact raises NotImplementedError."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
        }
        client = QuickBooksClient("org-123", creds)

        contact = StandardContact(
            id="test",
            name="Test Contact",
            type=ContactType.CUSTOMER,
        )

        with pytest.raises(NotImplementedError):
            client.update_contact("test", contact)

    @patch('backend.accounting.quickbooks.client.requests.request')
    def test_get_accounts(self, mock_request):
        """Test getting accounts."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
            "access_token": "token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        response = {
            "QueryResponse": {
                "Account": [
                    {
                        "Id": "acct-1",
                        "Name": "Cash",
                        "AcctNum": "1000",
                        "AccountType": "Bank",
                    },
                    {
                        "Id": "acct-2",
                        "Name": "Accounts Receivable",
                        "AcctNum": "1200",
                        "AccountType": "Asset",
                    }
                ]
            }
        }

        mock_request.return_value = Mock(
            status_code=200,
            json=Mock(return_value=response)
        )

        accounts = client.get_accounts()

        assert len(accounts) == 2
        assert accounts[0].type == AccountType.BANK
        assert accounts[1].type == AccountType.ASSET

    @patch('backend.accounting.quickbooks.client.requests.request')
    def test_get_account_by_id(self, mock_request):
        """Test getting single account by ID."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
            "access_token": "token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        response = {
            "QueryResponse": {
                "Account": [
                    {
                        "Id": "acct-1",
                        "Name": "Cash",
                        "AcctNum": "1000",
                        "AccountType": "Bank",
                    }
                ]
            }
        }

        mock_request.return_value = Mock(
            status_code=200,
            json=Mock(return_value=response)
        )

        account = client.get_account("acct-1")

        assert account is not None
        assert account.id == "acct-1"
        assert account.type == AccountType.BANK


class TestQuickBooksClientErrorHandling:
    """Tests for error handling."""

    def test_authentication_error_missing_realm_id(self):
        """Test AuthenticationError when realm_id is missing."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
            "access_token": "token",
        }
        client = QuickBooksClient("org-123", creds)

        with pytest.raises(AuthenticationError):
            client.get_organization_info()

    def test_not_found_error_on_empty_result(self):
        """Test getting non-existent transaction returns None."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
            "access_token": "token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        with patch('backend.accounting.quickbooks.client.requests.request') as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                json=Mock(return_value={"QueryResponse": {"Invoice": []}})
            )
            result = client.get_transaction("nonexistent")
            assert result is None

    @patch('backend.accounting.quickbooks.client.requests.request')
    def test_rate_limit_handling(self, mock_request):
        """Test rate limit tracking."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
            "access_token": "token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        response = {
            "QueryResponse": {
                "Invoice": []
            }
        }

        mock_request.return_value = Mock(
            status_code=200,
            json=Mock(return_value=response)
        )

        client.get_transactions(date(2025, 1, 1), date(2025, 1, 31))
        sync_status = client.get_sync_status()
        assert "rate_limit_remaining" in sync_status

    def test_validation_error_missing_credentials(self):
        """Test ValidationError on missing required credentials."""
        from backend.accounting import ValidationError

        creds = {
            "client_id": "test-id",
            # Missing client_secret
            "redirect_uri": "http://localhost",
        }

        with pytest.raises(ValidationError):
            QuickBooksClient("org-123", creds)

    def test_api_error_on_bad_request(self):
        """Test APIError on bad request."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
            "access_token": "token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        with patch('backend.accounting.quickbooks.client.requests.request') as mock_request:
            mock_request.return_value = Mock(
                status_code=400,
                json=Mock(return_value={
                    "Fault": {
                        "Error": [{"Message": "Invalid query"}]
                    }
                }),
                text="Bad Request"
            )

            with pytest.raises(APIError):
                # Call _make_request directly to avoid exception catching in _get_invoices
                client._make_request("GET", "http://test", params={})

    def test_timeout_error_handling(self):
        """Test APIError on request timeout."""
        import requests

        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
            "access_token": "token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        with patch('backend.accounting.quickbooks.client.requests.request') as mock_request:
            mock_request.side_effect = requests.exceptions.Timeout()

            with pytest.raises(APIError):
                # Call _make_request directly to avoid exception catching in _get_invoices
                client._make_request("GET", "http://test", params={})


class TestQuickBooksClientOrganization:
    """Tests for organization information."""

    @patch('backend.accounting.quickbooks.client.requests.request')
    def test_get_organization_info(self, mock_request):
        """Test getting organization information."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
            "access_token": "token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        response = {
            "CompanyInfo": {
                "CompanyName": "Test Company",
                "Country": "US",
                "PreferredDeliveryMethod": "EMAIL",
            }
        }

        mock_request.return_value = Mock(
            status_code=200,
            json=Mock(return_value=response)
        )

        org_info = client.get_organization_info()

        assert org_info["id"] == "realm-123"
        assert org_info["name"] == "Test Company"
        assert org_info["status"] == "ACTIVE"

    def test_get_sync_status(self):
        """Test getting sync status."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
            "access_token": "token",
            "realm_id": "realm-123",
        }
        client = QuickBooksClient("org-123", creds)

        status = client.get_sync_status()

        assert "rate_limit_remaining" in status
        assert "authenticated" in status


class TestQuickBooksClientIntegration:
    """Tests for interface compliance and integration."""

    def test_quickbooks_client_implements_interface(self):
        """Test that QuickBooksClient implements AccountingClient interface."""
        from backend.accounting import AccountingClient

        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
        }
        client = QuickBooksClient("org-123", creds)

        assert isinstance(client, AccountingClient)

    def test_platform_name_is_set(self):
        """Test that PLATFORM_NAME is set correctly."""
        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
        }
        client = QuickBooksClient("org-123", creds)

        assert client.PLATFORM_NAME == "quickbooks"

    def test_factory_can_create_quickbooks_client(self):
        """Test that factory can create QuickBooksClient."""
        from backend.accounting import AccountingClientFactory

        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
        }

        client = AccountingClientFactory.create_from_platform(
            "quickbooks",
            "org-123",
            creds
        )

        assert client is not None
        assert client.PLATFORM_NAME == "quickbooks"
        assert client.organization_id == "org-123"

    def test_all_abstract_methods_implemented(self):
        """Test that all abstract methods are implemented."""
        from backend.accounting import AccountingClient
        import inspect

        creds = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uri": "http://localhost",
        }
        client = QuickBooksClient("org-123", creds)

        # Get all abstract methods from AccountingClient
        abstract_methods = [
            method for method in dir(AccountingClient)
            if not method.startswith('_') and callable(getattr(AccountingClient, method))
        ]

        # Verify they're all implemented
        for method_name in abstract_methods:
            assert hasattr(client, method_name), f"Missing method: {method_name}"
            method = getattr(client, method_name)
            assert callable(method), f"{method_name} is not callable"
