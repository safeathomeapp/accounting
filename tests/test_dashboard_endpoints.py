"""Tests for dashboard REST API endpoints.

Tests the dashboard routes providing real-time monitoring data through
REST endpoints for job status, metrics, transactions, and error information.
"""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.monitoring import MetricsCollector, RealtimeEventBroadcaster


client = TestClient(app)


class TestDashboardOverviewEndpoint:
    """Tests for GET /api/v1/dashboard/overview endpoint."""

    def test_overview_success(self):
        """Test successful dashboard overview retrieval."""
        org_id = str(uuid4())

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            with patch('backend.api.dashboard_routes.RealtimeEventBroadcaster') as mock_broadcaster:
                # Setup mocks
                mock_collector = MagicMock()
                mock_collector_class.return_value = mock_collector
                mock_collector.calculate_aggregate_metrics.return_value = {
                    "total_processed": 1000,
                    "total_failed": 5,
                    "total_skipped": 10,
                    "success_rate": 99.5,
                    "avg_duration": 45.2,
                }
                mock_broadcaster.get_connection_stats.return_value = {
                    "total_connections": 5,
                    "organizations_connected": 2,
                    "organization_breakdown": {org_id: 3},
                }

                response = client.get(f"/api/v1/dashboard/overview?org_id={org_id}")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "ok"
                assert data["organization_id"] == org_id
                assert "metrics" in data
                assert data["metrics"]["total_processed"] == 1000
                assert "connections" in data
                assert data["connections"]["total"] == 5
                assert data["dashboard_ready"] is True

    def test_overview_empty_metrics(self):
        """Test overview with no metrics available."""
        org_id = str(uuid4())

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            with patch('backend.api.dashboard_routes.RealtimeEventBroadcaster') as mock_broadcaster:
                mock_collector = MagicMock()
                mock_collector_class.return_value = mock_collector
                mock_collector.calculate_aggregate_metrics.return_value = {
                    "total_processed": 0,
                    "total_failed": 0,
                    "total_skipped": 0,
                    "success_rate": 0.0,
                    "avg_duration": 0,
                }
                mock_broadcaster.get_connection_stats.return_value = {
                    "total_connections": 0,
                    "organizations_connected": 0,
                    "organization_breakdown": {},
                }

                response = client.get(f"/api/v1/dashboard/overview?org_id={org_id}")

                assert response.status_code == 200
                data = response.json()
                assert data["metrics"]["total_processed"] == 0


