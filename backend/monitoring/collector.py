"""Metrics collection from sync operations.

Collects performance data from sync engine runs and stores metrics
for monitoring dashboard and analysis.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from backend.monitoring.models import SyncJobMetric, DashboardEvent, ErrorLog, EventType, ErrorSeverity
from backend.sync.models import SyncResult

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and records metrics from sync operations."""

    def __init__(self, db: Session):
        """
        Initialize metrics collector.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def record_sync_metrics(
        self,
        job_id: UUID,
        organization_id: UUID,
        result: SyncResult,
        platform_name: str = "unknown"
    ) -> Optional[SyncJobMetric]:
        """
        Record metrics from a completed sync operation.

        Extracts performance data from SyncResult and stores as SyncJobMetric.
        Also emits dashboard events and error logs for monitoring.

        Args:
            job_id: UUID of the sync job
            organization_id: UUID of the organization
            result: SyncResult from sync engine
            platform_name: Name of the platform synced

        Returns:
            Created SyncJobMetric object or None if recording fails
        """
        try:
            # Calculate metrics
            duration_seconds = max(result.duration_seconds, 0.1)  # Avoid division by zero
            total_transactions = result.transactions.total_processed
            transactions_per_minute = (total_transactions / duration_seconds) * 60 if duration_seconds > 0 else 0

            avg_transaction_time_ms = (
                (duration_seconds * 1000 / total_transactions)
                if total_transactions > 0
                else 0.0
            )

            # Create metric record
            metric = SyncJobMetric(
                job_id=job_id,
                organization_id=organization_id,
                transactions_processed=total_transactions,
                transactions_failed=result.total_failed,
                transactions_skipped=result.transactions.skipped,
                avg_transaction_time_ms=avg_transaction_time_ms,
                transactions_per_minute=transactions_per_minute,
                data={
                    "platform": platform_name,
                    "sync_status": result.status,
                    "duration_seconds": result.duration_seconds,
                    "accounts_created": result.accounts.created,
                    "accounts_updated": result.accounts.updated,
                    "accounts_failed": result.accounts.failed,
                    "clients_created": result.clients.created,
                    "clients_updated": result.clients.updated,
                    "clients_failed": result.clients.failed,
                }
            )

            self.db.add(metric)
            self.db.flush()

            # Emit dashboard event for job completion
            self._emit_job_event(job_id, organization_id, result)

            # Record any errors as error logs
            self._record_errors(job_id, organization_id, result)

            self.db.commit()

            logger.info(
                f"Recorded metrics for job {job_id}: "
                f"processed={total_transactions}, failed={result.total_failed}, "
                f"duration={result.duration_seconds:.1f}s"
            )

            return metric

        except Exception as e:
            logger.error(f"Failed to record metrics for job {job_id}: {e}", exc_info=True)
            self.db.rollback()
            return None

    def _emit_job_event(
        self,
        job_id: UUID,
        organization_id: UUID,
        result: SyncResult
    ) -> None:
        """
        Emit a dashboard event for job completion.

        Args:
            job_id: UUID of the job
            organization_id: UUID of the organization
            result: SyncResult with job outcome
        """
        try:
            # Determine event type and severity based on result
            if result.status == "success":
                event_type = EventType.JOB_COMPLETED
                severity = ErrorSeverity.INFO
                title = f"Sync completed successfully"
            elif result.status == "partial":
                event_type = EventType.JOB_COMPLETED
                severity = ErrorSeverity.WARNING
                title = f"Sync completed with errors"
            else:
                event_type = EventType.JOB_FAILED
                severity = ErrorSeverity.ERROR
                title = f"Sync failed"

            message = (
                f"Processed: {result.transactions.total_processed}, "
                f"Failed: {result.total_failed}, "
                f"Duration: {result.duration_seconds:.1f}s"
            )

            event = DashboardEvent(
                job_id=job_id,
                organization_id=organization_id,
                event_type=event_type,
                severity=severity,
                title=title,
                message=message,
                data={
                    "transactions_processed": result.transactions.total_processed,
                    "transactions_failed": result.total_failed,
                    "transactions_skipped": result.transactions.skipped,
                    "duration_seconds": result.duration_seconds,
                    "accounts": {
                        "created": result.accounts.created,
                        "updated": result.accounts.updated,
                        "failed": result.accounts.failed,
                    },
                    "clients": {
                        "created": result.clients.created,
                        "updated": result.clients.updated,
                        "failed": result.clients.failed,
                    },
                }
            )

            self.db.add(event)

        except Exception as e:
            logger.error(f"Failed to emit job event for {job_id}: {e}")

    def _record_errors(
        self,
        job_id: UUID,
        organization_id: UUID,
        result: SyncResult
    ) -> None:
        """
        Record errors from sync result as error logs.

        Args:
            job_id: UUID of the job
            organization_id: UUID of the organization
            result: SyncResult containing errors
        """
        try:
            for sync_error in result.errors:
                # Map sync error type to error severity
                severity_map = {
                    "fetch": ErrorSeverity.ERROR,
                    "parse": ErrorSeverity.ERROR,
                    "validation": ErrorSeverity.WARNING,
                    "database": ErrorSeverity.CRITICAL,
                }
                severity = severity_map.get(sync_error.error_type, ErrorSeverity.ERROR)

                error_log = ErrorLog(
                    job_id=job_id,
                    organization_id=organization_id,
                    error_type=sync_error.error_type,
                    severity=severity,
                    error_message=sync_error.error_message,
                    context={
                        "entity_type": sync_error.entity_type,
                        "entity_id": sync_error.entity_id,
                        "timestamp": sync_error.timestamp.isoformat() if sync_error.timestamp else None,
                    }
                )

                self.db.add(error_log)

        except Exception as e:
            logger.error(f"Failed to record errors for job {job_id}: {e}")

    def get_job_metrics(self, job_id: UUID) -> Optional[SyncJobMetric]:
        """
        Get metrics for a specific job.

        Args:
            job_id: UUID of the job

        Returns:
            SyncJobMetric if found, None otherwise
        """
        try:
            return self.db.query(SyncJobMetric).filter_by(
                job_id=job_id
            ).first()
        except Exception as e:
            logger.error(f"Failed to retrieve metrics for job {job_id}: {e}")
            return None

    def get_organization_metrics(
        self,
        organization_id: UUID,
        timeframe_minutes: int = 60
    ) -> list:
        """
        Get metrics for an organization within a timeframe.

        Args:
            organization_id: UUID of the organization
            timeframe_minutes: Number of minutes to look back (default 60)

        Returns:
            List of SyncJobMetric records
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=timeframe_minutes)

            return self.db.query(SyncJobMetric).filter(
                SyncJobMetric.organization_id == organization_id,
                SyncJobMetric.timestamp >= cutoff_time
            ).order_by(SyncJobMetric.timestamp.desc()).all()

        except Exception as e:
            logger.error(f"Failed to retrieve organization metrics: {e}")
            return []

    def calculate_aggregate_metrics(
        self,
        organization_id: UUID,
        timeframe_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Calculate aggregate metrics for an organization.

        Args:
            organization_id: UUID of the organization
            timeframe_minutes: Number of minutes to look back (default 60)

        Returns:
            Dictionary with aggregated metrics
        """
        try:
            metrics = self.get_organization_metrics(organization_id, timeframe_minutes)

            if not metrics:
                return {
                    "organization_id": str(organization_id),
                    "total_processed": 0,
                    "total_failed": 0,
                    "total_skipped": 0,
                    "avg_transaction_time_ms": 0.0,
                    "avg_transactions_per_minute": 0.0,
                    "job_count": 0,
                }

            total_processed = sum(m.transactions_processed for m in metrics)
            total_failed = sum(m.transactions_failed for m in metrics)
            total_skipped = sum(m.transactions_skipped for m in metrics)
            avg_time = sum(m.avg_transaction_time_ms for m in metrics) / len(metrics) if metrics else 0
            avg_tpm = sum(m.transactions_per_minute for m in metrics) / len(metrics) if metrics else 0

            return {
                "organization_id": str(organization_id),
                "total_processed": total_processed,
                "total_failed": total_failed,
                "total_skipped": total_skipped,
                "avg_transaction_time_ms": round(avg_time, 2),
                "avg_transactions_per_minute": round(avg_tpm, 2),
                "job_count": len(metrics),
                "timeframe_minutes": timeframe_minutes,
            }

        except Exception as e:
            logger.error(f"Failed to calculate aggregate metrics: {e}")
            return {}
