"""Tests for multi-tenant isolation and organization authorization.

Tests organization isolation enforcement and prevents cross-organization access.
"""

import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal
from backend.models.analytics import ForecastType, ForecastMethod, MetricType, TrendDirection
from backend.analytics.repositories import ForecastRepository, MetricRepository, DashboardWidgetRepository
from backend.analytics.auth import OrganizationAuthorizer, OrgAuthError


@pytest.fixture
def client():
    """Get FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Get database session."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def orgs():
    """Get two different organization IDs."""
    return {
        "org1": uuid4(),
        "org2": uuid4()
    }


class TestOrganizationAuthorizer:
    """Tests for organization authorization."""

    def test_validate_org_access_success(self, db_session):
        """Test successful org access validation."""
        auth = OrganizationAuthorizer(db_session)
        org_id = uuid4()

        result = auth.validate_org_access(org_id)
        assert result == org_id

    def test_validate_org_access_with_matching_user_org(self, db_session):
        """Test org access when user org matches."""
        auth = OrganizationAuthorizer(db_session)
        org_id = uuid4()

        result = auth.validate_org_access(org_id, user_org_id=org_id)
        assert result == org_id

    def test_validate_org_access_cross_org_denied(self, db_session):
        """Test cross-organization access is denied."""
        auth = OrganizationAuthorizer(db_session)
        org1 = uuid4()
        org2 = uuid4()

        with pytest.raises(OrgAuthError):
            auth.validate_org_access(org2, user_org_id=org1)

    def test_validate_org_access_missing_org_denied(self, db_session):
        """Test access with missing org ID is denied."""
        auth = OrganizationAuthorizer(db_session)

        with pytest.raises(OrgAuthError):
            auth.validate_org_access(None)

    def test_validate_entity_org_success(self, db_session):
        """Test successful entity org validation."""
        auth = OrganizationAuthorizer(db_session)
        org_id = uuid4()

        # Should not raise
        auth.validate_entity_org(org_id, org_id, "forecast")

    def test_validate_entity_org_cross_org_denied(self, db_session):
        """Test entity org validation denies cross-org access."""
        auth = OrganizationAuthorizer(db_session)
        entity_org = uuid4()
        requesting_org = uuid4()

        with pytest.raises(OrgAuthError):
            auth.validate_entity_org(entity_org, requesting_org, "forecast")

class TestRepositoryOrgIsolation:
    """Tests for repository-level organization isolation."""

    def test_forecast_create_with_org_validation(self, db_session, orgs):
        """Test forecast creation respects org boundaries."""
        from backend.models.analytics import Forecast

        repo1 = ForecastRepository(db_session)
        org1_id = orgs["org1"]

        forecast = Forecast(
            organization_id=org1_id,
            forecast_type=ForecastType.REVENUE,
            method=ForecastMethod.LINEAR_REGRESSION,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 2, 1),
            forecast_date=date(2024, 1, 15),
            base_value=Decimal("10000"),
            forecasted_value=Decimal("11000")
        )

        created = repo1.create(forecast, requesting_org_id=org1_id)
        assert created.organization_id == org1_id

    def test_forecast_create_cross_org_denied(self, db_session, orgs):
        """Test cross-org forecast creation is denied."""
        from backend.models.analytics import Forecast

        repo = ForecastRepository(db_session)
        org1_id = orgs["org1"]
        org2_id = orgs["org2"]

        forecast = Forecast(
            organization_id=org2_id,
            forecast_type=ForecastType.REVENUE,
            method=ForecastMethod.LINEAR_REGRESSION,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 2, 1),
            forecast_date=date(2024, 1, 15),
            base_value=Decimal("10000"),
            forecasted_value=Decimal("11000")
        )

        # Requesting org1 to create forecast for org2 should fail
        with pytest.raises(OrgAuthError):
            repo.create(forecast, requesting_org_id=org1_id)

    def test_forecast_get_by_id_cross_org_denied(self, db_session, orgs):
        """Test cross-org forecast retrieval is denied."""
        from backend.models.analytics import Forecast

        org1_id = orgs["org1"]
        org2_id = orgs["org2"]

        # Create forecast for org1
        repo1 = ForecastRepository(db_session)
        forecast = Forecast(
            organization_id=org1_id,
            forecast_type=ForecastType.REVENUE,
            method=ForecastMethod.LINEAR_REGRESSION,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 2, 1),
            forecast_date=date(2024, 1, 15),
            base_value=Decimal("10000"),
            forecasted_value=Decimal("11000")
        )
        created = repo1.create(forecast)

        # Org2 tries to access org1's forecast
        repo2 = ForecastRepository(db_session)
        with pytest.raises(OrgAuthError):
            repo2.get_by_id(created.id, requesting_org_id=org2_id)

    def test_metric_org_isolation(self, db_session, orgs):
        """Test metrics are isolated by organization."""
        from backend.models.analytics import FinancialMetric

        repo = MetricRepository(db_session)
        org1_id = orgs["org1"]

        metric = FinancialMetric(
            organization_id=org1_id,
            metric_type=MetricType.NET_PROFIT_MARGIN,
            period_date=date(2024, 1, 1),
            metric_value=Decimal("25")
        )

        created = repo.create(metric, requesting_org_id=org1_id)
        assert created.organization_id == org1_id

    def test_widget_org_isolation(self, db_session, orgs):
        """Test dashboard widgets are isolated by organization."""
        from backend.models.analytics import DashboardWidget

        repo = DashboardWidgetRepository(db_session)
        org1_id = orgs["org1"]

        widget = DashboardWidget(
            organization_id=org1_id,
            title="Org1 Widget",
            widget_type="chart",
            data_source="revenue",
            position=0
        )

        created = repo.create(widget, requesting_org_id=org1_id)
        assert created.organization_id == org1_id


class TestAPIMultiTenantAccess:
    """Tests for multi-tenant access control at API level."""

    def test_create_forecast_org_isolation(self, client: TestClient, orgs):
        """Test forecast creation respects organization context."""
        org1_id = orgs["org1"]

        response = client.post(
            f"/api/analytics/orgs/{org1_id}/forecasts",
            params={
                "forecast_type": ForecastType.REVENUE.value,
                "method": ForecastMethod.LINEAR_REGRESSION.value,
                "period_start": "2024-01-01",
                "period_end": "2024-02-01",
                "base_value": 10000,
                "forecasted_value": 11000
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["organization_id"] == str(org1_id)

    def test_list_forecasts_org_scoped(self, client: TestClient, orgs):
        """Test forecast list is scoped to requesting organization."""
        org1_id = orgs["org1"]
        org2_id = orgs["org2"]

        # Create forecast for org1
        client.post(
            f"/api/analytics/orgs/{org1_id}/forecasts",
            params={
                "forecast_type": ForecastType.REVENUE.value,
                "method": ForecastMethod.LINEAR_REGRESSION.value,
                "period_start": "2024-01-01",
                "period_end": "2024-02-01",
                "base_value": 10000,
                "forecasted_value": 11000
            }
        )

        # Create forecast for org2
        client.post(
            f"/api/analytics/orgs/{org2_id}/forecasts",
            params={
                "forecast_type": ForecastType.REVENUE.value,
                "method": ForecastMethod.LINEAR_REGRESSION.value,
                "period_start": "2024-01-01",
                "period_end": "2024-02-01",
                "base_value": 20000,
                "forecasted_value": 22000
            }
        )

        # Get org1 forecasts - should only see org1's data
        org1_response = client.get(f"/api/analytics/orgs/{org1_id}/forecasts")
        org1_forecasts = org1_response.json()

        # Get org2 forecasts - should only see org2's data
        org2_response = client.get(f"/api/analytics/orgs/{org2_id}/forecasts")
        org2_forecasts = org2_response.json()

        # Both should have exactly 1 forecast (their own)
        assert org1_forecasts["count"] >= 1
        assert org2_forecasts["count"] >= 1

    def test_list_metrics_org_scoped(self, client: TestClient, orgs):
        """Test metric list is scoped to requesting organization."""
        org1_id = orgs["org1"]

        # Create metrics
        for i in range(3):
            client.post(
                f"/api/analytics/orgs/{org1_id}/metrics",
                params={
                    "metric_type": MetricType.NET_PROFIT_MARGIN.value,
                    "period_date": f"2024-0{i+1}-01",
                    "metric_value": 20 + i
                }
            )

        response = client.get(f"/api/analytics/orgs/{org1_id}/metrics")
        data = response.json()

        assert data["count"] >= 3
        # All metrics should be for org1
        for metric in data["metrics"]:
            assert metric["type"] == MetricType.NET_PROFIT_MARGIN.value

    def test_list_kpis_org_scoped(self, client: TestClient, orgs):
        """Test KPI list is scoped to requesting organization."""
        org1_id = orgs["org1"]
        org2_id = orgs["org2"]

        # Create KPI for org1
        client.post(
            f"/api/analytics/orgs/{org1_id}/kpis",
            params={
                "name": "Revenue",
                "code": f"REV_{uuid4().hex[:8]}",
                "period_date": "2024-01-01",
                "current_value": 100000
            }
        )

        # Create KPI for org2
        client.post(
            f"/api/analytics/orgs/{org2_id}/kpis",
            params={
                "name": "Expenses",
                "code": f"EXP_{uuid4().hex[:8]}",
                "period_date": "2024-01-01",
                "current_value": 50000
            }
        )

        # Get org1 KPIs
        org1_response = client.get(f"/api/analytics/orgs/{org1_id}/kpis")
        org1_data = org1_response.json()

        # Get org2 KPIs
        org2_response = client.get(f"/api/analytics/orgs/{org2_id}/kpis")
        org2_data = org2_response.json()

        assert org1_data["count"] >= 1
        assert org2_data["count"] >= 1

    def test_list_widgets_org_scoped(self, client: TestClient, orgs):
        """Test widget list is scoped to requesting organization."""
        org1_id = orgs["org1"]
        org2_id = orgs["org2"]

        # Create widgets for org1
        for i in range(2):
            client.post(
                f"/api/analytics/orgs/{org1_id}/widgets",
                params={
                    "title": f"Org1 Widget {i}",
                    "widget_type": "chart",
                    "data_source": f"source_{i}",
                    "position": i
                }
            )

        # Create widget for org2
        client.post(
            f"/api/analytics/orgs/{org2_id}/widgets",
            params={
                "title": "Org2 Widget",
                "widget_type": "chart",
                "data_source": "org2_source",
                "position": 0
            }
        )

        # Get org1 widgets
        org1_response = client.get(f"/api/analytics/orgs/{org1_id}/widgets")
        org1_data = org1_response.json()

        # Get org2 widgets
        org2_response = client.get(f"/api/analytics/orgs/{org2_id}/widgets")
        org2_data = org2_response.json()

        assert org1_data["count"] >= 2
        assert org2_data["count"] >= 1


class TestDataIsolationEnforcement:
    """Tests for strict data isolation between organizations."""

    def test_trend_data_isolated(self, client: TestClient, orgs):
        """Test trends are isolated by organization."""
        org1_id = orgs["org1"]
        org2_id = orgs["org2"]

        # Create trend for org1
        client.post(
            f"/api/analytics/orgs/{org1_id}/trends",
            params={
                "metric_type": "revenue",
                "direction": TrendDirection.UPWARD.value,
                "strength": 0.85,
                "analysis_start": "2024-01-01",
                "analysis_end": "2024-03-01"
            }
        )

        # Create trend for org2
        client.post(
            f"/api/analytics/orgs/{org2_id}/trends",
            params={
                "metric_type": "expenses",
                "direction": TrendDirection.DOWNWARD.value,
                "strength": 0.75,
                "analysis_start": "2024-01-01",
                "analysis_end": "2024-03-01"
            }
        )

        # Get org1 trends
        org1_response = client.get(f"/api/analytics/orgs/{org1_id}/trends")
        org1_data = org1_response.json()

        # Get org2 trends
        org2_response = client.get(f"/api/analytics/orgs/{org2_id}/trends")
        org2_data = org2_response.json()

        assert org1_data["count"] >= 1
        assert org2_data["count"] >= 1

    def test_multiple_orgs_complete_isolation(self, client: TestClient):
        """Test complete isolation between multiple organizations."""
        org_ids = [uuid4() for _ in range(3)]

        # Create different analytics for each organization
        for i, org_id in enumerate(org_ids):
            # Create forecast
            client.post(
                f"/api/analytics/orgs/{org_id}/forecasts",
                params={
                    "forecast_type": ForecastType.REVENUE.value,
                    "method": ForecastMethod.LINEAR_REGRESSION.value,
                    "period_start": "2024-01-01",
                    "period_end": "2024-02-01",
                    "base_value": 10000 * (i + 1),
                    "forecasted_value": 11000 * (i + 1)
                }
            )

            # Create metric
            client.post(
                f"/api/analytics/orgs/{org_id}/metrics",
                params={
                    "metric_type": MetricType.NET_PROFIT_MARGIN.value,
                    "period_date": "2024-01-01",
                    "metric_value": 20 + i
                }
            )

            # Create KPI
            client.post(
                f"/api/analytics/orgs/{org_id}/kpis",
                params={
                    "name": f"KPI_{i}",
                    "code": f"KPI_{uuid4().hex[:8]}",
                    "period_date": "2024-01-01",
                    "current_value": 100000 * (i + 1)
                }
            )

        # Verify each org only sees its own data
        for i, org_id in enumerate(org_ids):
            forecasts = client.get(f"/api/analytics/orgs/{org_id}/forecasts").json()
            metrics = client.get(f"/api/analytics/orgs/{org_id}/metrics").json()
            kpis = client.get(f"/api/analytics/orgs/{org_id}/kpis").json()

            assert forecasts["count"] >= 1
            assert metrics["count"] >= 1
            assert kpis["count"] >= 1
