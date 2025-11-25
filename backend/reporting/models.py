"""Data models for financial reporting."""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID


@dataclass
class FinancialReport:
    """Base class for financial reports."""

    report_type: str
    period_start: date
    period_end: date
    organization_id: UUID
    generated_at: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "report_type": self.report_type,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "organization_id": str(self.organization_id),
            "generated_at": self.generated_at.isoformat(),
            "data": self.data,
        }


@dataclass
class ProfitLossReport:
    """Profit & Loss Statement: Revenue - Expenses = Net Income."""

    period_start: date
    period_end: date
    organization_id: UUID

    # Income
    revenue: Decimal = Decimal("0.00")
    other_income: Decimal = Decimal("0.00")
    total_income: Decimal = Decimal("0.00")

    # Cost of Goods Sold (if applicable)
    cost_of_goods_sold: Decimal = Decimal("0.00")
    gross_profit: Decimal = Decimal("0.00")

    # Operating Expenses
    operating_expenses: Decimal = Decimal("0.00")
    operating_income: Decimal = Decimal("0.00")

    # Non-operating items
    interest_expense: Decimal = Decimal("0.00")
    interest_income: Decimal = Decimal("0.00")
    tax_expense: Decimal = Decimal("0.00")

    # Net Income
    net_income: Decimal = Decimal("0.00")

    # Breakdowns
    by_period: List[Dict[str, Any]] = field(default_factory=list)
    by_category: List[Dict[str, Any]] = field(default_factory=list)
    by_account: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    currency: str = "USD"

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "report_type": "profit_loss",
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "revenue": float(self.revenue),
            "cost_of_goods_sold": float(self.cost_of_goods_sold),
            "gross_profit": float(self.gross_profit),
            "operating_expenses": float(self.operating_expenses),
            "operating_income": float(self.operating_income),
            "interest_expense": float(self.interest_expense),
            "interest_income": float(self.interest_income),
            "tax_expense": float(self.tax_expense),
            "net_income": float(self.net_income),
            "by_period": self.by_period,
            "by_category": self.by_category,
            "by_account": self.by_account,
            "generated_at": self.generated_at.isoformat(),
            "currency": self.currency,
        }

    def calculate_totals(self) -> None:
        """Calculate derived totals."""
        self.total_income = self.revenue + self.other_income
        self.gross_profit = self.total_income - self.cost_of_goods_sold
        self.operating_income = self.gross_profit - self.operating_expenses

        net_income = self.operating_income
        net_income += self.interest_income
        net_income -= self.interest_expense
        net_income -= self.tax_expense

        self.net_income = net_income


@dataclass
class BalanceSheet:
    """Balance Sheet: Assets = Liabilities + Equity."""

    as_of_date: date
    organization_id: UUID

    # Assets
    current_assets: Decimal = Decimal("0.00")
    fixed_assets: Decimal = Decimal("0.00")
    other_assets: Decimal = Decimal("0.00")
    total_assets: Decimal = Decimal("0.00")

    # Liabilities
    current_liabilities: Decimal = Decimal("0.00")
    long_term_liabilities: Decimal = Decimal("0.00")
    other_liabilities: Decimal = Decimal("0.00")
    total_liabilities: Decimal = Decimal("0.00")

    # Equity
    contributed_capital: Decimal = Decimal("0.00")
    retained_earnings: Decimal = Decimal("0.00")
    other_equity: Decimal = Decimal("0.00")
    total_equity: Decimal = Decimal("0.00")

    # Breakdowns by account
    assets_by_account: List[Dict[str, Any]] = field(default_factory=list)
    liabilities_by_account: List[Dict[str, Any]] = field(default_factory=list)
    equity_by_account: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    currency: str = "USD"
    is_balanced: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "report_type": "balance_sheet",
            "as_of_date": self.as_of_date.isoformat(),
            "current_assets": float(self.current_assets),
            "fixed_assets": float(self.fixed_assets),
            "other_assets": float(self.other_assets),
            "total_assets": float(self.total_assets),
            "current_liabilities": float(self.current_liabilities),
            "long_term_liabilities": float(self.long_term_liabilities),
            "other_liabilities": float(self.other_liabilities),
            "total_liabilities": float(self.total_liabilities),
            "contributed_capital": float(self.contributed_capital),
            "retained_earnings": float(self.retained_earnings),
            "other_equity": float(self.other_equity),
            "total_equity": float(self.total_equity),
            "assets_by_account": self.assets_by_account,
            "liabilities_by_account": self.liabilities_by_account,
            "equity_by_account": self.equity_by_account,
            "is_balanced": self.is_balanced,
            "generated_at": self.generated_at.isoformat(),
            "currency": self.currency,
        }

    def calculate_totals(self) -> None:
        """Calculate derived totals and check balance."""
        self.total_assets = (
            self.current_assets + self.fixed_assets + self.other_assets
        )
        self.total_liabilities = (
            self.current_liabilities
            + self.long_term_liabilities
            + self.other_liabilities
        )
        self.total_equity = (
            self.contributed_capital + self.retained_earnings + self.other_equity
        )

        # Check if balanced (Assets = Liabilities + Equity)
        self.is_balanced = (
            self.total_assets
            == (self.total_liabilities + self.total_equity)
        )


