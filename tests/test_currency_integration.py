"""Integration tests for multi-currency support.

Tests complete workflows combining currency management, exchange rates,
conversion, and report generation.
"""

import pytest
from uuid import uuid4
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

from backend.currency.manager import CurrencyManager
from backend.currency.rates import ExchangeRateManager
from backend.currency.converter import CurrencyConverter
from backend.currency.report_converter import ReportCurrencyConverter
from backend.reporting.models import ProfitLossReport


class TestMultiCurrencyIntegration:
    """Integration tests for multi-currency workflows."""

    def setup_method(self):
        """Set up for each test."""
        self.manager = CurrencyManager()
        self.rate_manager = ExchangeRateManager()
        self.converter = CurrencyConverter(self.rate_manager)
        self.report_converter = ReportCurrencyConverter(self.converter)

        self.org_id = uuid4()
        self.other_org_id = uuid4()
        self.today = datetime.now(timezone.utc)

    def test_complete_workflow_add_currency_set_rate_convert(self):
        """Test complete workflow: add currency → set rate → convert."""
        # Step 1: Add currencies
        usd = self.manager.add_currency(
            self.org_id, "USD", "United States Dollar", "$"
        )
        eur = self.manager.add_currency(
            self.org_id, "EUR", "Euro", "€"
        )

        assert usd.code == "USD"
        assert eur.code == "EUR"

        # Step 2: Set exchange rate
        rate = self.rate_manager.set_rate(
            self.org_id, "USD", "EUR", 0.92, source="provider"
        )

        assert rate.rate == 0.92

        # Step 3: Convert amount using the rate
        converted, rate_used = self.converter.convert_amount(
            self.org_id, 1000.0, "USD", "EUR"
        )

        assert converted == 920.0
        assert rate_used == 0.92

    def test_multi_currency_with_report_conversion(self):
        """Test multi-currency workflow with P&L report conversion."""
        # Setup currencies and rates
        self.manager.add_currency(self.org_id, "USD", "United States Dollar", "$")
        self.manager.add_currency(self.org_id, "EUR", "Euro", "€")

        self.rate_manager.set_rate(
            self.org_id, "USD", "EUR", 0.92, self.today, source="provider"
        )

        # Create USD P&L report
        usd_report = ProfitLossReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            organization_id=self.org_id,
            revenue=Decimal("100000.00"),
            operating_expenses=Decimal("60000.00"),
            currency="USD"
        )
        usd_report.calculate_totals()

        # Convert report to EUR
        eur_report = self.report_converter.convert_profit_loss(
            usd_report, self.org_id, "EUR", self.today
        )

        # Verify conversion
        assert eur_report.revenue == Decimal("92000.00")
        assert eur_report.operating_expenses == Decimal("55200.00")
        assert eur_report.currency == "EUR"

    def test_currency_activation_deactivation_impact(self):
        """Test impact of currency activation/deactivation."""
        # Add currencies
        self.manager.add_currency(self.org_id, "USD", "United States Dollar", "$")
        self.manager.add_currency(self.org_id, "EUR", "Euro", "€")

        # Verify both active
        currencies = self.manager.get_organization_currencies(self.org_id)
        assert len(currencies) == 2

        # Deactivate EUR
        self.manager.deactivate_currency(self.org_id, "EUR")

        # Should only get USD when not including inactive
        active_currencies = self.manager.get_organization_currencies(
            self.org_id, include_inactive=False
        )
        assert len(active_currencies) == 1
        assert active_currencies[0].code == "USD"

        # Should get both when including inactive
        all_currencies = self.manager.get_organization_currencies(
            self.org_id, include_inactive=True
        )
        assert len(all_currencies) == 2

        # Re-activate EUR
        self.manager.activate_currency(self.org_id, "EUR")
        currencies = self.manager.get_organization_currencies(self.org_id)
        assert len(currencies) == 2

    def test_cross_organization_currency_isolation(self):
        """Test that currencies are isolated between organizations."""
        # Add currencies to org 1
        self.manager.add_currency(self.org_id, "USD", "United States Dollar", "$")
        self.manager.add_currency(self.org_id, "EUR", "Euro", "€")

        # Add different currencies to org 2
        self.manager.add_currency(self.other_org_id, "GBP", "British Pound", "£")
        self.manager.add_currency(self.other_org_id, "JPY", "Japanese Yen", "¥")

        # Verify isolation
        org1_currencies = self.manager.get_organization_currencies(self.org_id)
        org2_currencies = self.manager.get_organization_currencies(self.other_org_id)

        assert len(org1_currencies) == 2
        assert len(org2_currencies) == 2

        org1_codes = {c.code for c in org1_currencies}
        org2_codes = {c.code for c in org2_currencies}

        assert org1_codes == {"USD", "EUR"}
        assert org2_codes == {"GBP", "JPY"}
        assert org1_codes.isdisjoint(org2_codes)

        # Verify each org only sees its own rates
        self.rate_manager.set_rate(
            self.org_id, "USD", "EUR", 0.92, source="provider"
        )
        self.rate_manager.set_rate(
            self.other_org_id, "GBP", "JPY", 180.0, source="provider"
        )

        rate1 = self.rate_manager.get_current_rate(self.org_id, "USD", "EUR")
        assert rate1 is not None
        assert rate1.rate == 0.92

        rate2 = self.rate_manager.get_current_rate(self.org_id, "GBP", "JPY")
        assert rate2 is None  # Org 1 doesn't have this rate

    def test_rate_provider_fallback_scenario(self):
        """Test fallback when provider rate unavailable (use manual)."""
        # Setup
        self.manager.add_currency(self.org_id, "USD", "United States Dollar", "$")
        self.manager.add_currency(self.org_id, "EUR", "Euro", "€")

        # Provider rate not available (simulated)
        # Fall back to manual rate
        manual_rate = self.rate_manager.set_manual_rate(
            self.org_id, "USD", "EUR", 0.95
        )

        assert manual_rate.source == "manual"

        # Verify manual rate is used for conversion
        converted, rate_used = self.converter.convert_amount(
            self.org_id, 1000.0, "USD", "EUR"
        )

        assert converted == 950.0
        assert rate_used == 0.95

    def test_historical_rate_usage_scenario(self):
        """Test using historical rates for conversions."""
        # Setup
        self.manager.add_currency(self.org_id, "USD", "United States Dollar", "$")
        self.manager.add_currency(self.org_id, "EUR", "Euro", "€")

        # Set rates for different dates
        past_date = self.today - timedelta(days=30)
        self.rate_manager.set_rate(
            self.org_id, "USD", "EUR", 0.87,
            effective_date=past_date, source="historical"
        )
        self.rate_manager.set_rate(
            self.org_id, "USD", "EUR", 0.92,
            effective_date=self.today, source="provider"
        )

        # Convert using current rate
        current_converted, current_rate = self.converter.convert_amount(
            self.org_id, 1000.0, "USD", "EUR"
        )
        assert current_rate == 0.92
        assert current_converted == 920.0

        # Convert using historical rate
        historical_converted, historical_rate = (
            self.converter.convert_amount_at_date(
                self.org_id, 1000.0, "USD", "EUR", past_date
            )
        )
        assert historical_rate == 0.87
        assert historical_converted == 870.0

    def test_batch_currency_operations(self):
        """Test batch operations across currencies."""
        # Setup
        self.manager.add_currency(self.org_id, "USD", "United States Dollar", "$")
        self.manager.add_currency(self.org_id, "EUR", "Euro", "€")
        self.manager.add_currency(self.org_id, "GBP", "British Pound", "£")

        # Set up rates
        self.rate_manager.set_rate(
            self.org_id, "USD", "EUR", 0.92, source="provider"
        )
        self.rate_manager.set_rate(
            self.org_id, "USD", "GBP", 0.79, source="provider"
        )

        # Batch convert multiple amounts
        amounts = [
            (100.0, "USD", "EUR"),
            (200.0, "USD", "GBP"),
            (300.0, "USD", "EUR"),
        ]

        results = self.converter.batch_convert(
            self.org_id, amounts, "USD"
        )

        assert len(results) == 3
        assert results[0][0] == 92.0      # 100 USD → EUR
        assert results[1][0] == 158.0     # 200 USD → GBP
        assert results[2][0] == 276.0     # 300 USD → EUR

    def test_conversion_history_tracking(self):
        """Test tracking conversion history across operations."""
        # Setup
        self.manager.add_currency(self.org_id, "USD", "United States Dollar", "$")
        self.manager.add_currency(self.org_id, "EUR", "Euro", "€")

        self.rate_manager.set_rate(
            self.org_id, "USD", "EUR", 0.92, self.today, source="provider"
        )

        # Perform multiple conversions
        tx_id_1 = uuid4()
        tx_id_2 = uuid4()

        self.converter.convert_with_history(
            self.org_id, 1000.0, "USD", "EUR", self.today, transaction_id=tx_id_1
        )

        self.converter.convert_with_history(
            self.org_id, 500.0, "USD", "EUR", self.today, transaction_id=tx_id_2
        )

        # Verify history
        all_history = self.converter.get_conversion_history(self.org_id)
        assert len(all_history) == 2

        tx1_history = self.converter.get_conversion_history(
            self.org_id, transaction_id=tx_id_1
        )
        assert len(tx1_history) == 1
        assert tx1_history[0].source_amount == 1000.0
        assert tx1_history[0].target_amount == 920.0
