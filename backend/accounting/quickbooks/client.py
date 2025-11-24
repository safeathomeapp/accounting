"""QuickBooks Online accounting adapter implementation."""

import requests
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta

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

from .auth import QuickBooksAuth
from .mapper import QuickBooksMapper


class QuickBooksClient(AccountingClient):
    """QuickBooks Online adapter implementing AccountingClient interface."""

    PLATFORM_NAME = "quickbooks"
    QBO_BASE_URL = "https://quickbooks.api.intuit.com/v2/company"

    def __init__(self, organization_id: str, credentials: Dict[str, Any]):
        """Initialize QuickBooksClient."""
        super().__init__(organization_id, credentials)
        self.auth = QuickBooksAuth(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            redirect_uri=credentials.get(
                "redirect_uri", "http://localhost:8000/auth/quickbooks/callback"
            ),
        )
        if credentials.get("access_token"):
            self.auth.tokens = {
                "access_token": credentials["access_token"],
                "refresh_token": credentials.get("refresh_token"),
                "realm_id": credentials.get("realm_id"),
                "expires_at": datetime.now() + timedelta(hours=1),
            }
        self.mapper = QuickBooksMapper()
        self._rate_limit_remaining = 10000

    def _validate_credentials(self) -> None:
        """Validate that required credentials are present."""
        required = ["client_id", "client_secret", "redirect_uri"]
        for key in required:
            if key not in self.credentials:
                raise ValidationError(f"Missing credential: {key}")

    def authenticate(self) -> bool:
        """Check if currently authenticated."""
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
        """Get transactions from QuickBooks."""
        transactions = []

        if self._should_fetch_type(transaction_types, TransactionType.INVOICE):
            invoices = self._get_invoices(start_date, end_date, limit)
            transactions.extend(invoices)

        if self._should_fetch_type(transaction_types, TransactionType.BILL):
            bills = self._get_bills(start_date, end_date, limit)
            transactions.extend(bills)

        return transactions[:limit]

    def get_transaction(self, transaction_id: str) -> Optional[StandardTransaction]:
        """Get single transaction by ID."""
        # Try invoice first
        try:
            query = f"SELECT * FROM Invoice WHERE Id = '{transaction_id}'"
            response = self._make_query_request(query)
            if response.get("QueryResponse", {}).get("Invoice"):
                return self.mapper.map_invoice_to_transaction(
                    response["QueryResponse"]["Invoice"][0]
                )
        except (NotFoundError, KeyError):
            pass

        # Try bill
        try:
            query = f"SELECT * FROM Bill WHERE Id = '{transaction_id}'"
            response = self._make_query_request(query)
            if response.get("QueryResponse", {}).get("Bill"):
                return self.mapper.map_bill_to_transaction(
                    response["QueryResponse"]["Bill"][0]
                )
        except (NotFoundError, KeyError):
            pass

        return None

    def create_transaction(self, transaction: StandardTransaction) -> StandardTransaction:
        """Create transaction - Not implemented (read-only Phase 1)."""
        raise NotImplementedError("Phase 1: Read-only access to QuickBooks")

    def update_transaction(
        self, transaction_id: str, transaction: StandardTransaction
    ) -> StandardTransaction:
        """Update transaction - Not implemented (read-only Phase 1)."""
        raise NotImplementedError("Phase 1: Read-only access to QuickBooks")

    def get_accounts(
        self, account_types: Optional[List[str]] = None
    ) -> List[StandardAccount]:
        """Get chart of accounts from QuickBooks."""
        query = "SELECT * FROM Account WHERE Active = true"
        response = self._make_query_request(query)

        accounts = []
        for account_data in response.get("QueryResponse", {}).get("Account", []):
            if account_types and account_data.get("AccountType") not in account_types:
                continue
            account = self.mapper.map_account_to_standard(account_data)
            accounts.append(account)

        return accounts

    def get_account(self, account_id: str) -> Optional[StandardAccount]:
        """Get single account by ID."""
        try:
            query = f"SELECT * FROM Account WHERE Id = '{account_id}'"
            response = self._make_query_request(query)
            if response.get("QueryResponse", {}).get("Account"):
                return self.mapper.map_account_to_standard(
                    response["QueryResponse"]["Account"][0]
                )
        except (NotFoundError, KeyError):
            pass
        return None

    def get_contacts(
        self, contact_types: Optional[List[ContactType]] = None, limit: int = 1000
    ) -> List[StandardContact]:
        """Get contacts from QuickBooks."""
        contacts = []

        # Get customers
        if not contact_types or ContactType.CUSTOMER in contact_types:
            query = "SELECT * FROM Customer MAXRESULTS 100"
            try:
                response = self._make_query_request(query)
                for customer_data in response.get("QueryResponse", {}).get(
                    "Customer", []
                ):
                    if len(contacts) >= limit:
                        break
                    contact = self.mapper.map_customer_to_standard(customer_data)
                    contacts.append(contact)
            except Exception:
                pass

        # Get vendors
        if not contact_types or ContactType.SUPPLIER in contact_types:
            query = "SELECT * FROM Vendor MAXRESULTS 100"
            try:
                response = self._make_query_request(query)
                for vendor_data in response.get("QueryResponse", {}).get("Vendor", []):
                    if len(contacts) >= limit:
                        break
                    contact = self.mapper.map_vendor_to_standard(vendor_data)
                    contacts.append(contact)
            except Exception:
                pass

        return contacts[:limit]

    def get_contact(self, contact_id: str) -> Optional[StandardContact]:
        """Get single contact by ID."""
        # Try customer first
        try:
            query = f"SELECT * FROM Customer WHERE Id = '{contact_id}'"
            response = self._make_query_request(query)
            if response.get("QueryResponse", {}).get("Customer"):
                return self.mapper.map_customer_to_standard(
                    response["QueryResponse"]["Customer"][0]
                )
        except (NotFoundError, KeyError):
            pass

        # Try vendor
        try:
            query = f"SELECT * FROM Vendor WHERE Id = '{contact_id}'"
            response = self._make_query_request(query)
            if response.get("QueryResponse", {}).get("Vendor"):
                return self.mapper.map_vendor_to_standard(
                    response["QueryResponse"]["Vendor"][0]
                )
        except (NotFoundError, KeyError):
            pass

        return None

    def create_contact(self, contact: StandardContact) -> StandardContact:
        """Create contact - Not implemented (read-only Phase 1)."""
        raise NotImplementedError("Phase 1: Read-only access to QuickBooks")

    def update_contact(
        self, contact_id: str, contact: StandardContact
    ) -> StandardContact:
        """Update contact - Not implemented (read-only Phase 1)."""
        raise NotImplementedError("Phase 1: Read-only access to QuickBooks")

    def get_organization_info(self) -> Dict[str, Any]:
        """Get organization information from QuickBooks."""
        realm_id = self.auth.get_realm_id()
        if not realm_id:
            raise AuthenticationError("No realm ID available")

        url = f"{self.QBO_BASE_URL}/{realm_id}/companyinfo/{realm_id}"
        response = self._make_request("GET", url)
        company = response.get("CompanyInfo", {})

        return {
            "id": realm_id,
            "name": company.get("CompanyName"),
            "legal_name": company.get("CompanyName"),
            "country_code": company.get("Country"),
            "tax_number": company.get("CompanyAddr", {}).get("Country"),
            "registration_number": realm_id,
            "base_currency": company.get("PreferredDeliveryMethod"),
            "status": "ACTIVE",
        }

    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status information."""
        return {
            "last_sync": None,
            "next_sync": None,
            "rate_limit_remaining": self._rate_limit_remaining,
            "authenticated": self.authenticate(),
        }

    def _get_invoices(self, start_date: date, end_date: date, limit: int) -> List[StandardTransaction]:
        """Fetch invoices from QuickBooks API."""
        query = f"""
            SELECT * FROM Invoice
            WHERE TxnDate >= '{start_date}'
            AND TxnDate <= '{end_date}'
            MAXRESULTS {min(limit, 100)}
        """
        try:
            response = self._make_query_request(query)
            invoices = []
            for invoice_data in response.get("QueryResponse", {}).get("Invoice", []):
                txn = self.mapper.map_invoice_to_transaction(invoice_data)
                invoices.append(txn)
            return invoices
        except Exception:
            return []

    def _get_bills(self, start_date: date, end_date: date, limit: int) -> List[StandardTransaction]:
        """Fetch bills from QuickBooks API."""
        query = f"""
            SELECT * FROM Bill
            WHERE TxnDate >= '{start_date}'
            AND TxnDate <= '{end_date}'
            MAXRESULTS {min(limit, 100)}
        """
        try:
            response = self._make_query_request(query)
            bills = []
            for bill_data in response.get("QueryResponse", {}).get("Bill", []):
                txn = self.mapper.map_bill_to_transaction(bill_data)
                bills.append(txn)
            return bills
        except Exception:
            return []

    def _should_fetch_type(
        self, requested_types: Optional[List[TransactionType]], check_type: TransactionType
    ) -> bool:
        """Determine if should fetch a transaction type."""
        if requested_types is None:
            return True
        return check_type in requested_types

    def _make_query_request(self, query: str) -> Dict[str, Any]:
        """Make a QB query request."""
        realm_id = self.auth.get_realm_id()
        if not realm_id:
            raise AuthenticationError("No realm ID available")

        url = f"{self.QBO_BASE_URL}/{realm_id}/query"
        params = {"query": query}
        return self._make_request("GET", url, params=params)

    def _make_request(
        self, method: str, url: str, params: Optional[Dict] = None, data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to QB API."""
        access_token = self.auth.get_access_token()
        if not access_token:
            raise AuthenticationError("Not authenticated with QuickBooks")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        if method in ["POST", "PUT"]:
            headers["Content-Type"] = "application/json"

        try:
            response = requests.request(
                method=method, url=url, headers=headers, params=params, json=data, timeout=30
            )

            if response.status_code == 401:
                raise AuthenticationError("QuickBooks authentication failed")
            elif response.status_code == 404:
                raise NotFoundError("Resource not found")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    if "Fault" in error_data:
                        errors = error_data["Fault"].get("Error", [])
                        if errors:
                            msg = errors[0].get("Message", "Unknown error")
                            raise APIError(f"QB API error: {msg}")
                except:
                    pass
                raise APIError(f"HTTP {response.status_code}: {response.text}")

            return response.json()
        except requests.exceptions.Timeout:
            raise APIError("Request to QuickBooks timed out")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}")
