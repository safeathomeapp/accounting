"""TEMPORARY: Mock accounting client for development and testing.

WARNING: This entire module (backend/accounting/mock/) is FOR DEVELOPMENT ONLY.
         Remove the entire backend/accounting/mock/ directory before production.

Module: backend.accounting.mock.client
Purpose: Mock adapter implementing AccountingClient interface with fixture data
Status: DEVELOPMENT ONLY - Will be removed before live deployment
Created: November 24, 2025

This MockClient is useful for:
- Unit testing without external API dependencies
- Demo purposes and presentations
- Development work while Xero OAuth is being set up
- CI/CD pipelines that don't have API access
- Testing error handling locally

To remove from production:
  1. Delete the entire backend/accounting/mock/ directory
  2. Remove "mock" entry from PLATFORM_CLIENTS in backend/accounting/factory.py
  3. No other code changes needed
"""

from typing import List, Optional, Dict, Any
from datetime import date

from backend.accounting import (
    AccountingClient,
    StandardTransaction,
    StandardContact,
    StandardAccount,
    TransactionType,
    ContactType,
    AccountType,
    NotFoundError,
    ValidationError,
)
from .fixtures import (
    MOCK_INVOICES,
    MOCK_BANK_TRANSFERS,
    MOCK_CONTACTS,
    MOCK_ACCOUNTS,
    MOCK_ORGANIZATION_INFO,
    get_mock_transactions,
    get_mock_transaction,
    get_mock_contact,
    get_mock_account,
)


