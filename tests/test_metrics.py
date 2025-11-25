"""Tests for financial metrics and KPI calculations."""

import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal

from backend.analytics.metrics import MetricsCalculator
from backend.models.analytics import MetricType


class TestMetricsCalculator:
    """Tests for MetricsCalculator."""

    def setup_method(self):
        """Set up for each test."""
        self.calculator = MetricsCalculator()
        self.org_id = uuid4()

    def test_calculate_profit_margin(self):
        """Test profit margin calculation."""
        metric = self.calculator.calculate_profit_margin(
            self.org_id, date(2024, 12, 31), Decimal("50000"), Decimal("200000")
        )
        assert metric.metric_value == Decimal("25")  # 50000/200000 * 100

    def test_profit_margin_with_zero_revenue(self):
        """Test profit margin with zero revenue."""
        metric = self.calculator.calculate_profit_margin(
            self.org_id, date(2024, 12, 31), Decimal("50000"), Decimal("0")
        )
        assert metric.metric_value == Decimal("0")

    def test_profit_margin_with_benchmark(self):
        """Test profit margin comparison to benchmark."""
        metric = self.calculator.calculate_profit_margin(
            self.org_id, date(2024, 12, 31),
            Decimal("50000"), Decimal("200000"),
            benchmark=Decimal("20")
        )
        assert metric.vs_benchmark == Decimal("5")  # 25 - 20

    def test_calculate_current_ratio(self):
        """Test current ratio calculation."""
        current, quick = self.calculator.calculate_liquidity_ratio(
            self.org_id, date(2024, 12, 31),
            Decimal("100000"), Decimal("50000")
        )
        assert current.metric_value == Decimal("2")  # 100000/50000

    def test_calculate_quick_ratio(self):
        """Test quick ratio calculation."""
        current, quick = self.calculator.calculate_liquidity_ratio(
            self.org_id, date(2024, 12, 31),
            Decimal("100000"), Decimal("50000"),
            quick_assets=Decimal("60000")
        )
        assert quick.metric_value == Decimal("1.2")  # 60000/50000

    def test_calculate_growth_rate(self):
        """Test growth rate calculation."""
        metric = self.calculator.calculate_growth_rate(
            self.org_id, date(2024, 12, 31),
            Decimal("120000"), Decimal("100000")
        )
        assert metric.metric_value == Decimal("20")  # (120000-100000)/100000 * 100

    def test_calculate_roa(self):
        """Test Return on Assets calculation."""
        metric = self.calculator.calculate_return_on_assets(
            self.org_id, date(2024, 12, 31),
            Decimal("50000"), Decimal("500000")
        )
        assert metric.metric_value == Decimal("10")  # 50000/500000 * 100

    def test_calculate_debt_to_equity(self):
        """Test Debt-to-Equity ratio."""
        metric = self.calculator.calculate_debt_to_equity(
            self.org_id, date(2024, 12, 31),
            Decimal("100000"), Decimal("200000")
        )
        assert metric.metric_value == Decimal("0.5")  # 100000/200000

    def test_create_kpi(self):
        """Test KPI creation."""
        kpi = self.calculator.create_kpi(
            self.org_id, "Days Sales Outstanding",
            "DSO", date(2024, 12, 31),
            Decimal("45"), Decimal("30"),
            unit="days"
        )
        assert kpi.name == "Days Sales Outstanding"
        assert kpi.current_value == Decimal("45")

    def test_kpi_status_vs_target(self):
        """Test KPI status vs target calculation."""
        kpi = self.calculator.create_kpi(
            self.org_id, "Revenue", "REV",
            date(2024, 12, 31),
            Decimal("120000"), Decimal("100000")
        )
        # (120000 - 100000) / 100000 = 0.2
        assert kpi.status_vs_target == Decimal("0.2")

    def test_get_metric(self):
        """Test retrieving a metric."""
        self.calculator.calculate_profit_margin(
            self.org_id, date(2024, 12, 31), Decimal("50000"), Decimal("200000")
        )
        metric = self.calculator.get_metric(
            self.org_id, MetricType.NET_PROFIT_MARGIN, date(2024, 12, 31)
        )
        assert metric is not None
        assert metric.metric_value == Decimal("25")

    def test_get_kpi(self):
        """Test retrieving a KPI."""
        self.calculator.create_kpi(
            self.org_id, "DSO", "DSO",
            date(2024, 12, 31), Decimal("45")
        )
        kpi = self.calculator.get_kpi(self.org_id, "DSO", date(2024, 12, 31))
        assert kpi is not None
        assert kpi.current_value == Decimal("45")

    def test_metrics_history(self):
        """Test retrieving metrics history."""
        self.calculator.calculate_profit_margin(
            self.org_id, date(2024, 1, 31), Decimal("40000"), Decimal("200000")
        )
        self.calculator.calculate_profit_margin(
            self.org_id, date(2024, 2, 29), Decimal("50000"), Decimal("200000")
        )

        history = self.calculator.get_metrics_history(
            self.org_id, MetricType.NET_PROFIT_MARGIN,
            date(2024, 1, 1), date(2024, 2, 28)
        )
        assert len(history) == 1

    def test_kpi_history(self):
        """Test retrieving KPI history."""
        self.calculator.create_kpi(
            self.org_id, "DSO", "DSO",
            date(2024, 1, 31), Decimal("50")
        )
        self.calculator.create_kpi(
            self.org_id, "DSO", "DSO",
            date(2024, 2, 29), Decimal("45")
        )

        history = self.calculator.get_kpi_history(
            self.org_id, "DSO",
            date(2024, 1, 1), date(2024, 2, 28)
        )
        assert len(history) == 1

    def test_organization_isolation(self):
        """Test metrics isolated between organizations."""
        org2_id = uuid4()

        self.calculator.calculate_profit_margin(
            self.org_id, date(2024, 12, 31), Decimal("50000"), Decimal("200000")
        )
        self.calculator.calculate_profit_margin(
            org2_id, date(2024, 12, 31), Decimal("60000"), Decimal("300000")
        )

        org1_metric = self.calculator.get_metric(
            self.org_id, MetricType.NET_PROFIT_MARGIN, date(2024, 12, 31)
        )
        org2_metric = self.calculator.get_metric(
            org2_id, MetricType.NET_PROFIT_MARGIN, date(2024, 12, 31)
        )

        assert org1_metric.metric_value == Decimal("25")
        assert org2_metric.metric_value == Decimal("20")

    def test_period_over_period_change(self):
        """Test period-over-period change calculation."""
        metric = self.calculator.calculate_profit_margin(
            self.org_id, date(2024, 12, 31),
            Decimal("50000"), Decimal("200000"),
            previous_margin=Decimal("20")
        )
        assert metric.period_over_period_change == Decimal("5")  # 25 - 20

    def test_annualized_growth_rate(self):
        """Test annualized growth rate for multiple periods."""
        metric = self.calculator.calculate_growth_rate(
            self.org_id, date(2024, 12, 31),
            Decimal("121000"), Decimal("100000"),
            periods=4  # Quarterly growth
        )
        # Should be lower than simple 21% when annualized quarterly growth
        assert metric.metric_value < Decimal("21")
