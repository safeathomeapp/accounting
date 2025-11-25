"""Report currency conversion service.

Converts financial reports from one currency to another.
"""

from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional
from copy import deepcopy

from backend.reporting.models import (
    ProfitLossReport, BalanceSheet, CashFlowStatement
)
from backend.currency.converter import CurrencyConverter


class ReportCurrencyConverter:
    """Converts financial reports to different currencies."""

    def __init__(self, currency_converter: CurrencyConverter):
        """Initialize report currency converter.

        Args:
            currency_converter: CurrencyConverter instance for conversions
        """
        self.converter = currency_converter

    def convert_profit_loss(
        self,
        report: ProfitLossReport,
        organization_id: UUID,
        target_currency: str,
        conversion_date: datetime,
        decimal_places: int = 2
    ) -> ProfitLossReport:
        """Convert P&L report to target currency.

        Args:
            report: Original ProfitLossReport
            organization_id: Organization UUID
            target_currency: Target currency code
            conversion_date: Date for rate lookup
            decimal_places: Decimal places for amounts

        Returns:
            New ProfitLossReport in target currency

        Raises:
            ValueError: If conversion rate not found
        """
        # Create copy to avoid modifying original
        converted = deepcopy(report)

        # Monetary fields to convert
        fields_to_convert = [
            "revenue", "other_income", "total_income",
            "cost_of_goods_sold", "gross_profit",
            "operating_expenses", "operating_income",
            "interest_expense", "interest_income", "tax_expense",
            "net_income"
        ]

        # Convert each field
        for field_name in fields_to_convert:
            original_amount = float(getattr(report, field_name))
            converted_amount, _ = self.converter.convert_amount_at_date(
                organization_id,
                original_amount,
                report.currency,
                target_currency,
                conversion_date,
                decimal_places=decimal_places
            )
            setattr(converted, field_name, Decimal(str(converted_amount)))

        # Convert breakdowns
        converted.by_period = self._convert_breakdown_list(
            report.by_period, organization_id,
            report.currency, target_currency,
            conversion_date, decimal_places
        )
        converted.by_category = self._convert_breakdown_list(
            report.by_category, organization_id,
            report.currency, target_currency,
            conversion_date, decimal_places
        )
        converted.by_account = self._convert_breakdown_list(
            report.by_account, organization_id,
            report.currency, target_currency,
            conversion_date, decimal_places
        )

        # Update metadata
        converted.currency = target_currency
        converted.generated_at = datetime.now(timezone.utc)

        return converted

    def convert_balance_sheet(
        self,
        report: BalanceSheet,
        organization_id: UUID,
        target_currency: str,
        conversion_date: datetime,
        decimal_places: int = 2
    ) -> BalanceSheet:
        """Convert Balance Sheet report to target currency.

        Args:
            report: Original BalanceSheet
            organization_id: Organization UUID
            target_currency: Target currency code
            conversion_date: Date for rate lookup
            decimal_places: Decimal places for amounts

        Returns:
            New BalanceSheet in target currency

        Raises:
            ValueError: If conversion rate not found
        """
        # Create copy to avoid modifying original
        converted = deepcopy(report)

        # Monetary fields to convert
        fields_to_convert = [
            "current_assets", "fixed_assets", "other_assets", "total_assets",
            "current_liabilities", "long_term_liabilities", "other_liabilities",
            "total_liabilities",
            "contributed_capital", "retained_earnings", "other_equity",
            "total_equity"
        ]

        # Convert each field
        for field_name in fields_to_convert:
            original_amount = float(getattr(report, field_name))
            converted_amount, _ = self.converter.convert_amount_at_date(
                organization_id,
                original_amount,
                report.currency,
                target_currency,
                conversion_date,
                decimal_places=decimal_places
            )
            setattr(converted, field_name, Decimal(str(converted_amount)))

        # Convert breakdowns
        converted.assets_by_account = self._convert_breakdown_list(
            report.assets_by_account, organization_id,
            report.currency, target_currency,
            conversion_date, decimal_places
        )
        converted.liabilities_by_account = self._convert_breakdown_list(
            report.liabilities_by_account, organization_id,
            report.currency, target_currency,
            conversion_date, decimal_places
        )
        converted.equity_by_account = self._convert_breakdown_list(
            report.equity_by_account, organization_id,
            report.currency, target_currency,
            conversion_date, decimal_places
        )

        # Update metadata
        converted.currency = target_currency
        converted.generated_at = datetime.now(timezone.utc)

        # Recalculate to ensure balance check is correct
        converted.calculate_totals()

        return converted

    def convert_cash_flow(
        self,
        report: CashFlowStatement,
        organization_id: UUID,
        target_currency: str,
        conversion_date: datetime,
        decimal_places: int = 2
    ) -> CashFlowStatement:
        """Convert Cash Flow report to target currency.

        Args:
            report: Original CashFlowStatement
            organization_id: Organization UUID
            target_currency: Target currency code
            conversion_date: Date for rate lookup
            decimal_places: Decimal places for amounts

        Returns:
            New CashFlowStatement in target currency

        Raises:
            ValueError: If conversion rate not found
        """
        # Create copy to avoid modifying original
        converted = deepcopy(report)

        # Monetary fields to convert
        fields_to_convert = [
            "net_income", "depreciation_amortization",
            "changes_in_working_capital", "operating_cash_flow",
            "purchase_fixed_assets", "sale_fixed_assets",
            "purchases_investments", "investing_cash_flow",
            "debt_proceeds", "debt_repayment", "equity_issuance",
            "dividends_paid", "financing_cash_flow",
            "net_cash_flow", "beginning_cash", "ending_cash"
        ]

        # Convert each field
        for field_name in fields_to_convert:
            original_amount = float(getattr(report, field_name))
            converted_amount, _ = self.converter.convert_amount_at_date(
                organization_id,
                original_amount,
                report.currency,
                target_currency,
                conversion_date,
                decimal_places=decimal_places
            )
            setattr(converted, field_name, Decimal(str(converted_amount)))

        # Convert breakdowns
        converted.by_period = self._convert_breakdown_list(
            report.by_period, organization_id,
            report.currency, target_currency,
            conversion_date, decimal_places
        )
        converted.by_account = self._convert_breakdown_list(
            report.by_account, organization_id,
            report.currency, target_currency,
            conversion_date, decimal_places
        )

        # Update metadata
        converted.currency = target_currency
        converted.generated_at = datetime.now(timezone.utc)

        # Recalculate flows
        converted.calculate_flows()

        return converted

    def _convert_breakdown_list(
        self,
        breakdown_list: list,
        organization_id: UUID,
        source_currency: str,
        target_currency: str,
        conversion_date: datetime,
        decimal_places: int
    ) -> list:
        """Convert a list of breakdown dictionaries.

        Args:
            breakdown_list: List of breakdown dicts with 'amount' or 'value' key
            organization_id: Organization UUID
            source_currency: Source currency code
            target_currency: Target currency code
            conversion_date: Date for rate lookup
            decimal_places: Decimal places for rounding

        Returns:
            New list with converted amounts
        """
        if not breakdown_list:
            return []

        converted_list = []
        for item in breakdown_list:
            converted_item = deepcopy(item)

            # Try to find and convert amount fields
            for key in ["amount", "value", "total"]:
                if key in item:
                    original = float(item[key])
                    converted_amount, _ = self.converter.convert_amount_at_date(
                        organization_id,
                        original,
                        source_currency,
                        target_currency,
                        conversion_date,
                        decimal_places=decimal_places
                    )
                    converted_item[key] = converted_amount
                    break

            converted_list.append(converted_item)

        return converted_list

    def consolidate_multi_currency(
        self,
        reports_by_currency: Dict[str, Any],
        organization_id: UUID,
        target_currency: str,
        conversion_date: datetime,
        decimal_places: int = 2
    ) -> Dict[str, Any]:
        """Consolidate reports from multiple currencies to one.

        Args:
            reports_by_currency: Dict of {currency: report_object}
            organization_id: Organization UUID
            target_currency: Target currency code
            conversion_date: Date for rate lookup
            decimal_places: Decimal places for rounding

        Returns:
            Dictionary with consolidated data
        """
        consolidated = {
            "source_currency_count": len(reports_by_currency),
            "target_currency": target_currency,
            "conversion_date": conversion_date.isoformat(),
            "reports": {}
        }

        for currency, report in reports_by_currency.items():
            if currency == target_currency:
                # Already in target currency
                consolidated["reports"][currency] = report
            else:
                # Convert based on report type
                if isinstance(report, ProfitLossReport):
                    converted = self.convert_profit_loss(
                        report, organization_id, target_currency,
                        conversion_date, decimal_places
                    )
                elif isinstance(report, BalanceSheet):
                    converted = self.convert_balance_sheet(
                        report, organization_id, target_currency,
                        conversion_date, decimal_places
                    )
                elif isinstance(report, CashFlowStatement):
                    converted = self.convert_cash_flow(
                        report, organization_id, target_currency,
                        conversion_date, decimal_places
                    )
                else:
                    # Unknown report type
                    converted = report

                consolidated["reports"][currency] = converted

        return consolidated

    def get_conversion_summary(
        self,
        original_report: Any,
        converted_report: Any,
        target_currency: str
    ) -> Dict[str, Any]:
        """Get summary of conversion changes.

        Args:
            original_report: Original report object
            converted_report: Converted report object
            target_currency: Target currency code

        Returns:
            Dictionary with conversion summary
        """
        return {
            "source_currency": original_report.currency,
            "target_currency": target_currency,
            "original_generated_at": original_report.generated_at.isoformat(),
            "converted_generated_at": converted_report.generated_at.isoformat(),
            "report_type": converted_report.__class__.__name__,
            "conversion_timestamp": datetime.now(timezone.utc).isoformat()
        }
