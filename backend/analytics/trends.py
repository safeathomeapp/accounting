"""Trend analysis engine for financial data.

Detects trends, patterns, and anomalies in financial metrics.
"""

from uuid import UUID
from datetime import date
from decimal import Decimal
from typing import List, Tuple, Optional
from statistics import mean, stdev

from backend.models.analytics import TrendAnalysis, TrendDirection


class TrendAnalysisEngine:
    """Analyzes trends in financial data."""

    def __init__(self):
        """Initialize trend engine."""
        self.trends = {}  # (org_id, metric_type, period_start) -> TrendAnalysis

    def analyze_trend(
        self,
        organization_id: UUID,
        metric_type: str,
        values: List[Tuple[date, Decimal]],
        category: Optional[str] = None,
        benchmark: Optional[Decimal] = None
    ) -> TrendAnalysis:
        """Analyze trend in a series of values.

        Args:
            organization_id: Organization UUID
            metric_type: Type of metric
            values: List of (date, value) tuples sorted chronologically
            category: Optional category (e.g., account type)
            benchmark: Optional benchmark value for comparison

        Returns:
            TrendAnalysis object
        """
        if len(values) < 2:
            raise ValueError("Need at least 2 data points")

        dates = [v[0] for v in values]
        data = [float(v[1]) for v in values]

        # Calculate trend direction
        trend_direction = self._calculate_direction(data)

        # Calculate trend strength (0-1)
        strength = self._calculate_strength(data)

        # Calculate growth rate
        growth_rate = ((data[-1] - data[0]) / data[0] * 100) if data[0] != 0 else Decimal("0")

        # Calculate volatility
        volatility = stdev(data) if len(data) > 1 else 0

        # Detect anomalies
        anomalies = self._detect_anomalies(data)

        trend = TrendAnalysis(
            organization_id=organization_id,
            metric_type=metric_type,
            category=category,
            analysis_period_start=dates[0],
            analysis_period_end=dates[-1],
            trend_direction=trend_direction,
            strength=strength,
            average_value=Decimal(str(mean(data))),
            min_value=Decimal(str(min(data))),
            max_value=Decimal(str(max(data))),
            growth_rate=Decimal(str(growth_rate)),
            volatility=volatility,
            anomalies_detected=len(anomalies)
        )

        key = (organization_id, metric_type, dates[0])
        self.trends[key] = trend

        return trend

    def _calculate_direction(self, values: List[float]) -> TrendDirection:
        """Calculate trend direction (upward, downward, stable)."""
        if len(values) < 2:
            return TrendDirection.STABLE

        # Compare first half to second half
        mid = len(values) // 2
        first_half_avg = mean(values[:mid]) if mid > 0 else values[0]
        second_half_avg = mean(values[mid:])

        change_pct = abs((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg != 0 else 0

        # Stable if less than 5% change
        if change_pct < 5:
            return TrendDirection.STABLE

        return TrendDirection.UPWARD if second_half_avg > first_half_avg else TrendDirection.DOWNWARD

    def _calculate_strength(self, values: List[float]) -> float:
        """Calculate trend strength (0-1)."""
        if len(values) < 2:
            return 0.0

        # Use coefficient of determination
        n = len(values)
        x = list(range(n))
        y = values

        x_mean = mean(x)
        y_mean = mean(y)

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator_x = sum((x[i] - x_mean) ** 2 for i in range(n))
        denominator_y = sum((y[i] - y_mean) ** 2 for i in range(n))

        if denominator_x == 0 or denominator_y == 0:
            return 0.0

        r = numerator / (denominator_x * denominator_y) ** 0.5
        r_squared = r ** 2

        return max(0, min(1, r_squared))

    def _detect_anomalies(self, values: List[float]) -> List[int]:
        """Detect anomalies using standard deviation method."""
        if len(values) < 3:
            return []

        mean_val = mean(values)
        std_val = stdev(values)

        if std_val == 0:
            return []

        anomalies = []
        for i, v in enumerate(values):
            z_score = abs((v - mean_val) / std_val)
            if z_score > 2.5:  # 2.5 std deviations
                anomalies.append(i)

        return anomalies

    def get_trend(
        self,
        organization_id: UUID,
        metric_type: str,
        start_date: date
    ) -> Optional[TrendAnalysis]:
        """Get a specific trend analysis."""
        key = (organization_id, metric_type, start_date)
        return self.trends.get(key)

    def get_trends_by_organization(
        self,
        organization_id: UUID,
        direction: Optional[TrendDirection] = None
    ) -> List[TrendAnalysis]:
        """Get all trends for an organization, optionally filtered by direction."""
        matching = [
            t for (org_id, _, _), t in self.trends.items()
            if org_id == organization_id
            and (direction is None or t.trend_direction == direction)
        ]
        return sorted(matching, key=lambda t: t.analysis_period_start)

    def compare_trends(
        self,
        organization_id: UUID,
        metric_type: str,
        current_trend: TrendAnalysis,
        previous_trend: TrendAnalysis
    ) -> dict:
        """Compare current and previous trends."""
        return {
            "direction_change": current_trend.trend_direction != previous_trend.trend_direction,
            "strength_change": current_trend.strength - previous_trend.strength,
            "growth_rate_change": current_trend.growth_rate - previous_trend.growth_rate,
            "volatility_change": current_trend.volatility - previous_trend.volatility,
            "improvement": (
                current_trend.strength > previous_trend.strength and
                current_trend.trend_direction == TrendDirection.UPWARD
            )
        }

    def get_uptrends(self, organization_id: UUID) -> List[TrendAnalysis]:
        """Get all uptrending metrics."""
        return self.get_trends_by_organization(organization_id, TrendDirection.UPWARD)

    def get_downtrends(self, organization_id: UUID) -> List[TrendAnalysis]:
        """Get all downtrending metrics."""
        return self.get_trends_by_organization(organization_id, TrendDirection.DOWNWARD)

    def get_stable_trends(self, organization_id: UUID) -> List[TrendAnalysis]:
        """Get all stable metrics."""
        return self.get_trends_by_organization(organization_id, TrendDirection.STABLE)
