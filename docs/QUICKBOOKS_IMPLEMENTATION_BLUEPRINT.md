# QuickBooks Client Implementation Blueprint

**Week**: 5
**Status**: Implementation Guide
**Target Completion**: Same week as documentation

## Implementation Checklist

### Step 1: Create Package Structure
- [ ] `mkdir backend/accounting/quickbooks/`
- [ ] Create `__init__.py` (13 lines - just export QuickBooksClient)
- [ ] Create `auth.py` (OAuth 2.0 handler)
- [ ] Create `mapper.py` (QB format → Standard format)
- [ ] Create `client.py` (Main adapter)

### Step 2: Implement auth.py (OAuth 2.0)

**Key differences from Xero**:
- QB doesn't use PKCE (just standard OAuth 2.0)
- Realm ID (company ID) is returned in token response
- Tokens must be stored with realm ID

**Methods to implement**:
```python
class QuickBooksAuth:
    def get_authorization_url(state) -> Tuple[str, str]
    def exchange_code_for_token(code, state) -> Dict
    def get_access_token() -> Optional[str]
    def refresh_access_token() -> Dict
    def get_realm_id() -> Optional[str]
    def is_authenticated() -> bool
    def revoke_token() -> bool
```

**Size**: ~120 lines

### Step 3: Implement mapper.py (Data Transformation)

**Key differences from Xero**:
- QB response structure is different (nested objects)
- QB has more transaction types (CreditMemo, Payment, PurchaseOrder)
- QB status values are different
- QB contact model different (customers vs vendors)

**Methods to implement**:
```python
class QuickBooksMapper:
    def map_invoice_to_transaction(invoice) -> StandardTransaction
    def map_bill_to_transaction(bill) -> StandardTransaction
    def map_credit_memo_to_transaction(memo) -> StandardTransaction
    def map_payment_to_transaction(payment) -> StandardTransaction
    def map_customer_to_standard(customer) -> StandardContact
    def map_vendor_to_standard(vendor) -> StandardContact
    def map_account_to_standard(account) -> StandardAccount
    def _parse_qbo_date(date_string) -> date
    def _map_invoice_status(qbo_status) -> str
    def _map_account_type(qbo_type) -> AccountType
```

**Size**: ~100 lines

### Step 4: Implement client.py (Main Adapter)

**Structure** (follow XeroClient as template):
```python
class QuickBooksClient(AccountingClient):
    PLATFORM_NAME = "quickbooks"
    QBO_BASE_URL = "https://quickbooks.api.intuit.com/v2/company"

    # 15 abstract methods to implement:
    def authenticate() -> bool
    def get_transactions(start_date, end_date, types, limit) -> List
    def get_transaction(id) -> Optional
    def create_transaction(txn) -> StandardTransaction  # NotImplementedError
    def update_transaction(id, txn) -> StandardTransaction  # NotImplementedError
    def get_accounts(types) -> List
    def get_account(id) -> Optional
    def get_contacts(types, limit) -> List
    def get_contact(id) -> Optional
    def create_contact(contact) -> StandardContact  # NotImplementedError
    def update_contact(id, contact) -> StandardContact  # NotImplementedError
    def get_organization_info() -> Dict
    def get_sync_status() -> Dict
    def _validate_credentials() -> None
    # Helpers:
    def _get_invoices(start, end, limit) -> List
    def _get_bills(start, end, limit) -> List
    def _make_request(method, url, query, data) -> Dict
```

**Size**: ~280 lines

### Step 5: Create Tests (test_accounting_quickbooks.py)

**Test structure** (follow test_accounting_xero.py):

```python
class TestQuickBooksMapper:
    # 10 tests for data transformation

class TestQuickBooksClientAuthentication:
    # 6 tests for auth and init

class TestQuickBooksClientTransactions:
    # 8 tests for get/create/update transactions

class TestQuickBooksClientContactsAndAccounts:
    # 8 tests for contacts and accounts

class TestQuickBooksClientErrorHandling:
    # 5 tests for error scenarios

class TestQuickBooksClientOrganization:
    # 2 tests for org info

class TestQuickBooksClientIntegration:
    # 4 tests for interface compliance
```

