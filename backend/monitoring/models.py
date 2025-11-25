"""Monitoring and dashboard data models.

Models for tracking sync job metrics, real-time events, and error logs
for the monitoring dashboard.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, Integer, Float, JSON, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from backend.models import Base


class EventType(str, Enum):
    """Dashboard event types."""
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    TRANSACTION_COUNT = "transaction_count"
    ERROR_OCCURRED = "error_occurred"
    METRIC_UPDATE = "metric_update"
    JOB_PAUSED = "job_paused"
    JOB_RESUMED = "job_resumed"


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SyncJobMetric(Base):
    """Metrics for a sync job during execution.

    Tracks performance data for each sync job to enable
    monitoring and analysis of sync performance.
    """

    __tablename__ = "sync_job_metrics"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)

    # Timing
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Transaction counts
    transactions_processed = Column(Integer, default=0, nullable=False)
    transactions_failed = Column(Integer, default=0, nullable=False)
    transactions_skipped = Column(Integer, default=0, nullable=False)

    # Performance metrics
    avg_transaction_time_ms = Column(Float, default=0.0, nullable=False)  # milliseconds
    transactions_per_minute = Column(Float, default=0.0, nullable=False)

    # Resource usage
    memory_usage_mb = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)

    # API metrics
    api_response_time_ms = Column(Float, nullable=True)
    rate_limit_remaining = Column(Integer, nullable=True)

    # Additional data
    data = Column(JSON, default=dict, nullable=False)  # For extensibility

    def __init__(self, **kwargs):
        """Initialize with defaults for non-database instantiation."""
        # Set defaults if not provided
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.now(timezone.utc)
        if 'id' not in kwargs:
            kwargs['id'] = uuid4()
        if 'transactions_processed' not in kwargs:
            kwargs['transactions_processed'] = 0
        if 'transactions_failed' not in kwargs:
            kwargs['transactions_failed'] = 0
        if 'transactions_skipped' not in kwargs:
            kwargs['transactions_skipped'] = 0
        if 'avg_transaction_time_ms' not in kwargs:
            kwargs['avg_transaction_time_ms'] = 0.0
        if 'transactions_per_minute' not in kwargs:
            kwargs['transactions_per_minute'] = 0.0
        if 'data' not in kwargs:
            kwargs['data'] = {}
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return (
            f"<SyncJobMetric job_id={self.job_id} "
            f"processed={self.transactions_processed} failed={self.transactions_failed}>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "job_id": str(self.job_id),
            "organization_id": str(self.organization_id),
            "timestamp": self.timestamp.isoformat(),
            "transactions_processed": self.transactions_processed,
            "transactions_failed": self.transactions_failed,
            "transactions_skipped": self.transactions_skipped,
            "avg_transaction_time_ms": self.avg_transaction_time_ms,
            "transactions_per_minute": self.transactions_per_minute,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "api_response_time_ms": self.api_response_time_ms,
            "rate_limit_remaining": self.rate_limit_remaining,
            "data": self.data,
        }


class DashboardEvent(Base):
    """Real-time events for dashboard streaming.

    Events emitted during sync operations that are broadcast
    to WebSocket clients for live dashboard updates.
    """

    __tablename__ = "dashboard_events"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)

    # Event classification
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    severity = Column(SQLEnum(ErrorSeverity), default=ErrorSeverity.INFO, nullable=False)

    # Timing
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Event data
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    data = Column(JSON, default=dict, nullable=False)  # Type-specific data

    # Status tracking
    is_broadcast = Column(String(1), default="N", nullable=False)  # Y/N - whether event was broadcast to clients
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __init__(self, **kwargs):
        """Initialize with defaults for non-database instantiation."""
        if 'id' not in kwargs:
            kwargs['id'] = uuid4()
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.now(timezone.utc)
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.now(timezone.utc)
        if 'severity' not in kwargs:
            kwargs['severity'] = ErrorSeverity.INFO
        if 'data' not in kwargs:
            kwargs['data'] = {}
        if 'is_broadcast' not in kwargs:
            kwargs['is_broadcast'] = "N"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return (
            f"<DashboardEvent type={self.event_type.value} "
            f"org={self.organization_id} severity={self.severity.value}>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "job_id": str(self.job_id) if self.job_id else None,
            "organization_id": str(self.organization_id),
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "message": self.message,
            "data": self.data,
        }


class ErrorLog(Base):
    """Detailed error logging for monitoring and debugging.

    Tracks all errors that occur during sync operations,
    including retry information and resolution status.
    """

    __tablename__ = "error_logs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)

    # Error classification
    error_type = Column(String(100), nullable=False, index=True)  # e.g., "APIError", "ValidationError", etc.
    severity = Column(SQLEnum(ErrorSeverity), default=ErrorSeverity.ERROR, nullable=False)

    # Error details
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    context = Column(JSON, default=dict, nullable=False)  # Additional context

    # Timing
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Retry information
    retry_count = Column(Integer, default=0, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    is_resolved = Column(String(1), default="N", nullable=False)  # Y/N

    # Additional data
    data = Column(JSON, default=dict, nullable=False)

    def __init__(self, **kwargs):
        """Initialize with defaults for non-database instantiation."""
        if 'id' not in kwargs:
            kwargs['id'] = uuid4()
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.now(timezone.utc)
        if 'severity' not in kwargs:
            kwargs['severity'] = ErrorSeverity.ERROR
        if 'retry_count' not in kwargs:
            kwargs['retry_count'] = 0
        if 'is_resolved' not in kwargs:
            kwargs['is_resolved'] = "N"
        if 'data' not in kwargs:
            kwargs['data'] = {}
        if 'context' not in kwargs:
            kwargs['context'] = {}
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return (
            f"<ErrorLog job={self.job_id} type={self.error_type} "
            f"severity={self.severity.value} resolved={self.is_resolved}>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "job_id": str(self.job_id),
            "organization_id": str(self.organization_id),
            "error_type": self.error_type,
            "severity": self.severity.value,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "retry_count": self.retry_count,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "is_resolved": self.is_resolved,
        }

    def mark_resolved(self) -> None:
        """Mark this error as resolved."""
        self.is_resolved = "Y"
        self.resolved_at = datetime.now(timezone.utc)

    def increment_retry(self, next_retry_at: Optional[datetime] = None) -> None:
        """Increment retry count and set next retry time."""
        self.retry_count += 1
        self.next_retry_at = next_retry_at
