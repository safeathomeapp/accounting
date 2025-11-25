"""
Sync job tasks for scheduled execution.

These are the actual tasks that get executed by the APScheduler
background scheduler for automated data synchronization.

Includes monitoring integration to emit real-time events for job status,
metrics, and errors.
"""

import logging
from uuid import UUID, uuid4
import asyncio

from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.sync.engine import SyncEngine
from backend.sync.retry import RetryManager
from backend.sync.monitoring import SyncMonitor

logger = logging.getLogger(__name__)


async def sync_all_platforms_job(
    organization_id: UUID,
    db: Session = None
) -> dict:
    """
    Scheduled job to sync all platforms for an organization.

    This job is typically scheduled to run periodically (e.g., hourly
    for incremental syncs, weekly for full syncs).

    Includes monitoring integration to emit real-time events.

    Args:
        organization_id: Organization UUID to sync
        db: Database session (creates new if not provided)

    Returns:
        Dict with sync result summary
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    job_id = uuid4()  # Generate unique job ID for this sync operation
    monitor = SyncMonitor(db)

    try:
        logger.info(f"[JOB] Syncing all platforms for organization {organization_id}")

        # Emit job started event (async, no await to avoid blocking)
        asyncio.create_task(
            monitor.on_sync_started(job_id, organization_id, "all_platforms")
        )

        engine = SyncEngine(db)
        result = engine.sync_all_platforms(organization_id)

        summary = {
            "status": result.status,
            "total_synced": result.total_synced,
            "total_failed": result.total_failed,
            "accounts": {
                "created": result.accounts.created,
                "updated": result.accounts.updated,
                "failed": result.accounts.failed
            },
            "clients": {
                "created": result.clients.created,
                "updated": result.clients.updated,
                "failed": result.clients.failed
            },
            "transactions": {
                "created": result.transactions.created,
                "updated": result.transactions.updated,
                "failed": result.transactions.failed
            }
        }

        # Emit job completed event
        success = result.status in ["success", "partial"]
        asyncio.create_task(
            monitor.on_sync_completed(job_id, organization_id, result, success)
        )

        logger.info(f"[JOB] Sync completed for {organization_id}: {result.status}")
        logger.info(f"[JOB] Results - Synced: {result.total_synced}, Failed: {result.total_failed}")

        return summary

    except Exception as e:
        logger.error(
            f"[JOB] Error syncing all platforms for {organization_id}: {e}",
            exc_info=True
        )

        # Emit error event
        asyncio.create_task(
            monitor.on_sync_error(
                job_id,
                organization_id,
                str(e),
                error_type="sync_job_exception",
                severity="critical"
            )
        )

        return {
            "status": "failed",
            "error": str(e),
            "organization_id": str(organization_id)
        }

    finally:
        if close_db:
            db.close()


async def sync_platform_job(
    organization_id: UUID,
    platform_name: str,
    db: Session = None
) -> dict:
    """
    Scheduled job to sync a specific platform for an organization.

    Args:
        organization_id: Organization UUID to sync
        platform_name: Platform name ('xero', 'quickbooks')
        db: Database session (creates new if not provided)

    Returns:
        Dict with sync result summary
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    try:
        logger.info(
            f"[JOB] Syncing platform {platform_name} for organization {organization_id}"
        )

        engine = SyncEngine(db)
        result = engine.sync_platform(organization_id, platform_name)

        summary = {
            "status": result.status,
            "platform": platform_name,
            "total_synced": result.total_synced,
            "total_failed": result.total_failed,
            "accounts": {
                "created": result.accounts.created,
                "updated": result.accounts.updated,
                "failed": result.accounts.failed
            },
            "clients": {
                "created": result.clients.created,
                "updated": result.clients.updated,
                "failed": result.clients.failed
            },
            "transactions": {
                "created": result.transactions.created,
                "updated": result.transactions.updated,
                "failed": result.transactions.failed
            }
        }

        logger.info(f"[JOB] Sync completed for {platform_name}: {result.status}")

        return summary

    except Exception as e:
        logger.error(
            f"[JOB] Error syncing {platform_name} for {organization_id}: {e}",
            exc_info=True
        )
        return {
            "status": "failed",
            "error": str(e),
            "platform": platform_name,
            "organization_id": str(organization_id)
        }

    finally:
        if close_db:
            db.close()


async def retry_failed_syncs_job(db: Session = None) -> dict:
    """
    Scheduled job to retry syncs that failed in the last 24 hours.

    Queries SyncHistory for failed syncs and retries them using the
    RetryManager for exponential backoff.

    Args:
        db: Database session (creates new if not provided)

    Returns:
        Dict with retry operation summary
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    try:
        from backend.models import SyncHistory
        from datetime import datetime, timedelta

        logger.info("[JOB] Starting retry job for failed syncs")

        # Get failed syncs from last 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        failed_syncs = db.query(SyncHistory).filter(
            SyncHistory.sync_status == "failed",
            SyncHistory.started_at >= cutoff_time
        ).all()

        if not failed_syncs:
            logger.info("[JOB] No failed syncs to retry")
            return {
                "status": "success",
                "retried_count": 0,
                "message": "No failed syncs in last 24 hours"
            }

        logger.info(f"[JOB] Found {len(failed_syncs)} failed syncs to retry")

        retry_manager = RetryManager(max_retries=3, base_delay=60)
        retried_count = 0
        skipped_count = 0

        engine = SyncEngine(db)

        for sync_history in failed_syncs:
            retry_count = sync_history.retry_count or 0

            if not retry_manager.should_retry(retry_count):
                logger.warning(
                    f"[JOB] Skipping sync {sync_history.id}: "
                    f"max retries ({retry_manager.max_retries}) exceeded"
                )
                skipped_count += 1
                continue

            try:
                logger.info(
                    f"[JOB] Retrying sync {sync_history.id} "
                    f"(attempt {retry_count + 1}/{retry_manager.max_retries})"
                )

                # Retry the sync for the platform
                result = engine.sync_platform(
                    sync_history.organization_id,
                    sync_history.platform.platform_name
                )

                # Update retry count
                sync_history.retry_count = retry_count + 1

                if result.status == "success":
                    logger.info(f"[JOB] Retry succeeded for sync {sync_history.id}")
                else:
                    logger.warning(
                        f"[JOB] Retry failed for sync {sync_history.id}, "
                        f"will retry again"
                    )
                    # Schedule next retry
                    retry_info = retry_manager.get_retry_info(retry_count + 1)
                    if retry_info:
                        sync_history.next_retry_at = retry_info["next_retry_at"]

                db.commit()
                retried_count += 1

            except Exception as e:
                logger.error(
                    f"[JOB] Error retrying sync {sync_history.id}: {e}",
                    exc_info=True
                )
                skipped_count += 1

        logger.info(
            f"[JOB] Retry job completed: "
            f"retried={retried_count}, skipped={skipped_count}"
        )

        return {
            "status": "success",
            "retried_count": retried_count,
            "skipped_count": skipped_count,
            "total_processed": len(failed_syncs)
        }

    except Exception as e:
        logger.error(f"[JOB] Retry job failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e)
        }

    finally:
        if close_db:
            db.close()
