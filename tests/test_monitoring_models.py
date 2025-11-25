"""Tests for monitoring and dashboard models.

Note: Tests use dataclass-like instantiation without database persistence.
Database interaction is tested separately with mocked sessions.
Models can be tested as plain Python objects.
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from backend.monitoring.models import (
    SyncJobMetric,
    DashboardEvent,
    ErrorLog,
    EventType,
    ErrorSeverity,
)


class TestSyncJobMetric:
    """Tests for SyncJobMetric model."""

    def test_sync_job_metric_creation(self):
        """Test creating a sync job metric."""
        job_id = uuid4()
        org_id = uuid4()

        metric = SyncJobMetric(
            job_id=job_id,
            organization_id=org_id,
            transactions_processed=100,
            transactions_failed=5,
            transactions_skipped=2,
            avg_transaction_time_ms=125.5,
            transactions_per_minute=2000.0,
            memory_usage_mb=256.5,
            cpu_usage_percent=45.2,
            api_response_time_ms=45.3,
            rate_limit_remaining=3500,
        )

        assert metric.job_id == job_id
        assert metric.organization_id == org_id
        assert metric.transactions_processed == 100
        assert metric.transactions_failed == 5
        assert metric.transactions_skipped == 2
        assert metric.avg_transaction_time_ms == 125.5
        assert metric.transactions_per_minute == 2000.0
        assert metric.memory_usage_mb == 256.5
        assert metric.cpu_usage_percent == 45.2
        assert metric.api_response_time_ms == 45.3
        assert metric.rate_limit_remaining == 3500

    def test_sync_job_metric_defaults(self):
        """Test default values for sync job metric."""
        job_id = uuid4()
        org_id = uuid4()

        metric = SyncJobMetric(
            job_id=job_id,
            organization_id=org_id,
        )

        assert metric.job_id == job_id
        assert metric.organization_id == org_id
        assert metric.timestamp is not None

    def test_sync_job_metric_to_dict(self):
        """Test converting metric to dictionary."""
        job_id = uuid4()
        org_id = uuid4()

        metric = SyncJobMetric(
            job_id=job_id,
            organization_id=org_id,
            transactions_processed=50,
            memory_usage_mb=128.5,
        )

        data = metric.to_dict()

        assert data["job_id"] == str(job_id)
        assert data["organization_id"] == str(org_id)
        assert data["transactions_processed"] == 50
        assert data["memory_usage_mb"] == 128.5
        assert "timestamp" in data
        assert "id" in data

    def test_sync_job_metric_repr(self):
        """Test string representation of metric."""
        job_id = uuid4()
        org_id = uuid4()

        metric = SyncJobMetric(
            job_id=job_id,
            organization_id=org_id,
            transactions_processed=75,
            transactions_failed=3,
        )

        repr_str = repr(metric)
        assert "SyncJobMetric" in repr_str
        assert "processed=75" in repr_str
        assert "failed=3" in repr_str

    def test_sync_job_metric_with_extended_data(self):
        """Test metric with additional JSON data."""
        metric = SyncJobMetric(
            job_id=uuid4(),
            organization_id=uuid4(),
            transactions_processed=100,
            data={
                "platform": "xero",
                "sync_type": "full",
                "batch_size": 50,
            },
        )

        assert metric.data["platform"] == "xero"
        assert metric.data["sync_type"] == "full"
        assert metric.data["batch_size"] == 50


class TestDashboardEvent:
    """Tests for DashboardEvent model."""

    def test_dashboard_event_creation(self):
        """Test creating a dashboard event."""
        job_id = uuid4()
        org_id = uuid4()

        event = DashboardEvent(
            job_id=job_id,
            organization_id=org_id,
            event_type=EventType.JOB_STARTED,
            severity=ErrorSeverity.INFO,
            title="Sync job started",
            message="Full sync started for Xero",
            data={"platform": "xero", "sync_type": "full"},
        )

        assert event.job_id == job_id
        assert event.organization_id == org_id
        assert event.event_type == EventType.JOB_STARTED
        assert event.severity == ErrorSeverity.INFO
        assert event.title == "Sync job started"
        assert event.message == "Full sync started for Xero"
        assert event.data["platform"] == "xero"

    def test_dashboard_event_types(self):
        """Test different event types."""
        org_id = uuid4()

        event_types = [
            EventType.JOB_STARTED,
            EventType.JOB_COMPLETED,
            EventType.JOB_FAILED,
            EventType.TRANSACTION_COUNT,
            EventType.ERROR_OCCURRED,
            EventType.METRIC_UPDATE,
        ]

        for event_type in event_types:
            event = DashboardEvent(
                organization_id=org_id,
                event_type=event_type,
                title=f"Event: {event_type.value}",
            )
            assert event.event_type == event_type

    def test_dashboard_event_severity_levels(self):
        """Test different severity levels."""
        org_id = uuid4()

        severities = [
            ErrorSeverity.INFO,
            ErrorSeverity.WARNING,
            ErrorSeverity.ERROR,
            ErrorSeverity.CRITICAL,
        ]

        for severity in severities:
            event = DashboardEvent(
                organization_id=org_id,
                event_type=EventType.METRIC_UPDATE,
                severity=severity,
                title=f"Event with {severity.value} severity",
            )
            assert event.severity == severity

    def test_dashboard_event_defaults(self):
        """Test default values for dashboard event."""
        event = DashboardEvent(
            organization_id=uuid4(),
            event_type=EventType.JOB_STARTED,
            title="Test event",
        )

        assert event.severity == ErrorSeverity.INFO
        assert event.message is None
        assert event.data == {}
        assert event.is_broadcast == "N"
        assert event.timestamp is not None

    def test_dashboard_event_to_dict(self):
        """Test converting event to dictionary."""
        job_id = uuid4()
        org_id = uuid4()

        event = DashboardEvent(
            job_id=job_id,
            organization_id=org_id,
            event_type=EventType.JOB_COMPLETED,
            severity=ErrorSeverity.INFO,
            title="Sync completed",
            message="Successfully synced 500 transactions",
        )

        data = event.to_dict()

        assert data["job_id"] == str(job_id)
        assert data["organization_id"] == str(org_id)
        assert data["event_type"] == "job_completed"
        assert data["severity"] == "info"
        assert data["title"] == "Sync completed"
        assert "timestamp" in data

    def test_dashboard_event_repr(self):
        """Test string representation of event."""
        org_id = uuid4()

        event = DashboardEvent(
            organization_id=org_id,
            event_type=EventType.ERROR_OCCURRED,
            severity=ErrorSeverity.CRITICAL,
            title="Critical error",
        )

        repr_str = repr(event)
        assert "DashboardEvent" in repr_str
        assert "error_occurred" in repr_str
        assert "critical" in repr_str

    def test_dashboard_event_with_data(self):
        """Test event with additional data."""
        event = DashboardEvent(
            organization_id=uuid4(),
            event_type=EventType.TRANSACTION_COUNT,
            title="Transaction count update",
            data={
                "total_processed": 500,
                "failed": 10,
                "skipped": 5,
                "rate": 100.5,
            },
        )

        assert event.data["total_processed"] == 500
        assert event.data["failed"] == 10
        assert event.data["rate"] == 100.5


class TestErrorLog:
    """Tests for ErrorLog model."""

    def test_error_log_creation(self):
        """Test creating an error log."""
        job_id = uuid4()
        org_id = uuid4()

        error = ErrorLog(
            job_id=job_id,
            organization_id=org_id,
            error_type="APIError",
            severity=ErrorSeverity.ERROR,
            error_message="API rate limit exceeded",
            stack_trace="Traceback...",
            context={"endpoint": "/transactions", "status_code": 429},
        )

        assert error.job_id == job_id
        assert error.organization_id == org_id
        assert error.error_type == "APIError"
        assert error.severity == ErrorSeverity.ERROR
        assert error.error_message == "API rate limit exceeded"
        assert error.context["status_code"] == 429

    def test_error_log_defaults(self):
        """Test default values for error log."""
        error = ErrorLog(
            job_id=uuid4(),
            organization_id=uuid4(),
            error_type="ValidationError",
            error_message="Invalid data",
        )

        assert error.severity == ErrorSeverity.ERROR
        assert error.retry_count == 0
        assert error.is_resolved == "N"
        assert error.resolved_at is None
        assert error.next_retry_at is None
        assert error.data == {}

    def test_error_log_mark_resolved(self):
        """Test marking error as resolved."""
        error = ErrorLog(
            job_id=uuid4(),
            organization_id=uuid4(),
            error_type="APIError",
            error_message="Connection timeout",
        )

        assert error.is_resolved == "N"
        assert error.resolved_at is None

        error.mark_resolved()

        assert error.is_resolved == "Y"
        assert error.resolved_at is not None
        assert isinstance(error.resolved_at, datetime)

    def test_error_log_increment_retry(self):
        """Test incrementing retry count."""
        error = ErrorLog(
            job_id=uuid4(),
            organization_id=uuid4(),
            error_type="NetworkError",
            error_message="Connection refused",
        )

        assert error.retry_count == 0
        assert error.next_retry_at is None

        next_retry = datetime.now(timezone.utc) + timedelta(minutes=5)
        error.increment_retry(next_retry)

        assert error.retry_count == 1
        assert error.next_retry_at == next_retry

        # Increment again
        error.increment_retry()
        assert error.retry_count == 2

    def test_error_log_to_dict(self):
        """Test converting error log to dictionary."""
        job_id = uuid4()
        org_id = uuid4()

        error = ErrorLog(
            job_id=job_id,
            organization_id=org_id,
            error_type="DatabaseError",
            severity=ErrorSeverity.CRITICAL,
            error_message="Connection pool exhausted",
            retry_count=2,
        )

        data = error.to_dict()

        assert data["job_id"] == str(job_id)
        assert data["organization_id"] == str(org_id)
        assert data["error_type"] == "DatabaseError"
        assert data["severity"] == "critical"
        assert data["retry_count"] == 2
        assert "created_at" in data

    def test_error_log_repr(self):
        """Test string representation of error log."""
        job_id = uuid4()

        error = ErrorLog(
            job_id=job_id,
            organization_id=uuid4(),
            error_type="SyncError",
            error_message="Sync failed",
        )

        repr_str = repr(error)
        assert "ErrorLog" in repr_str
        assert "SyncError" in repr_str
        assert "resolved=N" in repr_str

    def test_error_log_multiple_retries(self):
        """Test multiple retries of an error."""
        error = ErrorLog(
            job_id=uuid4(),
            organization_id=uuid4(),
            error_type="TemporaryError",
            error_message="Service unavailable",
        )

        # Simulate retries
        for i in range(3):
            next_retry = datetime.now(timezone.utc) + timedelta(minutes=2 ** i)
            error.increment_retry(next_retry)
            assert error.retry_count == i + 1

        # Finally resolve it
        error.mark_resolved()
        assert error.is_resolved == "Y"
        assert error.retry_count == 3

    def test_error_log_severity_types(self):
        """Test different error severity levels."""
        job_id = uuid4()
        org_id = uuid4()

        severities = [
            ErrorSeverity.INFO,
            ErrorSeverity.WARNING,
            ErrorSeverity.ERROR,
            ErrorSeverity.CRITICAL,
        ]

        for severity in severities:
            error = ErrorLog(
                job_id=job_id,
                organization_id=org_id,
                error_type="TestError",
                error_message=f"Error with {severity.value} severity",
                severity=severity,
            )
            assert error.severity == severity


class TestModelIntegration:
    """Integration tests for monitoring models."""

    def test_models_with_uuid_conversion(self):
        """Test UUID handling in models."""
        job_id = uuid4()
        org_id = uuid4()

        metric = SyncJobMetric(job_id=job_id, organization_id=org_id, transactions_processed=10)
        event = DashboardEvent(job_id=job_id, organization_id=org_id, event_type=EventType.JOB_STARTED, title="Test")
        error = ErrorLog(job_id=job_id, organization_id=org_id, error_type="TestError", error_message="Test")

        # Test to_dict conversions preserve UUIDs as strings
        assert isinstance(metric.to_dict()["job_id"], str)
        assert isinstance(event.to_dict()["job_id"], str)
        assert isinstance(error.to_dict()["job_id"], str)

    def test_models_timestamp_handling(self):
        """Test timestamp handling in models."""
        metric = SyncJobMetric(job_id=uuid4(), organization_id=uuid4())
        event = DashboardEvent(organization_id=uuid4(), event_type=EventType.METRIC_UPDATE, title="Test")
        error = ErrorLog(job_id=uuid4(), organization_id=uuid4(), error_type="TestError", error_message="Test")

        # All should have timestamps
        assert metric.timestamp is not None
        assert event.timestamp is not None
        assert error.created_at is not None

        # Timestamps should be timezone-aware
        assert metric.timestamp.tzinfo is not None
        assert event.timestamp.tzinfo is not None
        assert error.created_at.tzinfo is not None

    def test_event_and_error_relationship(self):
        """Test relationship between events and errors."""
        job_id = uuid4()
        org_id = uuid4()

        # Create an error event
        event = DashboardEvent(
            job_id=job_id,
            organization_id=org_id,
            event_type=EventType.ERROR_OCCURRED,
            severity=ErrorSeverity.ERROR,
            title="Error occurred",
        )

        # Create corresponding error log
        error = ErrorLog(
            job_id=job_id,
            organization_id=org_id,
            error_type="SyncError",
            severity=ErrorSeverity.ERROR,
            error_message="Sync failed",
        )

        # Both should reference same job and org
        assert event.job_id == error.job_id
        assert event.organization_id == error.organization_id
