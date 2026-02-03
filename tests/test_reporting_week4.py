"""Tests for Week 4: Reporting & Analytics Layer."""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.reporting.models import (
    FinancialReport,
    ProfitLossReport,
    BalanceSheet,
    CashFlowStatement,
)
from backend.reporting.generators import ReportGenerator
from backend.accounting import AccountType, TransactionType


class TestProfitLossReport:
    """Tests for P&L report model."""

    def test_pl_report_initialization(self):
        """Test P&L report initialization."""
        start = date(2025, 1, 1)
        end = date(2025, 12, 31)
        org_id = uuid4()

        report = ProfitLossReport(
            period_start=start,
            period_end=end,
            organization_id=org_id,
        )

        assert report.period_start == start
        assert report.period_end == end
        assert report.organization_id == org_id
        assert report.revenue == Decimal("0.00")
        assert report.net_income == Decimal("0.00")

    def test_pl_report_calculate_totals(self):
        """Test P&L total calculation."""
        report = ProfitLossReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=uuid4(),
            revenue=Decimal("100000.00"),
            operating_expenses=Decimal("60000.00"),
            tax_expense=Decimal("8000.00"),
        )

        report.calculate_totals()

        assert report.gross_profit == Decimal("100000.00")
        assert report.operating_income == Decimal("40000.00")
        assert report.net_income == Decimal("32000.00")

    def test_pl_report_to_dict(self):
        """Test P&L report serialization."""
        org_id = uuid4()
        report = ProfitLossReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=org_id,
            revenue=Decimal("100000.00"),
            net_income=Decimal("25000.00"),
        )

        data = report.to_dict()

        assert data["report_type"] == "profit_loss"
        assert data["revenue"] == 100000.0
        assert data["net_income"] == 25000.0
        assert "generated_at" in data

    def test_pl_report_with_other_income(self):
        """Test P&L with other income items."""
        report = ProfitLossReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=uuid4(),
            revenue=Decimal("100000.00"),
            other_income=Decimal("5000.00"),
            operating_expenses=Decimal("60000.00"),
            interest_income=Decimal("1000.00"),
            interest_expense=Decimal("2000.00"),
            tax_expense=Decimal("8000.00"),
        )

        report.calculate_totals()

        assert report.total_income == Decimal("105000.00")
        assert report.gross_profit == Decimal("105000.00")
        assert report.operating_income == Decimal("45000.00")
        # Operating income + interest_income - interest_expense - tax
        assert report.net_income == Decimal("36000.00")


class TestBalanceSheet:
    """Tests for Balance Sheet model."""

    def test_balance_sheet_initialization(self):
        """Test balance sheet initialization."""
        as_of = date(2025, 12, 31)
        org_id = uuid4()

        bs = BalanceSheet(
            as_of_date=as_of,
            organization_id=org_id,
        )

        assert bs.as_of_date == as_of
        assert bs.organization_id == org_id
        assert bs.total_assets == Decimal("0.00")
        assert bs.total_liabilities == Decimal("0.00")
        assert bs.total_equity == Decimal("0.00")
        assert bs.is_balanced is False

    def test_balance_sheet_calculate_totals(self):
        """Test balance sheet total calculation."""
        bs = BalanceSheet(
            as_of_date=date(2025, 12, 31),
            organization_id=uuid4(),
            current_assets=Decimal("50000.00"),
            fixed_assets=Decimal("30000.00"),
            current_liabilities=Decimal("20000.00"),
            long_term_liabilities=Decimal("30000.00"),
            contributed_capital=Decimal("20000.00"),
            retained_earnings=Decimal("10000.00"),
        )

        bs.calculate_totals()

        assert bs.total_assets == Decimal("80000.00")
        assert bs.total_liabilities == Decimal("50000.00")
        assert bs.total_equity == Decimal("30000.00")
        assert bs.is_balanced is True

    def test_balance_sheet_unbalanced(self):
        """Test unbalanced balance sheet detection."""
        bs = BalanceSheet(
            as_of_date=date(2025, 12, 31),
            organization_id=uuid4(),
            current_assets=Decimal("50000.00"),
            fixed_assets=Decimal("30000.00"),
            current_liabilities=Decimal("20000.00"),
            long_term_liabilities=Decimal("30000.00"),
            contributed_capital=Decimal("15000.00"),  # Should be 20000
            retained_earnings=Decimal("10000.00"),
        )

        bs.calculate_totals()

        assert bs.total_assets == Decimal("80000.00")
        assert bs.total_liabilities == Decimal("50000.00")
        assert bs.total_equity == Decimal("25000.00")
        assert bs.is_balanced is False

    def test_balance_sheet_to_dict(self):
        """Test balance sheet serialization."""
        org_id = uuid4()
        bs = BalanceSheet(
            as_of_date=date(2025, 12, 31),
            organization_id=org_id,
            current_assets=Decimal("50000.00"),
            total_assets=Decimal("80000.00"),
        )

        data = bs.to_dict()

        assert data["report_type"] == "balance_sheet"
        assert data["current_assets"] == 50000.0
        assert data["total_assets"] == 80000.0
        assert "generated_at" in data


