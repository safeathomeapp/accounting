# FreeAgent API Integration Guide

**Status:** Ready for Implementation
**Date:** January 24, 2026
**Purpose:** Understand FreeAgent API before building FreeAgentClient adapter

---

## Table of Contents

1. [FreeAgent Overview](#freeagent-overview)
2. [Authentication (OAuth 2.0)](#authentication-oauth-20)
3. [API Endpoints](#api-endpoints)
4. [Key Data Models](#key-data-models)
5. [Rate Limiting](#rate-limiting)
6. [Error Handling](#error-handling)
7. [FreeAgent-Specific Quirks](#freeagent-specific-quirks)
8. [Testing with Sandbox](#testing-with-sandbox)

---

## FreeAgent Overview

### What is FreeAgent?

- Cloud-based accounting software designed for UK small businesses and freelancers
- Strong focus on UK tax compliance (MTD, HMRC integration, VAT)
- RESTful API with OAuth 2.0 authentication
- Supports both JSON and XML responses
- Popular with UK accountancy practices managing multiple clients

### Our Integration Strategy

- Read-only access to invoices, bills, contacts, accounts (Phase 1)
- No write operations initially
- All data normalized to StandardTransaction format
- Support for Accountancy Practice API (multi-client access)

### FreeAgent Credentials Needed

```
FREEAGENT_CLIENT_ID=<OAuth identifier from Developer Dashboard>
FREEAGENT_CLIENT_SECRET=<OAuth secret from Developer Dashboard>
FREEAGENT_REDIRECT_URI=<Your registered callback URL>
```

**Current Status:** Pending sandbox access from FreeAgent integrations team

---

## Authentication (OAuth 2.0)

### OAuth 2.0 Flow

FreeAgent uses standard OAuth 2.0 (Draft 22) without PKCE:

```
1. User clicks "Connect to FreeAgent"
   |
2. Redirect to FreeAgent authorization endpoint
   |
3. User logs in and grants permission
   |
4. FreeAgent redirects back with authorization code
   |
5. Exchange code for access token (backend)
   |
6. Store access + refresh tokens
   |
7. Use tokens to make API calls
```

### Key OAuth URLs

```
# Authorization endpoint (user goes here)
https://api.freeagent.com/v2/approve_app

# Token endpoint (we call this)
https://api.freeagent.com/v2/token_endpoint

# Sandbox authorization
https://api.sandbox.freeagent.com/v2/approve_app

# Sandbox token endpoint
https://api.sandbox.freeagent.com/v2/token_endpoint
```

### OAuth Parameters

**Authorization Request:**
```
GET https://api.freeagent.com/v2/approve_app?
  client_id=YOUR_CLIENT_ID
  response_type=code
  redirect_uri=http://localhost:8000/auth/freeagent/callback
  state=<random_string>
```

**Token Request (after getting code):**
```
POST https://api.freeagent.com/v2/token_endpoint
Content-Type: application/x-www-form-urlencoded
Authorization: Basic base64(client_id:client_secret)

grant_type=authorization_code
code=<authorization_code>
redirect_uri=http://localhost:8000/auth/freeagent/callback
```

### Token Handling

**Access Token:**
- 1-hour lifetime (3600 seconds)
- Used for API requests
- Include in Authorization header: `Authorization: Bearer <access_token>`

**Refresh Token:**
- Long-lived (does not expire quickly)
- Exchange for new access token when expired
- MUST be stored securely (encrypted in database)

**Token Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "...",
  "refresh_token_expires_in": 5184000
}
```

### Refresh Token Process

```
POST https://api.freeagent.com/v2/token_endpoint
Content-Type: application/x-www-form-urlencoded
Authorization: Basic base64(client_id:client_secret)

grant_type=refresh_token
refresh_token=<refresh_token>
```

### Important: HTTP Basic Auth

Unlike Xero, FreeAgent requires HTTP Basic Authentication for token requests:
- Username: Client ID
- Password: Client Secret
- Header: `Authorization: Basic base64(client_id:client_secret)`

---

## API Endpoints

### Base URL

```
# Production
https://api.freeagent.com/v2

# Sandbox
https://api.sandbox.freeagent.com/v2
```

### Required Headers

```
Authorization: Bearer <access_token>
Accept: application/json
Content-Type: application/json
User-Agent: YourAppName/1.0
```

**Note:** The `User-Agent` header is required for all requests.

### Invoice Endpoints

#### List Invoices
```
GET /invoices
Parameters:
  view: Filter (all, recent_open_or_overdue, open, overdue, draft, paid, scheduled_to_email)
  contact: Filter by contact URI
  project: Filter by project URI
  updated_since: ISO 8601 timestamp
  sort: Sort field (created_at, updated_at, -created_at, -updated_at)
  nested_invoice_items: true (include line items)
  page: Page number
  per_page: Items per page (max 100)

Response:
{
  "invoices": [
    {
      "url": "https://api.freeagent.com/v2/invoices/12345",
      "contact": "https://api.freeagent.com/v2/contacts/67890",
      "dated_on": "2026-01-15",
      "due_on": "2026-02-15",
      "reference": "INV-001",
      "currency": "GBP",
      "exchange_rate": "1.0",
      "net_value": "1000.00",
      "sales_tax_value": "200.00",
      "total_value": "1200.00",
      "paid_value": "0.00",
      "due_value": "1200.00",
      "status": "Open",
      "invoice_items": [...]
    }
  ]
}
```

#### Get Single Invoice
```
GET /invoices/:id

Response:
{
  "invoice": {
    "url": "https://api.freeagent.com/v2/invoices/12345",
    ...
  }
}
```

#### Invoice Status Values
- Draft
- Scheduled To Email
- Open
- Zero Value
- Overdue
- Paid
- Overpaid
- Refunded
- Written-off
- Part written-off

### Bill Endpoints

#### List Bills
```
GET /bills
Parameters:
  view: Filter (open, overdue, open_or_overdue, paid, recurring, hire_purchase, cis)
  contact: Filter by contact URI
  project: Filter by project URI
  from_date: YYYY-MM-DD
  to_date: YYYY-MM-DD
  updated_since: ISO 8601 timestamp
  nested_bill_items: true (include line items)
  page: Page number
  per_page: Items per page (max 100)

Response:
{
  "bills": [
    {
      "url": "https://api.freeagent.com/v2/bills/12345",
      "contact": "https://api.freeagent.com/v2/contacts/67890",
      "reference": "BILL-001",
      "dated_on": "2026-01-10",
      "due_on": "2026-02-10",
      "currency": "GBP",
      "total_value": "500.00",
      "net_value": "416.67",
      "sales_tax_value": "83.33",
      "due_value": "500.00",
      "status": "Open",
      "bill_items": [...]
    }
  ]
}
```

#### Bill Status Values
- Zero Value
- Open
- Paid
- Overdue
- Refunded

### Credit Note Endpoints

#### List Credit Notes
```
GET /credit_notes
Parameters:
  contact: Filter by contact URI
  project: Filter by project URI
  updated_since: ISO 8601 timestamp
  nested_credit_note_items: true
  page: Page number
  per_page: Items per page (max 100)

Response:
{
  "credit_notes": [
    {
      "url": "https://api.freeagent.com/v2/credit_notes/12345",
      "contact": "https://api.freeagent.com/v2/contacts/67890",
      "dated_on": "2026-01-15",
      "reference": "CN-001",
      "net_value": "-100.00",
      "sales_tax_value": "-20.00",
      "total_value": "-120.00",
      "status": "Open"
    }
  ]
}
```

#### Credit Note Status Values
- Draft
- Open
- Overdue
- Refunded
- Written-off

### Contact Endpoints

#### List Contacts
```
GET /contacts
Parameters:
  view: Filter (all, active, clients, suppliers, active_projects, completed_projects, open_clients, open_suppliers, hidden)
  sort: Sort field (name, created_at, updated_at, -name, -created_at, -updated_at)
  updated_since: ISO 8601 timestamp
  page: Page number
  per_page: Items per page (max 100)

Response:
{
  "contacts": [
    {
      "url": "https://api.freeagent.com/v2/contacts/12345",
      "organisation_name": "ACME Corp",
      "first_name": "John",
      "last_name": "Smith",
      "email": "john@acme.com",
      "phone_number": "020 1234 5678",
      "mobile": "07700 900000",
      "address1": "123 Main Street",
      "town": "London",
      "postcode": "SW1A 1AA",
      "country": "United Kingdom",
      "sales_tax_registration_number": "GB123456789",
      "locale": "en",
      "account_balance": "1200.00",
      "status": "Active",
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2026-01-15T14:30:00Z"
    }
  ]
}
```

**Note:** FreeAgent doesn't have explicit "customer" vs "supplier" types. Use the `view` filter (clients vs suppliers) or infer from transaction usage.

### Category Endpoints (Chart of Accounts)

FreeAgent uses "Categories" instead of a traditional chart of accounts:

#### List Categories
```
GET /categories

Response:
{
  "categories": [
    {
      "url": "https://api.freeagent.com/v2/categories/001",
      "description": "Sales",
      "nominal_code": "001",
      "group_description": "Income",
      "auto_sales_tax_rate": "Standard Rate"
    }
  ]
}
```

#### Category Nominal Code Ranges

| Type | Code Range | Purpose |
|------|------------|---------|
| Income | 001-049 | Revenue accounts |
| Cost of Sales | 096-199 | Direct costs |
| Admin Expenses | 200-399 | Operating expenses |
| Current Assets | 671-720 | Working capital |
| Liabilities | 731-780 | Payables & obligations |
| Equities | 921-960 | Owner's equity |

### Bank Account Endpoints

#### List Bank Accounts
```
GET /bank_accounts
Parameters:
  view: Filter (standard_bank_accounts, credit_card_accounts, paypal_accounts)

Response:
{
  "bank_accounts": [
    {
      "url": "https://api.freeagent.com/v2/bank_accounts/12345",
      "name": "Business Current Account",
      "type": "StandardBankAccount",
      "currency": "GBP",
      "current_balance": "5000.00",
      "opening_balance": "1000.00",
      "status": "Active",
      "is_primary": true,
      "account_number": "12345678",
      "sort_code": "12-34-56"
    }
  ]
}
```

#### Bank Account Types
- StandardBankAccount
- CreditCardAccount
- PaypalAccount

### Bank Transaction Endpoints

#### List Bank Transactions
```
GET /bank_transactions?bank_account=<bank_account_uri>
Parameters:
  bank_account: Required - URI of bank account
  from_date: YYYY-MM-DD
  to_date: YYYY-MM-DD
  updated_since: ISO 8601 timestamp

Response:
{
  "bank_transactions": [
    {
      "url": "https://api.freeagent.com/v2/bank_transactions/12345",
      "amount": "-150.00",
      "bank_account": "https://api.freeagent.com/v2/bank_accounts/67890",
      "dated_on": "2026-01-15",
      "description": "Office Supplies",
      "unexplained_amount": "0.00",
      "is_manual": false
    }
  ]
}
```

#### Bank Transaction Types
- CREDIT, DEBIT
- INT (interest), DIV (dividend)
- FEE, SRVCHG (service charge)
- DEP (deposit), ATM, POS (point of sale)
- XFER (transfer), CHECK, PAYMENT
- CASH, DIRECTDEP, DIRECTDEBIT
- REPEATPMT, OTHER

### Company Endpoint

#### Get Company Info
```
GET /company

Response:
{
  "company": {
    "url": "https://api.freeagent.com/v2/company",
    "name": "My Business Ltd",
    "subdomain": "mybusiness",
    "type": "UkLimitedCompany",
    "currency": "GBP",
    "mileage_units": "miles",
    "company_start_date": "2020-01-01",
    "freeagent_start_date": "2020-01-01",
    "first_accounting_year_end": "2020-12-31",
    "company_registration_number": "12345678",
    "sales_tax_registration_number": "GB123456789",
    "sales_tax_registration_status": "Registered",
    "sales_tax_effective_date": "2020-01-01"
  }
}
```

---

## Key Data Models

### Invoice Model

```
FreeAgent Invoice -> StandardTransaction

Mapping:
- url (extract ID)        -> id
- "INVOICE"               -> type (hardcoded)
- dated_on                -> date
- reference               -> reference
- (from items)            -> description
- total_value             -> amount
- sales_tax_value         -> tax_amount
- status                  -> status (mapped)
- contact (extract ID)    -> contact_id
- (from items)            -> account_id
- "freeagent"             -> platform_name
```

### Bill Model

```
FreeAgent Bill -> StandardTransaction

Mapping:
- url (extract ID)        -> id
- "BILL"                  -> type (hardcoded)
- dated_on                -> date
- reference               -> reference
- (from items)            -> description
- total_value             -> amount
- sales_tax_value         -> tax_amount
- status                  -> status (mapped)
- contact (extract ID)    -> contact_id
- (from items)            -> account_id
- "freeagent"             -> platform_name
```

### Contact Model

```
FreeAgent Contact -> StandardContact

Mapping:
- url (extract ID)        -> id
- organisation_name/name  -> name
- email                   -> email
- phone_number            -> phone
- address fields          -> address (concatenated)
- sales_tax_registration_number -> tax_id
- (inferred from usage)   -> type (CUSTOMER/SUPPLIER)
- "freeagent"             -> platform_name
```

### Category Model (Account)

```
FreeAgent Category -> StandardAccount

Mapping:
- nominal_code            -> id
- nominal_code            -> code
- description             -> name
- (from code range)       -> type (INCOME/EXPENSE/ASSET/LIABILITY/EQUITY)
- auto_sales_tax_rate     -> tax_type
- "freeagent"             -> platform_name
```

---

## Rate Limiting

### FreeAgent Rate Limits

- **Per user:** 120 API calls per minute
- **Per user:** 3,600 API calls per hour
- **Token refresh:** 15 refreshes per minute

### Rate Limit Response

When rate limited, FreeAgent returns:
- HTTP Status: `429 Too Many Requests`
- Header: `Retry-After: <seconds>`

### Handling Rate Limits

1. **Check Retry-After header** - Wait the specified time
2. **Exponential backoff** - If no header, wait 1s, 2s, 4s...
3. **Track locally** - Count requests per minute
4. **Cache aggressively** - Reduce unnecessary API calls

### Rate Limit Strategy for Our App

```python
# If approaching limit (>100 requests in last minute):
#   Slow down requests
#   Wait before retrying

# Cache transaction data:
#   - Full sync: Cache for 1 hour
#   - Incremental sync: Use updated_since parameter
```

### Testing Rate Limits

In sandbox, use the header `X-RateLimit-Test: true` to lower limits to 5 requests/minute for testing your rate limit handling.

---

## Error Handling

### FreeAgent Error Response Format

```json
{
  "errors": [
    {
      "message": "Validation failed: Contact can't be blank"
    }
  ]
}
```

Or for authentication errors:
```json
{
  "error": "invalid_token",
  "error_description": "The access token is invalid"
}
```

### Common FreeAgent Errors

| Status | Meaning | Action |
|--------|---------|--------|
| 400 | Bad Request | Check request format/validation |
| 401 | Unauthorized | Refresh OAuth token |
| 403 | Forbidden | Check permissions/access level |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 429 | Rate Limited | Backoff and retry |
| 500 | Server Error | Retry with backoff |

### Our Error Mapping

```
FreeAgent Error -> Our Exception

400/422  -> ValidationError (data issue)
401      -> AuthenticationError (token expired)
403      -> AuthenticationError (insufficient permissions)
404      -> NotFoundError (resource missing)
429      -> RateLimitError (wait and retry)
500+     -> APIError (server problem)
```

---

## FreeAgent-Specific Quirks

### 1. URL-Based IDs

FreeAgent uses URLs as resource identifiers, not simple IDs:
```
"contact": "https://api.freeagent.com/v2/contacts/12345"
```

**Handling:** Extract the numeric ID from the URL:
```python
def extract_id(url: str) -> str:
    return url.rstrip('/').split('/')[-1]
```

### 2. No Explicit Contact Types

FreeAgent doesn't have CUSTOMER vs SUPPLIER types. Contacts can be both.

**Handling:**
- Use `view=clients` filter to get customers
- Use `view=suppliers` filter to get suppliers
- Or infer from transaction usage (appears in invoices vs bills)

### 3. Categories Instead of Chart of Accounts

FreeAgent uses "Categories" with nominal codes instead of traditional accounts.

**Handling:** Map nominal code ranges to account types:
```python
def map_category_type(nominal_code: str) -> AccountType:
    code = int(nominal_code)
    if 1 <= code <= 49:
        return AccountType.INCOME
    elif 96 <= code <= 199:
        return AccountType.EXPENSE  # Cost of Sales
    elif 200 <= code <= 399:
        return AccountType.EXPENSE  # Admin
    elif 671 <= code <= 720:
        return AccountType.ASSET
    elif 731 <= code <= 780:
        return AccountType.LIABILITY
    elif 921 <= code <= 960:
        return AccountType.EQUITY
    else:
        return AccountType.EXPENSE  # Default
```

### 4. Date Formats

FreeAgent uses simple date format for date fields:
```
"dated_on": "2026-01-15"
```

And ISO 8601 for timestamps:
```
"created_at": "2026-01-15T10:30:00Z"
```

**Handling:** Parse dates appropriately based on field type.

### 5. Pagination via Link Headers

FreeAgent provides pagination info in HTTP headers:
```
Link: <https://api.freeagent.com/v2/invoices?page=2>; rel="next",
      <https://api.freeagent.com/v2/invoices?page=5>; rel="last"
X-Total-Count: 125
```

**Handling:** Parse Link header or use `page` parameter manually.

### 6. Nested Items Parameter

To include line items in list responses, add:
```
?nested_invoice_items=true
?nested_bill_items=true
?nested_credit_note_items=true
```

Without this, you'd need to fetch each item individually.

### 7. HTTP Basic Auth for Token Requests

Token endpoint requires Basic Auth, not just POST body:
```python
import base64

credentials = base64.b64encode(
    f"{client_id}:{client_secret}".encode()
).decode()

headers = {
    "Authorization": f"Basic {credentials}",
    "Content-Type": "application/x-www-form-urlencoded"
}
```

### 8. User-Agent Required

All API requests must include a User-Agent header:
```
User-Agent: MyAccountingApp/1.0
```

### 9. Soft Deletes Not Visible

Unlike Xero, deleted resources in FreeAgent are not returned at all (no "archived" status to filter).

### 10. Currency on Company, Not Transactions

Most transactions inherit currency from the company. Multi-currency is supported but the `currency` field defaults to company currency.

---

## Testing with Sandbox

### Sandbox Environment

FreeAgent provides a full sandbox environment at:
```
https://api.sandbox.freeagent.com/v2
```

### Getting Sandbox Access

**For Accountancy Practice API:**
1. Email integrationsrequests@freeagent.com requesting:
   - Temporary FreeAgent Practice Dashboard account
   - OAuth Playground access
2. Wait for credentials (typically a few business days)
3. Sign into Practice Dashboard
4. Create test client company
5. Create App with "Enable Accountancy Practice API" checked

**Status:** Pending - email sent to integrations team

### Sandbox Credentials

```
# TBC - awaiting sandbox access
FREEAGENT_SANDBOX_CLIENT_ID=<to be provided>
FREEAGENT_SANDBOX_CLIENT_SECRET=<to be provided>
FREEAGENT_SANDBOX_REDIRECT_URI=http://localhost:8000/auth/freeagent/callback
```

### Testing with Google OAuth Playground

FreeAgent supports testing via Google OAuth 2.0 Playground:
1. Go to https://developers.google.com/oauthplayground/
2. Configure with FreeAgent endpoints
3. Authorize and get tokens
4. Test API calls directly

### Safe Testing

```python
# What you can do (safe):
- GET invoices, bills, credit_notes
- GET contacts
- GET categories
- GET bank_accounts
- GET company info

# What to be careful with:
- POST/PUT (creates/modifies data)
- DELETE (removes records)
```

---

## UK-Specific Features

### Making Tax Digital (MTD)

FreeAgent is HMRC-recognised MTD-compatible software:
- VAT returns can be filed directly to HMRC
- Digital record-keeping requirements met
- API includes VAT return endpoints

### VAT Handling

FreeAgent tracks VAT with:
- `ec_status`: UK/Non-EC, EC Goods, EC Services, Reverse Charge
- `auto_sales_tax_rate`: Standard Rate, Zero Rate, Reduced Rate, Exempt, Outside Scope
- `sales_tax_registration_number`: VAT number on contacts

### CIS (Construction Industry Scheme)

FreeAgent supports CIS for construction businesses:
- CIS rate tracking on bills
- CIS deduction calculations
- Subcontractor management

---

## Ready for Implementation

This guide covers everything needed to build `FreeAgentClient`.

### Next Steps

1. **Receive sandbox access** from FreeAgent integrations team
2. **Read FREEAGENT_IMPLEMENTATION_BLUEPRINT.md** - Step-by-step code plan
3. **Start implementing** - Create `backend/accounting/freeagent/` with client.py, auth.py, mapper.py

### Key Takeaways

- OAuth 2.0 with HTTP Basic Auth for token requests
- RESTful endpoints for invoices, bills, contacts, categories
- Rate limiting: 120/minute, 3600/hour
- URL-based resource identifiers (extract IDs)
- Categories with nominal codes instead of chart of accounts
- Pagination via Link headers and X-Total-Count
- User-Agent header required
- Sandbox available for testing
- UK-focused: MTD, VAT, CIS support

---

**Status:** Ready for implementation (pending sandbox credentials)
**Next Doc:** [FREEAGENT_IMPLEMENTATION_BLUEPRINT.md](FREEAGENT_IMPLEMENTATION_BLUEPRINT.md)

---
