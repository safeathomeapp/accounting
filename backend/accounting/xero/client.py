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


class XeroClient(AccountingClient):
    """Xero adapter implementing AccountingClient interface."""

    PLATFORM_NAME = "xero"
    XERO_BASE_URL = "https://api.xero.com/api.xro/2.0"
    XERO_TENANT_HEADER = "Xero-tenant-id"

    def __init__(self, organization_id: str, credentials: Dict[str, Any]):
        """Initialize XeroClient."""
        super().__init__(organization_id, credentials)
        self.auth = XeroAuth(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            redirect_uri=credentials.get("redirect_uri", "http://localhost:8000/auth/xero/callback"),
        )
        if credentials.get("access_token"):
            self.auth.tokens = {
                "access_token": credentials["access_token"],
                "refresh_token": credentials.get("refresh_token"),
                "tenant_id": credentials.get("tenant_id"),
                "expires_at": None,
            }
        self.mapper = XeroMapper()
        self._rate_limit_remaining = 60

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
        """Get transactions from Xero."""
        transactions = []
        if self._should_fetch_type(transaction_types, TransactionType.INVOICE):
            invoices = self._get_invoices(start_date, end_date, "ACCREC", limit)
            transactions.extend(invoices)
        if self._should_fetch_type(transaction_types, TransactionType.BILL):
            bills = self._get_invoices(start_date, end_date, "ACCPAY", limit)
            transactions.extend(bills)
        if self._should_fetch_type(transaction_types, TransactionType.BANK_TRANSFER):
            transfers = self._get_bank_transfers(start_date, end_date, limit)
            transactions.extend(transfers)
        return transactions[:limit]

    def get_transaction(self, transaction_id: str) -> Optional[StandardTransaction]:
        """Get single transaction by ID."""
        try:
            url = f"{self.XERO_BASE_URL}/Invoices/{transaction_id}"
            response = self._make_request("GET", url)
            if response.get("Invoices"):
                return self.mapper.map_invoice_to_transaction(response["Invoices"][0])
        except NotFoundError:
            pass
        try:
            url = f"{self.XERO_BASE_URL}/BankTransfers/{transaction_id}"
            response = self._make_request("GET", url)
            if response.get("BankTransfers"):
                return self.mapper.map_bank_transfer_to_transaction(response["BankTransfers"][0])
        except NotFoundError:
            pass
        return None

    def create_transaction(self, transaction: StandardTransaction) -> StandardTransaction:
        """Create transaction - Not implemented (read-only)."""
        raise NotImplementedError("Phase 1: Read-only access to Xero")

    def update_transaction(self, transaction_id: str, transaction: StandardTransaction) -> StandardTransaction:
        """Update transaction - Not implemented (read-only)."""
        raise NotImplementedError("Phase 1: Read-only access to Xero")

    def get_accounts(self, account_types: Optional[List[str]] = None) -> List[StandardAccount]:
        """Get chart of accounts from Xero."""
        url = f"{self.XERO_BASE_URL}/Accounts"
        response = self._make_request("GET", url)
        accounts = []
        for account_data in response.get("Accounts", []):
            if account_types and account_data.get("Type") not in account_types:
                continue
            account = self.mapper.map_account_to_standard(account_data)
            accounts.append(account)
        return accounts

    def get_account(self, account_id: str) -> Optional[StandardAccount]:
        """Get single account by ID."""
        try:
            url = f"{self.XERO_BASE_URL}/Accounts/{account_id}"
            response = self._make_request("GET", url)
            if response.get("Accounts"):
                return self.mapper.map_account_to_standard(response["Accounts"][0])
        except NotFoundError:
            pass
        return None

    def get_contacts(self, contact_types: Optional[List[ContactType]] = None, limit: int = 1000) -> List[StandardContact]:
        """Get contacts from Xero."""
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
                if contact_types and contact.type not in contact_types:
                    continue
                contacts.append(contact)
            page += 1
        return contacts[:limit]

    def get_contact(self, contact_id: str) -> Optional[StandardContact]:
        """Get single contact by ID."""
        try:
            url = f"{self.XERO_BASE_URL}/Contacts/{contact_id}"
            response = self._make_request("GET", url)
            if response.get("Contacts"):
                return self.mapper.map_contact_to_standard(response["Contacts"][0])
        except NotFoundError:
            pass
        return None

    def create_contact(self, contact: StandardContact) -> StandardContact:
        """Create contact - Not implemented (read-only)."""
        raise NotImplementedError("Phase 1: Read-only access to Xero")

    def update_contact(self, contact_id: str, contact: StandardContact) -> StandardContact:
        """Update contact - Not implemented (read-only)."""
        raise NotImplementedError("Phase 1: Read-only access to Xero")

    def get_organization_info(self) -> Dict[str, Any]:
        """Get organization information from Xero."""
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
        """Get sync status information."""
        return {
            "last_sync": None,
            "next_sync": None,
            "rate_limit_remaining": self._rate_limit_remaining,
            "authenticated": self.authenticate(),
        }

    def _get_invoices(self, start_date: date, end_date: date, invoice_type: str, limit: int) -> List[StandardTransaction]:
        """Fetch invoices from Xero API."""
        invoices = []
        page = 1
        while len(invoices) < limit:
            where = f'Type=="{invoice_type}" AND InvoiceDate>DateTime({start_date.year},{start_date.month},{start_date.day}) AND InvoiceDate<DateTime({end_date.year},{end_date.month},{end_date.day})'
            url = f"{self.XERO_BASE_URL}/Invoices"
            params = {"where": where, "page": page}
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

    def _get_bank_transfers(self, start_date: date, end_date: date, limit: int) -> List[StandardTransaction]:
        """Fetch bank transfers from Xero API."""
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

    def _should_fetch_type(self, requested_types: Optional[List[TransactionType]], check_type: TransactionType) -> bool:
        """Determine if should fetch a transaction type."""
        if requested_types is None:
            return True
        return check_type in requested_types

    def _make_request(self, method: str, url: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to Xero API."""
        access_token = self.auth.get_access_token()
        if not access_token:
            raise AuthenticationError("Not authenticated with Xero")
        headers = {
            "Authorization": f"Bearer {access_token}",
            self.XERO_TENANT_HEADER: self.auth.get_tenant_id() or "",
            "Accept": "application/json",
        }
        if method in ["POST", "PUT"]:
            headers["Content-Type"] = "application/json"
        try:
            response = requests.request(method=method, url=url, headers=headers, params=params, json=data, timeout=30)
            if "X-Rate-Limit-Remaining-Minute" in response.headers:
                self._rate_limit_remaining = int(response.headers["X-Rate-Limit-Remaining-Minute"])
            if response.status_code == 401:
                raise AuthenticationError("Xero authentication failed")
            elif response.status_code == 404:
                raise NotFoundError("Resource not found")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code >= 400:
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
