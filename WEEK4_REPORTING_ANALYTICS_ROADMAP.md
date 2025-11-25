# Month 2, Week 4: Reporting & Analytics Layer Roadmap

## Overview
Build comprehensive financial reporting and analytics capabilities on top of the synced accounting data. This provides crucial insights for accounting practices and their clients through financial statements, categorization tools, and reconciliation utilities.

**Current Status**: Week 3 Complete (262/262 tests passing)
**Target**: 300+ passing tests, production-grade reporting engine

## Architecture

```
Reporting & Analytics Layer
  ├── Financial Reports
  │   ├── Profit & Loss (P&L) Statement
  │   ├── Balance Sheet
  │   ├── Cash Flow Statement
  │   └── Trial Balance
  │
  ├── Transaction Analysis
  │   ├── Smart categorization engine
  │   ├── Category suggestions (ML-ready)
  │   └── Category mapping rules
  │
  ├── Reconciliation Tools
  │   ├── Account reconciliation
  │   ├── Bank reconciliation
  │   ├── Variance analysis
  │   └── Discrepancy detection
  │
  └── Analytics Endpoints
      ├── GET /reports/financial - P&L, Balance Sheet
      ├── GET /reports/cashflow - Cash flow analysis
      ├── POST /categorize - Categorize transaction
      ├── GET /reconciliation/{account_id} - Reconciliation status
      └── GET /insights - Financial insights & metrics
```

## Implementation Steps

### Step 1: Financial Report Models (80 lines)
**File**: `backend/reporting/models.py`

Create data models for financial reports:

```python
class FinancialReport:
    """Base class for all reports"""
    report_type: str
    period_start: date
    period_end: date
    organization_id: UUID
    generated_at: datetime
    data: dict

class ProfitLossReport:
    """P&L Statement: Income - Expenses = Net Income"""
    revenue: Decimal
    cost_of_goods_sold: Decimal
    gross_profit: Decimal
    operating_expenses: Decimal
    operating_income: Decimal
    interest_and_taxes: Decimal
    net_income: Decimal

    # Monthly/quarterly breakdowns
    by_period: List[dict]
    by_category: List[dict]

class BalanceSheet:
    """Balance Sheet: Assets = Liabilities + Equity"""
    assets: Dict[str, Decimal]  # current, fixed, etc.
    liabilities: Dict[str, Decimal]
    equity: Dict[str, Decimal]
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal

class CashFlowStatement:
    """Cash Flow: Operating, Investing, Financing"""
    operating_cash_flow: Decimal
    investing_cash_flow: Decimal
    financing_cash_flow: Decimal
    net_cash_flow: Decimal
    beginning_cash: Decimal
    ending_cash: Decimal
```

### Step 2: Report Generator Engine (150 lines)
**File**: `backend/reporting/generators.py`

Create report generation logic:

```python
class ReportGenerator:
    """Base class for generating financial reports"""

    def __init__(self, db: Session, organization_id: UUID):
        self.db = db
        self.organization_id = organization_id

    def get_transactions(
        self,
        start_date: date,
        end_date: date,
        account_ids: List[str] = None
    ) -> List[Transaction]:
        """Get transactions for date range"""

    def generate_p_and_l(
        self,
        start_date: date,
        end_date: date
    ) -> ProfitLossReport:
        """
        Generate P&L statement

        Algorithm:
        1. Sum all revenue (income type accounts)
        2. Sum COGS (if applicable)
        3. Calculate gross profit
        4. Sum operating expenses
        5. Calculate operating income
        6. Add/subtract taxes and interest
        7. Calculate net income
        """

    def generate_balance_sheet(
        self,
        as_of_date: date = None
    ) -> BalanceSheet:
        """
        Generate Balance Sheet as of date

        Algorithm:
        1. Get all asset accounts (ASSET type)
        2. Get all liability accounts (LIABILITY type)
        3. Get all equity accounts (EQUITY type)
        4. Sum each category
        5. Verify: Assets = Liabilities + Equity
        """

    def generate_cash_flow(
        self,
        start_date: date,
        end_date: date
    ) -> CashFlowStatement:
        """Generate cash flow statement"""
```

### Step 3: Transaction Categorization (120 lines)
**File**: `backend/reporting/categorization.py`

Intelligent transaction categorization:

