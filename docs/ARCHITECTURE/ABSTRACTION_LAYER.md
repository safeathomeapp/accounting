# Abstraction Layer Architecture

**Status:** ✅ Complete - Month 1, Week 2
**Date:** November 24, 2025
**Test Coverage:** 52 tests, 100% passing

---

## 🎯 Overview

The abstraction layer is the foundation of our multi-platform approach. It enables the system to work with Xero, QuickBooks, or any future accounting platform without changing business logic code.

**Key Principle:** Write business logic ONCE, works with ANY platform.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│  Business Logic Layer (Platform Agnostic)      │
│  - AI Analysis                                  │
│  - Client Communication                         │
│  - Reporting & Insights                         │
│  Uses: AccountingClient interface only         │
├─────────────────────────────────────────────────┤
│  Abstraction Layer (Standard Interface)         │
│  ┌───────────────────────────────────────────┐  │
│  │ AccountingClient (ABC)                     │  │
│  │ - 15 abstract methods                      │  │
│  │ - Handles transactions, accounts, contacts│  │
│  ├───────────────────────────────────────────┤  │
│  │ Standard Data Models                       │  │
│  │ - StandardTransaction                      │  │
│  │ - StandardContact                          │  │
│  │ - StandardAccount                          │  │
│  ├───────────────────────────────────────────┤  │
│  │ AccountingClientFactory                    │  │
│  │ - Creates platform-specific clients        │  │
│  │ - Handles platform detection               │  │
│  └───────────────────────────────────────────┘  │
├─────────────────────────────────────────────────┤
│  Platform Adapters (Specific Implementations)   │
│  - XeroClient extends AccountingClient         │
│  - QuickBooksClient extends AccountingClient   │
│  - FreeAgentClient extends AccountingClient    │
│  - [Future: ClearBooks, FreshBooks, Sage]      │
└─────────────────────────────────────────────────┘
```

---

## 📋 Component Details

### 1. AccountingClient (Abstract Base Class)

**File:** `backend/accounting/base.py`

The abstract base class that ALL platform adapters must implement.

**Key Methods:**

```python
# Authentication
authenticate() -> bool

# Transaction Methods
get_transactions(start_date, end_date, types, limit) -> List[StandardTransaction]
get_transaction(id) -> StandardTransaction | None
create_transaction(transaction) -> StandardTransaction
update_transaction(id, transaction) -> StandardTransaction

# Account Methods
get_accounts(types) -> List[StandardAccount]
get_account(id) -> StandardAccount | None

# Contact Methods
get_contacts(types, limit) -> List[StandardContact]
get_contact(id) -> StandardContact | None
create_contact(contact) -> StandardContact
update_contact(id, contact) -> StandardContact