class TestCashFlowStatement:
    """Tests for Cash Flow Statement model."""

    def test_cash_flow_initialization(self):
        """Test cash flow statement initialization."""
        start = date(2025, 1, 1)
        end = date(2025, 12, 31)
        org_id = uuid4()

        cf = CashFlowStatement(
            period_start=start,
            period_end=end,
            organization_id=org_id,
        )

        assert cf.period_start == start
        assert cf.period_end == end
        assert cf.organization_id == org_id
        assert cf.operating_cash_flow == Decimal("0.00")
        assert cf.net_cash_flow == Decimal("0.00")

    def test_cash_flow_calculate_flows(self):
        """Test cash flow calculation."""
        cf = CashFlowStatement(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=uuid4(),
            net_income=Decimal("30000.00"),
            depreciation_amortization=Decimal("5000.00"),
            purchase_fixed_assets=Decimal("10000.00"),
            sale_fixed_assets=Decimal("2000.00"),
            debt_proceeds=Decimal("20000.00"),
            dividends_paid=Decimal("5000.00"),
            beginning_cash=Decimal("10000.00"),
        )

        cf.calculate_flows()

        # Operating: net income + depreciation
        assert cf.operating_cash_flow == Decimal("35000.00")

        # Investing: sales - purchases
        assert cf.investing_cash_flow == Decimal("-8000.00")

        # Financing: debt - dividends
        assert cf.financing_cash_flow == Decimal("15000.00")

        # Net: sum of all
        assert cf.net_cash_flow == Decimal("42000.00")

        # Ending: beginning + net
        assert cf.ending_cash == Decimal("52000.00")

    def test_cash_flow_to_dict(self):
        """Test cash flow statement serialization."""
        org_id = uuid4()
        cf = CashFlowStatement(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=org_id,
            operating_cash_flow=Decimal("35000.00"),
            net_cash_flow=Decimal("42000.00"),
        )

        data = cf.to_dict()

        assert data["report_type"] == "cash_flow"
        assert data["operating_cash_flow"] == 35000.0
        assert data["net_cash_flow"] == 42000.0