**Size**: ~550 lines
**Target**: 35+ tests, 100% passing

## Key Implementation Details

### OAuth 2.0 with Realm ID

```python
# QB returns realm ID in token response
token_response = {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "x_refresh_token_expires_in": 8726400,
    "realm_id": "1234567890"  # Company ID!
}
```

### Query Language

QB uses SQL-like queries instead of REST endpoints for reads:

```python
# Get invoices for date range
query = """
    SELECT * FROM Invoice
    WHERE TxnDate >= '2025-01-01'
    AND TxnDate <= '2025-01-31'
    MAXRESULTS 100
"""

response = requests.get(
    f"{base_url}/{realm_id}/query",
    params={"query": query},
    headers={"Authorization": f"Bearer {token}"}
)
```

### Response Structure Differences

**Xero**:
```json
{
  "Invoices": [{ "InvoiceID": "123", ... }]
}
```

**QB**:
```json
{
  "QueryResponse": {
    "Invoice": [{ "Id": "123", ... }],
    "totalCount": 1,
    "startPosition": 1
  }
}
```

### Status Mapping

**QB Invoice Statuses**:
- Draft → draft
- Posted → approved/submitted
- Paid → paid
- Voided → voided

**QB Bill Statuses**:
- Draft → draft
- Voided → voided
- Processed → approved

## Common Pitfalls

### 1. Realm ID Required for All Calls
Every API call needs the realm ID in the URL. Store it after auth.

### 2. Token Refresh
QB tokens expire hourly. Auto-refresh before expiry.

### 3. Decimal Handling
QB sends monetary amounts as decimals. Use Decimal type.

### 4. Query Escaping
QB query language needs proper escaping for special characters.

### 5. SyncToken for Updates
When updating entities, you need the current SyncToken.

## Testing Strategy

### Unit Tests
- Mock QB API responses
- Test each mapper function
- Test error handling

### Integration Tests
- Verify factory creates QuickBooksClient
- Verify interface compliance
- Test with mock data

### Manual Testing (Later)
- Create QB sandbox account
- Test real OAuth flow
- Test with real company data

## File Checklist

| File | Lines | Status |
|------|-------|--------|
| `__init__.py` | 13 | To Create |
| `auth.py` | ~120 | To Create |
| `mapper.py` | ~100 | To Create |
| `client.py` | ~280 | To Create |
| `test_accounting_quickbooks.py` | ~550 | To Create |

**Total New Code**: ~1,063 lines

## Factory Integration

One line added to `backend/accounting/factory.py`:

```python
PLATFORM_CLIENTS = {
    "xero": "backend.accounting.xero.client.XeroClient",
    "quickbooks": "backend.accounting.quickbooks.client.QuickBooksClient",
    "mock": "backend.accounting.mock.client.MockClient",
}
```

Then it works automatically!

```python
# Works exactly like Xero
client = AccountingClientFactory.create_from_platform(
    "quickbooks",
    "org-123",
    credentials
)
```

## Success Criteria

- [ ] All 15 abstract methods implemented
- [ ] QB OAuth flow working
- [ ] Can fetch transactions (invoices, bills)
- [ ] Can fetch contacts (customers, vendors)
- [ ] Can fetch accounts
- [ ] All 35+ tests passing
- [ ] Factory integration verified
- [ ] Error handling comprehensive
- [ ] Code matches Xero quality

## Development Notes

### Why QB is Different from Xero
- Uses SQL-like query language (not REST endpoints)
- Requires realm ID for every call
- Different response structure
- Different status values
- No PKCE in OAuth

### What Stays the Same
- Abstract interface (AccountingClient)
- Standard data models (StandardTransaction, etc.)
- Factory pattern integration
- Test structure and patterns
- Error handling approach

## Next Week

Once QB is done:
- Total platforms supported: 3 (Xero, QB, Mock)
- All business logic stays platform-agnostic
- Ready for Month 2 (Sync, Reporting, Analytics)