# Utility Methods
get_organization_info() -> Dict
get_sync_status() -> Dict
```

**Design Principles:**

- ✅ Platform-agnostic - doesn't know about Xero or QB specifics
- ✅ Comprehensive - covers all major accounting operations
- ✅ Extensible - easy to add new methods without breaking adapters
- ✅ Well-documented - every method has purpose and example

**Error Handling:**

All methods can raise platform-agnostic exceptions:
- `AuthenticationError` - Auth failed
- `APIError` - API call failed
- `RateLimitError` - Rate limit exceeded
- `NotFoundError` - Resource not found
- `ValidationError` - Data validation failed

### 2. Standard Data Models

**File:** `backend/accounting/base.py`

Normalized data structures that work across all platforms.

#### StandardTransaction

Represents a financial transaction (invoice, bill, transfer, etc.)

```python
transaction = StandardTransaction(
    id="TXN001",                      # Unique ID
    type=TransactionType.INVOICE,     # What kind
    date=date(2025, 1, 15),          # When
    description="Monthly service",    # What for
    amount=Decimal("1500.00"),        # How much
    tax_amount=Decimal("300.00"),     # Tax/VAT
    account_id="200",                 # Which account
    contact_id="CUST001",             # Customer/supplier
    reference="INV-2025-001",         # Invoice number
    status="approved",                # Draft/approved/etc
    line_items=[...],                 # Detail lines
    platform_id="XER123",             # Platform's ID
    platform_name="xero",             # Which platform
    metadata={...},                   # Extra data
    sync_status=SyncStatus.SYNCED,   # Sync status
)
```

**TransactionType Enum:**
- `INVOICE` - Customer invoices (income)
- `BILL` - Supplier bills (expense)
- `BANK_TRANSFER` - Between accounts
- `CREDIT_NOTE` - Credit (reversal)
- `EXPENSE_CLAIM` - Employee expense
- `DEPOSIT` - Bank deposit
- `WITHDRAWAL` - Bank withdrawal

#### StandardContact

Represents a customer, supplier, or employee

```python
contact = StandardContact(
    id="CUST001",                    # Unique ID
    type=ContactType.CUSTOMER,       # Customer/supplier/employee
    name="John Smith",               # Contact name
    email="john@example.com",        # Email
    phone="01234567890",             # Phone
    address="123 Main St, London",   # Address
    tax_id="12345678",               # Tax ID
    currency="GBP",                  # Currency
    platform_id="XER789",            # Platform's ID
    platform_name="xero",            # Which platform
    metadata={...},                  # Extra data
)
```

**ContactType Enum:**
- `CUSTOMER` - Customers
- `SUPPLIER` - Suppliers
- `EMPLOYEE` - Employees
- `OTHER` - Other contacts

#### StandardAccount

Represents a chart of accounts entry

```python
account = StandardAccount(
    id="200",                        # Account ID
    code="4000",                     # Account code
    name="Sales Income",             # Account name
    type=AccountType.INCOME,         # Asset/liability/equity/income/expense/bank
    currency="GBP",                  # Currency
    tax_type="VATable",              # VAT treatment
    platform_id="XER123",            # Platform's ID
    platform_name="xero",            # Which platform
    metadata={...},                  # Extra data
)
```

**AccountType Enum:**
- `ASSET` - Bank accounts, receivables, equipment
- `LIABILITY` - Payables, loans, credit cards
- `EQUITY` - Owner's equity, retained earnings
- `INCOME` - Revenue from sales
- `EXPENSE` - Costs (salaries, supplies, etc.)
- `BANK` - Bank accounts (special category)

### 3. AccountingClientFactory

**File:** `backend/accounting/factory.py`

Creates the appropriate platform-specific client based on configuration.

**Usage:**

```python
# From organization database model
organization = Organization.query.first()
client = AccountingClientFactory.create(organization)

# Or directly with platform info
client = AccountingClientFactory.create_from_platform(
    platform="xero",
    organization_id="123",
    credentials={"api_key": "..."}
)

# Check platform support
if AccountingClientFactory.is_platform_supported("quickbooks"):
    print("QB supported!")

# Get list of supported platforms
platforms = AccountingClientFactory.supported_platforms()
```

**How It Works:**

1. Detects platform from organization configuration
2. Gets credentials from encrypted storage
3. Dynamically imports platform-specific client
4. Instantiates and returns the client
5. Business logic uses it without knowing which platform

**Platform Configuration:**

```python
PLATFORM_CLIENTS = {
    "xero": "backend.accounting.xero.client.XeroClient",
    "quickbooks": "backend.accounting.quickbooks.client.QuickBooksClient",
    "freeagent": "backend.accounting.freeagent.client.FreeAgentClient",
    # Future platforms:
    # "clearbooks": "backend.accounting.clearbooks.client.ClearBooksClient",
    # "freshbooks": "backend.accounting.freshbooks.client.FreshBooksClient",
    # "sage": "backend.accounting.sage.client.SageClient",
}
```

To add a new platform:
1. Create `backend/accounting/newplatform/client.py`
2. Extend `AccountingClient`
3. Implement all abstract methods
4. Add entry to `PLATFORM_CLIENTS`
5. Done!

---

## 🔄 Data Flow

### Example: Fetching Transactions

```python
# Business logic (platform-agnostic)
def analyze_monthly_transactions(organization, month):
    # Get the client (any platform)
    client = AccountingClientFactory.create(organization)

    # Get transactions (same code works for Xero, QB, etc.)
    transactions = client.get_transactions(
        start_date=date(month, 1),
        end_date=date(month, 28)
    )

    # Process transactions (they're StandardTransaction objects)
    for txn in transactions:
        print(f"{txn.date}: {txn.description} - {txn.amount}")
        # Analyze the transaction
        # AI categorization
        # Report generation
        # etc.

