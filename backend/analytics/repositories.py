"""Repository pattern for analytics data persistence.

Handles all database operations for analytics models with
organization isolation enforcement.
"""

from uuid import UUID
from datetime import date
from typing import List, Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.models.analytics import (
    Forecast, FinancialMetric, TrendAnalysis, KPI, DashboardWidget,
    ForecastType, ForecastMethod, MetricType, TrendDirection
)
from backend.analytics.auth import OrganizationAuthorizer, OrgAuthError


class ForecastRepository:
    """Repository for Forecast persistence with organization isolation."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
        self.auth = OrganizationAuthorizer(session)

    def create(self, forecast: Forecast, requesting_org_id: Optional[UUID] = None) -> Forecast:
        """Create a new forecast with org validation."""
        # Validate org access
        org_id = self.auth.validate_org_access(
            forecast.organization_id, requesting_org_id, "write"
        )
        self.session.add(forecast)
        self.session.commit()
        self.auth.log_access(org_id, "create", "forecast", forecast.id)
        return forecast

    def get_by_id(
        self, forecast_id: UUID, requesting_org_id: Optional[UUID] = None
    ) -> Optional[Forecast]:
        """Get forecast by ID with org validation."""
        forecast = self.session.query(Forecast).filter(
            Forecast.id == forecast_id
        ).first()

        if forecast and requesting_org_id:
            self.auth.validate_entity_org(forecast.organization_id, requesting_org_id, "forecast")
            self.auth.log_access(requesting_org_id, "read", "forecast", forecast_id)

        return forecast

    def get_by_org(
        self,
        organization_id: UUID,
        forecast_type: Optional[ForecastType] = None,
        method: Optional[ForecastMethod] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Forecast]:
        """Get forecasts for an organization with optional filters."""
        query = self.session.query(Forecast).filter(
            Forecast.organization_id == organization_id,
            Forecast.is_active == True
        )

        if forecast_type:
            query = query.filter(Forecast.forecast_type == forecast_type)

        if method:
            query = query.filter(Forecast.method == method)

        if start_date:
            query = query.filter(Forecast.period_start >= start_date)

        if end_date:
            query = query.filter(Forecast.period_end <= end_date)

        return query.order_by(Forecast.period_start).all()

    def get_active(self, organization_id: UUID) -> List[Forecast]:
        """Get all active forecasts."""
        return self.session.query(Forecast).filter(
            Forecast.organization_id == organization_id,
            Forecast.is_active == True
        ).order_by(Forecast.period_start).all()

    def update(self, forecast: Forecast) -> Forecast:
        """Update a forecast."""
        self.session.merge(forecast)
        self.session.commit()
        return forecast

    def delete(self, forecast_id: UUID) -> bool:
        """Soft delete a forecast."""
        forecast = self.get_by_id(forecast_id)
        if forecast:
            forecast.is_active = False
            self.session.commit()
            return True
        return False


class MetricRepository:
    """Repository for FinancialMetric persistence with organization isolation."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
        self.auth = OrganizationAuthorizer(session)

    def create(self, metric: FinancialMetric, requesting_org_id: Optional[UUID] = None) -> FinancialMetric:
        """Create a new metric with org validation."""
        org_id = self.auth.validate_org_access(
            metric.organization_id, requesting_org_id, "write"
        )
        self.session.add(metric)
        self.session.commit()
        self.auth.log_access(org_id, "create", "metric", metric.id)
        return metric

    def get_by_org_and_type(
        self,
        organization_id: UUID,
        metric_type: MetricType,
        period_date: Optional[date] = None
    ) -> Optional[FinancialMetric]:
        """Get metric by org and type."""
        query = self.session.query(FinancialMetric).filter(
            FinancialMetric.organization_id == organization_id,
            FinancialMetric.metric_type == metric_type,
            FinancialMetric.is_active == True
        )

        if period_date:
            query = query.filter(FinancialMetric.period_date == period_date)

        return query.first()

    def get_history(
        self,
        organization_id: UUID,
        metric_type: MetricType,
        start_date: date,
        end_date: date
    ) -> List[FinancialMetric]:
        """Get metric history for a period."""
        return self.session.query(FinancialMetric).filter(
            FinancialMetric.organization_id == organization_id,
            FinancialMetric.metric_type == metric_type,
            FinancialMetric.period_date.between(start_date, end_date),
            FinancialMetric.is_active == True
        ).order_by(FinancialMetric.period_date).all()

    def get_by_org(
        self,
        organization_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[FinancialMetric]:
        """Get all metrics for organization."""
        query = self.session.query(FinancialMetric).filter(
            FinancialMetric.organization_id == organization_id,
            FinancialMetric.is_active == True
        )

        if start_date:
            query = query.filter(FinancialMetric.period_date >= start_date)

        if end_date:
            query = query.filter(FinancialMetric.period_date <= end_date)

        return query.order_by(FinancialMetric.period_date).all()

    def update(self, metric: FinancialMetric) -> FinancialMetric:
        """Update a metric."""
        self.session.merge(metric)
        self.session.commit()
        return metric


class TrendRepository:
    """Repository for TrendAnalysis persistence with organization isolation."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
        self.auth = OrganizationAuthorizer(session)

    def create(self, trend: TrendAnalysis, requesting_org_id: Optional[UUID] = None) -> TrendAnalysis:
        """Create a new trend analysis with org validation."""
        org_id = self.auth.validate_org_access(
            trend.organization_id, requesting_org_id, "write"
        )
        self.session.add(trend)
        self.session.commit()
        self.auth.log_access(org_id, "create", "trend", trend.id)
        return trend

    def get_by_org(self, organization_id: UUID) -> List[TrendAnalysis]:
        """Get all trends for organization."""
        return self.session.query(TrendAnalysis).filter(
            TrendAnalysis.organization_id == organization_id
        ).order_by(TrendAnalysis.analysis_period_start).all()

    def get_by_org_and_type(
        self,
        organization_id: UUID,
        metric_type: str
    ) -> Optional[TrendAnalysis]:
        """Get trend by org and metric type."""
        return self.session.query(TrendAnalysis).filter(
            TrendAnalysis.organization_id == organization_id,
            TrendAnalysis.metric_type == metric_type
        ).first()

    def get_by_direction(
        self,
        organization_id: UUID,
        direction: TrendDirection
    ) -> List[TrendAnalysis]:
        """Get trends filtered by direction."""
        return self.session.query(TrendAnalysis).filter(
            TrendAnalysis.organization_id == organization_id,
            TrendAnalysis.trend_direction == direction
        ).all()

    def update(self, trend: TrendAnalysis) -> TrendAnalysis:
        """Update a trend."""
        self.session.merge(trend)
        self.session.commit()
        return trend


class KPIRepository:
    """Repository for KPI persistence with organization isolation."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
        self.auth = OrganizationAuthorizer(session)

    def create(self, kpi: KPI, requesting_org_id: Optional[UUID] = None) -> KPI:
        """Create a new KPI with org validation."""
        org_id = self.auth.validate_org_access(
            kpi.organization_id, requesting_org_id, "write"
        )
        self.session.add(kpi)
        self.session.commit()
        self.auth.log_access(org_id, "create", "kpi", kpi.id)
        return kpi

    def get_by_org_and_code(
        self,
        organization_id: UUID,
        code: str,
        period_date: Optional[date] = None
    ) -> Optional[KPI]:
        """Get KPI by org and code."""
        query = self.session.query(KPI).filter(
            KPI.organization_id == organization_id,
            KPI.code == code,
            KPI.is_active == True
        )

        if period_date:
            query = query.filter(KPI.period_date == period_date)

        return query.first()

    def get_history(
        self,
        organization_id: UUID,
        code: str,
        start_date: date,
        end_date: date
    ) -> List[KPI]:
        """Get KPI history for a period."""
        return self.session.query(KPI).filter(
            KPI.organization_id == organization_id,
            KPI.code == code,
            KPI.period_date.between(start_date, end_date),
            KPI.is_active == True
        ).order_by(KPI.period_date).all()

    def get_by_org(
        self,
        organization_id: UUID,
        period_date: Optional[date] = None
    ) -> List[KPI]:
        """Get all KPIs for organization."""
        query = self.session.query(KPI).filter(
            KPI.organization_id == organization_id,
            KPI.is_active == True
        )

        if period_date:
            query = query.filter(KPI.period_date == period_date)

        return query.order_by(KPI.code).all()

    def update(self, kpi: KPI) -> KPI:
        """Update a KPI."""
        self.session.merge(kpi)
        self.session.commit()
        return kpi


class DashboardWidgetRepository:
    """Repository for DashboardWidget persistence with organization isolation."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
        self.auth = OrganizationAuthorizer(session)

    def create(self, widget: DashboardWidget, requesting_org_id: Optional[UUID] = None) -> DashboardWidget:
        """Create a new widget with org validation."""
        org_id = self.auth.validate_org_access(
            widget.organization_id, requesting_org_id, "write"
        )
        self.session.add(widget)
        self.session.commit()
        self.auth.log_access(org_id, "create", "widget", widget.id)
        return widget

    def get_by_id(self, widget_id: UUID) -> Optional[DashboardWidget]:
        """Get widget by ID."""
        return self.session.query(DashboardWidget).filter(
            DashboardWidget.id == widget_id,
            DashboardWidget.is_active == True
        ).first()

    def get_by_org(self, organization_id: UUID) -> List[DashboardWidget]:
        """Get all widgets for organization."""
        return self.session.query(DashboardWidget).filter(
            DashboardWidget.organization_id == organization_id,
            DashboardWidget.is_active == True
        ).order_by(DashboardWidget.position).all()

    def get_by_org_and_source(
        self,
        organization_id: UUID,
        data_source: str
    ) -> Optional[DashboardWidget]:
        """Get widget by org and data source."""
        return self.session.query(DashboardWidget).filter(
            DashboardWidget.organization_id == organization_id,
            DashboardWidget.data_source == data_source,
            DashboardWidget.is_active == True
        ).first()

    def get_pinned(self, organization_id: UUID) -> List[DashboardWidget]:
        """Get pinned widgets."""
        return self.session.query(DashboardWidget).filter(
            DashboardWidget.organization_id == organization_id,
            DashboardWidget.is_pinned == True,
            DashboardWidget.is_active == True
        ).order_by(DashboardWidget.position).all()

    def update(self, widget: DashboardWidget) -> DashboardWidget:
        """Update a widget."""
        self.session.merge(widget)
        self.session.commit()
        return widget

    def delete(self, widget_id: UUID) -> bool:
        """Soft delete a widget."""
        widget = self.get_by_id(widget_id)
        if widget:
            widget.is_active = False
            self.session.commit()
            return True
        return False

    def update_position(self, organization_id: UUID, widget_id: UUID, position: int) -> bool:
        """Update widget position."""
        widget = self.session.query(DashboardWidget).filter(
            DashboardWidget.id == widget_id,
            DashboardWidget.organization_id == organization_id
        ).first()

        if widget:
            widget.position = position
            self.session.commit()
            return True
        return False
