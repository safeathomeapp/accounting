"""Financial metrics and KPI calculations.

Calculates key financial metrics and KPIs for analysis and reporting.
"""

from uuid import UUID
from datetime import date
from decimal import Decimal
from typing import Dict, Optional, List, Tuple

from backend.models.analytics import FinancialMetric, MetricType, KPI


class MetricsCalculator:
    """Calculates financial metrics and KPIs."""

    def __init__(self):
        """Initialize metrics calculator."""
        self.metrics = {}  # (org_id, metric_type, period_date) -> FinancialMetric
        self.kpis = {}  # (org_id, kpi_code, period_date) -> KPI

    def calculate_profit_margin(
        self,
        organization_id: UUID,
        period_date: date,
        profit: Decimal,
        revenue: Decimal,
        previous_margin: Optional[Decimal] = None,
        benchmark: Optional[Decimal] = None,
        metric_type: MetricType = MetricType.NET_PROFIT_MARGIN
    ) -> FinancialMetric:
        """Calculate profit margin metric.

        Args:
            organization_id: Organization UUID
            period_date: Period date
            profit: Profit amount
            revenue: Revenue amount
            previous_margin: Previous period margin for comparison
            benchmark: Benchmark margin value
            metric_type: Type of margin metric

        Returns:
            FinancialMetric object
        """
        if revenue == 0:
            margin = Decimal("0")
        else:
            margin = (profit / revenue) * 100

        pct_change = None
        if previous_margin is not None:
            pct_change = margin - previous_margin

        vs_benchmark = None
        if benchmark is not None:
            vs_benchmark = margin - benchmark

        metric = FinancialMetric(
            organization_id=organization_id,
            metric_type=metric_type,
            period_date=period_date,
            metric_value=margin,
            previous_period_value=previous_margin,
            period_over_period_change=pct_change,
            benchmark_value=benchmark,
            vs_benchmark=vs_benchmark
        )

        key = (organization_id, metric_type, period_date)
        self.metrics[key] = metric

        return metric

    def calculate_liquidity_ratio(
        self,
        organization_id: UUID,
        period_date: date,
        current_assets: Decimal,
        current_liabilities: Decimal,
        quick_assets: Optional[Decimal] = None,
        previous_ratio: Optional[Decimal] = None,
        benchmark: Optional[Decimal] = None
    ) -> Tuple[FinancialMetric, Optional[FinancialMetric]]:
        """Calculate current and quick ratios.

        Args:
            organization_id: Organization UUID
            period_date: Period date
            current_assets: Current assets
            current_liabilities: Current liabilities
            quick_assets: Quick assets (optional for quick ratio)
            previous_ratio: Previous period ratio
            benchmark: Benchmark ratio

        Returns:
            Tuple of (current_ratio_metric, quick_ratio_metric)
        """
        if current_liabilities == 0:
            current_ratio = Decimal("0")
        else:
            current_ratio = current_assets / current_liabilities

        pct_change = None
        if previous_ratio is not None:
            pct_change = current_ratio - previous_ratio

        vs_benchmark = None
        if benchmark is not None:
            vs_benchmark = current_ratio - benchmark

        current_metric = FinancialMetric(
            organization_id=organization_id,
            metric_type=MetricType.CURRENT_RATIO,
            period_date=period_date,
            metric_value=current_ratio,
            previous_period_value=previous_ratio,
            period_over_period_change=pct_change,
            benchmark_value=benchmark,
            vs_benchmark=vs_benchmark
        )

        key = (organization_id, MetricType.CURRENT_RATIO, period_date)
        self.metrics[key] = current_metric

        # Quick ratio if quick assets provided
        quick_metric = None
        if quick_assets is not None:
            if current_liabilities == 0:
                quick_ratio = Decimal("0")
            else:
                quick_ratio = quick_assets / current_liabilities

            quick_metric = FinancialMetric(
                organization_id=organization_id,
                metric_type=MetricType.QUICK_RATIO,
                period_date=period_date,
                metric_value=quick_ratio,
                benchmark_value=benchmark
            )

            key = (organization_id, MetricType.QUICK_RATIO, period_date)
            self.metrics[key] = quick_metric

        return current_metric, quick_metric

    def calculate_growth_rate(
        self,
        organization_id: UUID,
        period_date: date,
        current_value: Decimal,
        previous_value: Decimal,
        periods: int = 1
    ) -> FinancialMetric:
        """Calculate growth rate metric.

        Args:
            organization_id: Organization UUID
            period_date: Period date
            current_value: Current period value
            previous_value: Previous period value
            periods: Number of periods

        Returns:
            FinancialMetric object
        """
        if previous_value == 0:
            growth_rate = Decimal("0")
        else:
            growth_rate = ((current_value - previous_value) / previous_value) * 100

        # Annualize if multiple periods
        if periods > 1:
            # Convert to float for power calculation, then back to Decimal
            growth_factor = float(1 + growth_rate / 100)
            annualized_factor = growth_factor ** (1 / periods)
            annualized_rate = (annualized_factor - 1) * 100
        else:
            annualized_rate = growth_rate

        metric = FinancialMetric(
            organization_id=organization_id,
            metric_type=MetricType.REVENUE_GROWTH,
            period_date=period_date,
            metric_value=annualized_rate,
            previous_period_value=previous_value,
            period_over_period_change=growth_rate
        )

        key = (organization_id, MetricType.REVENUE_GROWTH, period_date)
        self.metrics[key] = metric

        return metric

    def calculate_return_on_assets(
        self,
        organization_id: UUID,
        period_date: date,
        net_income: Decimal,
        total_assets: Decimal,
        benchmark: Optional[Decimal] = None
    ) -> FinancialMetric:
        """Calculate Return on Assets (ROA).

        Args:
            organization_id: Organization UUID
            period_date: Period date
            net_income: Net income amount
            total_assets: Total assets amount
            benchmark: Benchmark ROA

        Returns:
            FinancialMetric object
        """
        if total_assets == 0:
            roa = Decimal("0")
        else:
            roa = (net_income / total_assets) * 100

        vs_benchmark = None
        if benchmark is not None:
            vs_benchmark = roa - benchmark

        metric = FinancialMetric(
            organization_id=organization_id,
            metric_type=MetricType.RETURN_ON_ASSETS,
            period_date=period_date,
            metric_value=roa,
            benchmark_value=benchmark,
            vs_benchmark=vs_benchmark
        )

        key = (organization_id, MetricType.RETURN_ON_ASSETS, period_date)
        self.metrics[key] = metric

        return metric

    def calculate_debt_to_equity(
        self,
        organization_id: UUID,
        period_date: date,
        total_debt: Decimal,
        total_equity: Decimal,
        benchmark: Optional[Decimal] = None
    ) -> FinancialMetric:
        """Calculate Debt-to-Equity ratio.

        Args:
            organization_id: Organization UUID
            period_date: Period date
            total_debt: Total debt amount
            total_equity: Total equity amount
            benchmark: Benchmark ratio

        Returns:
            FinancialMetric object
        """
        if total_equity == 0:
            debt_to_equity = Decimal("0")
        else:
            debt_to_equity = total_debt / total_equity

        vs_benchmark = None
        if benchmark is not None:
            vs_benchmark = debt_to_equity - benchmark

        metric = FinancialMetric(
            organization_id=organization_id,
            metric_type=MetricType.DEBT_TO_EQUITY,
            period_date=period_date,
            metric_value=debt_to_equity,
            benchmark_value=benchmark,
            vs_benchmark=vs_benchmark
        )

        key = (organization_id, MetricType.DEBT_TO_EQUITY, period_date)
        self.metrics[key] = metric

        return metric

    def create_kpi(
        self,
        organization_id: UUID,
        name: str,
        code: str,
        period_date: date,
        current_value: Decimal,
        target_value: Optional[Decimal] = None,
        trend: Optional[str] = None,
        unit: str = "",
        formula: Optional[str] = None
    ) -> KPI:
        """Create a KPI entry.

        Args:
            organization_id: Organization UUID
            name: KPI name
            code: KPI code
            period_date: Period date
            current_value: Current value
            target_value: Target value
            trend: Trend direction
            unit: Unit of measurement
            formula: Calculation formula

        Returns:
            KPI object
        """
        status_vs_target = None
        if target_value is not None and target_value != 0:
            status_vs_target = (current_value - target_value) / target_value

        kpi = KPI(
            organization_id=organization_id,
            name=name,
            code=code,
            period_date=period_date,
            current_value=current_value,
            target_value=target_value,
            status_vs_target=status_vs_target,
            unit=unit,
            formula=formula
        )

        key = (organization_id, code, period_date)
        self.kpis[key] = kpi

        return kpi

    def get_metric(
        self,
        organization_id: UUID,
        metric_type: MetricType,
        period_date: date
    ) -> Optional[FinancialMetric]:
        """Get a specific metric.

        Args:
            organization_id: Organization UUID
            metric_type: Metric type
            period_date: Period date

        Returns:
            FinancialMetric or None
        """
        key = (organization_id, metric_type, period_date)
        return self.metrics.get(key)

    def get_kpi(
        self,
        organization_id: UUID,
        kpi_code: str,
        period_date: date
    ) -> Optional[KPI]:
        """Get a specific KPI.

        Args:
            organization_id: Organization UUID
            kpi_code: KPI code
            period_date: Period date

        Returns:
            KPI or None
        """
        key = (organization_id, kpi_code, period_date)
        return self.kpis.get(key)

    def get_metrics_history(
        self,
        organization_id: UUID,
        metric_type: MetricType,
        start_date: date,
        end_date: date
    ) -> List[FinancialMetric]:
        """Get historical metrics for a period.

        Args:
            organization_id: Organization UUID
            metric_type: Metric type
            start_date: Start date
            end_date: End date

        Returns:
            List of FinancialMetric objects
        """
        matching = [
            m for (org_id, mtype, pdate), m in self.metrics.items()
            if org_id == organization_id
            and mtype == metric_type
            and start_date <= pdate <= end_date
        ]

        return sorted(matching, key=lambda m: m.period_date)

    def get_kpi_history(
        self,
        organization_id: UUID,
        kpi_code: str,
        start_date: date,
        end_date: date
    ) -> List[KPI]:
        """Get KPI history for a period.

        Args:
            organization_id: Organization UUID
            kpi_code: KPI code
            start_date: Start date
            end_date: End date

        Returns:
            List of KPI objects
        """
        matching = [
            k for (org_id, code, pdate), k in self.kpis.items()
            if org_id == organization_id
            and code == kpi_code
            and start_date <= pdate <= end_date
        ]

        return sorted(matching, key=lambda k: k.period_date)
