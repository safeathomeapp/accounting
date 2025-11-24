# Xero API Integration Guide

**Status:** Ready for Implementation (Week 3)
**Date:** November 24, 2025
**Purpose:** Understand Xero API before building XeroClient adapter

---

## 📋 Table of Contents

1. [Xero Overview](#xero-overview)
2. [Authentication (OAuth 2.0)](#authentication-oauth-20)
3. [API Endpoints](#api-endpoints)
4. [Key Data Models](#key-data-models)
5. [Rate Limiting](#rate-limiting)
6. [Error Handling](#error-handling)
7. [Xero-Specific Quirks](#xero-specific-quirks)
8. [Testing with Demo Company](#testing-with-demo-company)

---

## 🎯 Xero Overview

### What is Xero?
- Cloud-based accounting software
- 70% UK market share (primary target)
- RESTful API with OAuth 2.0 authentication
- Real-time data access
- Excellent for small-to-medium businesses

### Our Integration Strategy
- Read-only access to transactions, contacts, accounts
- No write operations in Phase 1
- All data normalized to StandardTransaction format
- Support both Xero Single Tenant and Multi-Tenant flows

### Xero Credentials Needed
```
XERO_CLIENT_ID=<from developer.xero.com>
XERO_CLIENT_SECRET=<from developer.xero.com>
XERO_TENANT_ID=<obtained after first authentication>
```

**Current Status:** ✅ Configured in `.env`

---

## 🔐 Authentication (OAuth 2.0)

### OAuth 2.0 Flow

Xero uses standard OAuth 2.0 with Proof Key for Code Exchange (PKCE):

```
1. User clicks "Connect to Xero"
   ↓
2. Redirect to Xero authorization endpoint
   ↓
3. User logs in and grants permission
   ↓
4. Xero redirects back with authorization code
   ↓
5. Exchange code for access token (backend)
   ↓
6. Store access + refresh tokens
   ↓
7. Use tokens to make API calls
```

### Key OAuth URLs

```
# Authorization endpoint (user goes here)
https://login.xero.com/identity/connect/authorize

# Token endpoint (we call this)
https://identity.xero.com/connect/token

# Revoke endpoint (optional)
https://identity.xero.com/connect/revoke
```

### OAuth Parameters

**Authorization Request:**
```
GET https://login.xero.com/identity/connect/authorize?
  client_id=YOUR_CLIENT_ID
  response_type=code
  scope=offline_access accounting.transactions accounting.contacts accounting.settings
  redirect_uri=http://localhost:8000/auth/xero/callback
  state=<random_string>
  code_challenge=<PKCE_challenge>
```

**Token Request (after getting code):**
```
POST https://identity.xero.com/connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
code=<authorization_code>
redirect_uri=http://localhost:8000/auth/xero/callback
client_id=YOUR_CLIENT_ID
client_secret=YOUR_CLIENT_SECRET
code_verifier=<PKCE_verifier>
```

### OAuth Scopes We Need

```
offline_access                        # Long-lived tokens
accounting.transactions               # Read transactions (invoices, bills, etc.)
accounting.contacts                   # Read contacts (customers, suppliers)
accounting.settings                   # Read organization info
```

### Token Handling

**Access Token:**
- 30-minute lifetime
- Used for API requests
- Include in Authorization header: `Authorization: Bearer <access_token>`

**Refresh Token:**
- Never expires (if offline_access scope used)
- Exchange for new access token when expired
- MUST be stored securely (encrypted in database)

**Token Response:**
```json
{
  "access_token": "eyJhbGc...",
  "expires_in": 1800,
  "token_type": "Bearer",
  "refresh_token": "...",
  "Xero-tenant-id": "12345678-1234-1234-1234-123456789012"
}
```

### Important: Tenant ID

Xero returns `Xero-tenant-id` in the token response. This is REQUIRED for all API calls:

```
Authorization: Bearer <access_token>
Xero-tenant-id: 12345678-1234-1234-1234-123456789012
```

**Store this in OAuthToken model.**

---

## 📡 API Endpoints

### Base URL
```
https://api.xero.com/api.xro/2.0
```

### Transaction Endpoints

#### Get Invoices (Customer Invoices)
```
GET /Invoices
Parameters:
  where: Filtering (e.g., "Status=="AUTHORISED"")
  page: Pagination (starting at 1)
  orderBy: Sort field and direction

Response:
{
  "Invoices": [
    {
      "InvoiceID": "uuid",
      "InvoiceNumber": "INV-001",
      "Description": "Service provided",
      "Type": "ACCREC",  # Accounts Receivable (customer invoice)
      "Status": "AUTHORISED",  # DRAFT, SUBMITTED, AUTHORISED, PAID, etc.
      "LineItems": [...],
      "Total": 1000.00,
      "TaxTotal": 200.00,
      "InvoiceDate": "2025-01-15T00:00:00Z",
      "DueDate": "2025-02-15T00:00:00Z",
      "Contact": {...},
      "Reference": "ABC123"
    }
  ]
}
```

#### Get Bills (Supplier Bills)
```
GET /Invoices?where=Type=="ACCPAY"
(Same response structure, but ACCPAY = Accounts Payable)
```

#### Get Bank Transfers
```
GET /BankTransfers

Response:
{
  "BankTransfers": [
    {
      "BankTransferID": "uuid",
      "FromBankAccount": {...},
      "ToBankAccount": {...},
      "LineAmountTypes": "Inclusive",
      "LineItems": [
        {
          "Description": "Transfer",
          "Quantity": 1,
          "UnitAmount": 1000,
          "AccountCode": "200"
        }
      ]
    }
  ]
}
```

### Contact Endpoints

#### Get Contacts
```
GET /Contacts
Parameters:
  where: Filter (e.g., "Name=="ACME"")
  page: Pagination

Response:
{
  "Contacts": [
    {
      "ContactID": "uuid",
      "Name": "ACME Corp",
      "ContactNumber": "001",
      "ContactStatus": "ACTIVE",
      "EmailAddress": "hello@acme.com",
      "Website": "www.acme.com",
      "ContactGroups": [...],
      "Addresses": [
        {
          "AddressType": "STREET",
          "City": "London",
          "PostalCode": "SW1A1AA",
          "Country": "GB"
        }
      ],
      "Phones": [
        {
          "PhoneType": "DEFAULT",
          "PhoneNumber": "02012345678"
        }
      ]
    }
  ]
}
```

### Account Endpoints

#### Get Chart of Accounts
```
GET /Accounts

Response:
{
  "Accounts": [
    {
      "AccountID": "uuid",
      "Code": "200",
      "Name": "Sales",
      "Type": "REVENUE",  # ASSET, BANK, CURRENT, EQUITY, EXPENSE, FIXED, LIABILITY, REVENUE, etc.
      "Status": "ACTIVE",
      "TaxType": "Tax on Sales",  # VAT/Tax treatment
      "UpdatedDateUTC": "2025-01-15T10:30:00Z",
      "SystemAccount": true,  # Xero built-in account
      "EnablePayments": false
    }
  ]
}
```

### Organization Endpoints

#### Get Organization Details
```
GET /Organisation

Response:
{
  "Organisations": [
    {
      "OrganisationID": "uuid",
      "Name": "My Business",
      "LegalName": "My Business Ltd",
      "CountryCode": "GB",
      "TaxNumber": "123456789",
      "RegistrationNumber": "12345678",
      "PaysTax": true,
      "OrganisationStatus": "ACTIVE",
      "BaseCurrency": "GBP",
      "ShortCode": "xero",
      "LineOfBusiness": "Professional Services",
      "YearEndDay": 31,
      "YearEndMonth": "12"
    }
  ]
}
```

---

## 🗂️ Key Data Models

### Invoice/Bill Model

```
Xero Invoice → StandardTransaction

Mapping:
- InvoiceID → id
- Type (ACCREC/ACCPAY) → type (INVOICE/BILL)
- InvoiceDate → date
- Description → description
- Total → amount
- TaxTotal → tax_amount
- Status → status
- InvoiceNumber → reference
- Contact → contact_id
- LineItems[0].AccountCode → account_id
```

### Contact Model

```
Xero Contact → StandardContact

Mapping:
- ContactID → id
- Name → name
- EmailAddress → email
- Phones[0].PhoneNumber → phone
- Addresses[0] → address
- TaxNumber → tax_id
- ContactStatus → status
```

### Account Model

```
Xero Account → StandardAccount

Mapping:
- AccountID → id
- Code → code
- Name → name
- Type → type (map REVENUE→INCOME, etc.)
- TaxType → tax_type
```

### VAT/Tax Mapping

Xero uses tax types that map to standard accounts:

```
Xero Tax Type          → Standard Handling
"Tax on Sales"         → VAT output (LIABILITY)
"Tax on Purchases"     → VAT input (EXPENSE recovery)
"No Tax"               → Non-VAT (INCOME/EXPENSE)
"Tax on Capital"       → Capital asset tax
"Input Tax on Fixed"   → Fixed asset VAT
"Exemption"            → VAT exempt
```

---

## ⚠️ Rate Limiting

### Xero Rate Limits

- **Per tenant:** 60 API calls per minute
- **Across app:** May have additional throttling
- **Limit headers:** Included in response

### Rate Limit Headers

```
X-Rate-Limit-Problem: <count>
X-Rate-Limit-Limit-Minute: 60
X-Rate-Limit-Remaining-Minute: 59
```

### Handling Rate Limits

1. **Read headers** - Check remaining before calling
2. **Exponential backoff** - Wait before retrying
3. **Batch requests** - Use pagination efficiently
4. **Cache aggressively** - Reduce API calls

### Rate Limit Strategy for Our App

```python
# If X-Rate-Limit-Remaining < 5:
#   Wait until next minute
#   OR delay requests by 1 second

# Cache transaction data:
#   - Full sync: Cache for 1 hour
#   - Incremental sync: Cache for 15 minutes
```

---

## ❌ Error Handling

### Xero Error Response Format

```json
{
  "ApiException": {
    "ErrorNumber": 400,
    "Type": "ValidationException",
    "Message": "The element 'Contact' is required",
    "Elements": [
      {
        "ValidationErrors": [
          {
            "Message": "Contact is not a valid Xero identifier",
            "ErrorNumber": 10
          }
        ]
      }
    ]
  }
}
```

### Common Xero Errors

| Error | Meaning | Action |
|-------|---------|--------|
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Refresh OAuth token |
| 403 | Forbidden | Check scopes/permissions |
| 404 | Not Found | Resource doesn't exist |
| 429 | Rate Limited | Backoff and retry |
| 500 | Server Error | Retry with backoff |

### Our Error Mapping

```
Xero Error → Our Exception

400/422  → ValidationError (data issue)
401      → AuthenticationError (token expired)
403      → AuthenticationError (missing scope)
404      → NotFoundError (resource missing)
429      → RateLimitError (wait and retry)
500+     → APIError (server problem)
```

---

## 🤔 Xero-Specific Quirks

### 1. UUID vs String IDs

Xero uses UUIDs for IDs:
```
InvoiceID: "12345678-1234-1234-1234-123456789012"
ContactID: "87654321-4321-4321-4321-210987654321"
```

**Handling:** Store as strings, match against UUID format.

### 2. Invoice Amounts

Amounts may be in different line amount types:

```
"LineAmountTypes": "Inclusive"  # Total includes tax
"LineAmountTypes": "Exclusive"  # Total excludes tax

Always check and handle both cases!
```

### 3. Contact Types vs Our Contact Model

Xero doesn't have explicit "type" field. Contact is used for:
- CUSTOMER (used in ACCREC invoices)
- SUPPLIER (used in ACCPAY invoices)
- EMPLOYEE (not in standard contacts, different endpoint)

**Handling:** Infer type from how they appear in transactions.

### 4. Status Values

Different statuses for different document types:

**Invoice/Bill Status:**
- DRAFT
- SUBMITTED
- AUTHORISED
- PAID (invoices only)
- AWAITING_PAYMENT (invoices only)

**Contact Status:**
- ACTIVE
- ARCHIVED
- DELETED

### 5. Date Formats

Xero returns dates in ISO 8601 format with Z (UTC):
```
"InvoiceDate": "2025-01-15T00:00:00Z"
```

**Handling:** Parse as datetime with timezone info.

### 6. Pagination

Xero paginating uses `page` parameter:
```
GET /Invoices?page=1      # First 100 items
GET /Invoices?page=2      # Items 101-200
```

Always check if more pages exist in response.

### 7. Filtering

Xero uses `where` parameter with specific syntax:

```
GET /Invoices?where=Status=="AUTHORISED"
GET /Contacts?where=Name=="ACME*"  (* is wildcard)
GET /Invoices?where=InvoiceDate>DateTime(2025,1,1)
```

### 8. Soft Deletes

Xero doesn't hard-delete. Use status:
```
DELETE /Contact/123  → Sets ContactStatus="ARCHIVED"
```

Check status field to filter out archived records.

### 9. Line Items

Invoices/Bills have line items:
```json
{
  "LineItems": [
    {
      "Description": "Service",
      "Quantity": 1,
      "UnitAmount": 1000.00,
      "AccountCode": "200",
      "TaxType": "Tax on Sales",
      "TaxAmount": 200.00,
      "LineAmount": 1000.00
    }
  ]
}
```

**Handling:** For simplicity, take first line item's account code.

### 10. Version Requirements

Different endpoints available based on API version:

- **v2.0** - Current version (what we use)
- Some endpoints deprecated in newer versions

Always use `/api.xro/2.0/` base URL.

---

## 🧪 Testing with Demo Company

### Getting Demo Company Access

1. **In Xero Settings:**
   - Go to Settings → Organization
   - Note the Organization ID in the URL

2. **In Your .env:**
   ```
   XERO_DEMO_TENANT_ID=<noted from above>
   ```

3. **Available Demo Data:**
   - Preloaded invoices, bills, contacts
   - Test transactions (amounts vary)
   - Chart of accounts already set up

### Test Data Available

```
Invoices (ACCREC):
- INV-0001 to INV-0010 (various amounts)
- Status: AUTHORISED

Bills (ACCPAY):
- Bill-0001 to Bill-0005
- Status: AUTHORISED

Contacts:
- Northwind Traders
- Acme Inc
- Others

Chart of Accounts:
- Full UK chart (assets, liabilities, income, expenses)
- VAT accounts (Output, Input)
```

### Safe Testing

```python
# What you can do (safe):
- GET transactions
- GET contacts
- GET accounts
- GET organization info

# What to avoid (affects demo data):
- POST/PUT (creates actual data)
- DELETE (modifies demo account)
```

---

## 🚀 Ready for Implementation

This guide covers everything needed to build `XeroClient`.

### Next Steps

1. **Read [DATA_MAPPING_SPEC.md](DATA_MAPPING_SPEC.md)** - Exact data transformations
2. **Read [XERO_IMPLEMENTATION_BLUEPRINT.md](XERO_IMPLEMENTATION_BLUEPRINT.md)** - Step-by-step code plan
3. **Start implementing** - Create `backend/accounting/xero/` with client.py, auth.py, mapper.py

### Key Takeaways

- ✅ OAuth 2.0 with PKCE
- ✅ RESTful endpoints for invoices, bills, contacts, accounts
- ✅ Rate limiting: 60/minute per tenant
- ✅ ISO 8601 datetime format (parse with timezone)
- ✅ UUID for all IDs (store as strings)
- ✅ UnicodeDecodeError: handle status carefully
- ✅ Pagination with `page` parameter
- ✅ Demo company available for testing

---

**Status:** Ready for Week 3 implementation
**Next Doc:** [DATA_MAPPING_SPEC.md](DATA_MAPPING_SPEC.md)

---
