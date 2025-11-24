# Sync Engine Implementation Roadmap

**Week**: Month 2, Week 1-2
**Status**: Planning
**Target Completion**: 2 weeks
**Test Target**: 40+ tests, 100% passing

---

## Overview

The Sync Engine is the core component that pulls data from accounting platforms (Xero, QuickBooks) and synchronizes it into the local PostgreSQL database. It handles:

- **Full syncs**: Pull all data from platform
- **Incremental syncs**: Pull only changed data since last sync
- **Error recovery**: Retry failed records, skip duplicates
- **Audit trail**: Complete sync history for debugging
- **Conflict resolution**: Handle platform vs local data discrepancies

---

## Architecture

### Components

```
sync/
├── __init__.py
├── engine.py           # SyncEngine class (orchestrator)
├── handlers/           # Entity-specific sync logic
│   ├── __init__.py
│   ├── transaction_handler.py
│   ├── account_handler.py
│   └── client_handler.py
├── strategies/         # Sync approach implementations
│   ├── __init__.py
│   ├── full_sync.py    # Pull all data
│   └── incremental_sync.py  # Pull changed data
└── utils/
    ├── __init__.py
    ├── sync_tracker.py  # Track sync progress
    └── error_handler.py # Handle sync errors
```

### Data Flow

```
┌─────────────────────────────────────────────────────────┐
│ SyncEngine (Orchestrator)                              │
│ - get_organization()                                    │
│ - sync_all_platforms() or sync_platform(platform_name) │
│ - determine_sync_type() (full vs incremental)           │
└─────────────────────────────────────────────────────────┘
            │
            ├─→ AccountingClientFactory
            │   Creates XeroClient / QuickBooksClient
            │
            ├─→ AccountSyncHandler
            │   .sync_accounts(client, org, sync_type)
            │
            ├─→ ClientSyncHandler
            │   .sync_contacts(client, org, sync_type)
            │
            └─→ TransactionSyncHandler
                .sync_transactions(client, org, sync_type)

Each Handler:
1. Fetches data from client
2. Maps to StandardModel
3. Checks for existing records (by platform_id)
4. Creates or updates in database
5. Records success/failure in sync_tracker
6. Returns statistics
```

### Key Classes

#### SyncEngine (Main Orchestrator)
```python
class SyncEngine:
    """Orchestrates sync across all platforms and entities."""

    def __init__(self, db: Session):
        self.db = db

    def sync_all_platforms(self, org_id: str) -> SyncResult:
        """Sync all platforms for organization."""

    def sync_platform(self, org_id: str, platform_name: str) -> SyncResult:
        """Sync specific platform for organization."""

    def determine_sync_type(self, platform: AccountingPlatform) -> str:
        """full or incremental based on sync history."""

    def _sync_entities(self, client, org, sync_type) -> SyncResult:
        """Sync accounts, clients, transactions."""
```

#### SyncResult (Data Class)
```python
@dataclass
class SyncResult:
    """Result of a sync operation."""
    status: str  # 'success', 'partial', 'failed'
    accounts: SyncStats
    clients: SyncStats
    transactions: SyncStats
    errors: List[SyncError]
    sync_history_id: UUID
    duration_seconds: float
```

#### Entity Handlers
Each handler (Account, Client, Transaction) follows same pattern:

```python
class AccountSyncHandler:
    """Handles account synchronization."""

    def __init__(self, db: Session):
        self.db = db

    def sync_accounts(
        self,
        client: AccountingClient,
        org_id: UUID,
        sync_type: str  # 'full' or 'incremental'
    ) -> SyncStats:
        """
        1. Get accounts from client
        2. For each account:
           - Check if exists (platform_id)
           - Create or update
        3. Return stats
        """
```

---

## Implementation Steps

### Step 1: Core SyncEngine Infrastructure (4-5 hours)

**Files to create**:
- `backend/sync/__init__.py` - Package init
- `backend/sync/engine.py` - Main SyncEngine class
- `backend/sync/models.py` - SyncResult, SyncStats, SyncError dataclasses
- `backend/sync/exceptions.py` - Custom exceptions

**Key Methods**:
```python
# SyncEngine
- __init__(db: Session)
- sync_all_platforms(org_id: str) → SyncResult
- sync_platform(org_id: str, platform_name: str) → SyncResult
- determine_sync_type(platform: AccountingPlatform) → str
- _create_sync_history() → SyncHistory
- _finalize_sync_history(sync_history: SyncHistory, result: SyncResult)
```

