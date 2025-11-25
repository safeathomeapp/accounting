"""Real-time event broadcasting system for monitoring dashboard.

Emits real-time events from sync operations and broadcasts them
to connected WebSocket clients.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from uuid import UUID
import asyncio

from backend.monitoring.models import DashboardEvent, EventType, ErrorSeverity
from backend.monitoring.websocket import manager, format_ws_message

logger = logging.getLogger(__name__)


class RealtimeEventBroadcaster:
    """Broadcasts real-time events to connected dashboard clients."""

    @staticmethod
    async def emit_job_started(
        job_id: UUID,
        organization_id: UUID,
        platform_name: str = "unknown"
    ) -> None:
        """
        Emit event when a sync job starts.

        Args:
            job_id: UUID of the sync job
            organization_id: UUID of the organization
            platform_name: Name of the accounting platform
        """
        try:
            message = format_ws_message(
                message_type="job_started",
                data={
                    "platform": platform_name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                organization_id=str(organization_id),
                job_id=str(job_id)
            )

            await manager.broadcast_to_organization(
                str(organization_id), message
            )

            logger.debug(f"Emitted job_started event for job {job_id}")

        except Exception as e:
            logger.error(f"Failed to emit job_started event: {e}")

    @staticmethod
    async def emit_metric_update(
        job_id: UUID,
        organization_id: UUID,
        metric_data: Dict[str, Any]
    ) -> None:
        """
        Emit event when metrics are updated during sync.

        Args:
            job_id: UUID of the sync job
            organization_id: UUID of the organization
            metric_data: Metric data to broadcast
        """
        try:
            message = format_ws_message(
                message_type="metric_update",
                data=metric_data,
                organization_id=str(organization_id),
                job_id=str(job_id)
            )

            await manager.broadcast_to_organization(
                str(organization_id), message
            )

            logger.debug(f"Emitted metric_update event for job {job_id}")

        except Exception as e:
            logger.error(f"Failed to emit metric_update event: {e}")

    @staticmethod
    async def emit_transaction_count(
        job_id: UUID,
        organization_id: UUID,
        count_data: Dict[str, Any]
    ) -> None:
        """
        Emit event for transaction count updates.

        Args:
            job_id: UUID of the sync job
            organization_id: UUID of the organization
            count_data: Transaction count data
        """
        try:
            message = format_ws_message(
                message_type="transaction_count",
                data=count_data,
                organization_id=str(organization_id),
                job_id=str(job_id)
            )

            await manager.broadcast_to_organization(
                str(organization_id), message
            )

            logger.debug(f"Emitted transaction_count event for job {job_id}")

        except Exception as e:
            logger.error(f"Failed to emit transaction_count event: {e}")

    @staticmethod
    async def emit_error(
        job_id: UUID,
        organization_id: UUID,
        error_data: Dict[str, Any],
        severity: ErrorSeverity = ErrorSeverity.ERROR
    ) -> None:
        """
        Emit event when an error occurs during sync.

        Args:
            job_id: UUID of the sync job
            organization_id: UUID of the organization
            error_data: Error details
            severity: Severity level of the error
        """
        try:
            message = format_ws_message(
                message_type="error",
                data={
                    **error_data,
                    "severity": severity.value,
                },
                organization_id=str(organization_id),
                job_id=str(job_id)
            )

            await manager.broadcast_to_organization(
                str(organization_id), message
            )

            logger.debug(f"Emitted error event for job {job_id}")

        except Exception as e:
            logger.error(f"Failed to emit error event: {e}")

    @staticmethod
    async def emit_job_completed(
        job_id: UUID,
        organization_id: UUID,
        result_data: Dict[str, Any],
        success: bool = True
    ) -> None:
        """
        Emit event when a sync job completes.

        Args:
            job_id: UUID of the sync job
            organization_id: UUID of the organization
            result_data: Result summary data
            success: Whether the job succeeded
        """
        try:
            message_type = "job_completed" if success else "job_failed"

            message = format_ws_message(
                message_type=message_type,
                data=result_data,
                organization_id=str(organization_id),
                job_id=str(job_id)
            )

            await manager.broadcast_to_organization(
                str(organization_id), message
            )

            logger.debug(f"Emitted {message_type} event for job {job_id}")

        except Exception as e:
            logger.error(f"Failed to emit job_completed event: {e}")

    @staticmethod
    async def emit_custom_event(
        event_type: str,
        organization_id: UUID,
        data: Dict[str, Any],
        job_id: Optional[UUID] = None
    ) -> None:
        """
        Emit a custom event to organization clients.

        Args:
            event_type: Type of event
            organization_id: UUID of the organization
            data: Event data
            job_id: Optional job UUID
        """
        try:
            message = format_ws_message(
                message_type=event_type,
                data=data,
                organization_id=str(organization_id),
                job_id=str(job_id)
            )

            await manager.broadcast_to_organization(
                str(organization_id), message
            )

            logger.debug(f"Emitted custom event {event_type}")

        except Exception as e:
            logger.error(f"Failed to emit custom event: {e}")

    @staticmethod
    def get_connection_stats() -> Dict[str, Any]:
        """
        Get current WebSocket connection statistics.

        Returns:
            Dictionary with connection stats
        """
        return {
            "total_connections": manager.get_total_connection_count(),
            "organizations_connected": len(manager.get_organizations_with_connections()),
            "organization_breakdown": {
                org_id: manager.get_organization_connection_count(org_id)
                for org_id in manager.get_organizations_with_connections()
            },
        }


# Convenience function for quick access
async def broadcast_job_status(
    job_id: UUID,
    organization_id: UUID,
    status: str,
    **kwargs
) -> None:
    """
    Broadcast job status update.

    Args:
        job_id: UUID of the job
        organization_id: UUID of the organization
        status: Job status (running, completed, failed, etc.)
        **kwargs: Additional data to include
    """
    data = {"status": status, **kwargs}

    if status == "started":
        await RealtimeEventBroadcaster.emit_job_started(
            job_id, organization_id, data.get("platform", "unknown")
        )
    elif status == "completed":
        await RealtimeEventBroadcaster.emit_job_completed(
            job_id, organization_id, data, success=True
        )
    elif status == "failed":
        await RealtimeEventBroadcaster.emit_job_completed(
            job_id, organization_id, data, success=False
        )
    else:
        await RealtimeEventBroadcaster.emit_custom_event(
            f"job_{status}", organization_id, data, job_id
        )
