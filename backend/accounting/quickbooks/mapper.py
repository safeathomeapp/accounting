"""Data mapping for QuickBooks Online API responses."""
from datetime import date
from decimal import Decimal
from typing import Dict, Any, Optional

from backend.accounting import (
    StandardTransaction,
    StandardContact,
    StandardAccount,
    TransactionType,
    ContactType,
    AccountType,
)


class QuickBooksMapper:
    """Maps QB API responses to standard models."""

    @staticmethod
    def map_invoice_to_transaction(invoice: Dict[str, Any]) -> StandardTransaction:
        """Convert QB Invoice to StandardTransaction."""
        return StandardTransaction(
            id=invoice.get("Id"),
            type=TransactionType.INVOICE,
            date=QuickBooksMapper._parse_qbo_date(invoice.get("TxnDate", "")),
            description=invoice.get("DocNumber", ""),
            contact_id=invoice.get("CustomerRef", {}).get("value"),
            amount=Decimal(str(invoice.get("TotalAmt", 0))),
            tax_amount=Decimal(
                str(invoice.get("TxnTaxDetail", {}).get("TotalTax", 0))
            ),
            account_id="",  # QB doesn't have direct account mapping for invoices
            status=QuickBooksMapper._map_invoice_status(
                invoice.get("DocStatus", "Draft")
            ),
            reference=invoice.get("DocNumber", ""),
        )

    @staticmethod
    def map_bill_to_transaction(bill: Dict[str, Any]) -> StandardTransaction:
        """Convert QB Bill to StandardTransaction."""
        return StandardTransaction(
            id=bill.get("Id"),
            type=TransactionType.BILL,
            date=QuickBooksMapper._parse_qbo_date(bill.get("TxnDate", "")),
            description=bill.get("DocNumber", ""),
            contact_id=bill.get("VendorRef", {}).get("value"),
            amount=Decimal(str(bill.get("TotalAmt", 0))),
            tax_amount=Decimal(str(bill.get("TxnTaxDetail", {}).get("TotalTax", 0))),
            account_id="",
            status=QuickBooksMapper._map_bill_status(bill.get("DocStatus", "Draft")),
            reference=bill.get("DocNumber", ""),
        )

    @staticmethod
    def map_customer_to_standard(customer: Dict[str, Any]) -> StandardContact:
        """Convert QB Customer to StandardContact."""
        # Build address from QB address structure
        billing_addr = customer.get("BillAddr", {})
        address_parts = [
            billing_addr.get("Line1"),
            billing_addr.get("Line2"),
            billing_addr.get("City"),
            billing_addr.get("CountrySubDivisionCode"),
            billing_addr.get("PostalCode"),
        ]
        address = " ".join([p for p in address_parts if p])

        return StandardContact(
            id=customer.get("Id"),
            name=customer.get("DisplayName", ""),
            type=ContactType.CUSTOMER,
            email=next(
                (email.get("Address") for email in customer.get("PrimaryEmailAddr", []) if email.get("Address")),
                None,
            ),
            phone=next(
                (phone.get("FreeFormNumber")
                 for phone in customer.get("PrimaryPhone", [])
                 if phone.get("FreeFormNumber")),
                None,
            ),
            address=address or None,
            tax_id=customer.get("ResaleNum"),
        )

    @staticmethod
    def map_vendor_to_standard(vendor: Dict[str, Any]) -> StandardContact:
        """Convert QB Vendor to StandardContact."""
        # Build address from QB address structure
        billing_addr = vendor.get("BillAddr", {})
        address_parts = [
            billing_addr.get("Line1"),
            billing_addr.get("Line2"),
            billing_addr.get("City"),
            billing_addr.get("CountrySubDivisionCode"),
            billing_addr.get("PostalCode"),
        ]
        address = " ".join([p for p in address_parts if p])

        return StandardContact(
            id=vendor.get("Id"),
            name=vendor.get("DisplayName", ""),
            type=ContactType.SUPPLIER,
            email=next(
                (email.get("Address")
                 for email in vendor.get("PrimaryEmailAddr", [])
                 if email.get("Address")),
                None,
            ),
            phone=next(
                (phone.get("FreeFormNumber")
                 for phone in vendor.get("PrimaryPhone", [])
                 if phone.get("FreeFormNumber")),
                None,
            ),
            address=address or None,
            tax_id=vendor.get("TaxId"),
        )

    @staticmethod
    def map_account_to_standard(account: Dict[str, Any]) -> StandardAccount:
        """Convert QB Account to StandardAccount."""
        return StandardAccount(
            id=account.get("Id"),
            code=account.get("AcctNum", ""),
            name=account.get("Name", ""),
            type=QuickBooksMapper._map_account_type(account.get("AccountType", "")),
            tax_type=account.get("TaxAccount"),
        )

    @staticmethod
    def _parse_qbo_date(date_string: str) -> date:
        """Parse QB date string (YYYY-MM-DD format)."""
        if not date_string:
            return date.today()
        try:
            parts = date_string.split("T")[0].split("-")
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            return date.today()

    @staticmethod
    def _map_invoice_status(qbo_status: str) -> str:
        """Map QB invoice status to standard status."""
        status_map = {
            "Draft": "draft",
            "Posted": "approved",
            "Paid": "paid",
            "Voided": "voided",
        }
        return status_map.get(qbo_status, "approved")

    @staticmethod
    def _map_bill_status(qbo_status: str) -> str:
        """Map QB bill status to standard status."""
        status_map = {
            "Draft": "draft",
            "Voided": "voided",
            "Processed": "approved",
        }
        return status_map.get(qbo_status, "draft")

    @staticmethod
    def _map_account_type(qbo_type: str) -> AccountType:
        """Map QB account type to standard account type."""
        type_map = {
            "Asset": AccountType.ASSET,
            "Bank": AccountType.BANK,
            "Credit Card": AccountType.LIABILITY,
            "Equity": AccountType.EQUITY,
            "Expense": AccountType.EXPENSE,
            "Other Expense": AccountType.EXPENSE,
            "Income": AccountType.INCOME,
            "Other Income": AccountType.INCOME,
            "Liability": AccountType.LIABILITY,
            "Other Current Liability": AccountType.LIABILITY,
            "Other Current Asset": AccountType.ASSET,
            "Fixed Asset": AccountType.ASSET,
        }
        return type_map.get(qbo_type, AccountType.ASSET)
