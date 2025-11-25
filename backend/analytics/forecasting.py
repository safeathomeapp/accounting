"""Financial forecasting engine.

Provides forecasting capabilities including linear regression,
moving averages, and seasonal analysis.
"""

from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple, Dict
from statistics import mean, stdev

from backend.models.analytics import Forecast, ForecastType, ForecastMethod


class ForecastingEngine:
    """Generates financial forecasts using multiple methods."""

    def __init__(self):
        """Initialize forecasting engine."""
        self.forecasts = {}  # In-memory storage: (org_id, forecast_type) -> List[Forecast]

    def forecast_linear_regression(
        self,
        organization_id: UUID,
        forecast_type: ForecastType,
        historical_values: List[Tuple[date, Decimal]],
        forecast_periods: int = 12,
        confidence_level: float = 0.95
    ) -> List[Forecast]:
        """Generate forecasts using linear regression.

        Args:
            organization_id: Organization UUID
            forecast_type: Type of forecast
            historical_values: List of (date, value) tuples
            forecast_periods: Number of periods to forecast
            confidence_level: Confidence level for intervals (0.95 = 95%)

        Returns:
            List of Forecast objects
        """
        if len(historical_values) < 2:
            raise ValueError("Need at least 2 historical data points")

        # Convert to numeric x values (days from start)
        start_date = historical_values[0][0]
        x_values = [(d - start_date).days for d, _ in historical_values]
        y_values = [float(v) for _, v in historical_values]

        # Calculate slope and intercept
        n = len(x_values)
        x_mean = mean(x_values)
        y_mean = mean(y_values)

        numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            raise ValueError("Cannot calculate regression: no variance in x values")

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Calculate standard error
        residuals = [y_values[i] - (slope * x_values[i] + intercept) for i in range(n)]
        std_error = (sum(r ** 2 for r in residuals) / (n - 2)) ** 0.5 if n > 2 else 0

        # Calculate R²
        ss_res = sum(r ** 2 for r in residuals)
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # Generate forecasts
        forecasts = []
        last_date = historical_values[-1][0]
        base_value = Decimal(str(historical_values[-1][1]))

        for i in range(1, forecast_periods + 1):
            forecast_date = last_date + timedelta(days=30 * i)
            x_forecast = (forecast_date - start_date).days
            y_forecast = slope * x_forecast + intercept

            # Calculate confidence interval
            t_value = 1.96 if confidence_level == 0.95 else 2.576  # t-values for 95% and 99%
            margin = t_value * std_error * (1 + 1/n + (x_forecast - x_mean)**2 / denominator) ** 0.5

            forecast = Forecast(
                organization_id=organization_id,
                forecast_type=forecast_type,
                method=ForecastMethod.LINEAR_REGRESSION,
                period_start=last_date + timedelta(days=30*(i-1)),
                period_end=forecast_date,
                forecast_date=date.today(),
                base_value=base_value,
                forecasted_value=Decimal(str(max(0, y_forecast))),
                lower_bound=Decimal(str(max(0, y_forecast - margin))),
                upper_bound=Decimal(str(y_forecast + margin)),
                confidence_level=confidence_level,
                accuracy_score=r_squared
            )
            forecasts.append(forecast)

        # Store forecasts
        key = (organization_id, forecast_type)
        if key not in self.forecasts:
            self.forecasts[key] = []
        self.forecasts[key].extend(forecasts)

        return forecasts

    def forecast_moving_average(
        self,
        organization_id: UUID,
        forecast_type: ForecastType,
        historical_values: List[Tuple[date, Decimal]],
        window_size: int = 3,
        forecast_periods: int = 12
    ) -> List[Forecast]:
        """Generate forecasts using moving average method.

        Args:
            organization_id: Organization UUID
            forecast_type: Type of forecast
            historical_values: List of (date, value) tuples
            window_size: Size of moving average window
            forecast_periods: Number of periods to forecast

        Returns:
            List of Forecast objects
        """
        if len(historical_values) < window_size:
            raise ValueError(f"Need at least {window_size} historical data points")

        y_values = [float(v) for _, v in historical_values]

        # Calculate moving averages
        moving_avgs = []
        for i in range(window_size - 1, len(y_values)):
            avg = mean(y_values[i - window_size + 1:i + 1])
            moving_avgs.append(avg)

        # Use last moving average as base forecast
        last_moving_avg = moving_avgs[-1]

        # Calculate volatility
        if len(moving_avgs) > 1:
            volatility = stdev(moving_avgs)
        else:
            volatility = 0

        # Generate forecasts
        forecasts = []
        last_date = historical_values[-1][0]
        base_value = Decimal(str(historical_values[-1][1]))

        for i in range(1, forecast_periods + 1):
            forecast_date = last_date + timedelta(days=30 * i)
            forecasted_value = Decimal(str(max(0, last_moving_avg)))

            # Confidence interval based on volatility
            margin = 1.96 * volatility

            forecast = Forecast(
                organization_id=organization_id,
                forecast_type=forecast_type,
                method=ForecastMethod.MOVING_AVERAGE,
                period_start=last_date + timedelta(days=30*(i-1)),
                period_end=forecast_date,
                forecast_date=date.today(),
                base_value=base_value,
                forecasted_value=forecasted_value,
                lower_bound=Decimal(str(max(0, last_moving_avg - margin))),
                upper_bound=Decimal(str(last_moving_avg + margin)),
                confidence_level=0.95
            )
            forecasts.append(forecast)

        # Store forecasts
        key = (organization_id, forecast_type)
        if key not in self.forecasts:
            self.forecasts[key] = []
        self.forecasts[key].extend(forecasts)

        return forecasts

    def get_forecast(
        self,
        organization_id: UUID,
        forecast_type: ForecastType,
        forecast_date: date
    ) -> Optional[Forecast]:
        """Get a specific forecast.

        Args:
            organization_id: Organization UUID
            forecast_type: Type of forecast
            forecast_date: Date of forecast

        Returns:
            Forecast object or None if not found
        """
        key = (organization_id, forecast_type)
        forecasts = self.forecasts.get(key, [])

        for forecast in forecasts:
            if forecast.period_end >= forecast_date >= forecast.period_start:
                return forecast

        return None

    def get_forecasts(
        self,
        organization_id: UUID,
        forecast_type: Optional[ForecastType] = None,
        method: Optional[ForecastMethod] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Forecast]:
        """Get forecasts with optional filtering.

        Args:
            organization_id: Organization UUID
            forecast_type: Filter by forecast type
            method: Filter by forecasting method
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of matching Forecast objects
        """
        matching = []

        for (org_id, ftype), forecasts in self.forecasts.items():
            if org_id != organization_id:
                continue

            if forecast_type and ftype != forecast_type:
                continue

            for forecast in forecasts:
                if method and forecast.method != method:
                    continue

                if start_date and forecast.period_end < start_date:
                    continue

                if end_date and forecast.period_start > end_date:
                    continue

                matching.append(forecast)

        return sorted(matching, key=lambda f: f.period_start)

    def calculate_forecast_accuracy(
        self,
        forecast: Forecast,
        actual_value: Decimal
    ) -> Tuple[Decimal, Decimal]:
        """Calculate forecast accuracy.

        Args:
            forecast: Forecast object
            actual_value: Actual observed value

        Returns:
            Tuple of (error, percentage_error)
        """
        error = actual_value - forecast.forecasted_value
        if forecast.forecasted_value != 0:
            pct_error = (error / forecast.forecasted_value) * 100
        else:
            pct_error = Decimal("0")

        return error, pct_error

    def get_forecast_accuracy_summary(
        self,
        organization_id: UUID,
        forecast_type: ForecastType
    ) -> Dict[str, float]:
        """Get summary of forecast accuracy for a type.

        Args:
            organization_id: Organization UUID
            forecast_type: Type of forecast

        Returns:
            Dict with MAPE and other accuracy metrics
        """
        key = (organization_id, forecast_type)
        forecasts = self.forecasts.get(key, [])

        if not forecasts:
            return {"mape": 0, "count": 0}

        # Filter forecasts with accuracy scores
        accurate = [f for f in forecasts if f.accuracy_score is not None]

        if not accurate:
            return {"mape": 0, "count": len(forecasts)}

        avg_accuracy = sum(f.accuracy_score for f in accurate) / len(accurate)

        # Handle MAPE calculation safely
        mapes = [f.mape for f in accurate if f.mape is not None]
        avg_mape = sum(mapes) / len(mapes) if mapes else 0

        return {
            "mape": avg_mape,
            "r_squared": avg_accuracy,
            "count": len(forecasts),
            "accurate_count": len(accurate)
        }

    def create_composite_forecast(
        self,
        organization_id: UUID,
        forecast_type: ForecastType,
        forecasts: List[Forecast],
        weights: Optional[List[float]] = None
    ) -> Forecast:
        """Combine multiple forecasts into composite forecast.

        Args:
            organization_id: Organization UUID
            forecast_type: Type of forecast
            forecasts: List of forecast objects
            weights: Optional weights for each forecast

        Returns:
            Composite Forecast object
        """
        if not forecasts:
            raise ValueError("Need at least one forecast")

        if weights is None:
            weights = [1.0 / len(forecasts)] * len(forecasts)

        if len(weights) != len(forecasts):
            raise ValueError("Weights must match number of forecasts")

        # Calculate weighted average
        weighted_value = sum(
            float(f.forecasted_value) * w
            for f, w in zip(forecasts, weights)
        )

        lower_bound = sum(
            float(f.lower_bound) * w
            for f, w in zip(forecasts, weights)
        ) if all(f.lower_bound for f in forecasts) else None

        upper_bound = sum(
            float(f.upper_bound) * w
            for f, w in zip(forecasts, weights)
        ) if all(f.upper_bound for f in forecasts) else None

        composite = Forecast(
            organization_id=organization_id,
            forecast_type=forecast_type,
            method=ForecastMethod.MOVING_AVERAGE,  # Composite method
            period_start=forecasts[0].period_start,
            period_end=forecasts[0].period_end,
            forecast_date=date.today(),
            base_value=Decimal(str(weighted_value)),
            forecasted_value=Decimal(str(weighted_value)),
            lower_bound=Decimal(str(lower_bound)) if lower_bound else None,
            upper_bound=Decimal(str(upper_bound)) if upper_bound else None,
            notes="Composite forecast from multiple methods"
        )

        return composite
