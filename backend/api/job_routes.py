"""API routes for managing background sync jobs."""

import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.sync.scheduler import SyncScheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])

# Global scheduler instance (initialized in main.py)
_scheduler: Optional[SyncScheduler] = None


def set_scheduler(scheduler: SyncScheduler) -> None:
    """Set the global scheduler instance."""
    global _scheduler
    _scheduler = scheduler


def get_scheduler() -> SyncScheduler:
    """Get the global scheduler instance."""
    if _scheduler is None:
        raise HTTPException(
            status_code=503,
            detail="Sync scheduler not initialized"
        )
    return _scheduler


@router.get("/")
def list_sync_jobs(db: Session = Depends(get_db)):
    """
    List all active sync jobs.

    Returns all scheduled sync jobs with their status and next run time.

    Returns:
        List of job info dicts
    """
    try:
        scheduler = get_scheduler()
        jobs = scheduler.list_jobs()

        return {
            "total": len(jobs),
            "jobs": jobs
        }

    except Exception as e:
        logger.error(f"Error listing sync jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list sync jobs")


@router.get("/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get detailed status of a specific job.

    Args:
        job_id: Job ID to query

    Returns:
        Detailed job status info

    Example:
        GET /api/v1/jobs/full_sync_123e4567-e89b-12d3-a456-426614174000
    """
    try:
        scheduler = get_scheduler()
        status = scheduler.get_job_status(job_id)

        return status

    except ValueError as e:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    except Exception as e:
        logger.error(f"Error getting job status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get job status")


@router.post("/")
def create_sync_job(
    org_id: UUID,
    job_type: str = Query(..., description="Job type: 'full' or 'incremental'"),
    cron_expression: str = Query(None, description="Optional custom cron expression"),
    job_id: str = Query(None, description="Optional custom job ID"),
    db: Session = Depends(get_db)
):
    """
    Create a new scheduled sync job.

    Args:
        org_id: Organization UUID
        job_type: Job type ('full' or 'incremental')
        cron_expression: Optional cron expression for custom scheduling
        job_id: Optional custom job ID

    Returns:
        Created job info

    Example:
        POST /api/v1/jobs?org_id=123e4567-e89b-12d3-a456-426614174000&job_type=full
    """
    try:
        scheduler = get_scheduler()

        if job_type not in ["full", "incremental"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid job_type. Must be 'full' or 'incremental'"
            )

        if job_type == "full":
            if cron_expression is None:
                cron_expression = "0 2 * * 0"  # Default: Sunday 2 AM

            created_job_id = scheduler.add_full_sync_job(
                org_id,
                job_id=job_id,
                cron_expression=cron_expression
            )
        else:  # incremental
            if cron_expression is None:
                cron_expression = "0 * * * *"  # Default: Every hour

            created_job_id = scheduler.add_incremental_sync_job(
                org_id,
                job_id=job_id,
                cron_expression=cron_expression
            )

        logger.info(f"Created {job_type} sync job: {created_job_id}")

        return {
            "job_id": created_job_id,
            "job_type": job_type,
            "organization_id": str(org_id),
            "cron_expression": cron_expression,
            "status": "created"
        }

    except ValueError as e:
        logger.error(f"Invalid cron expression: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: {e}")

    except Exception as e:
        logger.error(f"Error creating sync job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create sync job")


@router.post("/{job_id}/pause")
def pause_sync_job(job_id: str, db: Session = Depends(get_db)):
    """
    Pause a scheduled sync job.

    The job will not run until resumed.

    Args:
        job_id: Job ID to pause

    Returns:
        Updated job status

    Example:
        POST /api/v1/jobs/full_sync_123e4567-e89b-12d3-a456-426614174000/pause
    """
    try:
        scheduler = get_scheduler()
        scheduler.pause_job(job_id)

        status = scheduler.get_job_status(job_id)
        logger.info(f"Paused sync job: {job_id}")

        return {
            "job_id": job_id,
            "action": "paused",
            "status": status
        }

    except ValueError as e:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    except Exception as e:
        logger.error(f"Error pausing sync job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to pause sync job")


@router.post("/{job_id}/resume")
def resume_sync_job(job_id: str, db: Session = Depends(get_db)):
    """
    Resume a paused sync job.

    The job will continue running on its schedule.

    Args:
        job_id: Job ID to resume

    Returns:
        Updated job status

    Example:
        POST /api/v1/jobs/full_sync_123e4567-e89b-12d3-a456-426614174000/resume
    """
    try:
        scheduler = get_scheduler()
        scheduler.resume_job(job_id)

        status = scheduler.get_job_status(job_id)
        logger.info(f"Resumed sync job: {job_id}")

        return {
            "job_id": job_id,
            "action": "resumed",
            "status": status
        }

    except ValueError as e:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    except Exception as e:
        logger.error(f"Error resuming sync job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to resume sync job")


@router.delete("/{job_id}")
def delete_sync_job(job_id: str, db: Session = Depends(get_db)):
    """
    Delete and cancel a sync job.

    The job will no longer run.

    Args:
        job_id: Job ID to delete

    Returns:
        Confirmation of deletion

    Example:
        DELETE /api/v1/jobs/full_sync_123e4567-e89b-12d3-a456-426614174000
    """
    try:
        scheduler = get_scheduler()
        scheduler.remove_job(job_id)

        logger.info(f"Deleted sync job: {job_id}")

        return {
            "job_id": job_id,
            "action": "deleted",
            "status": "success"
        }

    except ValueError as e:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    except Exception as e:
        logger.error(f"Error deleting sync job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete sync job")
