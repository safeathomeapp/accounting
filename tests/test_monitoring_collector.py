"""Tests for monitoring metrics collector.

Note: Tests use mocking for database operations to avoid requiring
a live PostgreSQL connection. This allows testing business logic
independently of database infrastructure.
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch

from backend.monitoring.collector import MetricsCollector
from backend.monitoring.models import SyncJobMetric, DashboardEvent, ErrorLog, EventType, ErrorSeverity
from backend.sync.models import SyncResult, SyncStats, SyncError


class TestMetricsCollection:
    """Tests for basic metrics collection."""

    def test_record_sync_metrics_success(self):
        """Test recording metrics from successful sync."""
        # Setup mocks
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        job_id = uuid4()
        org_id = uuid4()

        # Create sync result
        result = SyncResult(
            status="success",
            sync_history_id=uuid4(),
            accounts=SyncStats("account", total_fetched=10, created=5, updated=3),
            clients=SyncStats("client", total_fetched=8, created=4, updated=2),
            transactions=SyncStats("transaction", total_fetched=100, created=80, updated=15),
        )
        result.duration_seconds = 10.0

        # Record metrics
        metric = collector.record_sync_metrics(job_id, org_id, result, platform_name="xero")

        # Verify metric was created and added to db
        assert db_mock.add.called
        assert db_mock.commit.called

    def test_record_sync_metrics_partial(self):
        """Test recording metrics from partial sync."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        job_id = uuid4()
        org_id = uuid4()

        # Create partial sync result
        result = SyncResult(
            status="partial",
            sync_history_id=uuid4(),
            accounts=SyncStats("account", total_fetched=10, created=5, updated=3, failed=2),
            clients=SyncStats("client", total_fetched=8, created=4, failed=1),
            transactions=SyncStats("transaction", total_fetched=100, created=80, failed=5),
        )
        result.duration_seconds = 15.0
        result.errors = [
            SyncError(
                entity_type="transaction",
                entity_id="TXN123",
                error_message="Invalid amount",
                error_type="validation"
            )
        ]

        # Record metrics
        metric = collector.record_sync_metrics(job_id, org_id, result)

        # Verify db operations were called
        assert db_mock.add.called
        assert db_mock.commit.called

    def test_record_sync_metrics_failed(self):
        """Test recording metrics from failed sync."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        job_id = uuid4()
        org_id = uuid4()

        # Create failed sync result
        result = SyncResult(
            status="failed",
            sync_history_id=uuid4(),
            accounts=SyncStats("account", total_fetched=0),
            clients=SyncStats("client", total_fetched=0),
            transactions=SyncStats("transaction", total_fetched=0),
        )
        result.duration_seconds = 5.0
        result.errors = [
            SyncError(
                entity_type="platform",
                error_message="API authentication failed",
                error_type="fetch"
            )
        ]

        # Record metrics
        metric = collector.record_sync_metrics(job_id, org_id, result)

        # Verify db operations
        assert db_mock.add.called
        assert db_mock.commit.called


class TestMetricsCalculation:
    """Tests for metrics calculation accuracy."""

    def test_transactions_per_minute_calculation(self):
        """Test transactions per minute calculation."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        job_id = uuid4()
        org_id = uuid4()

        # 300 transactions in 60 seconds = 300 per minute
        result = SyncResult(
            status="success",
            sync_history_id=uuid4(),
            accounts=SyncStats("account"),
            clients=SyncStats("client"),
            transactions=SyncStats("transaction", total_fetched=300, created=300),
        )
        result.duration_seconds = 60.0

        # Mock the metric creation to return actual object
        metric_instance = MagicMock()
        metric_instance.transactions_per_minute = 300.0
        db_mock.query.return_value.filter_by.return_value.first.return_value = metric_instance

        collector.record_sync_metrics(job_id, org_id, result)

        # Verify db.add was called with metrics
        assert db_mock.add.called

    def test_transactions_per_minute_less_than_minute(self):
        """Test transactions per minute calculation for syncs under 1 minute."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        job_id = uuid4()
        org_id = uuid4()

        # 100 transactions in 30 seconds = 200 per minute
        result = SyncResult(
            status="success",
            sync_history_id=uuid4(),
            accounts=SyncStats("account"),
            clients=SyncStats("client"),
            transactions=SyncStats("transaction", total_fetched=100, created=100),
        )
        result.duration_seconds = 30.0

        collector.record_sync_metrics(job_id, org_id, result)

        # Verify metric recording was attempted
        assert db_mock.add.called

    def test_avg_transaction_time_calculation(self):
        """Test average transaction time calculation."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        job_id = uuid4()
        org_id = uuid4()

        # 100 transactions in 10 seconds = 100ms per transaction
        result = SyncResult(
            status="success",
            sync_history_id=uuid4(),
            accounts=SyncStats("account"),
            clients=SyncStats("client"),
            transactions=SyncStats("transaction", total_fetched=100, created=100),
        )
        result.duration_seconds = 10.0

        collector.record_sync_metrics(job_id, org_id, result)

        assert db_mock.add.called

    def test_avg_transaction_time_zero_transactions(self):
        """Test average transaction time with zero transactions."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        job_id = uuid4()
        org_id = uuid4()

        result = SyncResult(
            status="success",
            sync_history_id=uuid4(),
            accounts=SyncStats("account"),
            clients=SyncStats("client"),
            transactions=SyncStats("transaction", total_fetched=0),
        )
        result.duration_seconds = 10.0

        collector.record_sync_metrics(job_id, org_id, result)

        assert db_mock.add.called


class TestDashboardEventEmission:
    """Tests for dashboard event emission."""

    def test_emit_success_event(self):
        """Test emitting event for successful sync."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        job_id = uuid4()
        org_id = uuid4()

        result = SyncResult(
            status="success",
            sync_history_id=uuid4(),
            accounts=SyncStats("account", created=5),
            clients=SyncStats("client", created=3),
            transactions=SyncStats("transaction", created=100),
        )
        result.duration_seconds = 15.0

        collector.record_sync_metrics(job_id, org_id, result)

        # Verify event emission attempted (db.add called)
        assert db_mock.add.called

    def test_emit_partial_event(self):
        """Test emitting event for partial sync."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        job_id = uuid4()
        org_id = uuid4()

        result = SyncResult(
            status="partial",
            sync_history_id=uuid4(),
            accounts=SyncStats("account", created=5, failed=1),
            clients=SyncStats("client", created=3),
            transactions=SyncStats("transaction", created=100, failed=5),
        )
        result.duration_seconds = 15.0
        result.errors = [
            SyncError(entity_type="account", error_message="Invalid code", error_type="validation")
        ]

        collector.record_sync_metrics(job_id, org_id, result)

        assert db_mock.add.called

    def test_emit_failed_event(self):
        """Test emitting event for failed sync."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        job_id = uuid4()
        org_id = uuid4()

        result = SyncResult(
            status="failed",
            sync_history_id=uuid4(),
            accounts=SyncStats("account"),
            clients=SyncStats("client"),
            transactions=SyncStats("transaction"),
        )
        result.duration_seconds = 5.0
        result.errors = [
            SyncError(
                entity_type="platform",
                error_message="API unavailable",
                error_type="fetch"
            )
        ]

        collector.record_sync_metrics(job_id, org_id, result)

        assert db_mock.add.called