```python
class TransactionCategory:
    """Transaction categorization record"""
    id: UUID
    name: str  # "Travel", "Software", "Office Supplies", etc.
    description: str
    category_type: str  # "Expense", "Revenue", "Other"
    color: str  # For UI visualization
    parent_category: Optional[UUID]

class CategorizationEngine:
    """Engine for categorizing transactions"""

    def suggest_categories(
        self,
        transaction: Transaction,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Suggest categories for a transaction

        Uses rules-based matching:
        1. Keyword matching in description
        2. Amount range matching
        3. Vendor/payee matching
        4. Historical patterns

        Returns top-k suggestions with confidence scores
        """

    def auto_categorize(
        self,
        transaction: Transaction
    ) -> Optional[TransactionCategory]:
        """
        Auto-categorize transaction if confidence > threshold

        Returns category or None if low confidence
        """

    def create_categorization_rule(
        self,
        name: str,
        condition: Dict[str, Any],  # keyword, amount_range, etc.
        category_id: UUID
    ) -> CategorizationRule:
        """Create custom categorization rule"""

    def apply_rules(
        self,
        transaction: Transaction
    ) -> Optional[TransactionCategory]:
        """Apply user-defined rules to categorize"""
```

### Step 4: Reconciliation System (130 lines)
**File**: `backend/reporting/reconciliation.py`

Account reconciliation and variance detection:

```python
class ReconciliationStatus:
    """Track reconciliation status for an account"""
    account_id: UUID
    last_reconciled_at: datetime
    reconciliation_date: date
    reconciled_balance: Decimal
    system_balance: Decimal
    variance: Decimal
    is_reconciled: bool
    discrepancies: List[Dict]

class ReconciliationEngine:
    """Engine for account reconciliation"""

    def reconcile_account(
        self,
        account_id: UUID,
        reconciliation_date: date,
        cleared_amount: Decimal,
        cleared_items: List[str] = None  # Transaction IDs
    ) -> ReconciliationStatus:
        """
        Reconcile an account

        Algorithm:
        1. Get all transactions for account up to date
        2. Mark specified transactions as cleared
        3. Calculate system balance (all transactions)
        4. Compare with reconciliation_amount
        5. Identify discrepancies
        6. Update reconciliation status
        """

    def detect_discrepancies(
        self,
        account_id: UUID,
        reference_balance: Decimal
    ) -> List[Dict]:
        """
        Detect transactions that might be problematic

        Finds:
        - Duplicate transactions
        - Round-trip transactions (matching debit/credit pairs)
        - Unusual amounts
        - Timing issues (dated in future, etc.)
        """

    def bank_reconciliation(
        self,
        account_id: UUID,
        bank_statement: List[Dict]  # [{date, amount, description}]
    ) -> ReconciliationStatus:
        """
        Match bank statement to account transactions

        Uses fuzzy matching:
        1. Exact match (date + amount)
        2. Date variance ±3 days
        3. Amount variance ±$1
        """

    def generate_reconciliation_report(
        self,
        account_id: UUID,
        as_of_date: date
    ) -> Dict:
        """Generate detailed reconciliation report"""
```

### Step 5: Analytics Endpoints (100 lines)
**File**: `backend/api/reporting_routes.py`

REST API for reporting and analytics:

```python
@router.get("/reports/financial")
def get_financial_reports(
    org_id: UUID,
    start_date: date,
    end_date: date,
    db: Session
):
    """
    Get comprehensive financial reports

    Returns:
    - P&L Statement
    - Balance Sheet (as of end_date)
    - Key metrics (net income, assets, equity)
    """

@router.get("/reports/cashflow")
def get_cash_flow(
    org_id: UUID,
    start_date: date,
    end_date: date,
    db: Session
):
    """Get cash flow statement for period"""

@router.post("/categorize")
def suggest_categorization(
    transaction_id: UUID,
    top_k: int = 3,
    db: Session = Depends(get_db)
):
    """
    Get category suggestions for a transaction

    Returns:
    - Top 3 suggested categories with confidence
    - Option to auto-categorize if confident
    """

@router.get("/reconciliation/{account_id}")
def get_reconciliation_status(
    org_id: UUID,
    account_id: UUID,
    db: Session
):
    """
    Get reconciliation status for account

    Returns:
    - Last reconciliation date
    - Current variance
    - List of unreconciled items
    """

@router.post("/reconciliation/{account_id}")
def reconcile_account(
    org_id: UUID,
    account_id: UUID,
    reconciliation_date: date,
    cleared_amount: Decimal,
    cleared_items: List[str] = None,
    db: Session = Depends(get_db)
):
    """Complete account reconciliation"""

@router.get("/insights")
def get_financial_insights(
    org_id: UUID,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db)
):
    """
    Get key financial insights and metrics

    Returns:
    - Revenue trends
    - Expense breakdown
    - Top accounts by activity
    - Financial ratios
    """
```