class MockClient(AccountingClient):
    """Mock accounting client for development and testing.

    IMPORTANT: This is DEMO/TEMPORARY code. Remove before production.

    This client returns hardcoded fixture data instead of calling real APIs.
    Useful for development, testing, and demos without API dependencies.

    All methods work with the fixture data defined in fixtures.py.
    """

    PLATFORM_NAME = "mock"

    def __init__(self, organization_id: str, credentials: Dict[str, Any]):
        """Initialize MockClient.

        Note: Credentials are not validated or used. This is a demo client.
        """
        super().__init__(organization_id, credentials)
        self._demo_warning_logged = False

    def _validate_credentials(self) -> None:
        """Validate credentials. Mock: No validation needed."""
        # For mock client, we don't need real credentials
        # This satisfies the abstract method requirement
        pass

    def _log_demo_warning_once(self) -> None:
        """Log that this is a demo client (once per session)."""
        if not self._demo_warning_logged:
            print(
                "\n"
                "WARNING: Using MOCK CLIENT for testing/development.\n"
                "This returns fixture data only. Remove backend/accounting/mock/ before production.\n"
            )
            self._demo_warning_logged = True

    def authenticate(self) -> bool:
        """Check if authenticated.

        Mock: Always returns True since there's no real authentication.
        """
        self._log_demo_warning_once()
        return True

    def get_transactions(
        self,
        start_date: date,
        end_date: date,
        transaction_types: Optional[List[TransactionType]] = None,
        limit: int = 1000,
    ) -> List[StandardTransaction]:
        """Get mock transactions.

        Returns fixture data for the date range.
        """
        self._log_demo_warning_once()
        transactions = []

        # Get invoices and bills if requested
        if self._should_fetch_type(transaction_types, TransactionType.INVOICE) or self._should_fetch_type(transaction_types, TransactionType.BILL):
            for invoice in MOCK_INVOICES:
                if start_date <= invoice["date"] <= end_date:
                    txn_type = TransactionType.INVOICE if invoice["type"] == "INVOICE" else TransactionType.BILL
                    # Skip if filtering by type and this doesn't match
                    if transaction_types and txn_type not in transaction_types:
                        continue
                    txn = StandardTransaction(
                        id=invoice["id"],
                        type=txn_type,
                        date=invoice["date"],
                        description=invoice["description"],
                        contact_id=invoice["contact_id"],
                        amount=invoice["amount"],
                        tax_amount=invoice["tax_amount"],
                        account_id=invoice["account_code"],
                        status=invoice["status"].lower(),
                    )
                    transactions.append(txn)

        # Get bank transfers if requested
        if self._should_fetch_type(transaction_types, TransactionType.BANK_TRANSFER):
            for transfer in MOCK_BANK_TRANSFERS:
                if start_date <= transfer["date"] <= end_date:
                    txn = StandardTransaction(
                        id=transfer["id"],
                        type=TransactionType.BANK_TRANSFER,
                        date=transfer["date"],
                        description=transfer["description"],
                        amount=transfer["amount"],
                        tax_amount=0,  # Bank transfers typically have no tax
                        account_id="",  # Not applicable for transfers
                        status=transfer["status"].lower(),
                    )
                    transactions.append(txn)

        return transactions[:limit]

    def get_transaction(self, transaction_id: str) -> Optional[StandardTransaction]:
        """Get single mock transaction by ID."""
        self._log_demo_warning_once()
        txn_data = get_mock_transaction(transaction_id)
        if not txn_data:
            return None

        txn_type = txn_data.get("type")

        # Map transaction type
        if txn_type == "INVOICE":
            mapped_type = TransactionType.INVOICE
        elif txn_type == "BILL":
            mapped_type = TransactionType.BILL
        else:
            mapped_type = TransactionType.BANK_TRANSFER

        return StandardTransaction(
            id=txn_data["id"],
            type=mapped_type,
            date=txn_data["date"],
            description=txn_data["description"],
            amount=txn_data.get("amount", 0),
            tax_amount=txn_data.get("tax_amount", 0),
            account_id=txn_data.get("account_code", ""),
            status=txn_data["status"].lower(),
        )

    def create_transaction(self, transaction: StandardTransaction) -> StandardTransaction:
        """Create transaction - Not implemented (mock is read-only)."""
        raise NotImplementedError("Mock client is read-only for testing")

    def update_transaction(
        self, transaction_id: str, transaction: StandardTransaction
    ) -> StandardTransaction:
        """Update transaction - Not implemented (mock is read-only)."""
        raise NotImplementedError("Mock client is read-only for testing")

    def get_accounts(
        self, account_types: Optional[List[str]] = None
    ) -> List[StandardAccount]:
        """Get mock chart of accounts."""
        self._log_demo_warning_once()
        accounts = []
        for account_data in MOCK_ACCOUNTS:
            if account_types and account_data["type"] not in account_types:
                continue
            account = StandardAccount(
                id=account_data["id"],
                code=account_data["code"],
                name=account_data["name"],
                type=AccountType[account_data["type"]],
            )
            accounts.append(account)
        return accounts

    def get_account(self, account_id: str) -> Optional[StandardAccount]:
        """Get single mock account by ID."""
        self._log_demo_warning_once()
        account_data = get_mock_account(account_id)
        if not account_data:
            return None

        return StandardAccount(
            id=account_data["id"],
            code=account_data["code"],
            name=account_data["name"],
            type=AccountType[account_data["type"]],
        )

    def get_contacts(
        self,
        contact_types: Optional[List[ContactType]] = None,
        limit: int = 1000,
    ) -> List[StandardContact]:
        """Get mock contacts."""
        self._log_demo_warning_once()
        contacts = []
        for contact_data in MOCK_CONTACTS:
            if (
                contact_types
                and ContactType[contact_data["type"]] not in contact_types
            ):
                continue
            contact = StandardContact(
                id=contact_data["id"],
                name=contact_data["name"],
                email=contact_data["email"],
                phone=contact_data["phone"],
                type=ContactType[contact_data["type"]],
                address=contact_data["address"],
                tax_id=contact_data["tax_number"],
            )
            contacts.append(contact)
        return contacts[:limit]

    def get_contact(self, contact_id: str) -> Optional[StandardContact]:
        """Get single mock contact by ID."""
        self._log_demo_warning_once()
        contact_data = get_mock_contact(contact_id)
        if not contact_data:
            return None

        return StandardContact(
            id=contact_data["id"],
            name=contact_data["name"],
            email=contact_data["email"],
            phone=contact_data["phone"],
            type=ContactType[contact_data["type"]],
            address=contact_data["address"],
            tax_id=contact_data["tax_number"],
        )

    def create_contact(self, contact: StandardContact) -> StandardContact:
        """Create contact - Not implemented (mock is read-only)."""
        raise NotImplementedError("Mock client is read-only for testing")

    def update_contact(
        self, contact_id: str, contact: StandardContact
    ) -> StandardContact:
        """Update contact - Not implemented (mock is read-only)."""
        raise NotImplementedError("Mock client is read-only for testing")

    def get_organization_info(self) -> Dict[str, Any]:
        """Get mock organization information."""
        self._log_demo_warning_once()
        return {
            "id": MOCK_ORGANIZATION_INFO["id"],
            "name": MOCK_ORGANIZATION_INFO["name"],
            "legal_name": MOCK_ORGANIZATION_INFO["legal_name"],
            "country_code": MOCK_ORGANIZATION_INFO["country_code"],
            "tax_number": MOCK_ORGANIZATION_INFO["tax_number"],
            "registration_number": MOCK_ORGANIZATION_INFO["registration_number"],
            "base_currency": MOCK_ORGANIZATION_INFO["base_currency"],
            "status": MOCK_ORGANIZATION_INFO["status"],
            "platform": "MOCK (FOR DEVELOPMENT ONLY)",
        }

    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status."""
        self._log_demo_warning_once()
        return {
            "last_sync": None,
            "next_sync": None,
            "rate_limit_remaining": None,
            "authenticated": True,
            "platform": "mock",
            "is_demo": True,
        }

    def _should_fetch_type(
        self,
        requested_types: Optional[List[TransactionType]],
        check_type: TransactionType,
    ) -> bool:
        """Determine if should fetch a transaction type."""
        if requested_types is None:
            return True
        return check_type in requested_types
