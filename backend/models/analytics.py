"""Database models for advanced analytics and forecasting.

Models for forecasts, metrics, trends, and business intelligence.
"""

from datetime import datetime, timezone, date
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, Date, Text, Numeric, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
import enum

from backend.models import Base


class ForecastType(str, enum.Enum):
    """Types of forecasts."""
    REVENUE = "revenue"
    EXPENSE = "expense"
    CASH_FLOW = "cash_flow"
    PROFIT = "profit"
    ACCOUNT_BALANCE = "account_balance"


class ForecastMethod(str, enum.Enum):
    """Forecasting methods."""
    LINEAR_REGRESSION = "linear_regression"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"
    MANUAL = "manual"


class MetricType(str, enum.Enum):
    """Financial metrics."""
    GROSS_PROFIT_MARGIN = "gross_profit_margin"
    NET_PROFIT_MARGIN = "net_profit_margin"
    RETURN_ON_ASSETS = "return_on_assets"
    RETURN_ON_EQUITY = "return_on_equity"
    CURRENT_RATIO = "current_ratio"
    QUICK_RATIO = "quick_ratio"
    DEBT_TO_EQUITY = "debt_to_equity"
    ASSET_TURNOVER = "asset_turnover"
    REVENUE_GROWTH = "revenue_growth"
    EXPENSE_RATIO = "expense_ratio"


class TrendDirection(str, enum.Enum):
    """Trend direction."""
    UPWARD = "upward"
    DOWNWARD = "downward"
    STABLE = "stable"


class Forecast(Base):
    """Financial forecast model."""
    __tablename__ = "forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    forecast_type = Column(Enum(ForecastType), nullable=False)
    method = Column(Enum(ForecastMethod), nullable=False)

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    forecast_date = Column(Date, nullable=False)

    base_value = Column(Numeric(precision=15, scale=2), nullable=False)  # Starting value
    forecasted_value = Column(Numeric(precision=15, scale=2), nullable=False)  # Predicted value
    lower_bound = Column(Numeric(precision=15, scale=2))  # Confidence interval lower
    upper_bound = Column(Numeric(precision=15, scale=2))  # Confidence interval upper
    confidence_level = Column(Float, default=0.95)  # 95% confidence

    accuracy_score = Column(Float)  # R² or similar metric
    mape = Column(Float)  # Mean Absolute Percentage Error

    reference_account_id = Column(UUID(as_uuid=True))  # If forecast is account-specific
    reference_category = Column(String(100))  # Transaction category if applicable

    notes = Column(Text)
    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        """Initialize with defaults."""
        if 'is_active' not in kwargs:
            kwargs['is_active'] = True
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Forecast {self.forecast_type.value} {self.period_start} to {self.period_end}>"


class FinancialMetric(Base):
    """Financial metric calculation model."""
    __tablename__ = "financial_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    metric_type = Column(Enum(MetricType), nullable=False)

    period_date = Column(Date, nullable=False, index=True)
    metric_value = Column(Numeric(precision=15, scale=4), nullable=False)

    # For comparative analysis
    previous_period_value = Column(Numeric(precision=15, scale=4))
    period_over_period_change = Column(Numeric(precision=15, scale=4))  # Percentage

    benchmark_value = Column(Numeric(precision=15, scale=4))  # Industry/target benchmark
    vs_benchmark = Column(Numeric(precision=15, scale=4))  # Variance from benchmark

    calculation_notes = Column(Text)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        """Initialize with defaults."""
        if 'is_active' not in kwargs:
            kwargs['is_active'] = True
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Metric {self.metric_type.value} {self.period_date} = {self.metric_value}>"


class TrendAnalysis(Base):
    """Trend analysis model."""
    __tablename__ = "trend_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    metric_type = Column(String(100), nullable=False)  # e.g., "revenue", "gross_profit"
    category = Column(String(100))  # e.g., account category

    analysis_period_start = Column(Date, nullable=False)
    analysis_period_end = Column(Date, nullable=False)

    trend_direction = Column(Enum(TrendDirection), nullable=False)
    strength = Column(Float)  # 0.0 to 1.0, how strong is the trend

    average_value = Column(Numeric(precision=15, scale=2))
    min_value = Column(Numeric(precision=15, scale=2))
    max_value = Column(Numeric(precision=15, scale=2))

    growth_rate = Column(Numeric(precision=15, scale=4))  # Percentage per period
    volatility = Column(Float)  # Standard deviation

    seasonal_pattern = Column(Text)  # JSON: seasonal indices
    anomalies_detected = Column(Integer, default=0)  # Count of anomalies

    notes = Column(Text)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Trend {self.metric_type} {self.trend_direction.value} {self.analysis_period_start}>"


class KPI(Base):
    """Key Performance Indicator model."""
    __tablename__ = "kpis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False, unique=True)  # e.g., "DSO", "CCC"
    description = Column(Text)

    period_date = Column(Date, nullable=False, index=True)
    current_value = Column(Numeric(precision=15, scale=4), nullable=False)
    target_value = Column(Numeric(precision=15, scale=4))

    # Status: how close to target (-1 = worse, 0 = on target, 1 = exceeds)
    status_vs_target = Column(Float)

    # Trend: how it's changing relative to previous period
    trend = Column(Enum(TrendDirection))
    period_over_period_change = Column(Numeric(precision=15, scale=4))

    unit = Column(String(50))  # "days", "%", "$", etc.
    formula = Column(Text)  # How this KPI is calculated

    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        """Initialize with defaults."""
        if 'is_active' not in kwargs:
            kwargs['is_active'] = True
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<KPI {self.code} = {self.current_value} {self.unit}>"


class DashboardWidget(Base):
    """Dashboard widget configuration."""
    __tablename__ = "dashboard_widgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    title = Column(String(200), nullable=False)
    widget_type = Column(String(50), nullable=False)  # "chart", "metric", "forecast", etc.

    position = Column(Integer)  # Order on dashboard
    size = Column(String(20), default="medium")  # small, medium, large

    data_source = Column(String(100), nullable=False)  # e.g., "revenue_forecast", "profit_margin"
    metric_types = Column(String(500))  # Comma-separated list of metrics

    period_range = Column(String(50))  # "last_30_days", "last_quarter", "last_year", "custom"

    config = Column(Text)  # JSON: widget-specific config

    is_active = Column(Boolean, default=True, index=True)
    is_pinned = Column(Boolean, default=False)  # Always show on dashboard

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        """Initialize with defaults."""
        if 'is_active' not in kwargs:
            kwargs['is_active'] = True
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Widget {self.title} ({self.widget_type})>"