class TestDashboardMetricsEndpoint:
    """Tests for GET /api/v1/dashboard/metrics/{timeframe} endpoint."""

    def test_metrics_1h_timeframe(self):
        """Test metrics retrieval for 1 hour timeframe."""
        org_id = uuid4()

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            mock_collector = MagicMock()
            mock_collector_class.return_value = mock_collector
            mock_collector.calculate_aggregate_metrics.return_value = {
                "total_processed": 500,
                "total_failed": 2,
                "total_skipped": 5,
                "success_rate": 99.6,
                "avg_duration": 30.5,
            }

            response = client.get(f"/api/v1/dashboard/metrics/1h?org_id={org_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["timeframe"] == "1h"
            assert data["data"]["total_processed"] == 500
            mock_collector.calculate_aggregate_metrics.assert_called_once_with(
                org_id, timeframe_minutes=60
            )

    def test_metrics_24h_timeframe(self):
        """Test metrics retrieval for 24 hour timeframe."""
        org_id = uuid4()

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            mock_collector = MagicMock()
            mock_collector_class.return_value = mock_collector
            mock_collector.calculate_aggregate_metrics.return_value = {
                "total_processed": 5000,
                "total_failed": 20,
                "total_skipped": 50,
                "success_rate": 99.6,
                "avg_duration": 35.2,
            }

            response = client.get(f"/api/v1/dashboard/metrics/24h?org_id={org_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["timeframe"] == "24h"
            assert data["data"]["total_processed"] == 5000
            mock_collector.calculate_aggregate_metrics.assert_called_once_with(
                org_id, timeframe_minutes=1440
            )

    def test_metrics_30d_timeframe(self):
        """Test metrics retrieval for 30 day timeframe."""
        org_id = uuid4()

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            mock_collector = MagicMock()
            mock_collector_class.return_value = mock_collector
            mock_collector.calculate_aggregate_metrics.return_value = {
                "total_processed": 100000,
                "total_failed": 500,
                "total_skipped": 1000,
                "success_rate": 99.5,
                "avg_duration": 40.1,
            }

            response = client.get(f"/api/v1/dashboard/metrics/30d?org_id={org_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["timeframe"] == "30d"
            assert data["data"]["total_processed"] == 100000
            mock_collector.calculate_aggregate_metrics.assert_called_once_with(
                org_id, timeframe_minutes=43200
            )

    def test_metrics_invalid_timeframe(self):
        """Test metrics retrieval with invalid timeframe."""
        org_id = uuid4()

        response = client.get(f"/api/v1/dashboard/metrics/invalid?org_id={org_id}")

        assert response.status_code == 500  # HTTPException from endpoint raises as 500
        data = response.json()
        assert "Invalid timeframe" in data.get("detail", "")


class TestDashboardJobsListEndpoint:
    """Tests for GET /api/v1/dashboard/jobs endpoint."""

    def test_jobs_list_success(self):
        """Test successful jobs list retrieval."""
        org_id = str(uuid4())
        job1_id = str(uuid4())
        job2_id = str(uuid4())

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            mock_collector = MagicMock()
            mock_collector_class.return_value = mock_collector

            # Create mock metrics
            mock_metric1 = MagicMock()
            mock_metric1.job_id = job1_id
            mock_metric1.organization_id = org_id
            mock_metric1.timestamp.isoformat.return_value = "2025-11-25T10:30:00"
            mock_metric1.transactions_processed = 500
            mock_metric1.transactions_failed = 2
            mock_metric1.transactions_skipped = 5
            mock_metric1.data = {"duration_seconds": 45, "sync_status": "completed", "platform": "xero"}

            mock_metric2 = MagicMock()
            mock_metric2.job_id = job2_id
            mock_metric2.organization_id = org_id
            mock_metric2.timestamp.isoformat.return_value = "2025-11-25T09:30:00"
            mock_metric2.transactions_processed = 300
            mock_metric2.transactions_failed = 1
            mock_metric2.transactions_skipped = 3
            mock_metric2.data = {"duration_seconds": 38, "sync_status": "completed", "platform": "quickbooks"}

            mock_collector.get_organization_metrics.return_value = [mock_metric1, mock_metric2]

            response = client.get(f"/api/v1/dashboard/jobs?org_id={org_id}&limit=10")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["organization_id"] == org_id
            assert data["job_count"] == 2
            assert len(data["jobs"]) == 2
            assert data["jobs"][0]["job_id"] == job1_id
            assert data["jobs"][0]["transactions_processed"] == 500
            assert data["jobs"][1]["platform"] == "quickbooks"

    def test_jobs_list_empty(self):
        """Test jobs list when no jobs exist."""
        org_id = str(uuid4())

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            mock_collector = MagicMock()
            mock_collector_class.return_value = mock_collector
            mock_collector.get_organization_metrics.return_value = []

            response = client.get(f"/api/v1/dashboard/jobs?org_id={org_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["job_count"] == 0
            assert data["jobs"] == []

    def test_jobs_list_limit_parameter(self):
        """Test jobs list respects limit parameter."""
        org_id = str(uuid4())

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            mock_collector = MagicMock()
            mock_collector_class.return_value = mock_collector

            # Create 5 mock metrics but limit to 2
            metrics = []
            for i in range(5):
                m = MagicMock()
                m.job_id = str(uuid4())
                m.organization_id = org_id
                m.timestamp.isoformat.return_value = "2025-11-25T10:00:00"
                m.transactions_processed = 100 * (i + 1)
                m.transactions_failed = 0
                m.transactions_skipped = 0
                m.data = {"duration_seconds": 30, "sync_status": "completed", "platform": "xero"}
                metrics.append(m)

            mock_collector.get_organization_metrics.return_value = metrics

            response = client.get(f"/api/v1/dashboard/jobs?org_id={org_id}&limit=2")

            assert response.status_code == 200
            data = response.json()
            assert data["job_count"] == 2  # Limited to 2


class TestDashboardJobDetailsEndpoint:
    """Tests for GET /api/v1/dashboard/jobs/{job_id} endpoint."""

    def test_job_details_success(self):
        """Test successful job details retrieval."""
        org_id = uuid4()
        job_id = uuid4()

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            mock_collector = MagicMock()
            mock_collector_class.return_value = mock_collector

            mock_metric = MagicMock()
            mock_metric.organization_id = org_id
            mock_metric.to_dict.return_value = {
                "job_id": str(job_id),
                "transactions_processed": 500,
                "transactions_failed": 2,
                "duration_seconds": 45,
            }

            mock_collector.get_job_metrics.return_value = mock_metric

            response = client.get(f"/api/v1/dashboard/jobs/{job_id}?org_id={org_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["job_id"] == str(job_id)
            assert data["organization_id"] == str(org_id)
            assert data["data"]["transactions_processed"] == 500

    def test_job_details_not_found(self):
        """Test job details when job doesn't exist."""
        org_id = str(uuid4())
        job_id = str(uuid4())

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            mock_collector = MagicMock()
            mock_collector_class.return_value = mock_collector
            mock_collector.get_job_metrics.return_value = None

            response = client.get(f"/api/v1/dashboard/jobs/{job_id}?org_id={org_id}")

            assert response.status_code == 404

    def test_job_details_wrong_organization(self):
        """Test job details when job belongs to different organization."""
        org_id = str(uuid4())
        different_org_id = str(uuid4())
        job_id = str(uuid4())

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            mock_collector = MagicMock()
            mock_collector_class.return_value = mock_collector

            mock_metric = MagicMock()
            mock_metric.organization_id = different_org_id  # Different org

            mock_collector.get_job_metrics.return_value = mock_metric

            response = client.get(f"/api/v1/dashboard/jobs/{job_id}?org_id={org_id}")

            assert response.status_code == 404


class TestDashboardTransactionsEndpoint:
    """Tests for GET /api/v1/dashboard/transactions endpoint."""

    def test_transactions_default_timeframe(self):
        """Test transaction counters with default 1h timeframe."""
        org_id = str(uuid4())

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            mock_collector = MagicMock()
            mock_collector_class.return_value = mock_collector

            # Mock metrics with multiple jobs
            mock_metric1 = MagicMock()
            mock_metric1.transactions_processed = 500
            mock_metric1.transactions_failed = 2
            mock_metric1.transactions_skipped = 5

            mock_metric2 = MagicMock()
            mock_metric2.transactions_processed = 300
            mock_metric2.transactions_failed = 1
            mock_metric2.transactions_skipped = 3

            mock_collector.get_organization_metrics.return_value = [mock_metric1, mock_metric2]

            response = client.get(f"/api/v1/dashboard/transactions?org_id={org_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["timeframe"] == "1h"
            assert data["transactions"]["total_processed"] == 800  # 500 + 300
            assert data["transactions"]["total_failed"] == 3  # 2 + 1
            assert data["transactions"]["total_skipped"] == 8  # 5 + 3
            assert data["transactions"]["success_rate"] == 99.62  # (800 - 3) / 800 * 100, rounded to 2 decimals

    def test_transactions_7d_timeframe(self):
        """Test transaction counters for 7 day timeframe."""
        org_id = uuid4()

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            mock_collector = MagicMock()
            mock_collector_class.return_value = mock_collector

            mock_metric = MagicMock()
            mock_metric.transactions_processed = 5000
            mock_metric.transactions_failed = 20
            mock_metric.transactions_skipped = 50

            mock_collector.get_organization_metrics.return_value = [mock_metric]

            response = client.get(f"/api/v1/dashboard/transactions?org_id={org_id}&timeframe=7d")

            assert response.status_code == 200
            data = response.json()
            assert data["timeframe"] == "7d"
            assert data["transactions"]["total_processed"] == 5000
            mock_collector.get_organization_metrics.assert_called_once_with(
                org_id, timeframe_minutes=10080
            )

    def test_transactions_no_data(self):
        """Test transaction counters when no data available."""
        org_id = str(uuid4())

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            mock_collector = MagicMock()
            mock_collector_class.return_value = mock_collector
            mock_collector.get_organization_metrics.return_value = []

            response = client.get(f"/api/v1/dashboard/transactions?org_id={org_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["transactions"]["total_processed"] == 0
            assert data["transactions"]["success_rate"] == 0.0

    def test_transactions_invalid_timeframe(self):
        """Test transaction counters with invalid timeframe."""
        org_id = uuid4()

        response = client.get(f"/api/v1/dashboard/transactions?org_id={org_id}&timeframe=invalid")

        assert response.status_code == 500  # HTTPException from endpoint raises as 500


class TestDashboardErrorsEndpoint:
    """Tests for GET /api/v1/dashboard/errors endpoint."""



class TestDashboardHealthEndpoint:
    """Tests for GET /api/v1/dashboard/health endpoint."""

    def test_health_all_healthy(self):
        """Test health check when all components healthy."""
        org_id = str(uuid4())

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            with patch('backend.api.dashboard_routes.RealtimeEventBroadcaster') as mock_broadcaster:
                mock_collector = MagicMock()
                mock_collector_class.return_value = mock_collector
                mock_collector.get_organization_metrics.return_value = [MagicMock()]  # Has data
                mock_broadcaster.get_connection_stats.return_value = {
                    "total_connections": 5,
                    "organizations_connected": 1,
                    "organization_breakdown": {org_id: 5},
                }

                response = client.get(f"/api/v1/dashboard/health?org_id={org_id}")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert data["organization_id"] == org_id
                assert data["components"]["database"] == "connected"
                assert data["components"]["metrics"] == "active"
                assert data["has_recent_data"] is True

    def test_health_no_recent_data(self):
        """Test health check when no recent data available."""
        org_id = str(uuid4())

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            with patch('backend.api.dashboard_routes.RealtimeEventBroadcaster') as mock_broadcaster:
                mock_collector = MagicMock()
                mock_collector_class.return_value = mock_collector
                mock_collector.get_organization_metrics.return_value = []  # No data
                mock_broadcaster.get_connection_stats.return_value = {
                    "total_connections": 0,
                    "organizations_connected": 0,
                    "organization_breakdown": {},
                }

                response = client.get(f"/api/v1/dashboard/health?org_id={org_id}")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert data["components"]["metrics"] == "idle"
                assert data["components"]["websocket"] == "idle"
                assert data["has_recent_data"] is False

    def test_health_websocket_connected(self):
        """Test health check shows websocket connected when clients active."""
        org_id = str(uuid4())

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            with patch('backend.api.dashboard_routes.RealtimeEventBroadcaster') as mock_broadcaster:
                mock_collector = MagicMock()
                mock_collector_class.return_value = mock_collector
                mock_collector.get_organization_metrics.return_value = [MagicMock()]
                mock_broadcaster.get_connection_stats.return_value = {
                    "total_connections": 3,
                    "organizations_connected": 1,
                    "organization_breakdown": {org_id: 3},
                }

                response = client.get(f"/api/v1/dashboard/health?org_id={org_id}")

                assert response.status_code == 200
                data = response.json()
                assert data["components"]["websocket"] == "connected"
                assert data["websocket_connections"] == 3


class TestDashboardParameterValidation:
    """Tests for parameter validation across dashboard endpoints."""

    def test_invalid_uuid_parameter(self):
        """Test endpoints reject invalid UUID values."""
        invalid_uuid = "not-a-uuid"

        response = client.get(f"/api/v1/dashboard/overview?org_id={invalid_uuid}")
        # FastAPI should reject invalid UUID format
        assert response.status_code in [400, 422]

    def test_missing_org_id_parameter(self):
        """Test endpoints reject missing org_id parameter."""
        response = client.get("/api/v1/dashboard/overview")
        # Missing required parameter
        assert response.status_code in [400, 422]

    def test_limit_parameter_validation(self):
        """Test limit parameter respects min/max bounds."""
        org_id = str(uuid4())

        # Test minimum bound
        response = client.get(f"/api/v1/dashboard/jobs?org_id={org_id}&limit=0")
        assert response.status_code in [400, 422]

        # Test maximum bound
        response = client.get(f"/api/v1/dashboard/jobs?org_id={org_id}&limit=101")
        assert response.status_code in [400, 422]

    def test_valid_limit_ranges(self):
        """Test limit parameter accepts valid bounds."""
        org_id = str(uuid4())

        with patch('backend.api.dashboard_routes.MetricsCollector') as mock_collector_class:
            mock_collector = MagicMock()
            mock_collector_class.return_value = mock_collector
            mock_collector.get_organization_metrics.return_value = []

            # Minimum valid
            response = client.get(f"/api/v1/dashboard/jobs?org_id={org_id}&limit=1")
            assert response.status_code == 200

            # Maximum valid
            response = client.get(f"/api/v1/dashboard/jobs?org_id={org_id}&limit=100")
            assert response.status_code == 200
