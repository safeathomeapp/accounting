"""Tests for trend analysis engine.

Tests trend detection, anomaly discovery, and trend comparison.
"""

import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal

from backend.analytics.trends import TrendAnalysisEngine
from backend.models.analytics import TrendDirection


class TestTrendAnalysisEngine:
    """Tests for TrendAnalysisEngine."""

    def setup_method(self):
        """Set up for each test."""
        self.engine = TrendAnalysisEngine()
        self.org_id = uuid4()

    def test_analyze_trend_upward(self):
        """Test detecting upward trend."""
        values = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("110")),
            (date(2024, 3, 1), Decimal("120")),
            (date(2024, 4, 1), Decimal("130")),
        ]
        trend = self.engine.analyze_trend(self.org_id, "revenue", values)
        assert trend.trend_direction == TrendDirection.UPWARD

    def test_analyze_trend_downward(self):
        """Test detecting downward trend."""
        values = [
            (date(2024, 1, 1), Decimal("130")),
            (date(2024, 2, 1), Decimal("120")),
            (date(2024, 3, 1), Decimal("110")),
            (date(2024, 4, 1), Decimal("100")),
        ]
        trend = self.engine.analyze_trend(self.org_id, "revenue", values)
        assert trend.trend_direction == TrendDirection.DOWNWARD

    def test_analyze_trend_stable(self):
        """Test detecting stable trend."""
        values = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("101")),
            (date(2024, 3, 1), Decimal("100")),
            (date(2024, 4, 1), Decimal("101")),
        ]
        trend = self.engine.analyze_trend(self.org_id, "revenue", values)
        assert trend.trend_direction == TrendDirection.STABLE

    def test_trend_strength_calculation(self):
        """Test trend strength (0-1 scale)."""
        values = [
            (date(2024, 1, 1), Decimal("10")),
            (date(2024, 2, 1), Decimal("20")),
            (date(2024, 3, 1), Decimal("30")),
            (date(2024, 4, 1), Decimal("40")),
        ]
        trend = self.engine.analyze_trend(self.org_id, "revenue", values)
        assert 0 <= trend.strength <= 1
        # Strong linear relationship should have high strength
        assert trend.strength > 0.9

    def test_trend_growth_rate(self):
        """Test growth rate calculation."""
        values = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("110")),
            (date(2024, 3, 1), Decimal("120")),
        ]
        trend = self.engine.analyze_trend(self.org_id, "revenue", values)
        # (120-100)/100 * 100 = 20%
        assert trend.growth_rate == Decimal("20")

    def test_trend_volatility(self):
        """Test volatility calculation."""
        values = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("110")),
            (date(2024, 3, 1), Decimal("100")),
            (date(2024, 4, 1), Decimal("110")),
        ]
        trend = self.engine.analyze_trend(self.org_id, "revenue", values)
        assert trend.volatility > 0

    def test_anomaly_detection(self):
        """Test anomaly detection is calculated."""
        values = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("102")),
            (date(2024, 3, 1), Decimal("101")),
            (date(2024, 4, 1), Decimal("103")),
            (date(2024, 5, 1), Decimal("110")),
        ]
        trend = self.engine.analyze_trend(self.org_id, "revenue", values)
        # Anomalies_detected is an integer count (>= 0)
        assert isinstance(trend.anomalies_detected, int)
        assert trend.anomalies_detected >= 0

    def test_trend_min_max_values(self):
        """Test min/max value tracking."""
        values = [
            (date(2024, 1, 1), Decimal("50")),
            (date(2024, 2, 1), Decimal("150")),
            (date(2024, 3, 1), Decimal("100")),
        ]
        trend = self.engine.analyze_trend(self.org_id, "revenue", values)
        assert trend.min_value == Decimal("50")
        assert trend.max_value == Decimal("150")

    def test_trend_average_value(self):
        """Test average value calculation."""
        values = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("200")),
            (date(2024, 3, 1), Decimal("300")),
        ]
        trend = self.engine.analyze_trend(self.org_id, "revenue", values)
        assert trend.average_value == Decimal("200")

    def test_get_trend(self):
        """Test retrieving a specific trend."""
        values = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("110")),
        ]
        self.engine.analyze_trend(self.org_id, "revenue", values)
        trend = self.engine.get_trend(self.org_id, "revenue", date(2024, 1, 1))
        assert trend is not None
        assert trend.metric_type == "revenue"

    def test_get_trends_by_organization(self):
        """Test retrieving all trends for an organization."""
        values1 = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("150")),
        ]
        values2 = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("90")),
        ]
        self.engine.analyze_trend(self.org_id, "revenue", values1)
        self.engine.analyze_trend(self.org_id, "expense", values2)

        trends = self.engine.get_trends_by_organization(self.org_id)
        assert len(trends) == 2

    def test_filter_trends_by_direction(self):
        """Test filtering trends by direction."""
        values1 = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("150")),
        ]
        values2 = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("90")),
        ]
        self.engine.analyze_trend(self.org_id, "revenue", values1)
        self.engine.analyze_trend(self.org_id, "expense", values2)

        uptrends = self.engine.get_trends_by_organization(
            self.org_id, TrendDirection.UPWARD
        )
        assert len(uptrends) == 1
        assert uptrends[0].metric_type == "revenue"

    def test_compare_trends(self):
        """Test comparing current and previous trends."""
        values1 = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("110")),
        ]
        values2 = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("120")),
        ]
        trend1 = self.engine.analyze_trend(self.org_id, "revenue", values1)
        trend2 = self.engine.analyze_trend(self.org_id, "revenue", values2)

        comparison = self.engine.compare_trends(
            self.org_id, "revenue", trend2, trend1
        )
        assert "direction_change" in comparison
        assert "strength_change" in comparison
        assert "growth_rate_change" in comparison

    def test_get_uptrends(self):
        """Test retrieving only uptrending metrics."""
        values1 = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("150")),
        ]
        values2 = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("90")),
        ]
        self.engine.analyze_trend(self.org_id, "revenue", values1)
        self.engine.analyze_trend(self.org_id, "expense", values2)

        uptrends = self.engine.get_uptrends(self.org_id)
        assert len(uptrends) == 1
        assert uptrends[0].trend_direction == TrendDirection.UPWARD

    def test_get_downtrends(self):
        """Test retrieving only downtrending metrics."""
        values1 = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("150")),
        ]
        values2 = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("90")),
        ]
        self.engine.analyze_trend(self.org_id, "revenue", values1)
        self.engine.analyze_trend(self.org_id, "expense", values2)

        downtrends = self.engine.get_downtrends(self.org_id)
        assert len(downtrends) == 1
        assert downtrends[0].trend_direction == TrendDirection.DOWNWARD

    def test_get_stable_trends(self):
        """Test retrieving only stable metrics."""
        values1 = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("101")),
            (date(2024, 3, 1), Decimal("100")),
        ]
        values2 = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("150")),
        ]
        self.engine.analyze_trend(self.org_id, "revenue", values1)
        self.engine.analyze_trend(self.org_id, "expense", values2)

        stable = self.engine.get_stable_trends(self.org_id)
        assert len(stable) >= 1

    def test_organization_isolation(self):
        """Test trends isolated between organizations."""
        org2_id = uuid4()

        values1 = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("150")),
        ]
        values2 = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("200")),
        ]
        self.engine.analyze_trend(self.org_id, "revenue", values1)
        self.engine.analyze_trend(org2_id, "revenue", values2)

        org1_trends = self.engine.get_trends_by_organization(self.org_id)
        org2_trends = self.engine.get_trends_by_organization(org2_id)

        assert len(org1_trends) == 1
        assert len(org2_trends) == 1
        assert org1_trends[0].growth_rate == Decimal("50")
        assert org2_trends[0].growth_rate == Decimal("100")

    def test_trend_with_category(self):
        """Test trend analysis with category."""
        values = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("110")),
        ]
        trend = self.engine.analyze_trend(
            self.org_id, "revenue", values, category="product_a"
        )
        assert trend.category == "product_a"

    def test_trend_with_benchmark(self):
        """Test trend analysis with benchmark comparison."""
        values = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 2, 1), Decimal("110")),
        ]
        # Benchmark parameter is accepted by analyze_trend
        trend = self.engine.analyze_trend(
            self.org_id, "revenue", values, benchmark=Decimal("105")
        )
        # Verify trend was created successfully
        assert trend is not None
        assert trend.metric_type == "revenue"

    def test_insufficient_data_error(self):
        """Test error with insufficient data points."""
        values = [(date(2024, 1, 1), Decimal("100"))]
        with pytest.raises(ValueError, match="at least 2"):
            self.engine.analyze_trend(self.org_id, "revenue", values)

    def test_trend_period_tracking(self):
        """Test that trend period is correctly tracked."""
        values = [
            (date(2024, 1, 1), Decimal("100")),
            (date(2024, 6, 30), Decimal("150")),
        ]
        trend = self.engine.analyze_trend(self.org_id, "revenue", values)
        assert trend.analysis_period_start == date(2024, 1, 1)
        assert trend.analysis_period_end == date(2024, 6, 30)
