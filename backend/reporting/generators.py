"""Financial report generation engine.

Reads from the canonical cashflow_facts_v1 layer for normalized, platform-agnostic
reporting. Falls back to raw transactions if no facts exist (graceful degradation).
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import (
    Transaction,
    Account,
    Organization,
    Client,
)
from backend.accounting import TransactionType, AccountType
from backend.canonical.models import CashflowFact, CashflowBucket, NormalizedTxnType
from backend.canonical import queries as canonical_queries
from .models import (
    ProfitLossReport,
    BalanceSheet,
    CashFlowStatement,
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate financial reports from canonical facts layer."""

    def __init__(self, db: Session, organization_id: UUID):
        self.db = db
        self.organization_id = organization_id

        self.org = self.db.query(Organization).filter_by(
            id=organization_id
        ).first()

        if not self.org:
            raise ValueError(f"Organization not found: {organization_id}")

    def _has_facts(self) -> bool:
        """Check if canonical facts exist for this organization."""
        count = (
            self.db.query(func.count(CashflowFact.id))
            .filter(CashflowFact.organization_id == self.organization_id)
            .scalar()
        )
        return (count or 0) > 0

    def get_transactions(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[List[str]] = None,
        transaction_types: Optional[List[str]] = None,
    ) -> List[Transaction]:
        """Get raw transactions for date range (fallback path)."""
        query = self.db.query(Transaction).filter(
            Transaction.organization_id == self.organization_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )

        if account_ids:
            query = query.filter(Transaction.account_id.in_(account_ids))

        if transaction_types:
            query = query.filter(Transaction.transaction_type.in_(transaction_types))

        return query.all()

    def generate_profit_loss(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[List[str]] = None,
    ) -> ProfitLossReport:
        """
        Generate Profit & Loss statement.

        Uses canonical facts layer when available, falls back to raw transactions.
        Response shape is identical regardless of data source.
        """
        logger.info(
            f"Generating P&L report for {self.organization_id} "
            f"({start_date} to {end_date})"
        )

        report = ProfitLossReport(
            period_start=start_date,
            period_end=end_date,
            organization_id=self.organization_id,
        )

        if self._has_facts():
            # Canonical facts path
            report.revenue = canonical_queries.get_revenue(
                self.db, self.organization_id, start_date, end_date
            )
            report.operating_expenses = canonical_queries.get_expenses(
                self.db, self.organization_id, start_date, end_date
            )
            logger.debug("P&L generated from canonical facts")
        else:
            # Fallback: raw transactions path
            revenue_accounts = self.db.query(Account).filter(
                Account.organization_id == self.organization_id,
                Account.account_type == AccountType.INCOME,
            ).all()

            revenue_account_ids = [acc.id for acc in revenue_accounts]
            if revenue_account_ids:
                revenue_txns = self.get_transactions(
                    start_date, end_date, account_ids=revenue_account_ids
                )
                report.revenue = sum(
                    (t.total_amount for t in revenue_txns), Decimal("0.00")
                )

            expense_accounts = self.db.query(Account).filter(
                Account.organization_id == self.organization_id,
                Account.account_type == AccountType.EXPENSE,
            ).all()

            expense_account_ids = [acc.id for acc in expense_accounts]
            if expense_account_ids:
                expense_txns = self.get_transactions(
                    start_date, end_date, account_ids=expense_account_ids
                )
                report.operating_expenses = sum(
                    (t.total_amount for t in expense_txns), Decimal("0.00")
                )
            logger.debug("P&L generated from raw transactions (no facts available)")

        report.calculate_totals()

        logger.info(
            f"P&L Report generated: Revenue={report.revenue}, "
            f"Expenses={report.operating_expenses}, "
            f"Net Income={report.net_income}"
        )

        return report

    def generate_balance_sheet(
        self,
        as_of_date: Optional[date] = None,
        account_ids: Optional[List[str]] = None,
    ) -> BalanceSheet:
        """
        Generate Balance Sheet as of date.

        Uses canonical facts for AR/AP aging when available,
        falls back to raw account-based calculation.
        """
        if as_of_date is None:
            as_of_date = date.today()

        logger.info(
            f"Generating Balance Sheet for {self.organization_id} as of {as_of_date}"
        )

        report = BalanceSheet(
            as_of_date=as_of_date,
            organization_id=self.organization_id,
        )

        if self._has_facts():
            # Use canonical facts for AR/AP portions
            ar_data = canonical_queries.get_ar_aging(self.db, self.organization_id)
            ap_data = canonical_queries.get_ap_aging(self.db, self.organization_id)

            report.current_assets = ar_data["ar_total"]
            report.current_liabilities = ap_data["ap_total"]

            # Still need account-based data for equity and other accounts
            accounts = self.db.query(Account).filter(
                Account.organization_id == self.organization_id
            ).all()

            for account in accounts:
                if account.account_type == AccountType.EQUITY:
                    txns = self.db.query(Transaction).filter(
                        Transaction.account_id == account.id,
                        Transaction.transaction_date <= as_of_date,
                    ).all()
                    balance = sum((t.total_amount for t in txns), Decimal("0.00"))
                    report.total_equity += balance
                    report.equity_by_account.append({
                        "account_id": str(account.id),
                        "account_name": account.name,
                        "account_code": account.code,
                        "balance": float(balance),
                    })

            logger.debug("Balance sheet generated from canonical facts + accounts")
        else:
            # Fallback: pure account-based calculation
            accounts = self.db.query(Account).filter(
                Account.organization_id == self.organization_id
            ).all()

            for account in accounts:
                txns = self.db.query(Transaction).filter(
                    Transaction.account_id == account.id,
                    Transaction.transaction_date <= as_of_date,
                ).all()

                balance = sum((t.total_amount for t in txns), Decimal("0.00"))

                account_info = {
                    "account_id": str(account.id),
                    "account_name": account.name,
                    "account_code": account.code,
                    "balance": float(balance),
                }

                if account.account_type == AccountType.ASSET:
                    report.current_assets += balance
                    report.assets_by_account.append(account_info)
                elif account.account_type == AccountType.LIABILITY:
                    report.current_liabilities += balance
                    report.liabilities_by_account.append(account_info)
                elif account.account_type == AccountType.EQUITY:
                    report.total_equity += balance
                    report.equity_by_account.append(account_info)

            logger.debug("Balance sheet generated from raw transactions")

        report.calculate_totals()

        logger.info(
            f"Balance Sheet generated: "
            f"Assets={report.total_assets}, "
            f"Liabilities={report.total_liabilities}, "
            f"Equity={report.total_equity}, "
            f"Balanced={report.is_balanced}"
        )

        return report

    def generate_cash_flow(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[List[str]] = None,
    ) -> CashFlowStatement:
        """
        Generate Cash Flow statement.

        Uses canonical facts for cash movements when available.
        """
        logger.info(
            f"Generating Cash Flow Statement for {self.organization_id} "
            f"({start_date} to {end_date})"
        )

        report = CashFlowStatement(
            period_start=start_date,
            period_end=end_date,
            organization_id=self.organization_id,
        )

        if self._has_facts():
            # Canonical facts path
            cash = canonical_queries.get_cash_movements(
                self.db, self.organization_id, start_date, end_date
            )
            report.operating_cash_flow = cash["net_cash_flow"]
            report.net_income = cash["cash_in"] - cash["cash_out"]
            logger.debug("Cash flow generated from canonical facts")
        else:
            # Fallback: derive from P&L
            pl_report = self.generate_profit_loss(start_date, end_date)
            report.net_income = pl_report.net_income
            report.operating_cash_flow = report.net_income
            logger.debug("Cash flow generated from raw transactions via P&L")

        report.calculate_flows()

        logger.info(
            f"Cash Flow Statement generated: "
            f"Operating CF={report.operating_cash_flow}, "
            f"Net CF={report.net_cash_flow}"
        )

        return report

    def generate_trial_balance(
        self,
        as_of_date: Optional[date] = None,
        account_ids: Optional[List[str]] = None,
    ) -> dict:
        """
        Generate Trial Balance.

        Lists all accounts with their balances as of a date.
        Trial balance remains account-based (not bucket-based).
        """
        if as_of_date is None:
            as_of_date = date.today()

        logger.info(
            f"Generating Trial Balance for {self.organization_id} "
            f"as of {as_of_date}"
        )

        accounts = self.db.query(Account).filter(
            Account.organization_id == self.organization_id
        ).all()

        trial_balance = {
            "as_of_date": as_of_date.isoformat(),
            "accounts": [],
            "total_debits": 0.0,
            "total_credits": 0.0,
        }

        for account in accounts:
            txns = self.db.query(Transaction).filter(
                Transaction.account_id == account.id,
                Transaction.transaction_date <= as_of_date,
            ).all()

            balance = sum((t.total_amount for t in txns), Decimal("0.00"))

            if balance != 0:
                trial_balance["accounts"].append({
                    "account_id": str(account.id),
                    "account_code": account.code,
                    "account_name": account.name,
                    "account_type": account.account_type.value,
                    "balance": float(balance),
                })

                if balance > 0:
                    trial_balance["total_debits"] += float(balance)
                else:
                    trial_balance["total_credits"] += abs(float(balance))

        logger.info(
            f"Trial Balance generated: "
            f"Debits={trial_balance['total_debits']}, "
            f"Credits={trial_balance['total_credits']}"
        )

        return trial_balance