class TestReportGenerator:
    """Tests for report generation engine."""

    def test_report_generator_initialization(self):
        """Test report generator initialization."""
        db = Mock(spec=Session)
        org_id = uuid4()

        # Mock organization query
        mock_org = Mock()
        mock_query = Mock()
        mock_query.filter_by.return_value.first.return_value = mock_org
        db.query.return_value = mock_query

        generator = ReportGenerator(db, org_id)

        assert generator.db is db
        assert generator.organization_id == org_id
        assert generator.org is mock_org

    def test_report_generator_org_not_found(self):
        """Test report generator with non-existent organization."""
        db = Mock(spec=Session)
        org_id = uuid4()

        # Mock organization not found
        mock_query = Mock()
        mock_query.filter_by.return_value.first.return_value = None
        db.query.return_value = mock_query

        with pytest.raises(ValueError, match="Organization not found"):
            ReportGenerator(db, org_id)

    @patch('backend.reporting.generators.Organization')
    def test_get_transactions(self, mock_org_class):
        """Test getting transactions for date range."""
        db = Mock(spec=Session)
        org_id = uuid4()

        # Setup mock organization query
        mock_org = Mock()
        org_query_mock = Mock()
        org_query_mock.filter_by.return_value.first.return_value = mock_org

        # Setup mock transactions query with smart filter chaining
        mock_txns = [Mock(), Mock(), Mock()]
        txn_query_mock = Mock()
        # Make filter() return self so it can be chained, then .all() returns the list
        txn_query_mock.filter.return_value = txn_query_mock
        txn_query_mock.all.return_value = mock_txns

        # Use side_effect to return different mocks for each db.query() call
        db.query.side_effect = [org_query_mock, txn_query_mock]

        generator = ReportGenerator(db, org_id)

        start = date(2025, 1, 1)
        end = date(2025, 12, 31)

        txns = generator.get_transactions(start, end)

        assert len(txns) == 3

    @patch('backend.reporting.generators.Organization')
    def test_generate_profit_loss_simple(self, mock_org_class):
        """Test simple P&L generation."""
        db = Mock(spec=Session)
        org_id = uuid4()

        # Setup mock organization
        mock_org = Mock()
        org_query_mock = Mock()
        org_query_mock.filter_by.return_value.first.return_value = mock_org

        # Mock account query chains with self-returning filter
        mock_income_account = Mock()
        mock_income_account.id = uuid4()
        mock_income_account.account_type = AccountType.INCOME

        mock_expense_account = Mock()
        mock_expense_account.id = uuid4()
        mock_expense_account.account_type = AccountType.EXPENSE

        income_query_mock = Mock()
        income_query_mock.filter.return_value = income_query_mock
        income_query_mock.all.return_value = [mock_income_account]

        expense_query_mock = Mock()
        expense_query_mock.filter.return_value = expense_query_mock
        expense_query_mock.all.return_value = [mock_expense_account]

        # Mock transactions with self-returning filter
        mock_revenue_txn = Mock()
        mock_revenue_txn.total_amount = Decimal("100000.00")

        mock_expense_txn = Mock()
        mock_expense_txn.total_amount = Decimal("60000.00")

        revenue_txn_query_mock = Mock()
        revenue_txn_query_mock.filter.return_value = revenue_txn_query_mock
        revenue_txn_query_mock.all.return_value = [mock_revenue_txn]

        expense_txn_query_mock = Mock()
        expense_txn_query_mock.filter.return_value = expense_txn_query_mock
        expense_txn_query_mock.all.return_value = [mock_expense_txn]

        # Use side_effect to sequence all db.query() calls
        # Order matters: queries are called in this sequence by generate_profit_loss
        db.query.side_effect = [
            org_query_mock,           # __init__ org lookup
            income_query_mock,        # get income accounts (first Account query)
            revenue_txn_query_mock,   # get revenue transactions (called inside get_transactions)
            expense_query_mock,       # get expense accounts (second Account query)
            expense_txn_query_mock,   # get expense transactions (called inside get_transactions)
        ]

        generator = ReportGenerator(db, org_id)

        start = date(2025, 1, 1)
        end = date(2025, 12, 31)

        # Patch _has_facts to return False so it uses the raw transactions fallback path
        with patch.object(generator, '_has_facts', return_value=False):
            report = generator.generate_profit_loss(start, end)

        assert report.period_start == start
        assert report.period_end == end
        assert isinstance(report, ProfitLossReport)

    @patch('backend.reporting.generators.Organization')
    def test_generate_balance_sheet(self, mock_org_class):
        """Test balance sheet generation."""
        db = Mock(spec=Session)
        org_id = uuid4()

        # Setup mock organization
        mock_org = Mock()
        org_query_mock = Mock()
        org_query_mock.filter_by.return_value.first.return_value = mock_org

        # Mock accounts with self-returning filter
        mock_asset_account = Mock()
        mock_asset_account.id = uuid4()
        mock_asset_account.name = "Cash"
        mock_asset_account.code = "1000"
        mock_asset_account.account_type = AccountType.ASSET

        asset_query_mock = Mock()
        asset_query_mock.filter.return_value = asset_query_mock
        asset_query_mock.all.return_value = [mock_asset_account]

        # Mock transactions with self-returning filter
        mock_txn = Mock()
        mock_txn.total_amount = Decimal("50000.00")

        txn_query_mock = Mock()
        txn_query_mock.filter.return_value = txn_query_mock
        txn_query_mock.all.return_value = [mock_txn]

        # Use side_effect to sequence db.query() calls
        db.query.side_effect = [
            org_query_mock,      # __init__ org lookup
            asset_query_mock,    # get accounts
            txn_query_mock,      # get transactions
        ]

        generator = ReportGenerator(db, org_id)

        as_of = date(2025, 12, 31)

        # Patch _has_facts to return False so it uses the raw transactions fallback path
        with patch.object(generator, '_has_facts', return_value=False):
            report = generator.generate_balance_sheet(as_of)

        assert report.as_of_date == as_of
        assert isinstance(report, BalanceSheet)

    @patch('backend.reporting.generators.Organization')
    def test_generate_cash_flow(self, mock_org_class):
        """Test cash flow generation."""
        db = Mock(spec=Session)
        org_id = uuid4()

        # Setup mock organization
        mock_org = Mock()
        mock_query = Mock()
        db.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = mock_org

        generator = ReportGenerator(db, org_id)

        start = date(2025, 1, 1)
        end = date(2025, 12, 31)

        # Mock for P&L generation within cash flow
        mock_income_account = Mock()
        mock_income_account.account_type = AccountType.INCOME
        mock_expense_account = Mock()
        mock_expense_account.account_type = AccountType.EXPENSE

        # Setup complex mock chain for double calls to get_transactions
        transaction_calls = []

        def mock_get_transactions(*args, **kwargs):
            if kwargs.get('account_ids'):
                return [Mock(total_amount=Decimal("100000.00"))]
            return []

        # Patch _has_facts to return False, get_transactions, and generate_profit_loss
        with patch.object(generator, '_has_facts', return_value=False):
            with patch.object(generator, 'get_transactions', side_effect=mock_get_transactions):
                with patch.object(generator, 'generate_profit_loss') as mock_pl:
                    mock_pl_report = ProfitLossReport(
                        period_start=start,
                        period_end=end,
                        organization_id=org_id,
                        net_income=Decimal("25000.00"),
                    )
                    mock_pl.return_value = mock_pl_report

                    report = generator.generate_cash_flow(start, end)

                    assert report.period_start == start
                    assert report.period_end == end
                    assert isinstance(report, CashFlowStatement)
                    assert report.net_income == Decimal("25000.00")

    @patch('backend.reporting.generators.Organization')
    def test_generate_trial_balance(self, mock_org_class):
        """Test trial balance generation."""
        db = Mock(spec=Session)
        org_id = uuid4()

        # Setup mock organization
        mock_org = Mock()
        org_query_mock = Mock()
        org_query_mock.filter_by.return_value.first.return_value = mock_org

        # Mock accounts with self-returning filter
        mock_account = Mock()
        mock_account.id = uuid4()
        mock_account.name = "Cash"
        mock_account.code = "1000"
        mock_account.account_type = AccountType.ASSET

        account_query_mock = Mock()
        account_query_mock.filter.return_value = account_query_mock
        account_query_mock.all.return_value = [mock_account]

        # Mock transactions with self-returning filter
        mock_txn = Mock()
        mock_txn.total_amount = Decimal("50000.00")

        txn_query_mock = Mock()
        txn_query_mock.filter.return_value = txn_query_mock
        txn_query_mock.all.return_value = [mock_txn]

        # Use side_effect to sequence db.query() calls
        db.query.side_effect = [
            org_query_mock,        # __init__ org lookup
            account_query_mock,    # get accounts
            txn_query_mock,        # get transactions
        ]

        generator = ReportGenerator(db, org_id)

        as_of = date(2025, 12, 31)

        tb = generator.generate_trial_balance(as_of)

        assert tb["as_of_date"] == as_of.isoformat()
        assert len(tb["accounts"]) == 1
        assert tb["total_debits"] == 50000.0


