"""Tests for BI dashboard data provider.

Tests dashboard widget creation, data aggregation, and comparisons.
"""

import pytest
import json
from uuid import uuid4
from datetime import date
from decimal import Decimal

from backend.analytics.dashboard import DashboardProvider
from backend.models.analytics import (
    FinancialMetric, MetricType, Forecast, ForecastType, ForecastMethod,
    TrendAnalysis, TrendDirection, KPI
)


class TestDashboardProvider:
    """Tests for DashboardProvider."""

    def setup_method(self):
        """Set up for each test."""
        self.provider = DashboardProvider()
        self.org_id = uuid4()

    def test_create_widget(self):
        """Test basic widget creation."""
        widget = self.provider.create_widget(
            self.org_id, "revenue_trend", "Revenue Trend", "chart"
        )
        assert widget.title == "Revenue Trend"
        assert widget.widget_type == "chart"
        assert widget.data_source == "revenue_trend"

    def test_create_kpi_widget(self):
        """Test KPI widget creation."""
        widget = self.provider.create_kpi_widget(
            self.org_id, "profit_margin", "Profit Margin",
            Decimal("25"), Decimal("20"), unit="%"
        )
        assert widget.widget_type == "kpi"
        assert widget.data_source == "profit_margin"
        assert widget.size == "small"

    def test_create_chart_widget(self):
        """Test chart widget creation."""
        datasets = [{"label": "Revenue", "data": [100, 110, 120]}]
        widget = self.provider.create_chart_widget(
            self.org_id, "monthly_revenue", "Monthly Revenue",
            "line", ["Jan", "Feb", "Mar"], datasets, y_axis_label="Amount"
        )
        assert widget.widget_type == "chart"
        assert widget.size == "large"

        # Parse config to verify structure
        config = json.loads(widget.config)
        assert config["chart_type"] == "line"
        assert config["labels"] == ["Jan", "Feb", "Mar"]

    def test_get_widget(self):
        """Test retrieving a widget."""
        self.provider.create_widget(
            self.org_id, "test_widget", "Test Widget", "kpi"
        )
        widget = self.provider.get_widget(self.org_id, "test_widget")
        assert widget is not None
        assert widget.data_source == "test_widget"

    def test_get_dashboard_widgets(self):
        """Test retrieving all dashboard widgets."""
        self.provider.create_widget(
            self.org_id, "widget1", "Widget 1", "kpi", position=0
        )
        self.provider.create_widget(
            self.org_id, "widget2", "Widget 2", "chart", position=1
        )
        widgets = self.provider.get_dashboard_widgets(self.org_id)
        assert len(widgets) == 2

    def test_widget_position_sorting(self):
        """Test widgets are sorted by position."""
        self.provider.create_widget(
            self.org_id, "widget1", "Widget 1", "kpi", position=1
        )
        self.provider.create_widget(
            self.org_id, "widget2", "Widget 2", "kpi", position=0
        )
        widgets = self.provider.get_dashboard_widgets(self.org_id)
        # Should be sorted by position
        assert widgets[0].data_source == "widget2"
        assert widgets[1].data_source == "widget1"

    def test_metric_summary_average(self):
        """Test metric summary with average aggregation."""
        metrics = [
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 1, 1), metric_value=Decimal("20")
            ),
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 2, 1), metric_value=Decimal("24")
            ),
        ]
        summary = self.provider.create_metric_summary(metrics)
        assert summary["count"] == 2
        assert summary["value"] == Decimal("22")
        assert summary["min"] == Decimal("20")
        assert summary["max"] == Decimal("24")

    def test_metric_summary_sum(self):
        """Test metric summary with sum aggregation."""
        metrics = [
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 1, 1), metric_value=Decimal("1000")
            ),
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 2, 1), metric_value=Decimal("2000")
            ),
        ]
        summary = self.provider.create_metric_summary(metrics, "sum")
        assert summary["value"] == Decimal("3000")

    def test_metric_summary_min_max(self):
        """Test metric summary with min/max aggregation."""
        metrics = [
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 1, 1), metric_value=Decimal("50")
            ),
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 2, 1), metric_value=Decimal("30")
            ),
        ]
        summary_min = self.provider.create_metric_summary(metrics, "min")
        summary_max = self.provider.create_metric_summary(metrics, "max")

        assert summary_min["value"] == Decimal("30")
        assert summary_max["value"] == Decimal("50")

    def test_forecast_summary(self):
        """Test forecast summary creation."""
        forecasts = [
            Forecast(
                organization_id=self.org_id, forecast_type=ForecastType.REVENUE,
                method=ForecastMethod.LINEAR_REGRESSION, period_start=date(2024, 1, 1),
                period_end=date(2024, 2, 1), base_value=Decimal("10000"),
                forecasted_value=Decimal("11000"), accuracy_score=0.95
            ),
            Forecast(
                organization_id=self.org_id, forecast_type=ForecastType.REVENUE,
                method=ForecastMethod.LINEAR_REGRESSION, period_start=date(2024, 2, 1),
                period_end=date(2024, 3, 1), base_value=Decimal("11000"),
                forecasted_value=Decimal("12100"), accuracy_score=0.92
            ),
        ]
        summary = self.provider.create_forecast_summary(forecasts)
        assert summary["count"] == 2
        assert summary["avg_value"] == Decimal("11550")
        assert summary["avg_confidence"] == pytest.approx(0.935)

    def test_trend_summary(self):
        """Test trend summary creation."""
        trends = [
            TrendAnalysis(
                organization_id=self.org_id, metric_type="revenue",
                analysis_period_start=date(2024, 1, 1),
                analysis_period_end=date(2024, 3, 1),
                trend_direction=TrendDirection.UPWARD, strength=0.85
            ),
            TrendAnalysis(
                organization_id=self.org_id, metric_type="expense",
                analysis_period_start=date(2024, 1, 1),
                analysis_period_end=date(2024, 3, 1),
                trend_direction=TrendDirection.DOWNWARD, strength=0.75
            ),
        ]
        summary = self.provider.create_trend_summary(trends)
        assert summary["count"] == 2
        assert summary["uptrends"] == 1
        assert summary["downtrends"] == 1
        assert summary["stable"] == 0
        assert summary["avg_strength"] == 0.8

    def test_kpi_summary_on_target(self):
        """Test KPI summary with target tracking."""
        kpis = [
            KPI(
                organization_id=self.org_id, name="Revenue", code="REV",
                period_date=date(2024, 1, 1), current_value=Decimal("100000"),
                target_value=Decimal("100000"), status_vs_target=Decimal("0")
            ),
            KPI(
                organization_id=self.org_id, name="Expenses", code="EXP",
                period_date=date(2024, 1, 1), current_value=Decimal("48000"),
                target_value=Decimal("50000"), status_vs_target=Decimal("-0.04")
            ),
        ]
        summary = self.provider.create_kpi_summary(kpis)
        assert summary["count"] == 2
        assert summary["on_target"] == 2

    def test_kpi_summary_at_risk(self):
        """Test KPI summary with at-risk tracking."""
        kpis = [
            KPI(
                organization_id=self.org_id, name="Revenue", code="REV",
                period_date=date(2024, 1, 1), current_value=Decimal("75000"),
                target_value=Decimal("100000"), status_vs_target=Decimal("-0.25")
            ),
        ]
        summary = self.provider.create_kpi_summary(kpis)
        assert summary["at_risk"] == 1

    def test_kpi_summary_off_target(self):
        """Test KPI summary with off-target tracking."""
        kpis = [
            KPI(
                organization_id=self.org_id, name="Revenue", code="REV",
                period_date=date(2024, 1, 1), current_value=Decimal("50000"),
                target_value=Decimal("100000"), status_vs_target=Decimal("-0.5")
            ),
        ]
        summary = self.provider.create_kpi_summary(kpis)
        assert summary["off_target"] == 1

    def test_period_comparison(self):
        """Test period-over-period comparison."""
        current = [
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 2, 1), metric_value=Decimal("50000")
            ),
        ]
        previous = [
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 1, 1), metric_value=Decimal("40000")
            ),
        ]
        comparison = self.provider.create_period_comparison(current, previous)
        assert comparison["current"] == Decimal("50000")
        assert comparison["previous"] == Decimal("40000")
        assert comparison["change"] == Decimal("10000")
        assert comparison["change_pct"] == Decimal("25")

    def test_get_widget_positions(self):
        """Test retrieving widget positions."""
        self.provider.create_widget(
            self.org_id, "widget1", "Widget 1", "kpi", position=0
        )
        self.provider.create_widget(
            self.org_id, "widget2", "Widget 2", "chart", position=2
        )
        positions = self.provider.get_widget_positions(self.org_id)
        assert positions["widget1"] == 0
        assert positions["widget2"] == 2

    def test_update_widget_position(self):
        """Test updating widget position."""
        self.provider.create_widget(
            self.org_id, "widget1", "Widget 1", "kpi", position=0
        )
        updated = self.provider.update_widget_position(
            self.org_id, "widget1", 3
        )
        assert updated.position == 3

    def test_kpi_widget_status_vs_target(self):
        """Test KPI widget calculates vs_target."""
        widget = self.provider.create_kpi_widget(
            self.org_id, "test", "Test KPI",
            Decimal("120"), Decimal("100")
        )
        config = json.loads(widget.config)
        assert config["vs_target"] == pytest.approx(0.2)

    def test_kpi_widget_no_target(self):
        """Test KPI widget without target value."""
        widget = self.provider.create_kpi_widget(
            self.org_id, "test", "Test KPI",
            Decimal("50")
        )
        config = json.loads(widget.config)
        assert config["target_value"] is None
        assert "vs_target" not in config

    def test_metric_summary_empty(self):
        """Test metric summary with empty list."""
        summary = self.provider.create_metric_summary([])
        assert summary["count"] == 0
        assert summary["value"] == Decimal("0")

    def test_organization_isolation(self):
        """Test widgets isolated between organizations."""
        org2_id = uuid4()

        self.provider.create_widget(
            self.org_id, "widget1", "Widget 1", "kpi"
        )
        self.provider.create_widget(
            org2_id, "widget1", "Widget 1", "kpi"
        )

        org1_widgets = self.provider.get_dashboard_widgets(self.org_id)
        org2_widgets = self.provider.get_dashboard_widgets(org2_id)

        assert len(org1_widgets) == 1
        assert len(org2_widgets) == 1
        assert org1_widgets[0].organization_id == self.org_id
        assert org2_widgets[0].organization_id == org2_id
