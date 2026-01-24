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

# FreeAgent Data Mapping Specification

**Added:** January 24, 2026
**Purpose:** Define exact mappings from FreeAgent API data to StandardTransaction, StandardContact, StandardAccount

---

## FreeAgent Overview

FreeAgent is a UK-focused accounting platform with some key differences from Xero:
- Uses URL-based resource identifiers (not simple IDs)
- Uses "Categories" with nominal codes instead of chart of accounts
- No explicit customer/supplier types on contacts
- Date format: `YYYY-MM-DD` (simple dates) or ISO 8601 (timestamps)

---

## FreeAgent StandardTransaction Mapping

### Source: FreeAgent Invoice

FreeAgent Invoice → StandardTransaction with type=INVOICE

```
FreeAgent Field          →  StandardTransaction Field   →  Notes
─────────────────────────────────────────────────────────────────────────
url (extract ID)         →  id                          →  Extract from URL
"INVOICE"                →  type                        →  Hardcode INVOICE
dated_on                 →  date                        →  Parse YYYY-MM-DD
reference                →  reference                   →  "INV-001"
(from invoice_items[0])  →  description                 →  First item description
total_value              →  amount                      →  Decimal from response
sales_tax_value          →  tax_amount                  →  Decimal from response
status                   →  status                      →  Map per table below
contact (extract ID)     →  contact_id                  →  Extract from URL
invoice_items[0].category → account_id                  →  First item's category ID
(none)                   →  platform_id                 →  Same as id
"freeagent"              →  platform_name               →  Hardcode "freeagent"
(none)                   →  sync_status                 →  Default: SyncStatus.SYNCED
invoice_items            →  line_items                  →  Array of item dicts
due_on, currency, etc.   →  metadata                    →  Extra FreeAgent data
```

### Source: FreeAgent Bill

FreeAgent Bill → StandardTransaction with type=BILL

```
FreeAgent Field          →  StandardTransaction Field   →  Notes
─────────────────────────────────────────────────────────────────────────
url (extract ID)         →  id                          →  Extract from URL
"BILL"                   →  type                        →  Hardcode BILL
dated_on                 →  date                        →  Parse YYYY-MM-DD
reference                →  reference                   →  "BILL-001"
(from bill_items[0])     →  description                 →  First item description
total_value              →  amount                      →  Decimal from response
sales_tax_value          →  tax_amount                  →  Decimal from response
status                   →  status                      →  Map per table below
contact (extract ID)     →  contact_id                  →  Extract from URL
bill_items[0].category   →  account_id                  →  First item's category ID
(none)                   →  platform_id                 →  Same as id
"freeagent"              →  platform_name               →  Hardcode "freeagent"
(none)                   →  sync_status                 →  Default: SyncStatus.SYNCED
bill_items               →  line_items                  →  Array of item dicts
due_on, currency, etc.   →  metadata                    →  Extra FreeAgent data
```

### Source: FreeAgent Credit Note

FreeAgent Credit Note → StandardTransaction with type=CREDIT_NOTE

```
FreeAgent Field          →  StandardTransaction Field   →  Notes
─────────────────────────────────────────────────────────────────────────
url (extract ID)         →  id                          →  Extract from URL
"CREDIT_NOTE"            →  type                        →  Hardcode CREDIT_NOTE
dated_on                 →  date                        →  Parse YYYY-MM-DD
reference                →  reference                   →  "CN-001"
(none)                   →  description                 →  Use reference
total_value              →  amount                      →  Decimal (may be negative)
sales_tax_value          →  tax_amount                  →  Decimal (may be negative)
status                   →  status                      →  Map per table below
contact (extract ID)     →  contact_id                  →  Extract from URL
credit_note_items[0].category → account_id              →  First item's category ID
(none)                   →  platform_id                 →  Same as id
"freeagent"              →  platform_name               →  Hardcode "freeagent"
```

### Invoice Status Mapping

