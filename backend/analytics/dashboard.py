"""Business Intelligence dashboard data provider.

Aggregates analytics data for dashboard visualizations.
"""

from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

from backend.models.analytics import (
    DashboardWidget, FinancialMetric, Forecast, TrendAnalysis, KPI
)


class DashboardProvider:
    """Provides aggregated data for BI dashboards."""

    def __init__(self):
        """Initialize dashboard provider."""
        self.widgets = {}  # (org_id, widget_code) -> DashboardWidget

    def create_widget(
        self,
        organization_id: UUID,
        data_source: str,
        title: str,
        widget_type: str,
        position: int = 0,
        size: str = "medium",
        metric_types: Optional[str] = None,
        period_range: str = "last_30_days",
        config: Optional[str] = None,
        is_pinned: bool = False
    ) -> DashboardWidget:
        """Create a dashboard widget.

        Args:
            organization_id: Organization UUID
            data_source: Data source identifier
            title: Widget title
            widget_type: Type of widget (chart, metric, forecast, etc.)
            position: Position on dashboard
            size: Size (small, medium, large)
            metric_types: Comma-separated metric types
            period_range: Period range identifier
            config: JSON configuration
            is_pinned: Whether widget is pinned to dashboard

        Returns:
            DashboardWidget object
        """
        widget = DashboardWidget(
            organization_id=organization_id,
            title=title,
            widget_type=widget_type,
            data_source=data_source,
            position=position,
            size=size,
            metric_types=metric_types,
            period_range=period_range,
            config=config,
            is_pinned=is_pinned
        )

        key = (organization_id, data_source)
        self.widgets[key] = widget

        return widget

    def get_widget(self, organization_id: UUID, data_source: str) -> Optional[DashboardWidget]:
        """Get a specific widget.

        Args:
            organization_id: Organization UUID
            data_source: Data source identifier

        Returns:
            DashboardWidget or None
        """
        key = (organization_id, data_source)
        return self.widgets.get(key)

    def get_dashboard_widgets(self, organization_id: UUID) -> List[DashboardWidget]:
        """Get all widgets for a dashboard.

        Args:
            organization_id: Organization UUID

        Returns:
            List of DashboardWidget objects
        """
        widgets = [
            w for (org_id, _), w in self.widgets.items()
            if org_id == organization_id
        ]
        return sorted(widgets, key=lambda w: w.position)

    def create_kpi_widget(
        self,
        organization_id: UUID,
        data_source: str,
        title: str,
        current_value: Decimal,
        target_value: Optional[Decimal] = None,
        unit: str = ""
    ) -> DashboardWidget:
        """Create a KPI widget.

        Args:
            organization_id: Organization UUID
            data_source: Data source identifier
            title: Widget title
            current_value: Current KPI value
            target_value: Target value
            unit: Unit of measurement

        Returns:
            DashboardWidget
        """
        config_dict = {
            "current_value": str(current_value),
            "target_value": str(target_value) if target_value else None,
            "unit": unit
        }

        if target_value and target_value != 0:
            vs_target = (current_value - target_value) / target_value
            config_dict["vs_target"] = float(vs_target)

        import json
        config = json.dumps(config_dict)

        return self.create_widget(
            organization_id, data_source, title, "kpi",
            size="small", config=config
        )

    def create_chart_widget(
        self,
        organization_id: UUID,
        data_source: str,
        title: str,
        chart_type: str,
        labels: List[str],
        datasets: List[Dict],
        y_axis_label: str = ""
    ) -> DashboardWidget:
        """Create a chart widget.

        Args:
            organization_id: Organization UUID
            data_source: Data source identifier
            title: Widget title
            chart_type: Chart type (line, bar, pie, etc.)
            labels: X-axis labels
            datasets: Data series
            y_axis_label: Y-axis label

        Returns:
            DashboardWidget
        """
        import json
        config_dict = {
            "chart_type": chart_type,
            "labels": labels,
            "datasets": datasets,
            "y_axis_label": y_axis_label
        }
        config = json.dumps(config_dict)

        return self.create_widget(
            organization_id, data_source, title, "chart",
            size="large", config=config
        )

    def create_metric_summary(
        self,
        metrics: List[FinancialMetric],
        aggregate_func: str = "average"
    ) -> Dict:
        """Create a summary from multiple metrics.

        Args:
            metrics: List of FinancialMetric objects
            aggregate_func: Aggregation function (average, sum, min, max)

        Returns:
            Summary dictionary
        """
        if not metrics:
            return {"count": 0, "value": Decimal("0")}

        values = [m.metric_value for m in metrics]

        if aggregate_func == "sum":
            agg_value = sum(values)
        elif aggregate_func == "min":
            agg_value = min(values)
        elif aggregate_func == "max":
            agg_value = max(values)
        else:  # average
            agg_value = sum(values) / len(values)

        return {
            "count": len(metrics),
            "value": agg_value,
            "function": aggregate_func,
            "min": min(values),
            "max": max(values)
        }

    def create_forecast_summary(
        self,
        forecasts: List[Forecast]
    ) -> Dict:
        """Create a summary from multiple forecasts.

        Args:
            forecasts: List of Forecast objects

        Returns:
            Summary dictionary
        """
        if not forecasts:
            return {"count": 0, "avg_value": Decimal("0"), "avg_confidence": 0}

        values = [f.forecasted_value for f in forecasts]
        accuracies = [f.accuracy_score for f in forecasts if f.accuracy_score]

        return {
            "count": len(forecasts),
            "avg_value": sum(values) / len(values),
            "min_value": min(values),
            "max_value": max(values),
            "avg_confidence": sum(accuracies) / len(accuracies) if accuracies else 0
        }

    def create_trend_summary(
        self,
        trends: List[TrendAnalysis]
    ) -> Dict:
        """Create a summary from multiple trends.

        Args:
            trends: List of TrendAnalysis objects

        Returns:
            Summary dictionary
        """
        if not trends:
            return {
                "count": 0,
                "uptrends": 0,
                "downtrends": 0,
                "stable": 0,
                "avg_strength": 0
            }

        from backend.models.analytics import TrendDirection

        uptrends = sum(1 for t in trends if t.trend_direction == TrendDirection.UPWARD)
        downtrends = sum(1 for t in trends if t.trend_direction == TrendDirection.DOWNWARD)
        stable = sum(1 for t in trends if t.trend_direction == TrendDirection.STABLE)
        avg_strength = sum(t.strength for t in trends) / len(trends)

        return {
            "count": len(trends),
            "uptrends": uptrends,
            "downtrends": downtrends,
            "stable": stable,
            "avg_strength": avg_strength
        }

    def create_kpi_summary(
        self,
        kpis: List[KPI]
    ) -> Dict:
        """Create a summary from multiple KPIs.

        Args:
            kpis: List of KPI objects

        Returns:
            Summary dictionary
        """
        if not kpis:
            return {"count": 0, "on_target": 0, "at_risk": 0, "off_target": 0}

        on_target = 0
        at_risk = 0
        off_target = 0

        for kpi in kpis:
            if kpi.status_vs_target is None:
                continue
            elif kpi.status_vs_target >= -0.1:  # Within 10% of target
                on_target += 1
            elif kpi.status_vs_target >= -0.25:  # Within 25% of target
                at_risk += 1
            else:
                off_target += 1

        return {
            "count": len(kpis),
            "on_target": on_target,
            "at_risk": at_risk,
            "off_target": off_target
        }

    def create_period_comparison(
        self,
        current_metrics: List[FinancialMetric],
        previous_metrics: List[FinancialMetric]
    ) -> Dict:
        """Compare metrics between periods.

        Args:
            current_metrics: Current period metrics
            previous_metrics: Previous period metrics

        Returns:
            Comparison dictionary
        """
        current_sum = sum(m.metric_value for m in current_metrics)
        previous_sum = sum(m.metric_value for m in previous_metrics)

        change = current_sum - previous_sum
        change_pct = (change / previous_sum * 100) if previous_sum != 0 else Decimal("0")

        return {
            "current": current_sum,
            "previous": previous_sum,
            "change": change,
            "change_pct": change_pct
        }

    def get_widget_positions(self, organization_id: UUID) -> Dict[str, int]:
        """Get all widget positions.

        Args:
            organization_id: Organization UUID

        Returns:
            Dictionary mapping data_source to position
        """
        widgets = self.get_dashboard_widgets(organization_id)
        return {
            w.data_source: w.position
            for w in widgets
        }

    def update_widget_position(
        self,
        organization_id: UUID,
        data_source: str,
        position: int
    ) -> Optional[DashboardWidget]:
        """Update widget position.

        Args:
            organization_id: Organization UUID
            data_source: Data source identifier
            position: New position

        Returns:
            Updated DashboardWidget or None
        """
        widget = self.get_widget(organization_id, data_source)
        if widget:
            widget.position = position
        return widget