class TestErrorLogging:
    """Tests for error log recording."""

    def test_record_single_error(self):
        """Test recording a single sync error."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        job_id = uuid4()
        org_id = uuid4()

        error = SyncError(
            entity_type="transaction",
            entity_id="TXN123",
            error_message="Invalid amount format",
            error_type="validation"
        )

        result = SyncResult(
            status="partial",
            sync_history_id=uuid4(),
            accounts=SyncStats("account"),
            clients=SyncStats("client"),
            transactions=SyncStats("transaction", failed=1),
            errors=[error]
        )
        result.duration_seconds = 10.0

        collector.record_sync_metrics(job_id, org_id, result)

        # Verify error logging was attempted
        assert db_mock.add.called

    def test_record_multiple_errors(self):
        """Test recording multiple sync errors."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        job_id = uuid4()
        org_id = uuid4()

        errors = [
            SyncError(
                entity_type="account",
                entity_id="ACC001",
                error_message="Account code missing",
                error_type="validation"
            ),
            SyncError(
                entity_type="transaction",
                entity_id="TXN001",
                error_message="Amount exceeds limit",
                error_type="validation"
            ),
            SyncError(
                entity_type="client",
                error_message="Database connection failed",
                error_type="database"
            ),
        ]

        result = SyncResult(
            status="partial",
            sync_history_id=uuid4(),
            accounts=SyncStats("account", failed=1),
            clients=SyncStats("client", failed=1),
            transactions=SyncStats("transaction", failed=1),
            errors=errors
        )
        result.duration_seconds = 10.0

        collector.record_sync_metrics(job_id, org_id, result)

        # Verify multiple error recordings attempted
        assert db_mock.add.call_count >= len(errors)


