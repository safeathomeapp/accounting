"""Tests for analytics persistence layer.

Tests repository pattern for database operations on analytics models.
"""

import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.models.analytics import (
    Forecast, FinancialMetric, TrendAnalysis, KPI, DashboardWidget,
    ForecastType, ForecastMethod, MetricType, TrendDirection
)
from backend.analytics.repositories import (
    ForecastRepository, MetricRepository, TrendRepository,
    KPIRepository, DashboardWidgetRepository
)
from backend.database import get_db


@pytest.fixture
def db_session():
    """Get database session for tests."""
    from backend.database import SessionLocal
    session = SessionLocal()
    yield session
    session.close()


class TestForecastRepository:
    """Tests for ForecastRepository."""

    def test_create_forecast(self, db_session: Session):
        """Test creating a forecast."""
        repo = ForecastRepository(db_session)
        org_id = uuid4()

        forecast = Forecast(
            organization_id=org_id,
            forecast_type=ForecastType.REVENUE,
            method=ForecastMethod.LINEAR_REGRESSION,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 2, 1),
            forecast_date=date(2024, 1, 15),
            base_value=Decimal("10000"),
            forecasted_value=Decimal("11000"),
            accuracy_score=0.95
        )

        created = repo.create(forecast)
        assert created.id is not None
        assert created.organization_id == org_id

    def test_get_forecast_by_id(self, db_session: Session):
        """Test retrieving forecast by ID."""
        repo = ForecastRepository(db_session)
        org_id = uuid4()

        forecast = Forecast(
            organization_id=org_id,
            forecast_type=ForecastType.REVENUE,
            method=ForecastMethod.LINEAR_REGRESSION,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 2, 1),
            forecast_date=date(2024, 1, 15),
            base_value=Decimal("10000"),
            forecasted_value=Decimal("11000")
        )
        created = repo.create(forecast)

        retrieved = repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_forecasts_by_org(self, db_session: Session):
        """Test retrieving forecasts by organization."""
        repo = ForecastRepository(db_session)
        org_id = uuid4()

        for i in range(3):
            forecast = Forecast(
                organization_id=org_id,
                forecast_type=ForecastType.REVENUE,
                method=ForecastMethod.LINEAR_REGRESSION,
                period_start=date(2024, i + 1, 1),
                period_end=date(2024, i + 2, 1),
                forecast_date=date(2024, i + 1, 15),
                base_value=Decimal("10000"),
                forecasted_value=Decimal("11000")
            )
            repo.create(forecast)

        forecasts = repo.get_by_org(org_id)
        assert len(forecasts) == 3

    def test_filter_forecasts_by_type(self, db_session: Session):
        """Test filtering forecasts by type."""
        repo = ForecastRepository(db_session)
        org_id = uuid4()

        # Create different types
        for forecast_type in [ForecastType.REVENUE, ForecastType.EXPENSE]:
            forecast = Forecast(
                organization_id=org_id,
                forecast_type=forecast_type,
                method=ForecastMethod.LINEAR_REGRESSION,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 2, 1),
                forecast_date=date(2024, 1, 15),
                base_value=Decimal("10000"),
                forecasted_value=Decimal("11000")
            )
            repo.create(forecast)

        revenue_forecasts = repo.get_by_org(org_id, forecast_type=ForecastType.REVENUE)
        assert len(revenue_forecasts) == 1
        assert revenue_forecasts[0].forecast_type == ForecastType.REVENUE

    def test_organization_isolation(self, db_session: Session):
        """Test forecasts isolated between organizations."""
        repo = ForecastRepository(db_session)
        org1_id = uuid4()
        org2_id = uuid4()

        for org_id in [org1_id, org2_id]:
            forecast = Forecast(
                organization_id=org_id,
                forecast_type=ForecastType.REVENUE,
                method=ForecastMethod.LINEAR_REGRESSION,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 2, 1),
                forecast_date=date(2024, 1, 15),
                base_value=Decimal("10000"),
                forecasted_value=Decimal("11000")
            )
            repo.create(forecast)

        org1_forecasts = repo.get_by_org(org1_id)
        org2_forecasts = repo.get_by_org(org2_id)

        assert len(org1_forecasts) == 1
        assert len(org2_forecasts) == 1


