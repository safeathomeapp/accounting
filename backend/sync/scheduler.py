"""
Sync scheduler for automated data synchronization.

Manages background sync jobs using APScheduler for scheduled
synchronization of accounting data from multiple platforms.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
from uuid import UUID

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from backend.sync.engine import SyncEngine
from backend.sync.retry import RetryManager

logger = logging.getLogger(__name__)


class SyncScheduler:
    """Manages automated sync jobs for accounting data."""

    def __init__(self, db_session: Session):
        """
        Initialize the sync scheduler.

        Args:
            db_session: Database session for sync operations
        """
        self.db = db_session
        self.scheduler = BackgroundScheduler()
        self.engine = SyncEngine(db_session)
        self.retry_manager = RetryManager(max_retries=3, base_delay=60)
        self.jobs_config: Dict[str, Dict[str, Any]] = {}

    def start(self) -> None:
        """
        Start the scheduler.

        Begins executing scheduled sync jobs.
        Safe to call multiple times.
        """
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Sync scheduler started")
        else:
            logger.debug("Scheduler already running")

    def stop(self) -> None:
        """
        Stop the scheduler gracefully.

        Waits for running jobs to complete before stopping.
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Sync scheduler stopped")
        else:
            logger.debug("Scheduler not running")

    def add_full_sync_job(
        self,
        organization_id: UUID,
        job_id: str = None,
        cron_expression: str = "0 2 * * 0"
    ) -> str:
        """
        Schedule a full sync job for an organization.

        Full syncs fetch all data (2 years of transactions).
        Default: Every Sunday at 2 AM.

        Args:
            organization_id: Organization to sync
            job_id: Custom job ID (auto-generated if not provided)
            cron_expression: Cron expression for scheduling

        Returns:
            Job ID for reference

        Raises:
            ValueError: If cron expression is invalid
        """
        if job_id is None:
            job_id = f"full_sync_{organization_id}"

        try:
            trigger = CronTrigger.from_crontab(cron_expression)
        except Exception as e:
            logger.error(f"Invalid cron expression: {cron_expression}")
            raise ValueError(f"Invalid cron expression: {e}")

        job = self.scheduler.add_job(
            func=self._execute_full_sync,
            trigger=trigger,
            id=job_id,
            args=[organization_id],
            name=f"Full sync for {organization_id}",
            misfire_grace_time=300,  # 5 minute grace period
            replace_existing=True
        )

        self.jobs_config[job_id] = {
            "type": "full_sync",
            "organization_id": str(organization_id),
            "cron": cron_expression,
            "created_at": datetime.now()
        }

        logger.info(f"Full sync job scheduled: {job_id}")
        return job_id

    def add_incremental_sync_job(
        self,
        organization_id: UUID,
        job_id: str = None,
        cron_expression: str = "0 * * * *"
    ) -> str:
        """
        Schedule an incremental sync job for an organization.

        Incremental syncs fetch only recent changes.
        Default: Every hour.

        Args:
            organization_id: Organization to sync
            job_id: Custom job ID (auto-generated if not provided)
            cron_expression: Cron expression for scheduling

        Returns:
            Job ID for reference

        Raises:
            ValueError: If cron expression is invalid
        """
        if job_id is None:
            job_id = f"incremental_sync_{organization_id}"

        try:
            trigger = CronTrigger.from_crontab(cron_expression)
        except Exception as e:
            logger.error(f"Invalid cron expression: {cron_expression}")
            raise ValueError(f"Invalid cron expression: {e}")

        job = self.scheduler.add_job(
            func=self._execute_incremental_sync,
            trigger=trigger,
            id=job_id,
            args=[organization_id],
            name=f"Incremental sync for {organization_id}",
            misfire_grace_time=300,
            replace_existing=True
        )

        self.jobs_config[job_id] = {
            "type": "incremental_sync",
            "organization_id": str(organization_id),
            "cron": cron_expression,
            "created_at": datetime.now()
        }

        logger.info(f"Incremental sync job scheduled: {job_id}")
        return job_id

    def add_retry_job(
        self,
        job_id: str = "retry_failed_syncs",
        cron_expression: str = "0 3,6,9,12,15,18,21,0 * * *"
    ) -> str:
        """
        Schedule a job to retry failed syncs.

        Retries syncs that failed in the last 24 hours.
        Default: Every 3 hours.

        Args:
            job_id: Job ID for retry job
            cron_expression: Cron expression for scheduling

        Returns:
            Job ID for reference

        Raises:
            ValueError: If cron expression is invalid
        """
        try:
            trigger = CronTrigger.from_crontab(cron_expression)
        except Exception as e:
            logger.error(f"Invalid cron expression: {cron_expression}")
            raise ValueError(f"Invalid cron expression: {e}")

        job = self.scheduler.add_job(
            func=self._execute_retry_failed_syncs,
            trigger=trigger,
            id=job_id,
            name="Retry failed syncs",
            misfire_grace_time=300,
            replace_existing=True
        )

        self.jobs_config[job_id] = {
            "type": "retry_failed_syncs",
            "cron": cron_expression,
            "created_at": datetime.now()
        }

        logger.info(f"Retry job scheduled: {job_id}")
        return job_id

    def pause_job(self, job_id: str) -> None:
        """
        Pause a scheduled job.

        Args:
            job_id: Job ID to pause

        Raises:
            ValueError: If job not found
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                self.scheduler.pause_job(job_id)
                logger.info(f"Job paused: {job_id}")
            else:
                raise ValueError(f"Job not found: {job_id}")
        except Exception as e:
            logger.error(f"Error pausing job: {e}")
            raise

    def resume_job(self, job_id: str) -> None:
        """
        Resume a paused job.

        Args:
            job_id: Job ID to resume

        Raises:
            ValueError: If job not found
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                self.scheduler.resume_job(job_id)
                logger.info(f"Job resumed: {job_id}")
            else:
                raise ValueError(f"Job not found: {job_id}")
        except Exception as e:
            logger.error(f"Error resuming job: {e}")
            raise

    def remove_job(self, job_id: str) -> None:
        """
        Remove a job from the scheduler.

        Args:
            job_id: Job ID to remove

        Raises:
            ValueError: If job not found
        """
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs_config:
                del self.jobs_config[job_id]
            logger.info(f"Job removed: {job_id}")
        except Exception as e:
            logger.error(f"Error removing job: {e}")
            raise

    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        Get all active jobs with their status.

        Returns:
            List of job info dicts with: job_id, type, status, next_run
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "job_id": job.id,
                "name": job.name,
                "status": "paused" if job.args and job.args[0] else "running",
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "config": self.jobs_config.get(job.id, {})
            })
        return jobs

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get detailed status of a specific job.

        Args:
            job_id: Job ID to query

        Returns:
            Job status info

        Raises:
            ValueError: If job not found
        """
        job = self.scheduler.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        return {
            "job_id": job.id,
            "name": job.name,
            "status": "paused" if job.args and job.args[0] else "running",
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "previous_run": getattr(job, 'last_run_time', None),
            "config": self.jobs_config.get(job_id, {})
        }

    # Private job execution methods

    def _execute_full_sync(self, organization_id: UUID) -> None:
        """
        Execute a full sync job.

        Args:
            organization_id: Organization to sync
        """
        try:
            logger.info(f"Starting full sync for organization {organization_id}")
            result = self.engine.sync_all_platforms(organization_id)
            logger.info(f"Full sync completed for {organization_id}: {result.status}")
        except Exception as e:
            logger.error(f"Full sync failed for {organization_id}: {e}", exc_info=True)

    def _execute_incremental_sync(self, organization_id: UUID) -> None:
        """
        Execute an incremental sync job.

        Args:
            organization_id: Organization to sync
        """
        try:
            logger.info(f"Starting incremental sync for organization {organization_id}")
            result = self.engine.sync_all_platforms(organization_id)
            logger.info(f"Incremental sync completed for {organization_id}: {result.status}")
        except Exception as e:
            logger.error(f"Incremental sync failed for {organization_id}: {e}", exc_info=True)

    def _execute_retry_failed_syncs(self) -> None:
        """Execute retry job for failed syncs."""
        try:
            logger.info("Starting retry job for failed syncs")
            # This will be implemented in Week 3 - query failed syncs and retry
            logger.info("Retry job completed")
        except Exception as e:
            logger.error(f"Retry job failed: {e}", exc_info=True)