**Test Targets** (8-10 tests):
- `test_engine_initialization`
- `test_sync_all_platforms`
- `test_sync_platform`
- `test_determine_sync_type_full`
- `test_determine_sync_type_incremental`
- `test_create_sync_history`
- `test_sync_result_creation`
- `test_error_handling_during_sync`

---

### Step 2: Entity Handlers (8-10 hours)

**Files to create**:
- `backend/sync/handlers/__init__.py`
- `backend/sync/handlers/account_handler.py`
- `backend/sync/handlers/client_handler.py`
- `backend/sync/handlers/transaction_handler.py`

**Key Pattern for Each Handler**:
```python
class AccountSyncHandler:
    def __init__(self, db: Session):
        self.db = db

    def sync_accounts(
        self,
        client: AccountingClient,
        organization_id: UUID,
        sync_type: str
    ) -> SyncStats:
        """
        Flow:
        1. Call client.get_accounts()
        2. For each account:
           a. Look up existing by (platform_name, platform_id)
           b. If exists: update fields
           c. If new: create record
        3. Return SyncStats
        """
```

**SyncStats Dataclass**:
```python
@dataclass
class SyncStats:
    entity_type: str  # 'account', 'client', 'transaction'
    total_fetched: int
    created: int
    updated: int
    skipped: int  # Unchanged
    failed: int
    errors: List[str]
```

**Implementations**:

1. **AccountSyncHandler**:
   - Map: StandardAccount → Account model
   - Create/update: organization_id + platform_name + platform_id
   - Index by: account_type for filtering

2. **ClientSyncHandler**:
   - Map: StandardContact → Client model
   - Handle: CUSTOMER → contact_type='customer', SUPPLIER → 'supplier'
   - Create/update: organization_id + platform_name + platform_id

3. **TransactionSyncHandler** (Most Complex):
   - Map: StandardTransaction → Transaction model
   - Resolve: contact_id and account_id from their tables
   - Compute: total_amount = amount + tax_amount
   - Handle: Different transaction types (INVOICE, BILL, DEPOSIT, etc.)

**Test Targets** (20-25 tests):
- `test_sync_accounts_full`
- `test_sync_accounts_incremental`
- `test_sync_accounts_update_existing`
- `test_sync_accounts_new_records`
- `test_sync_accounts_error_handling`
- Similar for clients and transactions (5 tests each)

---

### Step 3: Sync Strategies (4-6 hours)

**Files to create**:
- `backend/sync/strategies/__init__.py`
- `backend/sync/strategies/full_sync.py`
- `backend/sync/strategies/incremental_sync.py`

**Full Sync Strategy**:
```python
class FullSyncStrategy:
    """Fetch all data from platform."""

    def sync_accounts(client: AccountingClient) → List[StandardAccount]:
        """Call client.get_accounts() with no filters."""

    def sync_contacts(client: AccountingClient) → List[StandardContact]:
        """Call client.get_contacts() with no filters."""

    def sync_transactions(client: AccountingClient) → List[StandardTransaction]:
        """Get last 2 years of transactions."""
```

**Incremental Sync Strategy**:
```python
class IncrementalSyncStrategy:
    """Fetch only changed data since last sync."""

    def sync_accounts(
        client: AccountingClient,
        since: datetime
    ) → List[StandardAccount]:
        """Only accounts modified since last sync."""

    def sync_contacts(client, since) → List[StandardContact]:
        """Only contacts modified since last sync."""

    def sync_transactions(client, since) → List[StandardTransaction]:
        """Only transactions after last sync date."""
```

**Test Targets** (8-10 tests):
- `test_full_sync_fetches_all_data`
- `test_incremental_sync_filters_by_date`
- `test_incremental_sync_with_no_previous_sync`
- `test_sync_strategy_selection`

---

### Step 4: Utilities & Error Handling (4-5 hours)

**Files to create**:
- `backend/sync/utils/__init__.py`
- `backend/sync/utils/sync_tracker.py` - Track progress and statistics
- `backend/sync/utils/error_handler.py` - Handle and log errors
- `backend/sync/utils/reconciler.py` - Reconcile data between systems

**SyncTracker**:
```python
class SyncTracker:
    """Track sync progress and collect statistics."""

    def __init__(self):
        self.accounts_stats = SyncStats()
        self.clients_stats = SyncStats()
        self.transactions_stats = SyncStats()
        self.errors = []

    def record_account_created()
    def record_account_updated()
    def record_account_error(error)
    def get_summary() → SyncResult
```

