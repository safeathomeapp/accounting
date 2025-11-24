# Data Mapping Specification

**Status:** Ready for Implementation (Week 3)
**Date:** November 24, 2025
**Purpose:** Define exact mappings from Xero API data to StandardTransaction, StandardContact, StandardAccount

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [StandardTransaction Mapping](#standardtransaction-mapping)
3. [StandardContact Mapping](#standardcontact-mapping)
4. [StandardAccount Mapping](#standardaccount-mapping)
5. [Special Cases & Transformations](#special-cases--transformations)
6. [Error Handling & Fallbacks](#error-handling--fallbacks)
7. [Implementation Checklist](#implementation-checklist)

---

## 🎯 Overview

This document specifies **exact field mappings** from Xero API responses to our standard data models. It's implementation-ready - use this as your reference while coding `mapper.py`.

**Key Principle:** The mapper's job is TRANSLATION, not transformation. Convert Xero → Standard format with minimal logic.

---

## 📊 StandardTransaction Mapping

### Source: Xero Invoice (Type = ACCREC)

Xero Invoice (customer invoice) → StandardTransaction with type=INVOICE

```
Xero Field              →  StandardTransaction Field   →  Notes
─────────────────────────────────────────────────────────────────────────
InvoiceID              →  id                          →  UUID string
InvoiceNumber          →  reference                   →  "INV-0001"
Description            →  description                 →  From line item or empty
Type                   →  type (INVOICE)              →  Hardcode INVOICE
Status                 →  status                      →  Map per table below
InvoiceDate            →  date                        →  Parse ISO 8601
DueDate                →  (metadata["due_date"])      →  Optional, store in metadata
Total                  →  amount                      →  Decimal from response
TaxTotal               →  tax_amount                  →  Decimal from response
Contact.ContactID      →  contact_id                  →  UUID string of customer
LineItems[0].AccountCode → account_id                 →  First line item's account
LineItems[0].TaxType   →  (metadata["tax_type"])      →  Store VAT treatment
(none)                 →  platform_id                 →  Set to InvoiceID
(none)                 →  platform_name               →  Set to "xero"
(none)                 →  sync_status                 →  Default: SyncStatus.SYNCED
(none)                 →  line_items                  →  List of line item dicts
(none)                 →  metadata                    →  Extra Xero data
```

### Source: Xero Invoice (Type = ACCPAY)

Xero Bill (supplier invoice) → StandardTransaction with type=BILL

```
Xero Field              →  StandardTransaction Field   →  Notes
─────────────────────────────────────────────────────────────────────────
InvoiceID              →  id                          →  UUID string
InvoiceNumber          →  reference                   →  "BILL-0001"
Description            →  description                 →  From line item or empty
Type                   →  type (BILL)                 →  Hardcode BILL
Status                 →  status                      →  Map per table below
InvoiceDate            →  date                        →  Parse ISO 8601
DueDate                →  (metadata["due_date"])      →  Optional, store in metadata
Total                  →  amount                      →  Decimal from response
TaxTotal               →  tax_amount                  →  Decimal from response
Contact.ContactID      →  contact_id                  →  UUID string of supplier
LineItems[0].AccountCode → account_id                 →  First line item's account
LineItems[0].TaxType   →  (metadata["tax_type"])      →  Store VAT treatment
(none)                 →  platform_id                 →  Set to InvoiceID
(none)                 →  platform_name               →  Set to "xero"
(none)                 →  sync_status                 →  Default: SyncStatus.SYNCED
(none)                 →  line_items                  →  List of line item dicts
(none)                 →  metadata                    →  Extra Xero data
```

### Source: Xero BankTransfer

Xero Bank Transfer → StandardTransaction with type=BANK_TRANSFER

```
Xero Field              →  StandardTransaction Field   →  Notes
─────────────────────────────────────────────────────────────────────────
BankTransferID         →  id                          →  UUID string
(generated)            →  reference                   →  "TRANSFER-" + timestamp
"Bank Transfer"        →  description                 →  Hardcode description
(none)                 →  type (BANK_TRANSFER)        →  Hardcode BANK_TRANSFER
"AUTHORISED"           →  status                      →  Hardcode "approved"
HasAttachments         →  (metadata["has_attachments"]) → Boolean flag
LineItems[0].UnitAmount → amount                      →  Amount transferred
(none)                 →  tax_amount                  →  Decimal("0.00")
FromBankAccount.Code   →  account_id                  →  From account code
ToBankAccount.Code     →  (metadata["to_account"])    →  To account code
(none)                 →  contact_id                  →  None (no contact)
(none)                 →  platform_id                 →  Set to BankTransferID
(none)                 →  platform_name               →  Set to "xero"
(none)                 →  sync_status                 →  Default: SyncStatus.SYNCED
(none)                 →  line_items                  →  [{...}] with transfer details
(none)                 →  metadata                    →  Extra data
```

### Source: Xero CreditNote

Xero Credit Note → StandardTransaction with type=CREDIT_NOTE

```
Xero Field              →  StandardTransaction Field   →  Notes
─────────────────────────────────────────────────────────────────────────
CreditNoteID           →  id                          →  UUID string
CreditNoteNumber       →  reference                   →  "CN-0001"
(none)                 →  description                 →  From line item or empty
(none)                 →  type (CREDIT_NOTE)          →  Hardcode CREDIT_NOTE
Status                 →  status                      →  Map per table below
DateString             →  date                        →  Parse ISO 8601
Total                  →  amount                      →  Negative Decimal
TaxTotal               →  tax_amount                  →  Negative Decimal
Contact.ContactID      →  contact_id                  →  UUID of customer
LineItems[0].AccountCode → account_id                 →  First line item's account
(none)                 →  platform_id                 →  Set to CreditNoteID
(none)                 →  platform_name               →  Set to "xero"
(none)                 →  sync_status                 →  Default: SyncStatus.SYNCED
(none)                 →  line_items                  →  List of line item dicts
(none)                 →  metadata                    →  Extra Xero data
```

### Status Mapping for Transactions

```
Xero Status         →  StandardTransaction.status   →  Notes
─────────────────────────────────────────────────────────────
DRAFT               →  "draft"                      →  Not yet authorised
SUBMITTED           →  "submitted"                  →  Awaiting approval
AUTHORISED          →  "approved"                   →  Approved/ready
PAID                →  "paid"                       →  Invoice only: payment received
AWAITING_PAYMENT    →  "awaiting_payment"           →  Invoice only: approved, waiting
VOIDED              →  "cancelled"                  →  Cancelled/voided
DELETED             →  "deleted"                    →  Soft-deleted
(archived)          →  Filter out (don't return)    →  Don't include archived
```

### Line Items Structure

In `StandardTransaction.line_items`, store each line item as a dict:

```python
{
    "line_item_id": "uuid",              # LineItemID from Xero
    "description": "Service provided",   # Description
    "quantity": 1.0,                     # Quantity
    "unit_amount": "500.00",             # UnitAmount as string
    "account_code": "4000",              # AccountCode
    "tax_type": "Tax on Sales",          # TaxType
    "tax_amount": "100.00",              # TaxAmount as string
    "line_amount": "500.00",             # LineAmount as string
    "tracking_name": "Job",              # Optional tracking
    "tracking_code": "JOB123",           # Optional tracking code
}
```

---

## 👥 StandardContact Mapping

### Source: Xero Contact

Xero Contact → StandardContact (can be customer, supplier, or employee)

```
Xero Field              →  StandardContact Field   →  Notes
──────────────────────────────────────────────────────────────
ContactID              →  id                      →  UUID string
Name                   →  name                    →  Contact name
EmailAddress           →  email                   →  Primary email
Phones[0].PhoneNumber  →  phone                   →  First phone number
ContactStatus          →  (metadata["status"])    →  ACTIVE, ARCHIVED, etc.
Addresses[0].City      →  address (partial)       →  See address handling below
Addresses[0].PostalCode → address (partial)      →  See address handling below
Addresses[0].Country   →  (metadata["country"])   →  Country code
TaxNumber              →  tax_id                  →  VAT/tax number
(inferred)             →  type                    →  See type inference below
(none)                 →  currency                →  Default: "GBP"
(none)                 →  platform_id             →  Set to ContactID
(none)                 →  platform_name           →  Set to "xero"
(none)                 →  metadata                →  All extra fields
```

### Contact Type Inference

Since Xero doesn't have explicit "type" field, infer from context:

```python
# Rule 1: Check ContactGroups for CUSTOMER or SUPPLIER
if "CUSTOMER" in contact.get("ContactGroups", []):
    type = ContactType.CUSTOMER
elif "SUPPLIER" in contact.get("ContactGroups", []):
    type = ContactType.SUPPLIER
# Rule 2: Check Addresses for POBOX (supplier indicator)
elif has_po_box_address:
    type = ContactType.SUPPLIER
# Rule 3: Default to CUSTOMER (most common)
else:
    type = ContactType.CUSTOMER
```

### Address Handling

Xero returns `Addresses` as array. Build a single address string:

```python
# Take first address of type "STREET" or first available
address_obj = next(
    (a for a in contact.get("Addresses", []) if a.get("AddressType") == "STREET"),
    contact.get("Addresses", [{}])[0] if contact.get("Addresses") else {}
)

# Build address string
address = ", ".join(filter(None, [
    address_obj.get("AddressLine1"),
    address_obj.get("AddressLine2"),
    address_obj.get("City"),
    address_obj.get("PostalCode"),
    address_obj.get("PostalCodeCountry", ""),
]))

# Store full address object in metadata
metadata["addresses"] = contact.get("Addresses", [])
metadata["country"] = address_obj.get("PostalCodeCountry")
```

### Contact Metadata (Store Extra Fields)

```python
metadata = {
    "contact_number": contact.get("ContactNumber"),
    "website": contact.get("Website"),
    "contact_status": contact.get("ContactStatus"),
    "discount": contact.get("Discount"),
    "sales_tracking_name": contact.get("SalesTrackingName"),
    "purchase_tracking_name": contact.get("PurchaseTrackingName"),
    "contact_groups": contact.get("ContactGroups", []),
    "addresses": contact.get("Addresses", []),
    "phones": contact.get("Phones", []),
    "country": address_obj.get("PostalCodeCountry"),
    "xero_updated_utc": contact.get("UpdatedDateUTC"),
}
```

---

## 💰 StandardAccount Mapping

### Source: Xero Account (Chart of Accounts)

Xero Account → StandardAccount

```
Xero Field              →  StandardAccount Field   →  Notes
───────────────────────────────────────────────────────────────
AccountID              →  id                      →  UUID string
Code                   →  code                    →  Account code (e.g., "4000")
Name                   →  name                    →  Account name
Type                   →  type                    →  Map per table below
Status                 →  (metadata["status"])    →  ACTIVE, ARCHIVED, etc.
TaxType                →  tax_type                →  "Tax on Sales", "Tax on Purchases", etc.
SystemAccount          →  (metadata["system"])    →  Boolean: Xero built-in
EnablePayments         →  (metadata["payments"])  →  Boolean: can receive payments
CurrencyCode           →  currency                →  Default to "GBP"
(none)                 →  platform_id             →  Set to AccountID
(none)                 →  platform_name           →  Set to "xero"
(none)                 →  metadata                →  Extra data
```

### Account Type Mapping

Map Xero Type → StandardAccount.type:

```
Xero Type              →  StandardAccount.type   →  Notes
──────────────────────────────────────────────────────────
ASSET                 →  AccountType.ASSET       →  Assets
BANK                  →  AccountType.BANK        →  Bank accounts (special)
CURRENT               →  AccountType.ASSET       →  Current asset
FIXED                 →  AccountType.ASSET       →  Fixed asset
EQUITY                →  AccountType.EQUITY      →  Owner's equity
EXPENSE               →  AccountType.EXPENSE     →  Expenses/costs
LIABILITY             →  AccountType.LIABILITY   →  Liabilities
OASSET                →  AccountType.ASSET       →  Other asset
PAYROLL               →  AccountType.EXPENSE     →  Payroll (is expense)
REVENUE               →  AccountType.INCOME      →  Income/sales
SALES                 →  AccountType.INCOME      →  Sales income
(unknown)             →  AccountType.EXPENSE     →  Default to expense if unsure
```

### Tax Type Handling

Store Xero's TaxType as-is in `tax_type` field. Common values:

```
Xero TaxType           →  Meaning
────────────────────────────────────────────
"Tax on Sales"         →  VAT output (customer VAT)
"Tax on Purchases"     →  VAT input (supplier VAT)
"No Tax"               →  Non-taxable
"Tax on Capital"       →  Capital goods tax
"Input Tax on Fixed"   →  Fixed asset VAT
"Exemption"            →  VAT exempt
"Zero Rated"           →  Zero-rated supply
```

### Account Metadata

```python
metadata = {
    "xero_status": account.get("Status"),
    "system_account": account.get("SystemAccount", False),
    "enable_payments": account.get("EnablePayments", False),
    "updated_utc": account.get("UpdatedDateUTC"),
    "description": account.get("Description"),
}
```

---

## 🔄 Special Cases & Transformations

### 1. Amount Handling (Inclusive vs Exclusive)

Xero invoices can have `LineAmountTypes` of "Inclusive" (includes tax) or "Exclusive" (excludes tax).

**Rule:** Always store amounts as-is. Don't try to recalculate.

```python
# In StandardTransaction
amount = Decimal(str(invoice["Total"]))           # Always the Total
tax_amount = Decimal(str(invoice["TaxTotal"]))   # Always the TaxTotal
# The "LineAmountTypes" note in metadata if you need to know the type
metadata["line_amount_types"] = invoice.get("LineAmountTypes", "Exclusive")
```

### 2. Date Parsing

Xero returns ISO 8601 dates with Z (UTC timezone):

```python
from datetime import datetime

# Example: "2025-01-15T00:00:00Z"
date_string = "2025-01-15T00:00:00Z"

# Parse and extract date only
date_obj = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
transaction.date = date_obj.date()  # Returns date(2025, 1, 15)
```

### 3. UUID Handling

Xero IDs are UUIDs like `12345678-1234-1234-1234-123456789012`. Store as strings.

```python
# Already a string in Xero response
id_value = invoice["InvoiceID"]  # "12345678-1234-1234-1234-123456789012"
transaction.id = str(id_value)   # Keep as string
```

### 4. Contact Relationship

Invoices have nested Contact object:

```python
# Xero structure:
# {
#   "InvoiceID": "...",
#   "Contact": {
#     "ContactID": "xyz",
#     "Name": "ACME Corp",
#     ...
#   }
# }

# Mapping:
transaction.contact_id = invoice["Contact"]["ContactID"]  # Just the ID
# If you need full contact data, fetch separately via get_contacts()
```

### 5. Line Items with Multiple Accounts

Invoice can have multiple line items with different accounts:

```python
# Rule: Use FIRST line item's account code
first_line = invoice["LineItems"][0] if invoice.get("LineItems") else {}
transaction.account_id = first_line.get("AccountCode", "")

# Store ALL line items in line_items array for reference
transaction.line_items = [
    {
        "description": item.get("Description"),
        "quantity": float(item.get("Quantity", 0)),
        "unit_amount": str(item.get("UnitAmount", "0")),
        "account_code": item.get("AccountCode"),
        "tax_type": item.get("TaxType"),
        "tax_amount": str(item.get("TaxAmount", "0")),
    }
    for item in invoice.get("LineItems", [])
]
```

### 6. Organization Info Mapping

When fetching `GET /Organisation`:

```python
# Xero returns array with one organization
org_data = response["Organisations"][0]

org_info = {
    "id": org_data.get("OrganisationID"),
    "name": org_data.get("Name"),
    "legal_name": org_data.get("LegalName"),
    "country_code": org_data.get("CountryCode"),  # e.g., "GB"
    "tax_number": org_data.get("TaxNumber"),
    "registration_number": org_data.get("RegistrationNumber"),
    "base_currency": org_data.get("BaseCurrency"),  # e.g., "GBP"
    "status": org_data.get("OrganisationStatus"),
    "line_of_business": org_data.get("LineOfBusiness"),
    "year_end_month": org_data.get("YearEndMonth"),
    "year_end_day": org_data.get("YearEndDay"),
}

return org_info
```

---

## ❌ Error Handling & Fallbacks

### Missing Fields

For optional fields, use sensible defaults:

```python
# If Description missing, use empty string
description = transaction_data.get("Description", "")

# If TaxTotal missing, use 0
tax_amount = Decimal(str(transaction_data.get("TaxTotal", "0")))

# If Contact missing, set to None
contact_id = transaction_data.get("Contact", {}).get("ContactID")

# If LineItems empty, use empty list
line_items = transaction_data.get("LineItems", [])
```

### Invalid Data Types

Convert everything to expected types:

```python
from decimal import Decimal

# Amounts should be Decimal (not float!)
amount = Decimal(str(transaction_data.get("Total", "0")))

# Dates should be date objects
from datetime import datetime
date_str = transaction_data.get("InvoiceDate", "2025-01-01T00:00:00Z")
date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()

# IDs should be strings
id_val = str(transaction_data.get("InvoiceID", ""))
```

### API Response Errors

If Xero API returns error response:

```python
# Example error response
{
  "ApiException": {
    "ErrorNumber": 400,
    "Type": "ValidationException",
    "Message": "The element 'Contact' is required"
  }
}

# Handle in try/except in client.py:
try:
    response = xero_api_call(...)
    if "ApiException" in response:
        raise APIError(f"Xero error: {response['ApiException']['Message']}")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        raise RateLimitError("Rate limit exceeded")
    elif e.response.status_code == 401:
        raise AuthenticationError("Token expired")
    raise APIError(f"API error: {e}")
```

### Contact Not Found

If invoice references non-existent contact:

```python
# Xero may still return invoice with empty Contact object
contact_id = transaction_data.get("Contact", {}).get("ContactID") or None

# Store None if not present, not empty string
if contact_id == "" or contact_id is None:
    transaction.contact_id = None
```

---

## ✅ Implementation Checklist

When building `mapper.py`, follow this checklist:

### StandardTransaction Mapper

- [ ] Handle Invoice (Type=ACCREC) → type=INVOICE
- [ ] Handle Invoice (Type=ACCPAY) → type=BILL
- [ ] Handle BankTransfer → type=BANK_TRANSFER
- [ ] Handle CreditNote → type=CREDIT_NOTE
- [ ] Map all status values correctly
- [ ] Parse dates with timezone handling
- [ ] Convert amounts to Decimal
- [ ] Store UUIDs as strings
- [ ] Handle missing Contact (set to None)
- [ ] Extract first line item's account_code
- [ ] Store all line items in line_items array
- [ ] Set platform_id = original Xero ID
- [ ] Set platform_name = "xero"
- [ ] Set sync_status = SyncStatus.SYNCED
- [ ] Handle inclusive/exclusive line amounts
- [ ] Store extra Xero fields in metadata

### StandardContact Mapper

- [ ] Infer type from ContactGroups or addresses
- [ ] Parse email from EmailAddress
- [ ] Parse phone from Phones[0]
- [ ] Build address string from Addresses array
- [ ] Handle missing address gracefully
- [ ] Store tax number in tax_id
- [ ] Default currency to "GBP"
- [ ] Set platform_id = ContactID
- [ ] Set platform_name = "xero"
- [ ] Store all extra fields in metadata
- [ ] Handle soft-deleted contacts (status=ARCHIVED)

### StandardAccount Mapper

- [ ] Map Xero Type → StandardAccount.type enum
- [ ] Store TaxType as-is in tax_type field
- [ ] Set platform_id = AccountID
- [ ] Set platform_name = "xero"
- [ ] Default currency to "GBP"
- [ ] Store status in metadata
- [ ] Handle system accounts flag
- [ ] Store updated timestamp in metadata

### Edge Cases

- [ ] Handle empty LineItems (use default account)
- [ ] Handle invalid dates (use default or raise)
- [ ] Handle missing Contact object
- [ ] Handle archived/deleted records
- [ ] Handle rate limit headers
- [ ] Handle Xero API errors (ApiException in response)
- [ ] Handle pagination (multiple pages)

### Testing

- [ ] Test invoice mapping (ACCREC)
- [ ] Test bill mapping (ACCPAY)
- [ ] Test bank transfer mapping
- [ ] Test credit note mapping
- [ ] Test contact mapping (customer/supplier)
- [ ] Test account mapping
- [ ] Test status mappings
- [ ] Test date parsing
- [ ] Test decimal amount handling
- [ ] Test missing optional fields
- [ ] Test metadata storage
- [ ] Test error handling

---

## 🔗 Related Documentation

- [XERO_API_GUIDE.md](XERO_API_GUIDE.md) - Xero API endpoints and response structures
- [XERO_IMPLEMENTATION_BLUEPRINT.md](XERO_IMPLEMENTATION_BLUEPRINT.md) - Step-by-step implementation guide
- [ABSTRACTION_LAYER.md](ABSTRACTION_LAYER.md) - Standard models definition

---

## 📝 Usage Example

Once `mapper.py` is implemented, usage will look like:

```python
from backend.accounting.xero.mapper import XeroMapper

# Initialize mapper
mapper = XeroMapper()

# Map Xero invoice to StandardTransaction
xero_invoice = {
    "InvoiceID": "12345678-1234-1234-1234-123456789012",
    "InvoiceNumber": "INV-001",
    "InvoiceDate": "2025-01-15T00:00:00Z",
    "Total": "1000.00",
    "TaxTotal": "200.00",
    # ... other fields
}

standard_transaction = mapper.map_invoice_to_transaction(xero_invoice)
# Returns StandardTransaction object with all fields properly mapped

# Map Xero contact to StandardContact
xero_contact = {
    "ContactID": "87654321-4321-4321-4321-210987654321",
    "Name": "ACME Corp",
    # ... other fields
}

standard_contact = mapper.map_contact_to_standard(xero_contact)
# Returns StandardContact object with type inferred

# Map Xero account to StandardAccount
xero_account = {
    "AccountID": "...",
    "Code": "4000",
    "Name": "Sales Income",
    "Type": "REVENUE",
    # ... other fields
}

standard_account = mapper.map_account_to_standard(xero_account)
# Returns StandardAccount object with type mapped
```

---

**Status:** Ready for Implementation
**Next Doc:** [XERO_IMPLEMENTATION_BLUEPRINT.md](XERO_IMPLEMENTATION_BLUEPRINT.md)

---