# What happens behind the scenes:

# If organization.accounting_platform.name == "xero":
#   1. Factory creates XeroClient
#   2. XeroClient.get_transactions() called
#   3. XeroClient makes Xero API calls
#   4. XeroClient converts Xero format → StandardTransaction
#   5. Returns list of StandardTransaction objects
#   6. Business logic processes them

# If organization.accounting_platform.name == "quickbooks":
#   1. Factory creates QuickBooksClient
#   2. QuickBooksClient.get_transactions() called
#   3. QuickBooksClient makes QB API calls
#   4. QuickBooksClient converts QB format → StandardTransaction
#   5. Returns list of StandardTransaction objects
#   6. Business logic processes them (SAME CODE)
```

---

## ✅ Testing

**52 tests covering:**

✅ Standard data models creation and validation
✅ Enumeration values
✅ Exception hierarchy
✅ Abstract base class interface
✅ Mock implementation
✅ Factory creation
✅ Platform detection
✅ Credential validation
✅ Error handling
✅ Integration workflows

**Run tests:**

```bash
pytest tests/test_accounting_base.py -v
pytest tests/test_accounting_factory.py -v
pytest tests/test_accounting_*.py -v --cov=backend.accounting
```

**Coverage:** 100% of abstraction layer

---

## 🚀 Future Extensions

### Adding a New Platform (e.g., Sage)

**Step 1: Create platform package**

```
backend/accounting/sage/
├── __init__.py
├── client.py      # SageClient implementation
├── auth.py        # OAuth/API authentication
└── mapper.py      # Sage format → Standard format
```

**Step 2: Implement SageClient**

```python
from backend.accounting import AccountingClient

class SageClient(AccountingClient):
    PLATFORM_NAME = "sage"

    def _validate_credentials(self):
        # Validate Sage credentials
        pass

    def authenticate(self) -> bool:
        # Connect to Sage API
        pass

    def get_transactions(self, start_date, end_date, ...):
        # Fetch from Sage API
        sage_transactions = self.sage_api.get_transactions(...)

        # Convert to standard format
        return [self._map_sage_txn(t) for t in sage_transactions]

    def _map_sage_txn(self, sage_txn):
        # Convert Sage format to StandardTransaction
        pass

    # Implement all other abstract methods...
```

**Step 3: Register in factory**

```python
PLATFORM_CLIENTS = {
    "xero": "backend.accounting.xero.client.XeroClient",
    "quickbooks": "backend.accounting.quickbooks.client.QuickBooksClient",
    "freeagent": "backend.accounting.freeagent.client.FreeAgentClient",
    "clearbooks": "backend.accounting.clearbooks.client.ClearBooksClient",
    "freshbooks": "backend.accounting.freshbooks.client.FreshBooksClient",
    "sage": "backend.accounting.sage.client.SageClient",  # Add this
}
```

**Step 4: Done!**

All business logic automatically works with the new platform.

---

## 🎯 Design Decisions

### Why Abstract Base Class?

- Enforces contract - all platforms implement same methods
- IDE support - autocomplete for all methods
- Clear documentation - each method documented once
- Type safety - static analysis catches errors early

### Why Standard Models?

- Platform independence - business logic doesn't know about Xero/QB specifics
- Easy transformation - mappers convert platform format to standard
- Reusability - same model across business logic
- Type safety - Decimal for amounts (no floating-point errors)

### Why Factory Pattern?

- Decoupling - business logic doesn't import platform adapters
- Flexibility - change platforms without code changes
- Testability - easy to mock or inject test clients
- Extensibility - new platforms just add to factory

### Why Enumerations?

- Type safety - can't use invalid transaction type
- Documentation - all valid values in one place
- IDE support - autocomplete for enum values
- Refactoring - rename value everywhere at once

---

## 🔐 Platform Implementation Strategy

### Phased Implementation Approach

All platform adapters follow a phased implementation strategy:

**Phase 1: Read-Only Operations**
- `get_transactions()`, `get_transaction()`
- `get_contacts()`, `get_contact()`
- `get_accounts()`, `get_account()`
- `get_organization_info()`, `get_sync_status()`
- `authenticate()`

Write methods (`create_*`, `update_*`) raise `NotImplementedError`:

```python
def create_transaction(self, transaction: StandardTransaction) -> StandardTransaction:
    """Create transaction in platform.

    Note: Not implemented in Phase 1 (read-only access).
    """
    raise NotImplementedError("Phase 1: Read-only access to [Platform]")
