"""Financial report generation engine."""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional
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
from .models import (
    ProfitLossReport,
    BalanceSheet,
    CashFlowStatement,
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate financial reports from synced accounting data."""

    def __init__(self, db: Session, organization_id: UUID):
        """
        Initialize report generator.

        Args:
            db: Database session
            organization_id: Organization UUID
        """
        self.db = db
        self.organization_id = organization_id

        # Verify organization exists
        self.org = self.db.query(Organization).filter_by(
            id=organization_id
        ).first()

        if not self.org:
            raise ValueError(f"Organization not found: {organization_id}")

    def get_transactions(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[List[str]] = None,
        transaction_types: Optional[List[str]] = None,
    ) -> List[Transaction]:
        """
        Get transactions for date range.

        Args:
            start_date: Start date
            end_date: End date
            account_ids: Optional filter by account IDs
            transaction_types: Optional filter by transaction types

        Returns:
            List of transactions
        """
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
    ) -> ProfitLossReport:
        """
        Generate Profit & Loss statement.

        Algorithm:
        1. Sum revenue from INCOME type accounts
        2. Sum cost of goods sold from COGS accounts
        3. Sum operating expenses from EXPENSE accounts
        4. Calculate gross profit = Revenue - COGS
        5. Calculate operating income = Gross profit - Operating expenses
        6. Add/subtract other income and expenses
        7. Apply taxes
        8. Calculate net income

        Args:
            start_date: Start date for report
            end_date: End date for report

        Returns:
            ProfitLossReport with calculated values
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

        # Get all revenue accounts
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

        # Get expense accounts
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

        # Calculate totals
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
    ) -> BalanceSheet:
        """
        Generate Balance Sheet as of date.

        Algorithm:
        1. Get all ASSET type accounts and sum balances
        2. Get all LIABILITY type accounts and sum balances
        3. Get all EQUITY type accounts and sum balances
        4. Verify: Total Assets = Total Liabilities + Total Equity

        Args:
            as_of_date: Date for balance sheet (default: today)

        Returns:
            BalanceSheet with account balances
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

        # Get all accounts for this organization
        accounts = self.db.query(Account).filter(
            Account.organization_id == self.organization_id
        ).all()

        # Group accounts by type and calculate balances
        for account in accounts:
            # Get transactions up to and including as_of_date
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

        # Calculate totals and verify balance
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
    ) -> CashFlowStatement:
        """
        Generate Cash Flow statement.

        Algorithm:
        1. Get net income from P&L
        2. Add back depreciation (from depreciation expense accounts)
        3. Calculate working capital changes
        4. Get cash from investing activities (asset purchases/sales)
        5. Get cash from financing activities (debt/equity changes)
        6. Calculate net cash change

        Args:
            start_date: Start date for period
            end_date: End date for period

        Returns:
            CashFlowStatement with calculated cash flows
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

        # Get net income from P&L
        pl_report = self.generate_profit_loss(start_date, end_date)
        report.net_income = pl_report.net_income

        # Simplified cash flow: use net income as operating cash flow
        # In production, would calculate working capital changes separately
        report.operating_cash_flow = report.net_income

        # Calculate flows
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
    ) -> dict:
        """
        Generate Trial Balance.

        Lists all accounts with their balances as of a date.

        Args:
            as_of_date: Date for trial balance (default: today)

        Returns:
            Dict with account balances
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
            # Get balance
            txns = self.db.query(Transaction).filter(
                Transaction.account_id == account.id,
                Transaction.transaction_date <= as_of_date,
            ).all()

            balance = sum((t.total_amount for t in txns), Decimal("0.00"))

            # Debit or credit based on account type
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
