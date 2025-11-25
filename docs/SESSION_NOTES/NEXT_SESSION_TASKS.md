# Next Session: Priority Tasks

## 🎯 PRIMARY OBJECTIVE: Achieve 100% Test Pass Rate

**Current Status**: 423/427 tests passing (99.1%)
**Target**: 427/427 tests passing (100%)
**Blocker**: 4 failing database mock tests in `test_reporting_week4.py`

## Failing Tests to Fix

### Test 1: `test_get_transactions` (line 283)
**File**: `tests/test_reporting_week4.py`
**Status**: FAILED

**Current Issue**:
```
TypeError: object of type 'Mock' has no len()
at line 306: assert len(txns) == 3
```

**Root Cause**:
The mock chain for `db.query()` is returning the same mock instance for both the organization query and the transaction query. When `get_transactions()` is called, it's getting a mock that doesn't have proper `.filter()` chaining configured.

**Fix Strategy**:
```python
# Instead of reusing mock_query, create separate mocks:
org_query_mock = Mock()
org_query_mock.filter_by.return_value.first.return_value = mock_org

txn_query_mock = Mock()
txn_query_mock.filter.return_value.filter.return_value.filter.return_value.all.return_value = [Mock(), Mock(), Mock()]

# Use side_effect to return different mocks
db.query.side_effect = [org_query_mock, txn_query_mock]
```

**Estimated Fix Time**: 10 minutes

---

### Test 2: `test_generate_profit_loss_simple` (line 309)
**File**: `tests/test_reporting_week4.py`
**Status**: FAILED

**Current Issue**:
```
TypeError: 'Mock' object is not iterable
at line 354: report = generator.generate_profit_loss(start, end)
```

**Root Cause**:
The `generate_profit_loss()` method calls `get_transactions()` multiple times (once for revenue, once for expenses). The current mock setup doesn't account for this sequential chaining. When the generator tries to iterate over the returned mock, it fails.

**Fix Strategy**:
```python
# Create separate query mocks for different stages:
# 1. Organization query (during __init__)
# 2. Income account query (to get income accounts)
# 3. Expense account query (to get expense accounts)
# 4. Revenue transaction query (to get revenue txns)
# 5. Expense transaction query (to get expense txns)

# Use side_effect with proper sequencing:
query_return_values = [
    org_query_mock,           # __init__ org lookup
    account_filter_mock,      # get income accounts
    account_filter_mock2,     # get expense accounts
    revenue_txn_mock,         # get revenue transactions
    expense_txn_mock,         # get expense transactions
]
db.query.side_effect = query_return_values
```

**Estimated Fix Time**: 15 minutes

---

### Test 3: `test_generate_balance_sheet` (line 361)
**File**: `tests/test_reporting_week4.py`
**Status**: FAILED

**Current Issue**:
Similar to test 2 - mock chain doesn't properly handle multiple sequential query calls.

**Fix Strategy**:
Same as test 2 - separate mocks for account queries and transaction queries, use `side_effect` for sequencing.

**Estimated Fix Time**: 15 minutes

---

### Test 4: `test_generate_trial_balance` (line 407)
**File**: `tests/test_reporting_week4.py`
**Status**: FAILED

**Current Issue**:
Trial balance expects to iterate over mock objects properly formatted.

**Fix Strategy**:
Configure mocks to return properly iterable Trial Balance format (list of dicts with account balances).

**Estimated Fix Time**: 10 minutes

---

## Secondary Fixes (After Tests Pass)

### 1. Fix DeprecationWarning
**File**: `backend/reporting/reconciliation.py` (line 181)

**Current**:
```python
last_reconciled_at=datetime.utcnow(),
```

**Should be**:
```python
from datetime import datetime, timezone
last_reconciled_at=datetime.now(timezone.utc),
```

**Impact**: Cleans up test output warnings

---

### 2. Verify Main.py Integration
**File**: `backend/main.py`

**Check**:
- Analytics engines initialized at startup
- Routes properly registered
- No missing imports

---

## Session Plan

### Phase 1: Test Fixes (45 minutes)
1. Fix `test_get_transactions` with proper side_effect setup (10 min)
2. Fix `test_generate_profit_loss_simple` with sequential mocks (15 min)
3. Fix `test_generate_balance_sheet` with account/txn separation (15 min)
4. Fix `test_generate_trial_balance` with format verification (5 min)

### Phase 2: Verification (10 minutes)
```bash
pytest tests/test_reporting_week4.py -v
pytest tests/ -v --tb=short  # Full suite
```

### Phase 3: Polish (10 minutes)
1. Fix datetime deprecation warning
2. Verify all 427 tests pass
3. Commit: "Month 2 Week 4 Complete: 427/427 tests passing (100%)"

---

## Testing Commands

### Run only failing tests:
```bash
cd C:/Users/kevth/Desktop/Projects/Accountancy
. venv/Scripts/activate
python -m pytest tests/test_reporting_week4.py::TestReportGenerator::test_get_transactions -v
python -m pytest tests/test_reporting_week4.py::TestReportGenerator::test_generate_profit_loss_simple -v
python -m pytest tests/test_reporting_week4.py::TestReportGenerator::test_generate_balance_sheet -v
python -m pytest tests/test_reporting_week4.py::TestReportGenerator::test_generate_trial_balance -v
```

### Run all Week 4 tests:
```bash
python -m pytest tests/test_reporting_week4.py tests/test_categorization_week4.py tests/test_reconciliation_week4.py tests/test_analytics_week4.py -v
```

### Run entire test suite:
```bash
python -m pytest tests/ -v --tb=short
```

---

## Success Criteria

✅ All 4 failing tests pass
✅ Full test suite: 427/427 tests passing (100%)
✅ No warnings in test output
✅ Clean commit message documenting completion
✅ Ready for Month 3 planning

---

## Expected Outcome

After completing these fixes:
- **100% test pass rate achieved** (427/427)
- Clean, working reporting and analytics layer
- Production-ready financial reporting API
- Foundation for Month 3: Advanced features (dashboards, multi-currency, compliance)