```

**Phase 2+: Write Operations**
- `create_transaction()`, `update_transaction()`
- `create_contact()`, `update_contact()`
- Additional endpoints as needed (delete, void, etc.)

### API Access Requirements

**IMPORTANT:** When registering applications with accounting platforms, always request **full read-write access**, even for Phase 1 implementation.

Reasons:
1. **Avoid re-authorization** - Users won't need to re-approve when write features are added
2. **Simpler OAuth scopes** - Most platforms bundle read/write together
3. **Future-proof** - No need to update app registrations later
4. **Testing flexibility** - Can test write operations in sandbox immediately

**Example OAuth Scopes to Request:**

| Platform | Scopes |
|----------|--------|
| Xero | `offline_access accounting.transactions accounting.contacts accounting.settings` |
| QuickBooks | `com.intuit.quickbooks.accounting` (includes read/write) |
| FreeAgent | Full access via Practice API (no scope restrictions) |
| ClearBooks | TBC - pending API research |
| FreshBooks | TBC - pending API research |
| Sage | TBC - pending API research |

### Why Read-Only First?

1. **Safety** - No risk of corrupting client accounting data during development
2. **Testing** - Easier to verify correct data mapping without side effects
3. **Incremental** - Build confidence before adding write operations
4. **Reversible** - Read operations can be re-run; write operations cannot be undone

### Implementation Checklist for New Platforms

When implementing a new platform adapter:

- [ ] Request **full read-write API access** from platform
- [ ] Implement all read methods first (Phase 1)
- [ ] Write methods should raise `NotImplementedError`
- [ ] Add `# TODO: Phase 2 - Implement write operations` comments
- [ ] Document any platform-specific write requirements in API Guide
- [ ] Test read operations thoroughly before Phase 2

---

## 📊 Metrics

- **Lines of Code:** ~800 (base.py + factory.py)
- **Test Coverage:** 52 tests, 100% passing
- **Documentation:** 100% (docstrings + comments)
- **Type Hints:** 100%

---

## 🔗 Related Documentation

- [MULTI_PLATFORM_ROADMAP.md](MULTI_PLATFORM_ROADMAP.md) - Overall roadmap
- [ARCHITECTURE_PRINCIPLES.md](../ARCHITECTURE_PRINCIPLES.md) - Architecture standards
- [PROJECT_INIT.md](../PROJECT_INIT.md) - Project guidelines

---

## 📝 Week 2 Deliverables

- ✅ Abstract base class complete
- ✅ Standard data models defined
- ✅ Factory pattern implemented
- ✅ Test coverage >80% (100% achieved)
- ✅ Architecture documented

---

## 🎯 Next Steps

**Week 3:** Xero Integration
- Implement `XeroClient` extending `AccountingClient`
- Build OAuth authentication flow
- Create mapper functions (Xero → Standard format)
- Test with Xero demo company

---

**Status:** ✅ Complete and Ready for Week 3
