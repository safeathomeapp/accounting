# Session Notes - February 2, 2026

## Completed

### Row-Level Security (RLS) Implementation - Phase 5 Foundation

Implemented comprehensive RLS for multi-tenant isolation at the database level.

#### Files Created
- `alembic/versions/v2_090_rls_policies.py` - Alembic migration for RLS
- `tests/test_rls_policies.py` - Test suite for RLS verification

#### Files Modified
- `backend/database.py` - Added tenant context management functions
- `backend/api/auth_routes.py` - Added RLS-aware authentication dependencies

#### What Was Implemented

1. **Database Roles** (created by migration):
   - `app_user` - Normal application role with RLS enforced
   - `app_readonly` - Read-only role with RLS enforced
   - `app_admin` - Admin role that bypasses RLS (for migrations/maintenance)

2. **RLS Policies on Tables with `organization_id`**:
   - `clients`
   - `transactions`
   - `accounts`
   - `accounting_platforms`
   - `oauth_tokens`
   - `ai_analysis_results`
   - `sync_history`
   - `audit_log`
   - `cashflow_facts_v1`
   - `ingestion_quarantine`

3. **RLS Policies on Document Tables** (use `org_id`):
   - `document_inbox_item`
   - `document_ocr_result`
   - `document_draft`
   - `document_draft_line`

4. **Special Handling**:
   - `organizations` - RLS enabled but no FORCE (allows registration)
   - `users` - RLS enabled but no FORCE (allows auth lookup)
   - `platform_transaction_mapping` - No RLS (global config table)

5. **Tenant Context Functions**:
   - `set_tenant_context(db, org_id)` - Set RLS context for session
   - `clear_tenant_context(db)` - Clear RLS context
   - `get_db_with_tenant(org_id)` - Get session with context pre-set

6. **Auth Dependencies**:
   - `get_current_user_with_rls()` - Returns (User, Session) with RLS set
   - `get_db_for_user()` - Returns Session with RLS set from JWT

## How to Apply

```bash
cd C:/Users/kevth/Desktop/Projects/Accountancy
# Activate virtual environment
source venv/Scripts/activate  # or venv\Scripts\activate on Windows

# Apply the migration
alembic upgrade head

# Verify RLS is enabled
psql -d accountancy_dev -c "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname='public' AND rowsecurity=true;"
```

## How to Use in Routes

### Option 1: Combined User + DB (Recommended)
```python
from backend.api.auth_routes import get_current_user_with_rls

@app.get("/clients")
def list_clients(auth: Tuple[User, Session] = Depends(get_current_user_with_rls)):
    user, db = auth
    # RLS is already set - queries only return this org's data
    return db.query(Client).all()
```

### Option 2: Separate Dependencies
```python
from backend.api.auth_routes import get_current_user, get_db_for_user

@app.get("/transactions")
def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_for_user)
):
    # RLS context set from JWT
    return db.query(Transaction).all()
```

### Option 3: Manual Context Setting
```python
from backend.database import get_db, set_tenant_context

@app.get("/items")
def list_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    set_tenant_context(db, current_user.organization_id)
    return db.query(Item).all()
```

## Testing

```bash
# Run RLS-specific tests
pytest tests/test_rls_policies.py -v

# Run all tests (should still pass)
pytest tests/ -v
```

### Claude Vision OCR Integration

Replaced stub OCR with real Claude Vision API for document extraction.

#### Files Created
- `backend/services/claude_ocr.py` - Claude OCR service with vision capabilities
- `backend/services/__init__.py` - Services module init
- `tests/test_claude_ocr.py` - 16 tests for Claude OCR service

#### Files Modified
- `backend/api/documents_routes.py` - Updated to use Claude OCR with fallback to mock
- `tests/test_reporting_week4.py` - Fixed 3 pre-existing test failures (mocked `_has_facts()`)

#### How It Works

1. **Upload document** via `POST /api/inbox/upload`
2. **Extract** via `POST /api/inbox/{id}/extract`:
   - If Claude API key configured → Uses Claude Vision
   - If extraction fails → Falls back to mock data
   - Returns structured invoice data (doc type, counterparty, totals, lines)
3. **Review/Edit** draft in UI
4. **Submit** → Creates internal transaction

#### Configuration

The Claude API key is already configured in `.env`:
```
CLAUDE_API_KEY=sk-ant-api03-...
CLAUDE_MODEL=claude-sonnet-4-20250514
CLAUDE_MAX_TOKENS=4096
```

#### Supported File Types
- PDF (application/pdf)
- PNG (image/png)
- JPEG (image/jpeg)
- GIF (image/gif)
- WebP (image/webp)

#### Usage Example
```python
from backend.services.claude_ocr import extract_document

result = extract_document("/path/to/invoice.pdf")
# Returns: {
#   "doc_type": "invoice",
#   "counterparty_name": "ABC Corp",
#   "doc_date": date(2025, 1, 15),
#   "currency": "GBP",
#   "invoice_no": "INV-001",
#   "totals": {"net": Decimal("100.00"), "vat": Decimal("20.00"), "gross": Decimal("120.00")},
#   "lines": [...],
# }
```

## In Progress

- None currently

## Blockers

- None

## Next Session

1. **Test Claude OCR** with real invoices/receipts
2. **Consider** adding more VAT code mapping (UK-specific)
3. **Consider** adding counterparty matching to existing clients
4. **Real OAuth** for FreeAgent/Xero/QuickBooks when API keys available

## Notes

### Design Decisions

1. **FORCE RLS** is enabled on most tables, meaning even the table owner is subject to RLS. However, `users` and `organizations` tables do NOT have FORCE RLS because:
   - Auth needs to query users by email before knowing org_id
   - Registration needs to create organizations before org_id exists

2. **Default-deny behavior**: If `app.org_id` is not set, the RLS policy evaluates to `organization_id = NULL`, which never matches, so no rows are returned. This is the safe default.

3. **Backward compatibility**: The current database connection (as postgres/owner) bypasses RLS on tables without FORCE. This means existing code continues to work, but for true tenant isolation, the application should eventually connect as `app_user`.

### Security Considerations

- RLS is defense-in-depth - application code should still filter by organization_id
- The JWT contains organization_id, so RLS context can be set without extra DB query
- Table owners bypass RLS by default; use FORCE ROW LEVEL SECURITY for stricter enforcement

## Files Modified

| File | Description |
|------|-------------|
| `alembic/versions/v2_090_rls_policies.py` | New migration for RLS policies |
| `backend/database.py` | Added set_tenant_context, clear_tenant_context, get_db_with_tenant |
| `backend/api/auth_routes.py` | Added get_current_user_with_rls, get_db_for_user |
| `tests/test_rls_policies.py` | New test file for RLS verification |
| `backend/services/claude_ocr.py` | New: Claude Vision OCR service |
| `backend/services/__init__.py` | New: Services module init |
| `backend/api/documents_routes.py` | Updated to use Claude OCR |
| `tests/test_claude_ocr.py` | New: 16 tests for Claude OCR |
| `tests/test_reporting_week4.py` | Fixed 3 pre-existing test failures |
| `docs/SESSION_NOTES/SESSION_NOTES_2026-02-02.md` | This file |
