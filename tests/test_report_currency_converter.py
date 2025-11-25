"""Tests for report currency conversion service.

Tests for ReportCurrencyConverter including P&L, Balance Sheet,
and Cash Flow conversions.
"""

import pytest
from uuid import uuid4
from datetime import date, datetime, timezone
from decimal import Decimal

from backend.reporting.models import (
    ProfitLossReport, BalanceSheet, CashFlowStatement
)
from backend.currency.converter import CurrencyConverter
from backend.currency.rates import ExchangeRateManager
from backend.currency.report_converter import ReportCurrencyConverter


class TestReportCurrencyConverter:
    """Tests for ReportCurrencyConverter."""

    def setup_method(self):
        """Set up for each test."""
        self.rate_manager = ExchangeRateManager()
        self.converter = CurrencyConverter(self.rate_manager)
        self.report_converter = ReportCurrencyConverter(self.converter)
        self.org_id = uuid4()
        self.today = datetime.now(timezone.utc)

        # Set up exchange rates
        self.rate_manager.set_rate(
            self.org_id, "USD", "EUR", 0.92, self.today, source="provider"
        )
        self.rate_manager.set_rate(
            self.org_id, "EUR", "USD", 1.09, self.today, source="provider"
        )

    def test_convert_profit_loss_to_eur(self):
        """Test converting P&L report from USD to EUR."""
        # Create USD P&L report
        report = ProfitLossReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=self.org_id,
            revenue=Decimal("100000.00"),
            other_income=Decimal("5000.00"),
            cost_of_goods_sold=Decimal("40000.00"),
            operating_expenses=Decimal("30000.00"),
            interest_expense=Decimal("2000.00"),
            tax_expense=Decimal("10000.00"),
            currency="USD"
        )
        report.calculate_totals()

        # Convert to EUR
        converted = self.report_converter.convert_profit_loss(
            report, self.org_id, "EUR", self.today
        )

        # Check conversion (USD to EUR at 0.92)
        assert converted.revenue == Decimal("92000.00")
        assert converted.other_income == Decimal("4600.00")
        assert converted.cost_of_goods_sold == Decimal("36800.00")
        assert converted.currency == "EUR"

    def test_convert_balance_sheet_to_eur(self):
        """Test converting Balance Sheet from USD to EUR."""
        # Create USD Balance Sheet
        report = BalanceSheet(
            as_of_date=date(2025, 12, 31),
            organization_id=self.org_id,
            current_assets=Decimal("50000.00"),
            fixed_assets=Decimal("100000.00"),
            current_liabilities=Decimal("30000.00"),
            long_term_liabilities=Decimal("50000.00"),
            contributed_capital=Decimal("70000.00"),
            currency="USD"
        )
        report.calculate_totals()

        # Convert to EUR
        converted = self.report_converter.convert_balance_sheet(
            report, self.org_id, "EUR", self.today
        )

        # Check conversion (USD to EUR at 0.92)
        assert converted.current_assets == Decimal("46000.00")
        assert converted.fixed_assets == Decimal("92000.00")
        assert converted.current_liabilities == Decimal("27600.00")
        assert converted.currency == "EUR"

    def test_convert_cash_flow_to_EUR(self):
        """Test converting Cash Flow report from USD to EUR."""
        # Create USD Cash Flow report
        report = CashFlowStatement(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=self.org_id,
            net_income=Decimal("20000.00"),
            depreciation_amortization=Decimal("5000.00"),
            purchase_fixed_assets=Decimal("15000.00"),
            beginning_cash=Decimal("10000.00"),
            currency="USD"
        )
        report.calculate_flows()

        # Convert to EUR
        converted = self.report_converter.convert_cash_flow(
            report, self.org_id, "EUR", self.today
        )

        # Check conversion (USD to EUR at 0.92)
        assert converted.net_income == Decimal("18400.00")
        assert converted.depreciation_amortization == Decimal("4600.00")
        assert converted.purchase_fixed_assets == Decimal("13800.00")
        assert converted.currency == "EUR"

    def test_conversion_preserves_structure(self):
        """Test that conversion preserves report structure."""
        report = ProfitLossReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=self.org_id,
            revenue=Decimal("100000.00"),
            currency="USD"
        )
        report.calculate_totals()

        converted = self.report_converter.convert_profit_loss(
            report, self.org_id, "EUR", self.today
        )

        # Structure should be preserved
        assert converted.period_start == report.period_start
        assert converted.period_end == report.period_end
        assert converted.organization_id == report.organization_id
        assert converted.generated_at != report.generated_at  # Updated

    def test_conversion_timestamp_updated(self):
        """Test that conversion updates generated_at timestamp."""
        report = ProfitLossReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=self.org_id,
            revenue=Decimal("100000.00"),
            currency="USD",
            generated_at=datetime(2025, 1, 1, tzinfo=timezone.utc)
        )

        original_timestamp = report.generated_at
        converted = self.report_converter.convert_profit_loss(
            report, self.org_id, "EUR", self.today
        )

        # Timestamp should be updated to approximately now
        assert converted.generated_at > original_timestamp
        assert (converted.generated_at - self.today).total_seconds() < 10

    def test_consolidate_multi_currency(self):
        """Test consolidating reports from multiple currencies."""
        # Create reports in USD and EUR
        usd_report = ProfitLossReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=self.org_id,
            revenue=Decimal("100000.00"),
            currency="USD"
        )

        eur_report = ProfitLossReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=self.org_id,
            revenue=Decimal("92000.00"),
            currency="EUR"
        )

        reports = {"USD": usd_report, "EUR": eur_report}

        # Consolidate to GBP (need to set rates first)
        self.rate_manager.set_rate(
            self.org_id, "USD", "GBP", 0.79, self.today, source="provider"
        )
        self.rate_manager.set_rate(
            self.org_id, "EUR", "GBP", 0.86, self.today, source="provider"
        )

        consolidated = self.report_converter.consolidate_multi_currency(
            reports, self.org_id, "GBP", self.today
        )

        assert consolidated["source_currency_count"] == 2
        assert consolidated["target_currency"] == "GBP"
        assert "USD" in consolidated["reports"]
        assert "EUR" in consolidated["reports"]

    def test_conversion_with_breakdown_lists(self):
        """Test that breakdown lists are converted."""
        # Create P&L with breakdown
        report = ProfitLossReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=self.org_id,
            revenue=Decimal("100000.00"),
            currency="USD",
            by_account=[
                {"account_code": "1000", "account_name": "Sales", "amount": 100000.00}
            ]
        )

        converted = self.report_converter.convert_profit_loss(
            report, self.org_id, "EUR", self.today
        )

        # Breakdown amounts should be converted (100000 * 0.92 = 92000)
        assert len(converted.by_account) == 1
        assert converted.by_account[0]["amount"] == 92000.00

    def test_balance_sheet_recalculated_after_conversion(self):
        """Test that balance sheet totals are recalculated after conversion."""
        report = BalanceSheet(
            as_of_date=date(2025, 12, 31),
            organization_id=self.org_id,
            current_assets=Decimal("50000.00"),
            fixed_assets=Decimal("100000.00"),
            current_liabilities=Decimal("30000.00"),
            long_term_liabilities=Decimal("50000.00"),
            contributed_capital=Decimal("70000.00"),
            currency="USD"
        )
        report.calculate_totals()

        converted = self.report_converter.convert_balance_sheet(
            report, self.org_id, "EUR", self.today
        )

        # Totals should be recalculated
        assert converted.total_assets == (
            converted.current_assets +
            converted.fixed_assets +
            converted.other_assets
        )

    def test_get_conversion_summary(self):
        """Test getting conversion summary."""
        original = ProfitLossReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=self.org_id,
            revenue=Decimal("100000.00"),
            currency="USD"
        )

        converted = ProfitLossReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=self.org_id,
            revenue=Decimal("92000.00"),
            currency="EUR"
        )

        summary = self.report_converter.get_conversion_summary(
            original, converted, "EUR"
        )

        assert summary["source_currency"] == "USD"
        assert summary["target_currency"] == "EUR"
        assert summary["report_type"] == "ProfitLossReport"
        assert "conversion_timestamp" in summary