**ErrorHandler**:
```python
class SyncErrorHandler:
    """Handle errors during sync."""

    def handle_fetch_error(entity_type, error)
    def handle_parse_error(entity, error)
    def handle_database_error(entity, error)
    def record_error(sync_history, error)
```

**Test Targets** (6-8 tests):
- `test_sync_tracker_statistics`
- `test_error_collection`
- `test_error_logging`

---

### Step 5: API Routes (3-4 hours)

**Files to create**:
- `backend/api/sync_routes.py`

**Endpoints**:
```python
@router.post("/sync/all")
def sync_all_platforms(org_id: str, db: Session) → SyncResult:
    """Sync all platforms for organization."""

@router.post("/sync/platform")
def sync_platform(org_id: str, platform_name: str, db: Session) → SyncResult:
    """Sync specific platform."""

@router.get("/sync/status")
def get_sync_status(org_id: str, db: Session):
    """Get latest sync status and statistics."""

@router.get("/sync/history")
def get_sync_history(org_id: str, limit: int = 10, db: Session):
    """Get sync history for organization."""
```

**Test Targets** (4-6 tests):
- `test_sync_all_endpoint`
- `test_sync_platform_endpoint`
- `test_sync_status_endpoint`
- `test_sync_history_endpoint`

---

## Testing Strategy

### Unit Tests (30+ tests)
- Test each handler independently with mocked clients
- Test error handling and recovery
- Test data mapping and validation

### Integration Tests (10+ tests)
- Test sync flow with real database
- Test sync history tracking
- Test concurrent syncs (if supported)

### Database Tests (5-8 tests)
- Verify records created/updated correctly
- Test unique constraints
- Test foreign key relationships

### End-to-End Tests (3-5 tests)
- Mock accounting platforms
- Run full sync cycle
- Verify all data synced correctly

---

## Database Schema (Already Exists)

### Tables Used by Sync Engine:
- `transactions` - Synced financial transactions
- `accounts` - Synced chart of accounts
- `clients` - Synced customers/suppliers
- `sync_history` - Audit trail of sync operations

### Key Fields for Sync:
```python
# All platform-aware tables have:
- platform_id (str): ID from platform
- platform_name (str): 'xero', 'quickbooks'
- last_synced_at (datetime): When last synced
- platform_updated_at (datetime): When platform updated
- created_at / updated_at: Local timestamps

# Uniqueness:
Index(platform_name, platform_id) - One record per platform per entity
```

---

## Success Criteria

- [ ] SyncEngine orchestrates full and incremental syncs
- [ ] All 3 entity types sync correctly (accounts, clients, transactions)
- [ ] Sync history tracked with complete audit trail
- [ ] Error handling with retry logic
- [ ] 45+ tests, 100% passing
- [ ] Can sync multiple platforms concurrently (Xero + QB)
- [ ] Incremental sync 90% faster than full sync
- [ ] API endpoints for manual sync triggers

---

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Full sync (1000 transactions) | < 30 seconds | Network + DB writes |
| Incremental sync (100 new) | < 5 seconds | Only changed data |
| Single account sync | < 1 second | DB write only |
| Concurrent platform sync | < 30 seconds | Both platforms parallel |

---

## Risk Mitigation

### Duplicate Prevention
- Check (platform_name, platform_id) before insert
- Update if exists, create if new
- Log any unexpected duplicates

### Data Integrity
- Use transactions for all writes
- Validate amounts (NUMERIC precision)
- Check foreign key constraints

### Error Recovery
- Log all errors to sync_history
- Collect errors for batch reporting
- Skip failed records, continue with others
- Allow manual retry

### Performance
- Batch database inserts/updates
- Index all query columns
- Cache client data between syncs
- Monitor sync duration

---

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| 1. Core Engine | 4-5h | SyncEngine, SyncResult, exceptions |
| 2. Handlers | 8-10h | Account, Client, Transaction handlers |
| 3. Strategies | 4-6h | Full and incremental sync logic |
| 4. Utilities | 4-5h | SyncTracker, ErrorHandler, utils |
| 5. API Routes | 3-4h | REST endpoints for sync triggers |
| 6. Testing | 5-6h | Unit, integration, E2E tests |
| **Total** | **28-36h** | ~4-5 days full-time work |

---

## Next Steps After Sync Engine

1. **Reporting Layer**: Financial reports built on synced data
2. **Reconciliation**: Match transactions across platforms
3. **Change Detection**: Real-time webhooks for platform updates
4. **Bulk Operations**: Create/update transactions in accounting platforms
5. **Analytics**: Dashboards and metrics
