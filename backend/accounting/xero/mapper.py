from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
from backend.accounting import (
    StandardTransaction, StandardContact, StandardAccount,
    TransactionType, ContactType, AccountType, SyncStatus,
)
class XeroMapper:
    @staticmethod
    def map_invoice_to_transaction(invoice):
        xero_type = invoice.get("Type", "ACCREC")
        txn_type = TransactionType.INVOICE if xero_type == "ACCREC" else (TransactionType.BILL if xero_type == "ACCPAY" else TransactionType.INVOICE)
        date_obj = XeroMapper._parse_xero_date(invoice.get("InvoiceDate", ""))
        contact_id = invoice.get("Contact", {}).get("ContactID") if invoice.get("Contact") else None
        line_items_list = invoice.get("LineItems", [])
        account_id = line_items_list[0].get("AccountCode", "") if line_items_list else ""
        status = XeroMapper._map_invoice_status(invoice.get("Status", "DRAFT"))
        metadata = {
            "xero_type": xero_type,
            "tax_type": line_items_list[0].get("TaxType") if line_items_list else None,
            "line_amount_types": invoice.get("LineAmountTypes", "Exclusive"),
            "has_attachments": invoice.get("HasAttachments", False),
            "updated_utc": invoice.get("UpdatedDateUTC"),
        }
        line_items = [{"description": item.get("Description", ""), "quantity": float(item.get("Quantity", 0)), "unit_amount": str(item.get("UnitAmount", "0")), "account_code": item.get("AccountCode", ""), "tax_type": item.get("TaxType"), "tax_amount": str(item.get("TaxAmount", "0")), "line_amount": str(item.get("LineAmount", "0")),} for item in line_items_list]
        return StandardTransaction(id=invoice.get("InvoiceID", ""), type=txn_type, date=date_obj, description=invoice.get("Description", ""), amount=Decimal(str(invoice.get("Total", "0"))), tax_amount=Decimal(str(invoice.get("TaxTotal", "0"))), account_id=account_id, contact_id=contact_id, reference=invoice.get("InvoiceNumber", ""), status=status, line_items=line_items, platform_id=invoice.get("InvoiceID", ""), platform_name="xero", metadata=metadata, sync_status=SyncStatus.SYNCED,)
    @staticmethod
    def map_bank_transfer_to_transaction(transfer):
        line_items_list = transfer.get("LineItems", [])
        amount = Decimal(str(line_items_list[0].get("UnitAmount", "0"))) if line_items_list else Decimal("0")
        from_account = transfer.get("FromBankAccount", {})
        to_account = transfer.get("ToBankAccount", {})
        metadata = {"from_account": from_account.get("Code"), "to_account": to_account.get("Code"), "has_attachments": transfer.get("HasAttachments", False),}
        return StandardTransaction(id=transfer.get("BankTransferID", ""), type=TransactionType.BANK_TRANSFER, date=XeroMapper._parse_xero_date(transfer.get("DateString", "")), description="Bank Transfer", amount=amount, tax_amount=Decimal("0"), account_id=from_account.get("Code", ""), contact_id=None, reference=f"TRANSFER-{transfer.get('BankTransferID', '')}", status="approved", line_items=[], platform_id=transfer.get("BankTransferID", ""), platform_name="xero", metadata=metadata, sync_status=SyncStatus.SYNCED,)
    @staticmethod
    def map_contact_to_standard(contact):
        contact_type = XeroMapper._infer_contact_type(contact)
        addresses = contact.get("Addresses", [])
        address_str = XeroMapper._build_address(addresses)
        phones = contact.get("Phones", [])
        phone = phones[0].get("PhoneNumber") if phones else None
        metadata = {"contact_number": contact.get("ContactNumber"), "website": contact.get("Website"), "contact_status": contact.get("ContactStatus"), "addresses": addresses, "phones": phones, "xero_updated_utc": contact.get("UpdatedDateUTC"),}
        return StandardContact(id=contact.get("ContactID", ""), type=contact_type, name=contact.get("Name", ""), email=contact.get("EmailAddress"), phone=phone, address=address_str, tax_id=contact.get("TaxNumber"), currency="GBP", platform_id=contact.get("ContactID", ""), platform_name="xero", metadata=metadata,)
    @staticmethod
    def map_account_to_standard(account):
        account_type = XeroMapper._map_account_type(account.get("Type", "EXPENSE"))
        metadata = {"xero_status": account.get("Status"), "system_account": account.get("SystemAccount", False), "enable_payments": account.get("EnablePayments", False), "xero_updated_utc": account.get("UpdatedDateUTC"),}
        return StandardAccount(id=account.get("AccountID", ""), code=account.get("Code", ""), name=account.get("Name", ""), type=account_type, currency="GBP", tax_type=account.get("TaxType"), platform_id=account.get("AccountID", ""), platform_name="xero", metadata=metadata,)
    @staticmethod
    def _parse_xero_date(date_string):
        if not date_string:
            return None
        try:
            dt = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
            return dt.date()
        except (ValueError, AttributeError):
            return None
    @staticmethod
    def _map_invoice_status(xero_status):
        status_map = {"DRAFT": "draft", "SUBMITTED": "submitted", "AUTHORISED": "approved", "PAID": "paid", "AWAITING_PAYMENT": "awaiting_payment", "VOIDED": "cancelled", "DELETED": "deleted",}
        return status_map.get(xero_status, "approved")
    @staticmethod
    def _infer_contact_type(contact):
        groups = contact.get("ContactGroups", [])
        if any("SUPPLIER" in str(g) for g in groups):
            return ContactType.SUPPLIER
        if any("CUSTOMER" in str(g) for g in groups):
            return ContactType.CUSTOMER
        addresses = contact.get("Addresses", [])
        for addr in addresses:
            if "PO BOX" in str(addr.get("AddressLine1", "")).upper():
                return ContactType.SUPPLIER
        return ContactType.CUSTOMER
    @staticmethod
    def _build_address(addresses):
        if not addresses:
            return ""
        address = next((a for a in addresses if a.get("AddressType") == "STREET"), addresses[0])
        parts = [address.get("AddressLine1"), address.get("AddressLine2"), address.get("City"), address.get("PostalCode"), address.get("PostalCodeCountry"),]
        return ", ".join(filter(None, parts))
    @staticmethod
    def _map_account_type(xero_type):
        type_map = {"ASSET": AccountType.ASSET, "BANK": AccountType.BANK, "CURRENT": AccountType.ASSET, "FIXED": AccountType.ASSET, "EQUITY": AccountType.EQUITY, "EXPENSE": AccountType.EXPENSE, "LIABILITY": AccountType.LIABILITY, "OASSET": AccountType.ASSET, "PAYROLL": AccountType.EXPENSE, "REVENUE": AccountType.INCOME, "SALES": AccountType.INCOME,}
        return type_map.get(xero_type, AccountType.EXPENSE)