class TestMetricRepository:
    """Tests for MetricRepository."""

    def test_create_metric(self, db_session: Session):
        """Test creating a metric."""
        repo = MetricRepository(db_session)
        org_id = uuid4()

        metric = FinancialMetric(
            organization_id=org_id,
            metric_type=MetricType.NET_PROFIT_MARGIN,
            period_date=date(2024, 1, 1),
            metric_value=Decimal("25.50")
        )

        created = repo.create(metric)
        assert created.id is not None
        assert created.metric_value == Decimal("25.50")

    def test_get_metric_by_org_and_type(self, db_session: Session):
        """Test retrieving metric by org and type."""
        repo = MetricRepository(db_session)
        org_id = uuid4()

        metric = FinancialMetric(
            organization_id=org_id,
            metric_type=MetricType.CURRENT_RATIO,
            period_date=date(2024, 1, 1),
            metric_value=Decimal("2.5")
        )
        repo.create(metric)

        retrieved = repo.get_by_org_and_type(
            org_id, MetricType.CURRENT_RATIO, date(2024, 1, 1)
        )
        assert retrieved is not None
        assert retrieved.metric_value == Decimal("2.5")

    def test_get_metric_history(self, db_session: Session):
        """Test retrieving metric history."""
        repo = MetricRepository(db_session)
        org_id = uuid4()

        for month in range(1, 4):
            metric = FinancialMetric(
                organization_id=org_id,
                metric_type=MetricType.REVENUE_GROWTH,
                period_date=date(2024, month, 1),
                metric_value=Decimal("10") + Decimal(month)
            )
            repo.create(metric)

        history = repo.get_history(
            org_id, MetricType.REVENUE_GROWTH,
            date(2024, 1, 1), date(2024, 3, 31)
        )
        assert len(history) == 3

    def test_metrics_ordered_by_date(self, db_session: Session):
        """Test metrics returned in chronological order."""
        repo = MetricRepository(db_session)
        org_id = uuid4()

        # Create in reverse order
        for month in [3, 1, 2]:
            metric = FinancialMetric(
                organization_id=org_id,
                metric_type=MetricType.NET_PROFIT_MARGIN,
                period_date=date(2024, month, 1),
                metric_value=Decimal("20")
            )
            repo.create(metric)

        history = repo.get_by_org(org_id)
        assert history[0].period_date == date(2024, 1, 1)
        assert history[1].period_date == date(2024, 2, 1)
        assert history[2].period_date == date(2024, 3, 1)


class TestTrendRepository:
    """Tests for TrendRepository."""

    def test_create_trend(self, db_session: Session):
        """Test creating a trend."""
        repo = TrendRepository(db_session)
        org_id = uuid4()

        trend = TrendAnalysis(
            organization_id=org_id,
            metric_type="revenue",
            analysis_period_start=date(2024, 1, 1),
            analysis_period_end=date(2024, 3, 1),
            trend_direction=TrendDirection.UPWARD,
            strength=0.85
        )

        created = repo.create(trend)
        assert created.id is not None
        assert created.trend_direction == TrendDirection.UPWARD

    def test_get_trends_by_org(self, db_session: Session):
        """Test retrieving trends by organization."""
        repo = TrendRepository(db_session)
        org_id = uuid4()

        for i in range(2):
            trend = TrendAnalysis(
                organization_id=org_id,
                metric_type=f"metric_{i}",
                analysis_period_start=date(2024, 1, 1),
                analysis_period_end=date(2024, 3, 1),
                trend_direction=TrendDirection.UPWARD,
                strength=0.85
            )
            repo.create(trend)

        trends = repo.get_by_org(org_id)
        assert len(trends) == 2

    def test_filter_trends_by_direction(self, db_session: Session):
        """Test filtering trends by direction."""
        repo = TrendRepository(db_session)
        org_id = uuid4()

        for direction in [TrendDirection.UPWARD, TrendDirection.DOWNWARD]:
            trend = TrendAnalysis(
                organization_id=org_id,
                metric_type=f"{direction.value}",
                analysis_period_start=date(2024, 1, 1),
                analysis_period_end=date(2024, 3, 1),
                trend_direction=direction,
                strength=0.85
            )
            repo.create(trend)

        uptrends = repo.get_by_direction(org_id, TrendDirection.UPWARD)
        assert len(uptrends) == 1
        assert uptrends[0].trend_direction == TrendDirection.UPWARD


class TestKPIRepository:
    """Tests for KPIRepository."""

    def test_create_kpi(self, db_session: Session):
        """Test creating a KPI."""
        repo = KPIRepository(db_session)
        org_id = uuid4()
        code = f"DSO_{uuid4().hex[:8]}"

        kpi = KPI(
            organization_id=org_id,
            name="Days Sales Outstanding",
            code=code,
            period_date=date(2024, 1, 1),
            current_value=Decimal("45"),
            target_value=Decimal("30"),
            unit="days"
        )

        created = repo.create(kpi)
        assert created.id is not None
        assert created.code == code

    def test_get_kpi_by_org_and_code(self, db_session: Session):
        """Test retrieving KPI by org and code."""
        repo = KPIRepository(db_session)
        org_id = uuid4()
        code = f"REV_{uuid4().hex[:8]}"

        kpi = KPI(
            organization_id=org_id,
            name="Revenue",
            code=code,
            period_date=date(2024, 1, 1),
            current_value=Decimal("100000"),
            unit="USD"
        )
        repo.create(kpi)

        retrieved = repo.get_by_org_and_code(org_id, code, date(2024, 1, 1))
        assert retrieved is not None
        assert retrieved.code == code

    def test_get_kpi_history(self, db_session: Session):
        """Test retrieving KPI history."""
        repo = KPIRepository(db_session)
        org_id = uuid4()
        code = f"CCC_{uuid4().hex[:8]}"

        for month in range(1, 4):
            kpi = KPI(
                organization_id=org_id,
                name="Cash Conversion Cycle",
                code=code,
                period_date=date(2024, month, 1),
                current_value=Decimal("50") + Decimal(month),
                unit="days"
            )
            repo.create(kpi)

        history = repo.get_history(
            org_id, code,
            date(2024, 1, 1), date(2024, 3, 31)
        )
        assert len(history) == 3

    def test_get_kpis_by_org(self, db_session: Session):
        """Test retrieving all KPIs for organization."""
        repo = KPIRepository(db_session)
        org_id = uuid4()

        names = ["DSO", "CCC", "ROA"]
        for name in names:
            code = f"{name}_{uuid4().hex[:8]}"
            kpi = KPI(
                organization_id=org_id,
                name=name,
                code=code,
                period_date=date(2024, 1, 1),
                current_value=Decimal("50"),
                unit="days"
            )
            repo.create(kpi)

        kpis = repo.get_by_org(org_id, date(2024, 1, 1))
        assert len(kpis) == 3


