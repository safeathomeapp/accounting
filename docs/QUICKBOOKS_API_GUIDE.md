# QuickBooks Online API Integration Guide

**Status**: Week 5 Implementation
**Target**: Full read-write support (Phase 1: Read-only)
**API Version**: QuickBooks Online REST API v2

## Overview

QuickBooks Online (QBO) is a cloud-based accounting system with a RESTful API. This guide explains the API structure, authentication, and key endpoints for integration.

## Authentication: OAuth 2.0

### Flow

1. **Authorization Request** → User approves app access
2. **Authorization Code** → Redirect back with code
3. **Token Exchange** → Code → Access Token + Refresh Token
4. **Realm ID** → Company ID (required for all API calls)
5. **API Calls** → Use access token + realm ID

### Endpoints

```
Authorization: https://appcenter.intuit.com/connect/oauth2
Token Exchange: https://quickbooks.api.intuit.com/v2/oauth2/tokens/bearer
Revoke Token: https://developer.api.intuit.com/v2/oauth2/tokens/revoke
```

### Scopes

```
com.intuit.quickbooks.accounting – Read/write accounting data
```

### Access Token Lifetime

- **Duration**: 1 hour
- **Refresh Token**: Valid for 100 days
- **Refresh Process**: Must be done before expiry

## API Base URL

```
https://quickbooks.api.intuit.com/v2/company/{realmId}
```

## Key Entities

### Transactions

**Invoices** (Customer invoices - income)
```
GET    /query?query=select * from Invoice
GET    /invoice/{id}
POST   /invoice
PUT    /invoice
DELETE /invoice
```

**Bills** (Supplier bills - expense)
```
GET    /query?query=select * from Bill
GET    /bill/{id}
POST   /bill
PUT    /bill
DELETE /bill
```

**PurchaseOrders** (Purchase orders)
```
GET    /query?query=select * from PurchaseOrder
GET    /purchaseorder/{id}
POST   /purchaseorder
```

**CreditMemos** (Customer credits)
```
GET    /creditMemo/{id}
POST   /creditMemo
```

**Payments** (Cash receipts)
```
GET    /payment/{id}
POST   /payment
```

### Contacts

**Customers** (Customer contacts)
```
GET    /query?query=select * from Customer
GET    /customer/{id}
POST   /customer
PUT    /customer
```

**Vendors** (Supplier contacts)
```
GET    /query?query=select * from Vendor
GET    /vendor/{id}
POST   /vendor
PUT    /vendor
```

### Chart of Accounts

**Account** (General ledger accounts)
```
GET    /query?query=select * from Account
GET    /account/{id}
POST   /account
PUT    /account
```

### Other

**Company** (Organization info)
```
GET    /companyinfo/{realmId}
```

## Query Language

QuickBooks uses its own SQL-like query language:

```sql
-- Select all invoices
SELECT * FROM Invoice

-- Select invoices for date range
SELECT * FROM Invoice WHERE TxnDate >= '2025-01-01' AND TxnDate <= '2025-01-31'

-- Select with limit
SELECT * FROM Invoice MAXRESULTS 100

-- Select by status
SELECT * FROM Invoice WHERE DocStatus = 'Posted'
```

## Response Format

### Successful Transaction Response

```json
{
  "Invoice": {
    "Id": "123",
    "SyncToken": "0",
    "MetaData": {
      "CreateTime": "2025-01-15T10:00:00Z",
      "UpdateTime": "2025-01-15T10:00:00Z"
    },
    "DocNumber": "INV-001",
    "TxnDate": "2025-01-15",
    "DueDate": "2025-02-15",
    "TxnTaxDetail": {
      "TotalTax": "200.00"
    },
    "TotalAmt": "1200.00",
    "Line": [
      {
        "DetailType": "SalesItemLineDetail",
        "SalesItemLineDetail": {
          "ItemRef": {
            "value": "item-id",
            "name": "Item Name"
          },
          "Qty": 1,
          "UnitPrice": "1000.00",
          "Amount": "1000.00"
        }
      }
    ],
    "CustomerRef": {
      "value": "customer-id",
      "name": "Customer Name"
    }
  }
}
```

### Error Response

```json
{
  "Fault": {
    "Error": [
      {
        "Message": "Resource not found",
        "Detail": "Entity with id [123] not found",
        "Code": "404"
      }
    ],
    "type": "AUTHENTICATION"
  }
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request (validation error) |
| 401 | Unauthorized (token expired) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not found |
| 429 | Rate limit exceeded |
| 500 | Server error |

## Rate Limiting

- **Limits**: 10,000 requests per hour
- **Window**: Hourly rolling
- **Headers**: Not provided; track locally

## Pagination

Unlike Xero's page parameter, QuickBooks uses MAXRESULTS:

```sql
SELECT * FROM Invoice MAXRESULTS 100
```

For large result sets, use pagination in the client.

## Required Fields for Mutations

### Creating Invoice

```
TxnDate: Date
Line: Array (at least 1)
CustomerRef: Reference to customer
```

### Creating Bill

```
TxnDate: Date
Line: Array (at least 1)
VendorRef: Reference to vendor
```

### Creating Customer

```
DisplayName: String (unique)
GivenName or FamilyName: Name fields
```

## Data Types

- **String**: Text
- **Number**: Decimal (use strings in JSON)
- **Boolean**: true/false
- **Date**: YYYY-MM-DD format
- **Decimal**: Sent as string ("100.00")

## Field Mapping Notes

### Transaction Types

| QBO | Standard |
|-----|----------|
| Invoice | INVOICE |
| Bill | BILL |
| CreditMemo | CREDIT_NOTE |
| Payment (received) | DEPOSIT |

### Contact Types

| QBO | Standard |
|-----|----------|
| Customer | CUSTOMER |
| Vendor | SUPPLIER |
| Employee | EMPLOYEE |

### Account Types

| QBO | Standard |
|-----|----------|
| Asset | ASSET |
| Bank | BANK |
| Credit Card | LIABILITY |
| Equity | EQUITY |
| Expense | EXPENSE |
| Other Current Liability | LIABILITY |
| Other Current Asset | ASSET |
| Fixed Asset | ASSET |
| Income | INCOME |
| Other Income | INCOME |

## Common Patterns

### Get recent transactions

```sql
SELECT * FROM Invoice
WHERE TxnDate >= '2025-01-01'
ORDER BY TxnDate DESC
```

### Filter by customer

```sql
SELECT * FROM Invoice
WHERE CustomerRef = 'customer-id'
```

### Get accounts

```sql
SELECT * FROM Account WHERE Active = true
```

## Error Handling

### InvalidToken (401)

Token expired or revoked. Refresh token and retry.

### AuthenticationFault

Invalid credentials or token not recognized.

### InvalidQueryPair

Query syntax error. Check SQL-like query format.

### ValidationFault

Missing required fields or invalid values.

## Testing Checklist

- [ ] Authenticate with QB OAuth
- [ ] Fetch invoices for date range
- [ ] Fetch bills for date range
- [ ] Fetch customers
- [ ] Fetch vendors
- [ ] Fetch accounts
- [ ] Get company info
- [ ] Handle token refresh
- [ ] Handle rate limiting
- [ ] Handle error responses

## Resources

- Official QB API Docs: https://developer.intuit.com/app/developer/qbo/docs/api
- OAuth Guide: https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth-2.0
- Query Language: https://developer.intuit.com/app/developer/qbo/docs/develop/querying-data
