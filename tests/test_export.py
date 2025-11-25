"""Tests for report export and distribution service.

Tests export functionality, format handling, and distribution tracking.
"""

import pytest
import json
from uuid import uuid4
from datetime import date
from decimal import Decimal

from backend.analytics.export import ExportService, ExportFormat
from backend.models.analytics import (
    FinancialMetric, MetricType, Forecast, ForecastType, ForecastMethod,
    TrendAnalysis, TrendDirection, KPI
)


class TestExportService:
    """Tests for ExportService."""

    def setup_method(self):
        """Set up for each test."""
        self.service = ExportService()
        self.org_id = uuid4()

    def test_export_metrics_json(self):
        """Test exporting metrics to JSON."""
        metrics = [
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 1, 1), metric_value=Decimal("25")
            ),
        ]
        export = self.service.export_metrics_json(self.org_id, metrics)

        assert export["report_type"] == "metrics"
        assert export["format"] == "json"
        assert len(export["metrics"]) == 1
        assert export["metrics"][0]["value"] == "25"

    def test_export_metrics_json_with_metadata(self):
        """Test JSON export includes metadata."""
        metrics = [
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 1, 1), metric_value=Decimal("25")
            ),
        ]
        export = self.service.export_metrics_json(
            self.org_id, metrics, include_metadata=True
        )

        assert "metadata" in export
        assert export["metadata"]["total_metrics"] == 1

    def test_export_metrics_json_with_benchmarks(self):
        """Test JSON export includes benchmark comparisons."""
        metrics = [
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 1, 1), metric_value=Decimal("25"),
                benchmark_value=Decimal("20"), vs_benchmark=Decimal("5")
            ),
        ]
        export = self.service.export_metrics_json(self.org_id, metrics)
        metric_data = export["metrics"][0]

        assert metric_data["benchmark"] == "20"
        assert metric_data["vs_benchmark"] == "5"

    def test_export_forecasts_json(self):
        """Test exporting forecasts to JSON."""
        forecasts = [
            Forecast(
                organization_id=self.org_id, forecast_type=ForecastType.REVENUE,
                method=ForecastMethod.LINEAR_REGRESSION, period_start=date(2024, 1, 1),
                period_end=date(2024, 2, 1), base_value=Decimal("10000"),
                forecasted_value=Decimal("11000"), accuracy_score=0.95
            ),
        ]
        export = self.service.export_forecasts_json(self.org_id, forecasts)

        assert export["report_type"] == "forecasts"
        assert len(export["forecasts"]) == 1
        assert export["forecasts"][0]["accuracy_score"] == 0.95

    def test_export_trends_json(self):
        """Test exporting trends to JSON."""
        trends = [
            TrendAnalysis(
                organization_id=self.org_id, metric_type="revenue",
                analysis_period_start=date(2024, 1, 1),
                analysis_period_end=date(2024, 3, 1),
                trend_direction=TrendDirection.UPWARD, strength=0.85
            ),
        ]
        export = self.service.export_trends_json(self.org_id, trends)

        assert export["report_type"] == "trends"
        assert len(export["trends"]) == 1
        assert export["trends"][0]["direction"] == str(TrendDirection.UPWARD)

    def test_export_metrics_csv(self):
        """Test exporting metrics to CSV."""
        metrics = [
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 1, 1), metric_value=Decimal("25")
            ),
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.CURRENT_RATIO,
                period_date=date(2024, 1, 1), metric_value=Decimal("2.5")
            ),
        ]
        csv_data = self.service.export_metrics_csv(metrics)

        assert "metric_type,value,period_date" in csv_data
        assert "25" in csv_data
        assert "2.5" in csv_data

    def test_export_metrics_csv_empty(self):
        """Test CSV export with empty metrics."""
        csv_data = self.service.export_metrics_csv([])
        assert "metric_type,value" in csv_data

    def test_create_distribution_record(self):
        """Test creating a distribution record."""
        record = self.service.create_distribution_record(
            self.org_id, "metrics", ExportFormat.JSON,
            recipient_email="test@example.com"
        )

        assert record["report_type"] == "metrics"
        assert record["format"] == "json"
        assert record["recipient_email"] == "test@example.com"
        assert record["status"] == "pending"

    def test_distribution_record_methods(self):
        """Test distribution record tracking."""
        self.service.create_distribution_record(
            self.org_id, "metrics", ExportFormat.JSON,
            recipient_email="test1@example.com"
        )
        self.service.create_distribution_record(
            self.org_id, "forecasts", ExportFormat.CSV,
            recipient_email="test2@example.com"
        )

        history = self.service.get_distribution_history(self.org_id)
        assert len(history) == 2

    def test_distribution_history_sorted(self):
        """Test distribution history is sorted by date."""
        self.service.create_distribution_record(
            self.org_id, "metrics", ExportFormat.JSON
        )
        self.service.create_distribution_record(
            self.org_id, "forecasts", ExportFormat.CSV
        )

        history = self.service.get_distribution_history(self.org_id)
        # Most recent first
        assert history[0]["report_type"] == "forecasts"
        assert history[1]["report_type"] == "metrics"

    def test_schedule_report_export(self):
        """Test scheduling recurring report export."""
        schedule = self.service.schedule_report_export(
            self.org_id, "metrics", ExportFormat.JSON,
            frequency="weekly", recipient_email="test@example.com"
        )

        assert schedule["frequency"] == "weekly"
        assert schedule["is_active"] is True
        assert schedule["format"] == "json"

    def test_export_summary_comprehensive(self):
        """Test creating executive summary export."""
        metrics = [
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 1, 1), metric_value=Decimal("25")
            ),
        ]
        forecasts = [
            Forecast(
                organization_id=self.org_id, forecast_type=ForecastType.REVENUE,
                method=ForecastMethod.LINEAR_REGRESSION, period_start=date(2024, 1, 1),
                period_end=date(2024, 2, 1), base_value=Decimal("10000"),
                forecasted_value=Decimal("11000"), accuracy_score=0.95
            ),
        ]
        trends = [
            TrendAnalysis(
                organization_id=self.org_id, metric_type="revenue",
                analysis_period_start=date(2024, 1, 1),
                analysis_period_end=date(2024, 3, 1),
                trend_direction=TrendDirection.UPWARD, strength=0.85
            ),
        ]
        kpis = [
            KPI(
                organization_id=self.org_id, name="Revenue", code="REV",
                period_date=date(2024, 1, 1), current_value=Decimal("100000"),
                target_value=Decimal("100000")
            ),
        ]

        summary = self.service.export_summary(
            self.org_id, metrics, forecasts, trends, kpis
        )

        assert summary["report_type"] == "executive_summary"
        assert summary["sections"]["metrics"]["count"] == 1
        assert summary["sections"]["forecasts"]["count"] == 1
        assert summary["sections"]["trends"]["count"] == 1
        assert summary["sections"]["kpis"]["count"] == 1

    def test_export_summary_forecast_accuracy(self):
        """Test summary includes forecast accuracy."""
        forecasts = [
            Forecast(
                organization_id=self.org_id, forecast_type=ForecastType.REVENUE,
                method=ForecastMethod.LINEAR_REGRESSION, period_start=date(2024, 1, 1),
                period_end=date(2024, 2, 1), base_value=Decimal("10000"),
                forecasted_value=Decimal("11000"), accuracy_score=0.90
            ),
            Forecast(
                organization_id=self.org_id, forecast_type=ForecastType.REVENUE,
                method=ForecastMethod.LINEAR_REGRESSION, period_start=date(2024, 2, 1),
                period_end=date(2024, 3, 1), base_value=Decimal("11000"),
                forecasted_value=Decimal("12100"), accuracy_score=0.95
            ),
        ]

        summary = self.service.export_summary(
            self.org_id, [], forecasts, [], []
        )

        assert summary["sections"]["forecasts"]["accuracy"] == pytest.approx(0.925)

    def test_export_summary_kpi_targeting(self):
        """Test summary includes KPI target status."""
        kpis = [
            KPI(
                organization_id=self.org_id, name="Revenue", code="REV",
                period_date=date(2024, 1, 1), current_value=Decimal("100000"),
                target_value=Decimal("100000"), status_vs_target=Decimal("0")
            ),
            KPI(
                organization_id=self.org_id, name="Expenses", code="EXP",
                period_date=date(2024, 1, 1), current_value=Decimal("50000"),
                target_value=Decimal("50000"), status_vs_target=Decimal("0")
            ),
        ]

        summary = self.service.export_summary(
            self.org_id, [], [], [], kpis
        )

        assert summary["sections"]["kpis"]["on_target"] == 2

    def test_export_multiple_formats(self):
        """Test exporting same data in multiple formats."""
        metrics = [
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 1, 1), metric_value=Decimal("25")
            ),
        ]

        json_export = self.service.export_metrics_json(self.org_id, metrics)
        csv_export = self.service.export_metrics_csv(metrics)

        assert json_export["format"] == "json"
        assert "value" in json_export["metrics"][0]
        assert isinstance(csv_export, str)
        assert "25" in csv_export

    def test_export_with_custom_title(self):
        """Test export with custom report title."""
        metrics = [
            FinancialMetric(
                organization_id=self.org_id, metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, 1, 1), metric_value=Decimal("25")
            ),
        ]

        export = self.service.export_metrics_json(
            self.org_id, metrics, title="Custom Title"
        )

        assert export["title"] == "Custom Title"

    def test_distribution_limit(self):
        """Test distribution history respects limit."""
        # Create many distributions
        for i in range(10):
            self.service.create_distribution_record(
                self.org_id, "metrics", ExportFormat.JSON
            )

        history = self.service.get_distribution_history(self.org_id, limit=5)
        assert len(history) == 5

    def test_organization_isolation_distributions(self):
        """Test distributions isolated between organizations."""
        org2_id = uuid4()

        self.service.create_distribution_record(
            self.org_id, "metrics", ExportFormat.JSON
        )
        self.service.create_distribution_record(
            org2_id, "forecasts", ExportFormat.CSV
        )

        org1_history = self.service.get_distribution_history(self.org_id)
        org2_history = self.service.get_distribution_history(org2_id)

        assert len(org1_history) == 1
        assert len(org2_history) == 1
        assert org1_history[0]["report_type"] == "metrics"
        assert org2_history[0]["report_type"] == "forecasts"
