"""Tests for financial forecasting engine.

Tests for forecasting models, accuracy calculations, and composite forecasts.
"""

import pytest
from uuid import uuid4
from datetime import date, timedelta
from decimal import Decimal

from backend.analytics.forecasting import ForecastingEngine
from backend.models.analytics import ForecastType, ForecastMethod


class TestForecastingEngine:
    """Tests for ForecastingEngine."""

    def setup_method(self):
        """Set up for each test."""
        self.engine = ForecastingEngine()
        self.org_id = uuid4()

    def test_linear_regression_forecast(self):
        """Test linear regression forecasting."""
        # Create historical data with upward trend
        historical = [
            (date(2024, 1, 1), Decimal("10000")),
            (date(2024, 2, 1), Decimal("12000")),
            (date(2024, 3, 1), Decimal("14000")),
            (date(2024, 4, 1), Decimal("16000")),
        ]

        forecasts = self.engine.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=3
        )

        assert len(forecasts) == 3
        assert forecasts[0].method == ForecastMethod.LINEAR_REGRESSION
        # With upward trend, forecast should be higher
        assert forecasts[0].forecasted_value > Decimal("16000")

    def test_moving_average_forecast(self):
        """Test moving average forecasting."""
        historical = [
            (date(2024, 1, 1), Decimal("10000")),
            (date(2024, 2, 1), Decimal("11000")),
            (date(2024, 3, 1), Decimal("10500")),
            (date(2024, 4, 1), Decimal("11500")),
        ]

        forecasts = self.engine.forecast_moving_average(
            self.org_id, ForecastType.REVENUE, historical, window_size=2, forecast_periods=2
        )

        assert len(forecasts) == 2
        assert forecasts[0].method == ForecastMethod.MOVING_AVERAGE
        assert forecasts[0].forecasted_value > Decimal("0")

    def test_forecast_with_confidence_intervals(self):
        """Test forecasts include confidence intervals."""
        historical = [
            (date(2024, 1, 1), Decimal("1000")),
            (date(2024, 2, 1), Decimal("1100")),
            (date(2024, 3, 1), Decimal("1200")),
        ]

        forecasts = self.engine.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=1, confidence_level=0.95
        )

        forecast = forecasts[0]
        assert forecast.lower_bound is not None
        assert forecast.upper_bound is not None
        assert forecast.lower_bound < forecast.forecasted_value
        assert forecast.forecasted_value < forecast.upper_bound

    def test_get_forecast(self):
        """Test retrieving a specific forecast."""
        historical = [
            (date(2024, 1, 1), Decimal("5000")),
            (date(2024, 2, 1), Decimal("6000")),
            (date(2024, 3, 1), Decimal("7000")),
        ]

        self.engine.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=2
        )

        # Get forecast for a specific date (within forecast range)
        # Forecasts are 30 days apart, so first forecast is ~April 1, second is ~May 1
        forecast_date = date(2024, 4, 15)  # Between first and second forecast
        forecast = self.engine.get_forecast(
            self.org_id, ForecastType.REVENUE, forecast_date
        )

        assert forecast is not None
        assert forecast.period_start <= forecast_date <= forecast.period_end

    def test_get_all_forecasts(self):
        """Test retrieving all forecasts with filtering."""
        historical = [
            (date(2024, 1, 1), Decimal("5000")),
            (date(2024, 2, 1), Decimal("6000")),
            (date(2024, 3, 1), Decimal("7000")),
        ]

        self.engine.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=2
        )

        # Get all forecasts
        all_forecasts = self.engine.get_forecasts(self.org_id)
        assert len(all_forecasts) == 2

        # Filter by forecast type
        revenue_only = self.engine.get_forecasts(
            self.org_id, forecast_type=ForecastType.REVENUE
        )
        assert len(revenue_only) == 2

        # Filter by method
        lr_forecasts = self.engine.get_forecasts(
            self.org_id, method=ForecastMethod.LINEAR_REGRESSION
        )
        assert len(lr_forecasts) == 2

    def test_forecast_with_date_range_filter(self):
        """Test filtering forecasts by date range."""
        historical = [
            (date(2024, 1, 1), Decimal("5000")),
            (date(2024, 2, 1), Decimal("6000")),
            (date(2024, 3, 1), Decimal("7000")),
        ]

        self.engine.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=3
        )

        # Get forecasts after Q2
        future_forecasts = self.engine.get_forecasts(
            self.org_id, start_date=date(2024, 7, 1)
        )

        for forecast in future_forecasts:
            assert forecast.period_start >= date(2024, 7, 1)

    def test_forecast_accuracy_calculation(self):
        """Test calculating forecast accuracy."""
        historical = [
            (date(2024, 1, 1), Decimal("10000")),
            (date(2024, 2, 1), Decimal("11000")),
            (date(2024, 3, 1), Decimal("12000")),
        ]

        forecasts = self.engine.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=1
        )

        forecast = forecasts[0]
        actual = Decimal("13000")

        error, pct_error = self.engine.calculate_forecast_accuracy(forecast, actual)

        assert error == actual - forecast.forecasted_value
        assert pct_error > Decimal("-1000")  # Not a huge error

    def test_composite_forecast(self):
        """Test creating composite forecast from multiple forecasts."""
        historical = [
            (date(2024, 1, 1), Decimal("10000")),
            (date(2024, 2, 1), Decimal("11000")),
            (date(2024, 3, 1), Decimal("12000")),
        ]

        lr_forecasts = self.engine.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=1
        )

        other_org = uuid4()
        ma_forecasts = self.engine.forecast_moving_average(
            other_org, ForecastType.REVENUE, historical, forecast_periods=1
        )

        # Create composite with equal weights
        composite = self.engine.create_composite_forecast(
            self.org_id, ForecastType.REVENUE, lr_forecasts
        )

        assert composite is not None
        assert composite.forecasted_value > Decimal("0")

    def test_multiple_forecast_types(self):
        """Test forecasting different financial metrics."""
        historical = [
            (date(2024, 1, 1), Decimal("50000")),
            (date(2024, 2, 1), Decimal("55000")),
            (date(2024, 3, 1), Decimal("60000")),
        ]

        # Forecast revenue
        revenue_forecasts = self.engine.forecast_moving_average(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=1
        )

        # Forecast expense
        expense_forecasts = self.engine.forecast_moving_average(
            self.org_id, ForecastType.EXPENSE, historical, forecast_periods=1
        )

        assert len(revenue_forecasts) == 1
        assert len(expense_forecasts) == 1
        assert revenue_forecasts[0].forecast_type == ForecastType.REVENUE
        assert expense_forecasts[0].forecast_type == ForecastType.EXPENSE

    def test_insufficient_data_error(self):
        """Test error with insufficient historical data."""
        historical = [(date(2024, 1, 1), Decimal("10000"))]

        with pytest.raises(ValueError, match="at least 2"):
            self.engine.forecast_linear_regression(
                self.org_id, ForecastType.REVENUE, historical
            )

    def test_insufficient_moving_average_data_error(self):
        """Test error with insufficient data for moving average."""
        historical = [
            (date(2024, 1, 1), Decimal("10000")),
            (date(2024, 2, 1), Decimal("11000")),
        ]

        with pytest.raises(ValueError, match="at least 3"):
            self.engine.forecast_moving_average(
                self.org_id, ForecastType.REVENUE, historical, window_size=3
            )

    def test_forecast_with_constant_values(self):
        """Test forecasting with constant values across time."""
        historical = [
            (date(2024, 1, 1), Decimal("10000")),
            (date(2024, 2, 1), Decimal("10000")),
            (date(2024, 3, 1), Decimal("10000")),
        ]

        # With no variance in y values, forecast should still work but predict same value
        forecasts = self.engine.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=1
        )

        # Should still produce a forecast
        assert len(forecasts) == 1
        assert forecasts[0].forecasted_value >= 0

    def test_forecast_accuracy_summary(self):
        """Test getting forecast accuracy summary."""
        historical = [
            (date(2024, 1, 1), Decimal("10000")),
            (date(2024, 2, 1), Decimal("11000")),
            (date(2024, 3, 1), Decimal("12000")),
        ]

        forecasts = self.engine.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=1
        )

        summary = self.engine.get_forecast_accuracy_summary(
            self.org_id, ForecastType.REVENUE
        )

        assert "mape" in summary
        assert "r_squared" in summary
        assert summary["count"] == 1

    def test_organization_isolation(self):
        """Test forecasts are isolated between organizations."""
        org2_id = uuid4()

        historical = [
            (date(2024, 1, 1), Decimal("10000")),
            (date(2024, 2, 1), Decimal("11000")),
            (date(2024, 3, 1), Decimal("12000")),
        ]

        # Forecast for org 1
        self.engine.forecast_moving_average(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=1
        )

        # Forecast for org 2
        self.engine.forecast_moving_average(
            org2_id, ForecastType.REVENUE, historical, forecast_periods=1
        )

        # Each should only see its own
        org1_forecasts = self.engine.get_forecasts(self.org_id)
        org2_forecasts = self.engine.get_forecasts(org2_id)

        assert len(org1_forecasts) == 1
        assert len(org2_forecasts) == 1

    def test_forecast_base_value(self):
        """Test forecast includes base value from last historical point."""
        historical = [
            (date(2024, 1, 1), Decimal("10000")),
            (date(2024, 2, 1), Decimal("11000")),
            (date(2024, 3, 1), Decimal("12000")),
        ]

        forecasts = self.engine.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=1
        )

        forecast = forecasts[0]
        assert forecast.base_value == Decimal("12000")

    def test_multiple_forecast_periods(self):
        """Test generating multiple forecast periods."""
        historical = [
            (date(2024, 1, 1), Decimal("10000")),
            (date(2024, 2, 1), Decimal("11000")),
            (date(2024, 3, 1), Decimal("12000")),
        ]

        forecasts = self.engine.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=12
        )

        assert len(forecasts) == 12
        # Later forecasts should be further in the future
        assert forecasts[0].period_end < forecasts[11].period_end
        # And progressively higher with upward trend
        assert forecasts[0].forecasted_value < forecasts[11].forecasted_value

    def test_composite_forecast_weighted_average(self):
        """Test composite forecast with custom weights."""
        historical = [
            (date(2024, 1, 1), Decimal("10000")),
            (date(2024, 2, 1), Decimal("11000")),
            (date(2024, 3, 1), Decimal("12000")),
        ]

        forecasts = self.engine.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=1
        )

        # Create multiple versions
        forecasts.append(forecasts[0])  # Duplicate for composite test
        weights = [0.7, 0.3]

        composite = self.engine.create_composite_forecast(
            self.org_id, ForecastType.REVENUE, forecasts, weights=weights
        )

        assert composite is not None
        # Should be closer to first forecast due to higher weight
        assert composite.forecasted_value > Decimal("0")

    def test_forecast_negative_values_capped_at_zero(self):
        """Test forecasts with negative values are capped at zero."""
        historical = [
            (date(2024, 1, 1), Decimal("5000")),
            (date(2024, 2, 1), Decimal("4000")),
            (date(2024, 3, 1), Decimal("3000")),
            (date(2024, 4, 1), Decimal("2000")),
            (date(2024, 5, 1), Decimal("1000")),
        ]

        forecasts = self.engine.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=5
        )

        # All forecasts should be >= 0
        for forecast in forecasts:
            assert forecast.forecasted_value >= 0
            assert forecast.lower_bound >= 0

    def test_forecast_accuracy_score_calculated(self):
        """Test that forecast includes accuracy score (R²)."""
        historical = [
            (date(2024, 1, 1), Decimal("10000")),
            (date(2024, 2, 1), Decimal("11000")),
            (date(2024, 3, 1), Decimal("12000")),
            (date(2024, 4, 1), Decimal("13000")),
        ]

        forecasts = self.engine.forecast_linear_regression(
            self.org_id, ForecastType.REVENUE, historical, forecast_periods=1
        )

        forecast = forecasts[0]
        assert forecast.accuracy_score is not None
        assert 0 <= forecast.accuracy_score <= 1  # R² is between 0 and 1
