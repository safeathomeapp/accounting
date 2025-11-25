"""Tests for analytics API integration with database persistence.

Tests REST endpoints for forecasts, metrics, trends, KPIs, and widgets.
"""

import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal
from backend.models.analytics import (
    ForecastType, ForecastMethod, MetricType, TrendDirection
)


@pytest.fixture
def client():
    """Get FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def org_id():
    """Get test organization ID."""
    return uuid4()


class TestForecastAPI:
    """Tests for forecast API endpoints."""

    def test_create_forecast(self, client: TestClient, org_id: str):
        """Test creating a forecast via API."""
        response = client.post(
            f"/api/analytics/orgs/{org_id}/forecasts",
            params={
                "forecast_type": ForecastType.REVENUE.value,
                "method": ForecastMethod.LINEAR_REGRESSION.value,
                "period_start": "2024-01-01",
                "period_end": "2024-02-01",
                "base_value": 10000,
                "forecasted_value": 11000,
                "accuracy_score": 0.95
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["organization_id"] == str(org_id)
        assert data["type"] == ForecastType.REVENUE.value
        assert "11000" in data["value"]  # Handle Decimal serialization

    def test_list_forecasts(self, client: TestClient, org_id: str):
        """Test listing forecasts via API."""
        # Create a forecast first
        client.post(
            f"/api/analytics/orgs/{org_id}/forecasts",
            params={
                "forecast_type": ForecastType.REVENUE.value,
                "method": ForecastMethod.LINEAR_REGRESSION.value,
                "period_start": "2024-01-01",
                "period_end": "2024-02-01",
                "base_value": 10000,
                "forecasted_value": 11000
            }
        )

        response = client.get(f"/api/analytics/orgs/{org_id}/forecasts")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert "forecasts" in data

    def test_get_forecast(self, client: TestClient, org_id: str):
        """Test retrieving a specific forecast."""
        # Create a forecast
        create_response = client.post(
            f"/api/analytics/orgs/{org_id}/forecasts",
            params={
                "forecast_type": ForecastType.REVENUE.value,
                "method": ForecastMethod.LINEAR_REGRESSION.value,
                "period_start": "2024-01-01",
                "period_end": "2024-02-01",
                "base_value": 10000,
                "forecasted_value": 11000,
                "accuracy_score": 0.95
            }
        )
        forecast_id = create_response.json()["id"]

        response = client.get(f"/api/analytics/forecasts/{forecast_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == forecast_id


class TestMetricAPI:
    """Tests for metric API endpoints."""

    def test_create_metric(self, client: TestClient, org_id: str):
        """Test creating a metric via API."""
        response = client.post(
            f"/api/analytics/orgs/{org_id}/metrics",
            params={
                "metric_type": MetricType.NET_PROFIT_MARGIN.value,
                "period_date": "2024-01-01",
                "metric_value": 25,
                "benchmark_value": 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == MetricType.NET_PROFIT_MARGIN.value
        assert "25" in data["value"]  # Handle Decimal serialization
        assert "20" in data["benchmark"]  # Handle Decimal serialization

    def test_list_metrics(self, client: TestClient, org_id: str):
        """Test listing metrics via API."""
        # Create a metric
        client.post(
            f"/api/analytics/orgs/{org_id}/metrics",
            params={
                "metric_type": MetricType.NET_PROFIT_MARGIN.value,
                "period_date": "2024-01-01",
                "metric_value": 25
            }
        )

        response = client.get(f"/api/analytics/orgs/{org_id}/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert "metrics" in data

    def test_list_metrics_with_date_range(self, client: TestClient, org_id: str):
        """Test listing metrics with date range filter."""
        # Create metrics for different dates
        for month in [1, 2, 3]:
            client.post(
                f"/api/analytics/orgs/{org_id}/metrics",
                params={
                    "metric_type": MetricType.NET_PROFIT_MARGIN.value,
                    "period_date": f"2024-0{month}-01",
                    "metric_value": 20 + month
                }
            )

        response = client.get(
            f"/api/analytics/orgs/{org_id}/metrics",
            params={
                "metric_type": MetricType.NET_PROFIT_MARGIN.value,
                "start_date": "2024-01-01",
                "end_date": "2024-03-31"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3


class TestTrendAPI:
    """Tests for trend API endpoints."""

    def test_create_trend(self, client: TestClient, org_id: str):
        """Test creating a trend via API."""
        response = client.post(
            f"/api/analytics/orgs/{org_id}/trends",
            params={
                "metric_type": "revenue",
                "direction": TrendDirection.UPWARD.value,
                "strength": 0.85,
                "analysis_start": "2024-01-01",
                "analysis_end": "2024-03-01"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "revenue"
        assert data["direction"] == TrendDirection.UPWARD.value

    def test_list_trends(self, client: TestClient, org_id: str):
        """Test listing trends via API."""
        # Create a trend
        client.post(
            f"/api/analytics/orgs/{org_id}/trends",
            params={
                "metric_type": "revenue",
                "direction": TrendDirection.UPWARD.value,
                "strength": 0.85,
                "analysis_start": "2024-01-01",
                "analysis_end": "2024-03-01"
            }
        )

        response = client.get(f"/api/analytics/orgs/{org_id}/trends")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert "trends" in data

    def test_list_trends_by_direction(self, client: TestClient, org_id: str):
        """Test listing trends filtered by direction."""
        # Create trends in different directions
        for direction in [TrendDirection.UPWARD.value, TrendDirection.DOWNWARD.value]:
            client.post(
                f"/api/analytics/orgs/{org_id}/trends",
                params={
                    "metric_type": f"metric_{direction}",
                    "direction": direction,
                    "strength": 0.75,
                    "analysis_start": "2024-01-01",
                    "analysis_end": "2024-03-01"
                }
            )

        response = client.get(
            f"/api/analytics/orgs/{org_id}/trends",
            params={"direction": TrendDirection.UPWARD.value}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1


class TestKPIAPI:
    """Tests for KPI API endpoints."""

    def test_create_kpi(self, client: TestClient, org_id: str):
        """Test creating a KPI via API."""
        response = client.post(
            f"/api/analytics/orgs/{org_id}/kpis",
            params={
                "name": "Revenue",
                "code": "REV_001",
                "period_date": "2024-01-01",
                "current_value": 100000,
                "target_value": 100000,
                "unit": "USD"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Revenue"
        assert data["code"] == "REV_001"

    def test_list_kpis(self, client: TestClient, org_id: str):
        """Test listing KPIs via API."""
        # Create a KPI
        client.post(
            f"/api/analytics/orgs/{org_id}/kpis",
            params={
                "name": "Revenue",
                "code": "REV_001",
                "period_date": "2024-01-01",
                "current_value": 100000
            }
        )

        response = client.get(f"/api/analytics/orgs/{org_id}/kpis")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert "kpis" in data

    def test_get_kpi_history(self, client: TestClient, org_id: str):
        """Test retrieving KPI history via API."""
        # Create KPI records for multiple periods
        code = f"DSO_{uuid4().hex[:8]}"
        for month in [1, 2, 3]:
            client.post(
                f"/api/analytics/orgs/{org_id}/kpis",
                params={
                    "name": "Days Sales Outstanding",
                    "code": code,
                    "period_date": f"2024-0{month}-01",
                    "current_value": 50 + month,
                    "unit": "days"
                }
            )

        response = client.get(
            f"/api/analytics/kpis/{code}/history",
            params={
                "org_id": org_id,
                "start_date": "2024-01-01",
                "end_date": "2024-03-31"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert len(data["history"]) == 3


class TestWidgetAPI:
    """Tests for dashboard widget API endpoints."""

    def test_create_widget(self, client: TestClient, org_id: str):
        """Test creating a widget via API."""
        response = client.post(
            f"/api/analytics/orgs/{org_id}/widgets",
            params={
                "title": "Revenue Chart",
                "widget_type": "chart",
                "data_source": "revenue_forecast",
                "position": 0,
                "is_pinned": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Revenue Chart"
        assert data["type"] == "chart"

    def test_list_widgets(self, client: TestClient, org_id: str):
        """Test listing widgets via API."""
        # Create widgets
        for i in range(3):
            client.post(
                f"/api/analytics/orgs/{org_id}/widgets",
                params={
                    "title": f"Widget {i}",
                    "widget_type": "chart",
                    "data_source": f"source_{i}",
                    "position": i
                }
            )

        response = client.get(f"/api/analytics/orgs/{org_id}/widgets")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

    def test_list_pinned_widgets(self, client: TestClient, org_id: str):
        """Test listing pinned widgets only."""
        # Create some pinned and unpinned widgets
        for i in range(3):
            client.post(
                f"/api/analytics/orgs/{org_id}/widgets",
                params={
                    "title": f"Widget {i}",
                    "widget_type": "chart",
                    "data_source": f"source_{i}",
                    "position": i,
                    "is_pinned": i < 2
                }
            )

        response = client.get(
            f"/api/analytics/orgs/{org_id}/widgets",
            params={"pinned_only": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    def test_update_widget_position(self, client: TestClient, org_id: str):
        """Test updating widget position."""
        # Create a widget
        create_response = client.post(
            f"/api/analytics/orgs/{org_id}/widgets",
            params={
                "title": "Test Widget",
                "widget_type": "chart",
                "data_source": "test",
                "position": 0
            }
        )
        widget_id = create_response.json()["id"]

        response = client.put(
            f"/api/analytics/widgets/{widget_id}/position",
            params={
                "org_id": org_id,
                "position": 5
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["position"] == 5

    def test_delete_widget(self, client: TestClient, org_id: str):
        """Test deleting a widget."""
        # Create a widget
        create_response = client.post(
            f"/api/analytics/orgs/{org_id}/widgets",
            params={
                "title": "Delete Me",
                "widget_type": "chart",
                "data_source": "delete",
                "position": 0
            }
        )
        widget_id = create_response.json()["id"]

        response = client.delete(f"/api/analytics/widgets/{widget_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAnalyticsAPIIntegration:
    """Integration tests for complete analytics workflows."""

    def test_complete_analytics_workflow(self, client: TestClient, org_id: str):
        """Test complete workflow: create all analytics types."""
        # Create forecast
        forecast_response = client.post(
            f"/api/analytics/orgs/{org_id}/forecasts",
            params={
                "forecast_type": ForecastType.REVENUE.value,
                "method": ForecastMethod.LINEAR_REGRESSION.value,
                "period_start": "2024-01-01",
                "period_end": "2024-02-01",
                "base_value": 10000,
                "forecasted_value": 11000
            }
        )
        assert forecast_response.status_code == 200

        # Create metric
        metric_response = client.post(
            f"/api/analytics/orgs/{org_id}/metrics",
            params={
                "metric_type": MetricType.NET_PROFIT_MARGIN.value,
                "period_date": "2024-01-01",
                "metric_value": 25
            }
        )
        assert metric_response.status_code == 200

        # Create trend
        trend_response = client.post(
            f"/api/analytics/orgs/{org_id}/trends",
            params={
                "metric_type": "revenue",
                "direction": TrendDirection.UPWARD.value,
                "strength": 0.85,
                "analysis_start": "2024-01-01",
                "analysis_end": "2024-03-01"
            }
        )
        assert trend_response.status_code == 200

        # Create KPI
        kpi_response = client.post(
            f"/api/analytics/orgs/{org_id}/kpis",
            params={
                "name": "Revenue",
                "code": "REV_TEST",
                "period_date": "2024-01-01",
                "current_value": 100000
            }
        )
        assert kpi_response.status_code == 200

        # Create widget
        widget_response = client.post(
            f"/api/analytics/orgs/{org_id}/widgets",
            params={
                "title": "Dashboard",
                "widget_type": "chart",
                "data_source": "revenue",
                "position": 0
            }
        )
        assert widget_response.status_code == 200

        # Verify all created
        forecasts = client.get(f"/api/analytics/orgs/{org_id}/forecasts")
        metrics = client.get(f"/api/analytics/orgs/{org_id}/metrics")
        trends = client.get(f"/api/analytics/orgs/{org_id}/trends")
        kpis = client.get(f"/api/analytics/orgs/{org_id}/kpis")
        widgets = client.get(f"/api/analytics/orgs/{org_id}/widgets")

        assert forecasts.json()["count"] >= 1
        assert metrics.json()["count"] >= 1
        assert trends.json()["count"] >= 1
        assert kpis.json()["count"] >= 1
        assert widgets.json()["count"] >= 1

    def test_organization_isolation(self, client: TestClient):
        """Test data isolation between organizations."""
        org1_id = uuid4()
        org2_id = uuid4()

        # Create data for org1
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

        # Create data for org2
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

        # Verify org1 only sees its data
        org1_forecasts = client.get(f"/api/analytics/orgs/{org1_id}/forecasts")
        org2_forecasts = client.get(f"/api/analytics/orgs/{org2_id}/forecasts")

        assert org1_forecasts.json()["count"] >= 1
        assert org2_forecasts.json()["count"] >= 1
        # Both should have their own data
        assert "11000" in org1_forecasts.json()["forecasts"][0]["value"]
        assert "22000" in org2_forecasts.json()["forecasts"][0]["value"]