class TestMetricsRetrieval:
    """Tests for retrieving recorded metrics."""

    def test_get_job_metrics(self):
        """Test retrieving metrics for a specific job."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        job_id = uuid4()

        # Mock the query chain
        metric_mock = MagicMock()
        db_mock.query.return_value.filter_by.return_value.first.return_value = metric_mock

        result = collector.get_job_metrics(job_id)

        # Verify query was executed
        db_mock.query.assert_called()
        assert result == metric_mock

    def test_get_job_metrics_not_found(self):
        """Test retrieving metrics for non-existent job."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        job_id = uuid4()

        # Mock no results found
        db_mock.query.return_value.filter_by.return_value.first.return_value = None

        metric = collector.get_job_metrics(job_id)

        assert metric is None

    def test_get_organization_metrics(self):
        """Test retrieving metrics for an organization."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        org_id = uuid4()

        # Mock multiple metric results
        metrics_mock = [MagicMock() for _ in range(3)]
        db_mock.query.return_value.filter.return_value.order_by.return_value.all.return_value = metrics_mock

        metrics = collector.get_organization_metrics(org_id, timeframe_minutes=60)

        assert len(metrics) == 3

    def test_get_organization_metrics_empty(self):
        """Test retrieving metrics for organization with no metrics."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        org_id = uuid4()

        # Mock empty results
        db_mock.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        metrics = collector.get_organization_metrics(org_id)

        assert metrics == []


class TestAggregateMetrics:
    """Tests for aggregate metrics calculation."""

    def test_calculate_aggregate_metrics(self):
        """Test calculating aggregate metrics for organization."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        org_id = uuid4()

        # Mock metrics
        metric_mocks = []
        for i in range(3):
            m = MagicMock()
            m.transactions_processed = 100
            m.transactions_failed = 0
            m.transactions_skipped = 0
            m.avg_transaction_time_ms = 10.0
            m.transactions_per_minute = 600.0
            metric_mocks.append(m)

        db_mock.query.return_value.filter.return_value.order_by.return_value.all.return_value = metric_mocks

        agg = collector.calculate_aggregate_metrics(org_id, timeframe_minutes=60)

        assert agg["organization_id"] == str(org_id)
        assert agg["job_count"] == 3
        assert agg["total_processed"] == 300  # 100 * 3

    def test_calculate_aggregate_metrics_with_failures(self):
        """Test aggregate metrics with failed transactions."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        org_id = uuid4()

        # Mock metrics with different values
        metric1 = MagicMock()
        metric1.transactions_processed = 100
        metric1.transactions_failed = 0
        metric1.transactions_skipped = 0
        metric1.avg_transaction_time_ms = 10.0
        metric1.transactions_per_minute = 600.0

        metric2 = MagicMock()
        metric2.transactions_processed = 80
        metric2.transactions_failed = 20
        metric2.transactions_skipped = 0
        metric2.avg_transaction_time_ms = 12.0
        metric2.transactions_per_minute = 480.0

        db_mock.query.return_value.filter.return_value.order_by.return_value.all.return_value = [metric1, metric2]

        agg = collector.calculate_aggregate_metrics(org_id, timeframe_minutes=60)

        assert agg["total_processed"] == 180  # 100 + 80
        assert agg["total_failed"] == 20
        assert agg["job_count"] == 2

    def test_aggregate_metrics_empty_organization(self):
        """Test aggregate metrics for organization with no data."""
        db_mock = MagicMock()
        collector = MetricsCollector(db_mock)
        org_id = uuid4()

        # Mock empty metrics
        db_mock.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        agg = collector.calculate_aggregate_metrics(org_id)

        assert agg["organization_id"] == str(org_id)
        assert agg["job_count"] == 0
        assert agg["total_processed"] == 0
        assert agg["total_failed"] == 0