class TestFinancialReports:
    """Integration tests for financial reports."""

    def test_pl_to_dict_complete(self):
        """Test complete P&L serialization."""
        org_id = uuid4()
        report = ProfitLossReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=org_id,
            revenue=Decimal("500000.00"),
            operating_expenses=Decimal("300000.00"),
            net_income=Decimal("100000.00"),
            by_category=[
                {"category": "Travel", "amount": 50000.00},
                {"category": "Supplies", "amount": 25000.00},
            ],
        )

        data = report.to_dict()

        assert data["report_type"] == "profit_loss"
        assert data["revenue"] == 500000.0
        assert len(data["by_category"]) == 2
        assert data["currency"] == "USD"

    def test_balance_sheet_detailed(self):
        """Test detailed balance sheet."""
        org_id = uuid4()
        bs = BalanceSheet(
            as_of_date=date(2025, 12, 31),
            organization_id=org_id,
            current_assets=Decimal("100000.00"),
            fixed_assets=Decimal("200000.00"),
            current_liabilities=Decimal("80000.00"),
            long_term_liabilities=Decimal("100000.00"),
            contributed_capital=Decimal("50000.00"),
            retained_earnings=Decimal("70000.00"),
            assets_by_account=[
                {"account_name": "Cash", "balance": 50000.0},
                {"account_name": "Equipment", "balance": 200000.0},
            ],
        )

        bs.calculate_totals()

        assert bs.is_balanced is True
        assert len(bs.assets_by_account) == 2