@dataclass
class CashFlowStatement:
    """Cash Flow Statement: Operating + Investing + Financing."""

    period_start: date
    period_end: date
    organization_id: UUID

    # Operating Cash Flow
    net_income: Decimal = Decimal("0.00")
    depreciation_amortization: Decimal = Decimal("0.00")
    changes_in_working_capital: Decimal = Decimal("0.00")
    operating_cash_flow: Decimal = Decimal("0.00")

    # Investing Cash Flow
    purchase_fixed_assets: Decimal = Decimal("0.00")
    sale_fixed_assets: Decimal = Decimal("0.00")
    purchases_investments: Decimal = Decimal("0.00")
    investing_cash_flow: Decimal = Decimal("0.00")

    # Financing Cash Flow
    debt_proceeds: Decimal = Decimal("0.00")
    debt_repayment: Decimal = Decimal("0.00")
    equity_issuance: Decimal = Decimal("0.00")
    dividends_paid: Decimal = Decimal("0.00")
    financing_cash_flow: Decimal = Decimal("0.00")

    # Net Effect
    net_cash_flow: Decimal = Decimal("0.00")
    beginning_cash: Decimal = Decimal("0.00")
    ending_cash: Decimal = Decimal("0.00")

    # Breakdowns
    by_period: List[Dict[str, Any]] = field(default_factory=list)
    by_account: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    currency: str = "USD"

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "report_type": "cash_flow",
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "operating_cash_flow": float(self.operating_cash_flow),
            "investing_cash_flow": float(self.investing_cash_flow),
            "financing_cash_flow": float(self.financing_cash_flow),
            "net_cash_flow": float(self.net_cash_flow),
            "beginning_cash": float(self.beginning_cash),
            "ending_cash": float(self.ending_cash),
            "by_period": self.by_period,
            "by_account": self.by_account,
            "generated_at": self.generated_at.isoformat(),
            "currency": self.currency,
        }

    def calculate_flows(self) -> None:
        """Calculate cash flows."""
        # Operating: Net income + non-cash items - changes in working capital
        self.operating_cash_flow = (
            self.net_income
            + self.depreciation_amortization
            + self.changes_in_working_capital
        )

        # Investing: Asset purchases/sales and investment changes
        self.investing_cash_flow = (
            self.sale_fixed_assets
            - self.purchase_fixed_assets
            - self.purchases_investments
        )

        # Financing: Debt and equity changes
        self.financing_cash_flow = (
            self.debt_proceeds
            - self.debt_repayment
            + self.equity_issuance
            - self.dividends_paid
        )

        # Net: Sum of all flows
        self.net_cash_flow = (
            self.operating_cash_flow
            + self.investing_cash_flow
            + self.financing_cash_flow
        )

        # Ending: Beginning + net change
        self.ending_cash = self.beginning_cash + self.net_cash_flow