```
FreeAgent Status       →  StandardTransaction.status   →  Notes
─────────────────────────────────────────────────────────────────
Draft                  →  "draft"                      →  Not yet sent
Scheduled To Email     →  "scheduled"                  →  Awaiting send
Open                   →  "approved"                   →  Sent, awaiting payment
Zero Value             →  "approved"                   →  No payment needed
Overdue                →  "overdue"                    →  Past due date
Paid                   →  "paid"                       →  Fully paid
Overpaid               →  "paid"                       →  Paid more than due
Refunded               →  "refunded"                   →  Money returned
Written-off            →  "written_off"                →  Bad debt
Part written-off       →  "partial_written_off"        →  Partial bad debt
```

### Bill Status Mapping

```
FreeAgent Status       →  StandardTransaction.status   →  Notes
─────────────────────────────────────────────────────────────────
Zero Value             →  "approved"                   →  No payment needed
Open                   →  "approved"                   →  Awaiting payment
Paid                   →  "paid"                       →  Fully paid
Overdue                →  "overdue"                    →  Past due date
Refunded               →  "refunded"                   →  Money returned
```

### Credit Note Status Mapping

```
FreeAgent Status       →  StandardTransaction.status   →  Notes
─────────────────────────────────────────────────────────────────
Draft                  →  "draft"                      →  Not yet sent
Open                   →  "approved"                   →  Active
Overdue                →  "overdue"                    →  Past due
Refunded               →  "refunded"                   →  Applied/used
Written-off            →  "written_off"                →  Cancelled
```

---

## FreeAgent StandardContact Mapping

### Source: FreeAgent Contact

FreeAgent Contact → StandardContact

```
FreeAgent Field          →  StandardContact Field   →  Notes
──────────────────────────────────────────────────────────────
url (extract ID)         →  id                      →  Extract from URL
organisation_name        →  name                    →  Or first_name + last_name
email                    →  email                   →  Primary email
phone_number             →  phone                   →  Office phone
address1/2/3/town/etc.   →  address                 →  Concatenated string
sales_tax_registration_number → tax_id              →  VAT number
(inferred)               →  type                    →  See type inference below
"GBP"                    →  currency                →  Default for UK
url (extract ID)         →  platform_id             →  Same as id
"freeagent"              →  platform_name           →  Hardcode "freeagent"
other fields             →  metadata                →  Extra data
```

### Contact Type Inference

FreeAgent doesn't have explicit contact types. Infer from context:

```python
# Method 1: Use API view parameter
GET /contacts?view=clients    → ContactType.CUSTOMER
GET /contacts?view=suppliers  → ContactType.SUPPLIER

# Method 2: Check transaction usage (requires additional queries)
# - Contact appears in invoices → CUSTOMER
# - Contact appears in bills → SUPPLIER

# Method 3: Default
# - Default to ContactType.CUSTOMER if unknown
```

### Contact Name Building

```python
# Priority 1: Organisation name
if contact.get("organisation_name"):
    name = contact["organisation_name"]

# Priority 2: First + Last name
elif contact.get("first_name") or contact.get("last_name"):
    name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()

# Priority 3: Empty string (shouldn't happen)
else:
    name = ""
```

### Address Building

```python
address_parts = [
    contact.get("address1"),
    contact.get("address2"),
    contact.get("address3"),
    contact.get("town"),
    contact.get("region"),
    contact.get("postcode"),
    contact.get("country"),
]
address = ", ".join(filter(None, address_parts))
```

---

## FreeAgent StandardAccount Mapping

### Source: FreeAgent Category

FreeAgent uses "Categories" with nominal codes instead of a traditional chart of accounts.

FreeAgent Category → StandardAccount

```
FreeAgent Field          →  StandardAccount Field   →  Notes
───────────────────────────────────────────────────────────────
nominal_code             →  id                      →  e.g., "001", "200"
nominal_code             →  code                    →  Same as id
description              →  name                    →  e.g., "Sales"
(from code range)        →  type                    →  Map per table below
auto_sales_tax_rate      →  tax_type                →  e.g., "Standard Rate"
"GBP"                    →  currency                →  Default for UK
nominal_code             →  platform_id             →  Same as id
"freeagent"              →  platform_name           →  Hardcode "freeagent"
group_description, etc.  →  metadata                →  Extra data
```

### Category Type Mapping (Nominal Code Ranges)

