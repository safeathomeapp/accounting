"""Tests for advanced analytics API integration.

Tests API endpoints for forecasting, metrics, trends, dashboards, and exports.
"""

import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal

from backend.analytics.forecasting import ForecastingEngine
from backend.analytics.metrics import MetricsCalculator
from backend.analytics.trends import TrendAnalysisEngine
from backend.analytics.dashboard import DashboardProvider
from backend.analytics.export import ExportService, ExportFormat

from backend.models.analytics import (
    ForecastType, MetricType, TrendDirection
)


class TestAnalyticsIntegration:
    """Tests for analytics services integration."""

    def setup_method(self):
        """Set up for each test."""
        self.forecasting = ForecastingEngine()
        self.metrics = MetricsCalculator()
        self.trends = TrendAnalysisEngine()
        self.dashboard = DashboardProvider()
        self.export = ExportService()
        self.org_id = uuid4()

    def test_end_to_end_forecasting_workflow(self):
        """Test complete forecasting workflow."""
        historical = [
            (date(2024, 1, 1), Decimal("10000")),
            (date(2024, 2, 1), Decimal("11000")),
            (date(2024, 3, 1), Decimal("12000")),
        ]

        forecasts = self.forecasting.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=3
        )

        assert len(forecasts) == 3
        assert all(f.organization_id == self.org_id for f in forecasts)
        assert all(f.forecast_type == ForecastType.REVENUE for f in forecasts)

    def test_end_to_end_metrics_workflow(self):
        """Test complete metrics calculation workflow."""
        metric1 = self.metrics.calculate_profit_margin(
            self.org_id, date(2024, 1, 1), Decimal("50000"), Decimal("200000")
        )
        metric2 = self.metrics.calculate_liquidity_ratio(
            self.org_id, date(2024, 1, 1), Decimal("100000"), Decimal("50000")
        )

        assert metric1.metric_value == Decimal("25")
        assert metric2[0].metric_value == Decimal("2")

        # Get metrics history
        history = self.metrics.get_metrics_history(
            self.org_id, MetricType.NET_PROFIT_MARGIN,
            date(2024, 1, 1), date(2024, 2, 1)
        )
        assert len(history) == 1

    def test_end_to_end_trends_workflow(self):
        """Test complete trend analysis workflow."""
        values = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("110")),
            (date(2024, 3, 1), Decimal("120")),
            (date(2024, 4, 1), Decimal("130")),
        ]

        trend = self.trends.analyze_trend(self.org_id, "revenue", values)

        assert trend.trend_direction == TrendDirection.UPWARD
        assert trend.strength > 0.9

        # Get all uptrends
        uptrends = self.trends.get_uptrends(self.org_id)
        assert len(uptrends) == 1
        assert uptrends[0].metric_type == "revenue"

    def test_end_to_end_dashboard_workflow(self):
        """Test complete dashboard creation workflow."""
        # Create metric
        metric = self.metrics.calculate_profit_margin(
            self.org_id, date(2024, 1, 1), Decimal("25000"), Decimal("100000")
        )

        # Create KPI widget
        widget = self.dashboard.create_kpi_widget(
            self.org_id, "profit_margin", "Profit Margin",
            Decimal("25"), Decimal("20"), unit="%"
        )

        assert widget.title == "Profit Margin"
        assert widget.widget_type == "kpi"

        # Retrieve widget
        retrieved = self.dashboard.get_widget(self.org_id, "profit_margin")
        assert retrieved is not None
        assert retrieved.data_source == "profit_margin"

    def test_end_to_end_export_workflow(self):
        """Test complete export workflow."""
        # Create metrics
        metrics = [
            self.metrics.calculate_profit_margin(
                self.org_id, date(2024, 1, 1), Decimal("25000"), Decimal("100000")
            ),
        ]

        # Export as JSON
        json_export = self.export.export_metrics_json(self.org_id, metrics)
        assert json_export["format"] == "json"
        assert len(json_export["metrics"]) == 1

        # Export as CSV
        csv_export = self.export.export_metrics_csv(metrics)
        assert "25" in csv_export

        # Record distribution
        record = self.export.create_distribution_record(
            self.org_id, "metrics", ExportFormat.JSON,
            recipient_email="test@example.com"
        )
        assert record["report_type"] == "metrics"

    def test_multi_metric_analytics_workflow(self):
        """Test workflow with multiple metric types."""
        # Create various metrics
        profit_margin = self.metrics.calculate_profit_margin(
            self.org_id, date(2024, 1, 1), Decimal("50000"), Decimal("200000")
        )
        liquidity = self.metrics.calculate_liquidity_ratio(
            self.org_id, date(2024, 1, 1), Decimal("100000"), Decimal("50000")
        )
        growth = self.metrics.calculate_growth_rate(
            self.org_id, date(2024, 1, 1),
            Decimal("120000"), Decimal("100000")
        )
        roa = self.metrics.calculate_return_on_assets(
            self.org_id, date(2024, 1, 1),
            Decimal("50000"), Decimal("500000")
        )

        # Get all metrics
        all_metrics = [
            m for (org, _, _), m in self.metrics.metrics.items()
            if org == self.org_id
        ]

        assert len(all_metrics) >= 4

        # Create summary export using dashboard
        metrics_list = [profit_margin, liquidity[0], growth, roa]
        summary = self.dashboard.create_metric_summary(metrics_list)
        assert summary["count"] >= 4

    def test_forecast_and_trend_comparison(self):
        """Test comparing forecasts with trend analysis."""
        historical = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("110")),
            (date(2024, 3, 1), Decimal("120")),
            (date(2024, 4, 1), Decimal("130")),
        ]

        # Forecast future
        forecasts = self.forecasting.forecast_moving_average(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=2
        )

        # Analyze historical trend
        trend = self.trends.analyze_trend(self.org_id, "revenue", historical)

        # Trend should be upward even if forecasts are more conservative
        assert trend.trend_direction == TrendDirection.UPWARD
        # Forecasts should be positive and reasonable
        assert forecasts[0].forecasted_value > 0

    def test_dashboard_with_aggregated_data(self):
        """Test dashboard with aggregated analytics data."""
        # Create metrics
        metrics = [
            self.metrics.calculate_profit_margin(
                self.org_id, date(2024, 1, 1), Decimal("25000"), Decimal("100000")
            ),
            self.metrics.calculate_profit_margin(
                self.org_id, date(2024, 2, 1), Decimal("27000"), Decimal("110000")
            ),
        ]

        # Create summary widget
        summary = self.dashboard.create_metric_summary(metrics)
        assert summary["count"] == 2
        assert summary["function"] == "average"

        # Create dashboard widget for summary
        widget = self.dashboard.create_widget(
            self.org_id, "profit_margin_trend", "Profit Margin Trend", "chart"
        )
        assert widget.data_source == "profit_margin_trend"

    def test_export_with_all_analytics_types(self):
        """Test exporting all types of analytics together."""
        # Create forecasts
        historical = [
            (date(2024, 1, 1), Decimal("10000")),
            (date(2024, 2, 1), Decimal("11000")),
            (date(2024, 3, 1), Decimal("12000")),
        ]
        forecasts = self.forecasting.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=1
        )

        # Create metrics
        metrics = [
            self.metrics.calculate_profit_margin(
                self.org_id, date(2024, 1, 1), Decimal("5000"), Decimal("50000")
            ),
        ]

        # Create trends
        values = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("110")),
            (date(2024, 3, 1), Decimal("120")),
        ]
        trends = [
            self.trends.analyze_trend(self.org_id, "revenue", values)
        ]

        # Create KPIs
        kpis = [
            self.metrics.create_kpi(
                self.org_id, "Revenue", "REV", date(2024, 1, 1),
                Decimal("50000"), Decimal("50000")
            ),
        ]

        # Create comprehensive summary
        summary = self.export.export_summary(
            self.org_id, metrics, forecasts, trends, kpis
        )

        assert summary["report_type"] == "executive_summary"
        assert summary["sections"]["forecasts"]["count"] == 1
        assert summary["sections"]["metrics"]["count"] == 1
        assert summary["sections"]["trends"]["count"] == 1
        assert summary["sections"]["kpis"]["count"] == 1

    def test_organization_data_isolation_across_services(self):
        """Test data isolation across all services."""
        org2_id = uuid4()

        # Create data for org1
        forecast1 = self.forecasting.forecast_moving_average(
            self.org_id, ForecastType.REVENUE,
            [(date(2024, 1, 1), Decimal("100")),
             (date(2024, 2, 1), Decimal("110")),
             (date(2024, 3, 1), Decimal("120"))],
            forecast_periods=1
        )

        # Create data for org2
        forecast2 = self.forecasting.forecast_moving_average(
            org2_id, ForecastType.REVENUE,
            [(date(2024, 1, 1), Decimal("200")),
             (date(2024, 2, 1), Decimal("220")),
             (date(2024, 3, 1), Decimal("240"))],
            forecast_periods=1
        )

        # Verify isolation
        org1_forecasts = self.forecasting.get_forecasts(self.org_id)
        org2_forecasts = self.forecasting.get_forecasts(org2_id)

        assert len(org1_forecasts) == 1
        assert len(org2_forecasts) == 1
        assert org1_forecasts[0].forecasted_value != org2_forecasts[0].forecasted_value

    def test_full_analytics_pipeline(self):
        """Test complete analytics pipeline from data to export."""
        # 1. Create raw metrics
        profit = self.metrics.calculate_profit_margin(
            self.org_id, date(2024, 1, 1),
            Decimal("50000"), Decimal("200000")
        )

        # 2. Create forecast based on trend
        forecasts = self.forecasting.forecast_linear_regression(
            self.org_id, ForecastType.PROFIT,
            [(date(2024, 1, 1), profit.metric_value),
             (date(2024, 2, 1), Decimal("26")),
             (date(2024, 3, 1), Decimal("27"))],
            forecast_periods=2
        )

        # 3. Analyze trends
        trend_values = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("110")),
            (date(2024, 3, 1), Decimal("120")),
        ]
        trend = self.trends.analyze_trend(self.org_id, "profit", trend_values)

        # 4. Create dashboard
        widget = self.dashboard.create_kpi_widget(
            self.org_id, "profit_margin", "Profit Margin",
            profit.metric_value
        )

        # 5. Export everything
        export_summary = self.export.export_summary(
            self.org_id,
            [profit],
            forecasts,
            [trend],
            []
        )

        # 6. Verify complete pipeline
        assert export_summary["sections"]["metrics"]["count"] == 1
        assert export_summary["sections"]["forecasts"]["count"] == 2
        assert export_summary["sections"]["trends"]["count"] == 1
        assert widget.title == "Profit Margin"

    def test_concurrent_operations_isolation(self):
        """Test that concurrent operations don't interfere."""
        # Simulate concurrent operations by creating multiple items
        metric_values = [Decimal("25"), Decimal("26"), Decimal("27"), Decimal("28")]

        for i, value in enumerate(metric_values):
            self.metrics.calculate_profit_margin(
                self.org_id, date(2024, 1, i + 1),
                value * 1000, Decimal("100000")
            )

        # Verify all were created
        all_metrics = [
            m for (org, _, _), m in self.metrics.metrics.items()
            if org == self.org_id
        ]
        assert len(all_metrics) == 4

        # Verify ordering
        sorted_metrics = sorted(all_metrics, key=lambda m: m.period_date)
        assert sorted_metrics[0].metric_value == Decimal("25")
        assert sorted_metrics[3].metric_value == Decimal("28")