### Step 6: Category Management (60 lines)
**File**: `backend/models.py` (modifications)

Add to existing models:

```python
class TransactionCategory(Base):
    __tablename__ = "transaction_categories"

    id = Column(UUID, primary_key=True, default=uuid4)
    organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    category_type = Column(String(50))  # Expense, Revenue, Other
    color = Column(String(7))  # Hex color
    parent_category_id = Column(UUID, ForeignKey("transaction_categories.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")
    parent_category = relationship("TransactionCategory", remote_side=[id])

class CategorizationRule(Base):
    __tablename__ = "categorization_rules"

    id = Column(UUID, primary_key=True, default=uuid4)
    organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=False)
    category_id = Column(UUID, ForeignKey("transaction_categories.id"), nullable=False)
    name = Column(String(100), nullable=False)
    condition_type = Column(String(50))  # keyword, amount_range, vendor
    condition_value = Column(String(500), nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Step 7: Comprehensive Testing (100+ lines)
**File**: `tests/test_reporting_week4.py`

Test categories:

1. **Financial Report Tests** (20 tests)
   - P&L generation with various data
   - Balance sheet correctness
   - Cash flow calculations
   - Currency handling
   - Period selection

2. **Categorization Tests** (20 tests)
   - Category suggestions
   - Auto-categorization
   - Rule creation and application
   - Confidence scoring
   - Custom rules

3. **Reconciliation Tests** (20 tests)
   - Account reconciliation flow
   - Variance detection
   - Discrepancy finding
   - Bank statement matching
   - Reconciliation reports

4. **Analytics Tests** (15 tests)
   - Financial insights calculation
   - Trends and ratios
   - Performance metrics
   - Data aggregation

5. **API Tests** (20 tests)
   - Report endpoint responses
   - Categorization endpoint
   - Reconciliation endpoints
   - Error handling
   - Authorization

**Target**: 100+ new tests, 360+ total passing

## Key Design Decisions

### 1. Report Generation Strategy
- Lazy generation (calculated on-demand, not stored)
- Caching for frequently accessed reports (5 minute TTL)
- Batch operations for multiple periods
- Incremental calculations where possible

### 2. Categorization Approach
- Rules-based + ML-ready (seed for future ML models)
- User-defined rules override suggestions
- Confidence scoring for validation
- Vendor/payee pattern learning

### 3. Reconciliation Model
- Flexible matching (exact, date range, amount range)
- Non-destructive (marks as cleared, doesn't delete)
- Audit trail of all reconciliations
- Support for multi-currency

### 4. Performance Optimization
- Database indices on date ranges and account_ids
- Materialized views for common aggregations
- Pagination for large result sets
- Async report generation for heavy computation

## Dependencies

No new external dependencies needed. Uses:
- SQLAlchemy (existing)
- Decimal (Python standard)
- datetime (Python standard)

## Testing Strategy

1. **Unit Tests**: Individual report/category/reconciliation functions
2. **Integration Tests**: Full workflows with real database
3. **Data Accuracy Tests**: Verify financial calculations
4. **Performance Tests**: Large dataset handling
5. **Edge Cases**: Missing data, currency conversion, etc.

## Success Criteria

- All 100+ new tests pass
- Financial calculations verified for accuracy
- Reports match industry standards (GAAP-compliant structure)
- Category suggestions useful (>70% accuracy on common transactions)
- Reconciliation workflow complete and intuitive
- **Total**: 360+ passing tests

## Deliverables Summary

### Core Reports
- Profit & Loss Statement (monthly, quarterly, annual)
- Balance Sheet (point-in-time)
- Cash Flow Statement
- Trial Balance

### Transaction Management
- Smart categorization with suggestions
- Category management UI-ready API
- Custom rule engine
- Categorization history

### Reconciliation Tools
- Full account reconciliation workflow
- Bank statement matching
- Discrepancy detection
- Reconciliation reports

### Analytics
- Financial metrics and ratios
- Trend analysis
- Top accounts/categories
- Period comparison

## Future Enhancements (Phase 2)

- ML-based categorization using historical patterns
- Predictive analytics and forecasting
- Multi-currency support with FX handling
- Audit trail and approval workflows
- Report generation and export (PDF, Excel)
- Dashboard visualizations
- Webhook notifications for reconciliation alerts

## Integration with Previous Weeks

The reporting layer depends on:
- **Week 1**: SyncEngine provides clean, normalized data
- **Week 2**: Sync routes ensure data is current
- **Week 3**: Scheduler keeps data fresh for reports

The reporting layer enables:
- Accounting practice insights
- Client advisory services
- Financial advisory features
- Compliance reporting