```
Nominal Code Range     →  StandardAccount.type   →  FreeAgent Usage
──────────────────────────────────────────────────────────────────
001-049               →  AccountType.INCOME      →  Income
096-199               →  AccountType.EXPENSE     →  Cost of Sales
200-399               →  AccountType.EXPENSE     →  Admin Expenses
671-720               →  AccountType.ASSET       →  Current Assets
731-780               →  AccountType.LIABILITY   →  Liabilities
921-960               →  AccountType.EQUITY      →  Equities
(other)               →  AccountType.EXPENSE     →  Default
```

### Implementation

```python
def map_category_type(nominal_code: str) -> AccountType:
    try:
        code = int(nominal_code)
    except (ValueError, TypeError):
        return AccountType.EXPENSE  # Default

    if 1 <= code <= 49:
        return AccountType.INCOME
    elif 96 <= code <= 199:
        return AccountType.EXPENSE  # Cost of Sales
    elif 200 <= code <= 399:
        return AccountType.EXPENSE  # Admin Expenses
    elif 671 <= code <= 720:
        return AccountType.ASSET
    elif 731 <= code <= 780:
        return AccountType.LIABILITY
    elif 921 <= code <= 960:
        return AccountType.EQUITY
    else:
        return AccountType.EXPENSE
```

---

## FreeAgent Special Cases & Transformations

### 1. URL ID Extraction

FreeAgent uses URLs as identifiers:
```
"contact": "https://api.freeagent.com/v2/contacts/12345"
```

**Handling:**
```python
def extract_id_from_url(url: str) -> str:
    if not url:
        return ""
    return url.rstrip('/').split('/')[-1]

# Example:
extract_id_from_url("https://api.freeagent.com/v2/invoices/12345")
# Returns: "12345"
```

### 2. Date Parsing

FreeAgent uses two date formats:

**Simple dates (transactions):**
```
"dated_on": "2026-01-15"
```

**ISO 8601 timestamps (metadata):**
```
"created_at": "2026-01-15T10:30:00Z"
```

**Handling:**
```python
from datetime import datetime, date

def parse_freeagent_date(date_string: str) -> date:
    """Parse simple date."""
    return datetime.strptime(date_string, "%Y-%m-%d").date()

def parse_freeagent_datetime(datetime_string: str) -> datetime:
    """Parse ISO 8601 datetime."""
    return datetime.fromisoformat(datetime_string.replace("Z", "+00:00"))
```

### 3. Nested Items

To get line items, add query parameter:
```
GET /invoices?nested_invoice_items=true
GET /bills?nested_bill_items=true
GET /credit_notes?nested_credit_note_items=true
```

Without this, items are not included in list responses.

### 4. Currency Handling

FreeAgent defaults to company currency (usually GBP for UK businesses).

```python
# Get currency from invoice, default to GBP
currency = invoice.get("currency", "GBP")

# Exchange rate for multi-currency
exchange_rate = invoice.get("exchange_rate", "1.0")
```

### 5. VAT/Tax Handling

FreeAgent tracks VAT with:
```python
# On categories
"auto_sales_tax_rate": "Standard Rate"  # or "Zero Rate", "Reduced Rate", "Exempt", "Outside Scope"

# On contacts
"sales_tax_registration_number": "GB123456789"

# On invoices/bills
"ec_status": "UK"  # or "Non-EC", "EC Goods", "EC Services", "Reverse Charge"
```

---

## FreeAgent Error Handling & Fallbacks

### Missing Fields

```python
# If description missing, use reference
description = invoice.get("reference", "")
if invoice.get("invoice_items"):
    description = invoice["invoice_items"][0].get("description", description)

# If contact missing, set to None
contact_url = invoice.get("contact", "")
contact_id = extract_id_from_url(contact_url) if contact_url else None

# If items empty, use empty list
line_items = invoice.get("invoice_items", [])
```

### Invalid Data Types

```python
from decimal import Decimal

# Amounts - FreeAgent returns strings
amount = Decimal(str(invoice.get("total_value", "0")))

# Dates - may be None
date_str = invoice.get("dated_on")
if date_str:
    date_obj = parse_freeagent_date(date_str)
else:
    date_obj = None

# IDs - extract from URL
contact_id = extract_id_from_url(invoice.get("contact", ""))
```

---