class TestDashboardWidgetRepository:
    """Tests for DashboardWidgetRepository."""

    def test_create_widget(self, db_session: Session):
        """Test creating a widget."""
        repo = DashboardWidgetRepository(db_session)
        org_id = uuid4()

        widget = DashboardWidget(
            organization_id=org_id,
            title="Revenue Trend",
            widget_type="chart",
            data_source="revenue_forecast",
            position=1
        )

        created = repo.create(widget)
        assert created.id is not None
        assert created.title == "Revenue Trend"

    def test_get_widget_by_id(self, db_session: Session):
        """Test retrieving widget by ID."""
        repo = DashboardWidgetRepository(db_session)
        org_id = uuid4()

        widget = DashboardWidget(
            organization_id=org_id,
            title="Test Widget",
            widget_type="kpi",
            data_source="test",
            position=0
        )
        created = repo.create(widget)

        retrieved = repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.title == "Test Widget"

    def test_get_widgets_by_org(self, db_session: Session):
        """Test retrieving widgets by organization."""
        repo = DashboardWidgetRepository(db_session)
        org_id = uuid4()

        for i in range(3):
            widget = DashboardWidget(
                organization_id=org_id,
                title=f"Widget {i}",
                widget_type="chart",
                data_source=f"source_{i}",
                position=i
            )
            repo.create(widget)

        widgets = repo.get_by_org(org_id)
        assert len(widgets) == 3

    def test_widgets_ordered_by_position(self, db_session: Session):
        """Test widgets returned in position order."""
        repo = DashboardWidgetRepository(db_session)
        org_id = uuid4()

        # Create in reverse order
        for pos in [3, 1, 2]:
            widget = DashboardWidget(
                organization_id=org_id,
                title=f"Widget {pos}",
                widget_type="chart",
                data_source=f"source_{pos}",
                position=pos
            )
            repo.create(widget)

        widgets = repo.get_by_org(org_id)
        assert widgets[0].position == 1
        assert widgets[1].position == 2
        assert widgets[2].position == 3

    def test_get_pinned_widgets(self, db_session: Session):
        """Test retrieving pinned widgets."""
        repo = DashboardWidgetRepository(db_session)
        org_id = uuid4()

        # Create some pinned, some not
        for i in range(3):
            widget = DashboardWidget(
                organization_id=org_id,
                title=f"Widget {i}",
                widget_type="chart",
                data_source=f"source_{i}",
                position=i,
                is_pinned=(i < 2)  # First 2 are pinned
            )
            repo.create(widget)

        pinned = repo.get_pinned(org_id)
        assert len(pinned) == 2

    def test_update_widget_position(self, db_session: Session):
        """Test updating widget position."""
        repo = DashboardWidgetRepository(db_session)
        org_id = uuid4()

        widget = DashboardWidget(
            organization_id=org_id,
            title="Test",
            widget_type="kpi",
            data_source="test",
            position=1
        )
        created = repo.create(widget)

        success = repo.update_position(org_id, created.id, 5)
        assert success is True

        updated = repo.get_by_id(created.id)
        assert updated.position == 5

    def test_soft_delete_widget(self, db_session: Session):
        """Test soft deleting a widget."""
        repo = DashboardWidgetRepository(db_session)
        org_id = uuid4()

        widget = DashboardWidget(
            organization_id=org_id,
            title="Delete Me",
            widget_type="chart",
            data_source="delete",
            position=0
        )
        created = repo.create(widget)

        repo.delete(created.id)

        retrieved = repo.get_by_id(created.id)
        assert retrieved is None

    def test_cross_org_isolation(self, db_session: Session):
        """Test widgets isolated between organizations."""
        repo = DashboardWidgetRepository(db_session)
        org1_id = uuid4()
        org2_id = uuid4()

        for org_id in [org1_id, org2_id]:
            widget = DashboardWidget(
                organization_id=org_id,
                title="Test",
                widget_type="chart",
                data_source="test",
                position=0
            )
            repo.create(widget)

        org1_widgets = repo.get_by_org(org1_id)
        org2_widgets = repo.get_by_org(org2_id)

        assert len(org1_widgets) == 1
        assert len(org2_widgets) == 1
        assert org1_widgets[0].organization_id == org1_id
        assert org2_widgets[0].organization_id == org2_id
