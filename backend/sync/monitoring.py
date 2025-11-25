"""Monitoring integration for sync engine.

Hooks the monitoring system into sync operations to provide real-time
visibility into job status, performance metrics, and error tracking.

This module:
- Wraps sync operations with monitoring callbacks
- Emits events via RealtimeEventBroadcaster
- Records metrics via MetricsCollector
- Tracks errors in ErrorLog
"""

import logging
import asyncio
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, Callable

from sqlalchemy.orm import Session

from backend.sync.models import SyncResult
from backend.monitoring import (
    MetricsCollector,
    RealtimeEventBroadcaster,
)

logger = logging.getLogger(__name__)


class SyncMonitor:
    """Monitors sync operations and emits real-time events."""

    def __init__(self, db: Session):
        """Initialize sync monitor.

        Args:
            db: Database session
        """
        self.db = db
        self.collector = MetricsCollector(db)

    async def on_sync_started(
        self,
        job_id: UUID,
        organization_id: UUID,
        platform: str
    ) -> None:
        """Called when sync job starts.

        Args:
            job_id: Unique job ID
            organization_id: Organization UUID
            platform: Platform name ('xero', 'quickbooks')
        """
        try:
            logger.info(f"[MONITOR] Sync job started: {job_id}")
            await RealtimeEventBroadcaster.emit_job_started(
                job_id,
                organization_id,
                platform
            )
        except Exception as e:
            logger.error(f"[MONITOR] Error emitting job_started event: {e}")

    async def on_sync_completed(
        self,
        job_id: UUID,
        organization_id: UUID,
        result: SyncResult,
        success: bool
    ) -> None:
        """Called when sync job completes.

        Args:
            job_id: Unique job ID
            organization_id: Organization UUID
            result: SyncResult with job metrics
            success: Whether sync succeeded
        """
        try:
            logger.info(
                f"[MONITOR] Sync job completed: {job_id}, "
                f"status={result.status}, duration={result.duration_seconds:.1f}s"
            )

            # Record metrics in database
            self.collector.record_sync_metrics(
                job_id=job_id,
                organization_id=organization_id,
                result=result
            )

            # Emit completion event
            result_data = {
                "job_id": str(job_id),
                "total_synced": result.total_synced,
                "total_failed": result.total_failed,
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
                "transactions": {
                    "created": result.transactions.created,
                    "updated": result.transactions.updated,
                    "failed": result.transactions.failed,
                },
            }

            await RealtimeEventBroadcaster.emit_job_completed(
                job_id,
                organization_id,
                result_data,
                success=success
            )

        except Exception as e:
            logger.error(f"[MONITOR] Error processing sync completion: {e}")

    async def on_sync_error(
        self,
        job_id: UUID,
        organization_id: UUID,
        error_message: str,
        error_type: str = "sync_error",
        severity: str = "error"
    ) -> None:
        """Called when sync job encounters an error.

        Args:
            job_id: Unique job ID
            organization_id: Organization UUID
            error_message: Error message
            error_type: Type of error
            severity: Error severity ('warning', 'error', 'critical')
        """
        try:
            logger.error(
                f"[MONITOR] Sync job error: {job_id}, "
                f"type={error_type}, msg={error_message}"
            )

            # Log error in database
            self.collector.log_error(
                job_id=job_id,
                organization_id=organization_id,
                error_type=error_type,
                error_message=error_message,
                severity=severity
            )

            # Emit error event
            await RealtimeEventBroadcaster.emit_error(
                job_id,
                organization_id,
                {
                    "error_type": error_type,
                    "message": error_message,
                    "severity": severity,
                }
            )

        except Exception as e:
            logger.error(f"[MONITOR] Error processing sync error event: {e}")

    async def on_sync_progress(
        self,
        job_id: UUID,
        organization_id: UUID,
        entity_type: str,
        processed: int,
        total: int,
        failed: int = 0
    ) -> None:
        """Called to report sync progress for an entity type.

        Args:
            job_id: Unique job ID
            organization_id: Organization UUID
            entity_type: Type of entity (accounts, clients, transactions)
            processed: Number of records processed
            total: Total number of records
            failed: Number of records failed
        """
        try:
            logger.info(
                f"[MONITOR] Sync progress: {job_id}, "
                f"{entity_type}: {processed}/{total} (failed: {failed})"
            )

            # Emit progress event
            await RealtimeEventBroadcaster.emit_metric_update(
                job_id,
                organization_id,
                {
                    "entity_type": entity_type,
                    "processed": processed,
                    "total": total,
                    "failed": failed,
                    "rate": (processed / total * 100) if total > 0 else 0,
                }
            )

        except Exception as e:
            logger.error(f"[MONITOR] Error emitting progress event: {e}")


def wrap_sync_with_monitoring(
    sync_func: Callable,
    job_id: UUID,
    organization_id: UUID,
    platform: str,
    db: Session
) -> Callable:
    """Wraps a sync function to emit monitoring events.

    Creates a wrapper that:
    1. Emits job_started event before calling sync_func
    2. Calls the sync function
    3. Records metrics and emits job_completed after sync_func

    Args:
        sync_func: The sync function to wrap
        job_id: Job ID for this sync operation
        organization_id: Organization ID
        platform: Platform name
        db: Database session

    Returns:
        Wrapped function that includes monitoring
    """
    monitor = SyncMonitor(db)

    async def wrapper():
        """Wrapped sync function with monitoring."""
        try:
            # Emit job started
            await monitor.on_sync_started(job_id, organization_id, platform)

            # Call the actual sync function
            result = sync_func()

            # Emit job completed
            success = result.status in ["success", "partial"]
            await monitor.on_sync_completed(job_id, organization_id, result, success)

            return result

        except Exception as e:
            # Emit error event
            await monitor.on_sync_error(
                job_id,
                organization_id,
                str(e),
                error_type="sync_exception",
                severity="critical"
            )
            raise

    return wrapper
