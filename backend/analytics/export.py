"""Report export and distribution service.

Exports financial reports in multiple formats and manages distribution.
"""

import json
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from enum import Enum

from backend.models.analytics import (
    FinancialMetric, Forecast, TrendAnalysis, KPI
)


class ExportFormat(Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    EXCEL = "excel"
    HTML = "html"


class ExportService:
    """Manages report export and distribution."""

    def __init__(self):
        """Initialize export service."""
        self.exports = {}  # (org_id, export_id) -> Export record
        self.distributions = []  # List of distribution records

    def export_metrics_json(
        self,
        organization_id: UUID,
        metrics: List[FinancialMetric],
        title: str = "Financial Metrics Report",
        include_metadata: bool = True
    ) -> Dict:
        """Export metrics in JSON format.

        Args:
            organization_id: Organization UUID
            metrics: List of FinancialMetric objects
            title: Report title
            include_metadata: Include report metadata

        Returns:
            Dictionary with JSON export data
        """
        data = {
            "report_type": "metrics",
            "format": ExportFormat.JSON.value,
            "title": title,
            "generated_at": datetime.now(datetime.now().astimezone().tzinfo).isoformat()
        }

        if include_metadata:
            data["metadata"] = {
                "organization_id": str(organization_id),
                "total_metrics": len(metrics),
                "metric_types": list(set(m.metric_type for m in metrics))
            }

        data["metrics"] = [
            {
                "type": str(m.metric_type),
                "value": str(m.metric_value),
                "period_date": m.period_date.isoformat(),
                "benchmark": str(m.benchmark_value) if m.benchmark_value else None,
                "vs_benchmark": str(m.vs_benchmark) if m.vs_benchmark else None,
                "change": str(m.period_over_period_change) if m.period_over_period_change else None
            }
            for m in metrics
        ]

        return data

    def export_forecasts_json(
        self,
        organization_id: UUID,
        forecasts: List[Forecast],
        title: str = "Forecast Report"
    ) -> Dict:
        """Export forecasts in JSON format.

        Args:
            organization_id: Organization UUID
            forecasts: List of Forecast objects
            title: Report title

        Returns:
            Dictionary with JSON export data
        """
        data = {
            "report_type": "forecasts",
            "format": ExportFormat.JSON.value,
            "title": title,
            "generated_at": datetime.now(datetime.now().astimezone().tzinfo).isoformat(),
            "metadata": {
                "organization_id": str(organization_id),
                "total_forecasts": len(forecasts)
            }
        }

        data["forecasts"] = [
            {
                "type": str(f.forecast_type),
                "method": str(f.method),
                "base_value": str(f.base_value),
                "forecasted_value": str(f.forecasted_value),
                "period_start": f.period_start.isoformat(),
                "period_end": f.period_end.isoformat(),
                "accuracy_score": f.accuracy_score,
                "lower_bound": str(f.lower_bound) if f.lower_bound else None,
                "upper_bound": str(f.upper_bound) if f.upper_bound else None,
                "mape": f.mape
            }
            for f in forecasts
        ]

        return data

    def export_trends_json(
        self,
        organization_id: UUID,
        trends: List[TrendAnalysis],
        title: str = "Trend Analysis Report"
    ) -> Dict:
        """Export trends in JSON format.

        Args:
            organization_id: Organization UUID
            trends: List of TrendAnalysis objects
            title: Report title

        Returns:
            Dictionary with JSON export data
        """
        data = {
            "report_type": "trends",
            "format": ExportFormat.JSON.value,
            "title": title,
            "generated_at": datetime.now(datetime.now().astimezone().tzinfo).isoformat(),
            "metadata": {
                "organization_id": str(organization_id),
                "total_trends": len(trends)
            }
        }

        data["trends"] = [
            {
                "metric_type": t.metric_type,
                "direction": str(t.trend_direction),
                "strength": t.strength,
                "growth_rate": str(t.growth_rate),
                "volatility": t.volatility,
                "anomalies_detected": t.anomalies_detected,
                "period_start": t.analysis_period_start.isoformat(),
                "period_end": t.analysis_period_end.isoformat(),
                "avg_value": str(t.average_value),
                "min_value": str(t.min_value),
                "max_value": str(t.max_value)
            }
            for t in trends
        ]

        return data

    def export_metrics_csv(
        self,
        metrics: List[FinancialMetric]
    ) -> str:
        """Export metrics in CSV format.

        Args:
            metrics: List of FinancialMetric objects

        Returns:
            CSV formatted string
        """
        if not metrics:
            return "metric_type,value,period_date,benchmark,vs_benchmark,change"

        lines = [
            "metric_type,value,period_date,benchmark,vs_benchmark,change"
        ]

        for m in metrics:
            benchmark = m.benchmark_value or ""
            vs_benchmark = m.vs_benchmark or ""
            change = m.period_over_period_change or ""

            line = f"{m.metric_type},{m.metric_value},{m.period_date},{benchmark},{vs_benchmark},{change}"
            lines.append(line)

        return "\n".join(lines)

    def create_distribution_record(
        self,
        organization_id: UUID,
        report_type: str,
        format_type: ExportFormat,
        recipient_email: Optional[str] = None,
        distribution_method: str = "email"
    ) -> Dict:
        """Create a distribution record.

        Args:
            organization_id: Organization UUID
            report_type: Type of report (metrics, forecasts, trends)
            format_type: Export format
            recipient_email: Email recipient
            distribution_method: Distribution method (email, download, etc.)

        Returns:
            Distribution record dictionary
        """
        record = {
            "organization_id": str(organization_id),
            "report_type": report_type,
            "format": format_type.value,
            "recipient_email": recipient_email,
            "distribution_method": distribution_method,
            "distributed_at": datetime.now(datetime.now().astimezone().tzinfo).isoformat(),
            "status": "pending"
        }

        self.distributions.append(record)
        return record

    def get_distribution_history(
        self,
        organization_id: UUID,
        limit: int = 50
    ) -> List[Dict]:
        """Get distribution history for an organization.

        Args:
            organization_id: Organization UUID
            limit: Maximum number of records

        Returns:
            List of distribution records
        """
        org_dists = [
            d for d in self.distributions
            if d["organization_id"] == str(organization_id)
        ]
        return sorted(
            org_dists,
            key=lambda x: x["distributed_at"],
            reverse=True
        )[:limit]

    def schedule_report_export(
        self,
        organization_id: UUID,
        report_type: str,
        format_type: ExportFormat,
        frequency: str,
        recipient_email: Optional[str] = None
    ) -> Dict:
        """Schedule recurring report export.

        Args:
            organization_id: Organization UUID
            report_type: Type of report
            format_type: Export format
            frequency: Frequency (daily, weekly, monthly)
            recipient_email: Email recipient

        Returns:
            Schedule record dictionary
        """
        schedule = {
            "organization_id": str(organization_id),
            "report_type": report_type,
            "format": format_type.value,
            "frequency": frequency,
            "recipient_email": recipient_email,
            "is_active": True,
            "created_at": datetime.now(datetime.now().astimezone().tzinfo).isoformat()
        }

        return schedule

    def export_summary(
        self,
        organization_id: UUID,
        metrics: List[FinancialMetric],
        forecasts: List[Forecast],
        trends: List[TrendAnalysis],
        kpis: List[KPI],
        title: str = "Executive Summary"
    ) -> Dict:
        """Create executive summary export combining all analytics.

        Args:
            organization_id: Organization UUID
            metrics: Financial metrics
            forecasts: Forecasts
            trends: Trends
            kpis: KPIs
            title: Report title

        Returns:
            Summary dictionary
        """
        summary = {
            "report_type": "executive_summary",
            "title": title,
            "generated_at": datetime.now(datetime.now().astimezone().tzinfo).isoformat(),
            "organization_id": str(organization_id),
            "sections": {
                "metrics": {
                    "count": len(metrics),
                    "sample": self._get_top_metrics(metrics, 3)
                },
                "forecasts": {
                    "count": len(forecasts),
                    "accuracy": self._calculate_forecast_accuracy(forecasts)
                },
                "trends": {
                    "count": len(trends),
                    "summary": self._get_trend_summary(trends)
                },
                "kpis": {
                    "count": len(kpis),
                    "on_target": sum(1 for k in kpis if k.status_vs_target is not None and k.status_vs_target >= -0.1)
                }
            }
        }

        return summary

    def _get_top_metrics(
        self,
        metrics: List[FinancialMetric],
        count: int
    ) -> List[Dict]:
        """Get top metrics by absolute value.

        Args:
            metrics: List of metrics
            count: Number of top metrics

        Returns:
            List of top metric summaries
        """
        sorted_metrics = sorted(
            metrics,
            key=lambda m: abs(m.metric_value) if m.metric_value else Decimal("0"),
            reverse=True
        )

        return [
            {
                "type": str(m.metric_type),
                "value": str(m.metric_value),
                "period": m.period_date.isoformat()
            }
            for m in sorted_metrics[:count]
        ]

    def _calculate_forecast_accuracy(self, forecasts: List[Forecast]) -> Optional[float]:
        """Calculate average forecast accuracy.

        Args:
            forecasts: List of forecasts

        Returns:
            Average accuracy score or None
        """
        scores = [f.accuracy_score for f in forecasts if f.accuracy_score]
        return sum(scores) / len(scores) if scores else None

    def _get_trend_summary(self, trends: List[TrendAnalysis]) -> Dict:
        """Get summary of trends.

        Args:
            trends: List of trends

        Returns:
            Trend summary dictionary
        """
        from backend.models.analytics import TrendDirection

        uptrends = sum(1 for t in trends if t.trend_direction == TrendDirection.UPWARD)
        downtrends = sum(1 for t in trends if t.trend_direction == TrendDirection.DOWNWARD)
        stable = sum(1 for t in trends if t.trend_direction == TrendDirection.STABLE)

        return {
            "uptrending": uptrends,
            "downtrending": downtrends,
            "stable": stable
        }