## FreeAgent Implementation Checklist

### StandardTransaction Mapper

- [ ] Handle Invoice → type=INVOICE
- [ ] Handle Bill → type=BILL
- [ ] Handle Credit Note → type=CREDIT_NOTE
- [ ] Extract IDs from URLs
- [ ] Parse dates (YYYY-MM-DD format)
- [ ] Convert amounts to Decimal
- [ ] Map all status values correctly
- [ ] Handle missing contact (set to None)
- [ ] Extract category from first line item
- [ ] Store all line items in line_items array
- [ ] Set platform_name = "freeagent"
- [ ] Set sync_status = SyncStatus.SYNCED
- [ ] Store extra fields in metadata

### StandardContact Mapper

- [ ] Extract ID from URL
- [ ] Build name from organisation_name or first/last name
- [ ] Concatenate address fields
- [ ] Handle missing email/phone gracefully
- [ ] Store VAT number in tax_id
- [ ] Accept contact_type from caller (view=clients/suppliers)
- [ ] Set platform_name = "freeagent"
- [ ] Store all extra fields in metadata

### StandardAccount Mapper (Category)

- [ ] Use nominal_code as id and code
- [ ] Map nominal code range → AccountType enum
- [ ] Store auto_sales_tax_rate as tax_type
- [ ] Set platform_name = "freeagent"
- [ ] Default currency to "GBP"
- [ ] Store group_description in metadata

### Edge Cases

- [ ] Handle empty URLs (return empty string for ID)
- [ ] Handle missing line items (use empty list)
- [ ] Handle invalid dates (return None or raise)
- [ ] Handle rate limiting (429 with Retry-After)
- [ ] Handle pagination (page and per_page params)

---

## FreeAgent Usage Example

```python
from backend.accounting.freeagent.mapper import FreeAgentMapper

# Initialize mapper
mapper = FreeAgentMapper()

# Map FreeAgent invoice to StandardTransaction
freeagent_invoice = {
    "url": "https://api.freeagent.com/v2/invoices/12345",
    "contact": "https://api.freeagent.com/v2/contacts/67890",
    "dated_on": "2026-01-15",
    "reference": "INV-001",
    "total_value": "1200.00",
    "sales_tax_value": "200.00",
    "status": "Open",
    "invoice_items": [
        {
            "description": "Consulting",
            "quantity": "10",
            "price": "100.00",
            "category": "https://api.freeagent.com/v2/categories/001",
        }
    ],
}

standard_transaction = mapper.map_invoice_to_transaction(freeagent_invoice)
# Returns StandardTransaction:
#   id="12345", type=INVOICE, amount=1200.00, contact_id="67890", account_id="001"

# Map FreeAgent contact to StandardContact
freeagent_contact = {
    "url": "https://api.freeagent.com/v2/contacts/67890",
    "organisation_name": "ACME Corp",
    "email": "hello@acme.com",
    "phone_number": "020 1234 5678",
    "address1": "123 Main Street",
    "town": "London",
    "postcode": "SW1A 1AA",
}

standard_contact = mapper.map_contact_to_standard(
    freeagent_contact,
    contact_type=ContactType.CUSTOMER
)
# Returns StandardContact:
#   id="67890", name="ACME Corp", type=CUSTOMER

# Map FreeAgent category to StandardAccount
freeagent_category = {
    "url": "https://api.freeagent.com/v2/categories/001",
    "description": "Sales",
    "nominal_code": "001",
    "auto_sales_tax_rate": "Standard Rate",
}

standard_account = mapper.map_category_to_account(freeagent_category)
# Returns StandardAccount:
#   id="001", code="001", name="Sales", type=INCOME
```

---

## Related Documentation

- [FREEAGENT_API_GUIDE.md](FREEAGENT_API_GUIDE.md) - FreeAgent API endpoints and authentication
- [FREEAGENT_IMPLEMENTATION_BLUEPRINT.md](FREEAGENT_IMPLEMENTATION_BLUEPRINT.md) - Step-by-step implementation
- [XERO_API_GUIDE.md](XERO_API_GUIDE.md) - Xero API (for comparison)

---

**FreeAgent Section Added:** January 24, 2026
**Status:** Ready for Implementation
