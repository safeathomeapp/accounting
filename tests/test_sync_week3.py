"""Tests for Week 3: Background Sync Jobs with APScheduler."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.sync.scheduler import SyncScheduler
from backend.sync.retry import RetryManager


class TestRetryManager:
    """Tests for retry manager with exponential backoff."""

    def test_retry_manager_initialization(self):
        """Test RetryManager initialization with defaults."""
        manager = RetryManager()
        assert manager.max_retries == 3
        assert manager.base_delay == 60

    def test_retry_manager_custom_initialization(self):
        """Test RetryManager initialization with custom values."""
        manager = RetryManager(max_retries=5, base_delay=30)
        assert manager.max_retries == 5
        assert manager.base_delay == 30

    def test_calculate_backoff_attempt_zero(self):
        """Test backoff calculation for first attempt."""
        manager = RetryManager(base_delay=60)
        delay = manager.calculate_backoff(0)
        assert delay == 60  # base_delay * 2^0

    def test_calculate_backoff_attempt_one(self):
        """Test backoff calculation for second attempt."""
        manager = RetryManager(base_delay=60)
        delay = manager.calculate_backoff(1)
        assert delay == 120  # base_delay * 2^1

    def test_calculate_backoff_attempt_two(self):
        """Test backoff calculation for third attempt."""
        manager = RetryManager(base_delay=60)
        delay = manager.calculate_backoff(2)
        assert delay == 240  # base_delay * 2^2

    def test_calculate_backoff_attempt_three(self):
        """Test backoff calculation for fourth attempt."""
        manager = RetryManager(base_delay=60)
        delay = manager.calculate_backoff(3)
        assert delay == 480  # base_delay * 2^3

    def test_calculate_backoff_negative_attempt(self):
        """Test backoff with negative attempt returns base delay."""
        manager = RetryManager(base_delay=60)
        delay = manager.calculate_backoff(-1)
        assert delay == 60

    def test_calculate_next_retry_time(self):
        """Test calculation of next retry time."""
        manager = RetryManager(base_delay=60)
        now = datetime.utcnow()

        next_retry = manager.calculate_next_retry_time(0)

        # Should be approximately 60 seconds from now
        assert next_retry > now
        assert (next_retry - now).total_seconds() >= 59
        assert (next_retry - now).total_seconds() <= 61

    def test_should_retry_within_limit(self):
        """Test should_retry when within retry limit."""
        manager = RetryManager(max_retries=3)
        assert manager.should_retry(0) is True
        assert manager.should_retry(1) is True
        assert manager.should_retry(2) is True

    def test_should_retry_at_limit(self):
        """Test should_retry when at retry limit."""
        manager = RetryManager(max_retries=3)
        assert manager.should_retry(3) is False

    def test_should_retry_exceeds_limit(self):
        """Test should_retry when exceeds retry limit."""
        manager = RetryManager(max_retries=3)
        assert manager.should_retry(4) is False
        assert manager.should_retry(10) is False

    def test_get_retry_info_within_limit(self):
        """Test get_retry_info returns info when within limit."""
        manager = RetryManager(max_retries=3, base_delay=60)
        retry_info = manager.get_retry_info(0)

        assert retry_info is not None
        assert retry_info["should_retry"] is True
        assert retry_info["attempt_number"] == 1
        assert retry_info["max_attempts"] == 3
        assert retry_info["delay_seconds"] == 60
        assert "next_retry_at" in retry_info

    def test_get_retry_info_exceeds_limit(self):
        """Test get_retry_info returns None when exceeds limit."""
        manager = RetryManager(max_retries=3)
        retry_info = manager.get_retry_info(3)

        assert retry_info is None

    def test_format_retry_message_within_limit(self):
        """Test format_retry_message for within limit."""
        manager = RetryManager(max_retries=3, base_delay=60)
        message = manager.format_retry_message(0)

        assert "Retry 1/3" in message
        assert "1.0 minutes" in message or "60.0 seconds" in message

    def test_format_retry_message_exceeds_limit(self):
        """Test format_retry_message when exceeds limit."""
        manager = RetryManager(max_retries=3)
        message = manager.format_retry_message(3)

        assert "Max retries" in message
        assert "exceeded" in message


class TestSyncScheduler:
    """Tests for sync scheduler with APScheduler."""

    def test_sync_scheduler_initialization(self):
        """Test SyncScheduler initialization."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)

        assert scheduler.db is db
        assert scheduler.scheduler is not None
        assert scheduler.engine is not None
        assert scheduler.retry_manager is not None

    def test_sync_scheduler_start(self):
        """Test starting the scheduler."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)

        scheduler.start()
        assert scheduler.scheduler.running is True

        scheduler.stop()

    def test_sync_scheduler_stop(self):
        """Test stopping the scheduler."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)

        scheduler.start()
        assert scheduler.scheduler.running is True

        scheduler.stop()
        assert scheduler.scheduler.running is False

    def test_sync_scheduler_start_already_running(self):
        """Test starting scheduler when already running."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)

        scheduler.start()
        # Starting again should not raise error
        scheduler.start()
        assert scheduler.scheduler.running is True

        scheduler.stop()

    def test_add_full_sync_job(self):
        """Test adding a full sync job."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        org_id = uuid4()
        job_id = scheduler.add_full_sync_job(org_id)

        assert job_id == f"full_sync_{org_id}"
        assert job_id in scheduler.jobs_config
        assert scheduler.jobs_config[job_id]["type"] == "full_sync"
        assert scheduler.jobs_config[job_id]["organization_id"] == str(org_id)

        scheduler.stop()

    def test_add_incremental_sync_job(self):
        """Test adding an incremental sync job."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        org_id = uuid4()
        job_id = scheduler.add_incremental_sync_job(org_id)

        assert job_id == f"incremental_sync_{org_id}"
        assert job_id in scheduler.jobs_config
        assert scheduler.jobs_config[job_id]["type"] == "incremental_sync"

        scheduler.stop()

    def test_add_retry_job(self):
        """Test adding a retry job."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        job_id = scheduler.add_retry_job()

        assert job_id == "retry_failed_syncs"
        assert job_id in scheduler.jobs_config
        assert scheduler.jobs_config[job_id]["type"] == "retry_failed_syncs"

        scheduler.stop()

    def test_add_job_with_custom_id(self):
        """Test adding a job with custom ID."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        org_id = uuid4()
        custom_id = "my_custom_sync"
        job_id = scheduler.add_full_sync_job(org_id, job_id=custom_id)

        assert job_id == custom_id
        assert job_id in scheduler.jobs_config

        scheduler.stop()

    def test_add_job_invalid_cron_expression(self):
        """Test adding job with invalid cron expression."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        org_id = uuid4()
        with pytest.raises(ValueError):
            scheduler.add_full_sync_job(org_id, cron_expression="invalid")

        scheduler.stop()

    def test_pause_job(self):
        """Test pausing a job."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        org_id = uuid4()
        job_id = scheduler.add_full_sync_job(org_id)

        # Pause the job
        scheduler.pause_job(job_id)
        job = scheduler.scheduler.get_job(job_id)
        assert job is not None

        scheduler.stop()

    def test_resume_job(self):
        """Test resuming a job."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        org_id = uuid4()
        job_id = scheduler.add_full_sync_job(org_id)

        scheduler.pause_job(job_id)
        scheduler.resume_job(job_id)

        job = scheduler.scheduler.get_job(job_id)
        assert job is not None

        scheduler.stop()

    def test_remove_job(self):
        """Test removing a job."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        org_id = uuid4()
        job_id = scheduler.add_full_sync_job(org_id)

        assert job_id in scheduler.jobs_config
        scheduler.remove_job(job_id)
        assert job_id not in scheduler.jobs_config

        scheduler.stop()

    def test_list_jobs(self):
        """Test listing all jobs."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        org_id_1 = uuid4()
        org_id_2 = uuid4()
        scheduler.add_full_sync_job(org_id_1)
        scheduler.add_incremental_sync_job(org_id_2)
        scheduler.add_retry_job()

        jobs = scheduler.list_jobs()

        assert len(jobs) == 3
        assert all("job_id" in job for job in jobs)
        assert all("name" in job for job in jobs)
        assert all("next_run" in job for job in jobs)

        scheduler.stop()

    def test_get_job_status(self):
        """Test getting job status."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        org_id = uuid4()
        job_id = scheduler.add_full_sync_job(org_id)

        status = scheduler.get_job_status(job_id)

        assert status["job_id"] == job_id
        assert status["name"] is not None
        assert "next_run" in status
        assert status["config"]["type"] == "full_sync"

        scheduler.stop()

    def test_get_job_status_not_found(self):
        """Test getting status of non-existent job."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        with pytest.raises(ValueError):
            scheduler.get_job_status("non_existent_job")

        scheduler.stop()

    def test_remove_nonexistent_job(self):
        """Test removing a job that doesn't exist."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        with pytest.raises(Exception):
            scheduler.remove_job("non_existent_job")

        scheduler.stop()


class TestSyncSchedulerJobExecution:
    """Tests for job execution functionality."""

    @patch('backend.sync.scheduler.SyncEngine')
    def test_execute_full_sync(self, mock_engine_class):
        """Test full sync job execution."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        # Mock the sync result
        mock_result = Mock()
        mock_result.status = "success"
        mock_result.total_synced = 150
        mock_result.total_failed = 0

        mock_engine = Mock()
        mock_engine.sync_all_platforms.return_value = mock_result
        scheduler.engine = mock_engine

        org_id = uuid4()
        scheduler._execute_full_sync(org_id)

        mock_engine.sync_all_platforms.assert_called_once_with(org_id)
        scheduler.stop()

    @patch('backend.sync.scheduler.SyncEngine')
    def test_execute_incremental_sync(self, mock_engine_class):
        """Test incremental sync job execution."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        # Mock the sync result
        mock_result = Mock()
        mock_result.status = "success"

        mock_engine = Mock()
        mock_engine.sync_all_platforms.return_value = mock_result
        scheduler.engine = mock_engine

        org_id = uuid4()
        scheduler._execute_incremental_sync(org_id)

        mock_engine.sync_all_platforms.assert_called_once_with(org_id)
        scheduler.stop()

    @patch('backend.sync.scheduler.SyncEngine')
    def test_execute_full_sync_with_error(self, mock_engine_class):
        """Test full sync job execution with error."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        mock_engine = Mock()
        mock_engine.sync_all_platforms.side_effect = Exception("API Error")
        scheduler.engine = mock_engine

        org_id = uuid4()
        # Should not raise, just log
        scheduler._execute_full_sync(org_id)

        scheduler.stop()


class TestSyncSchedulerIntegration:
    """Integration tests for sync scheduler."""

    def test_scheduler_lifecycle(self):
        """Test full scheduler lifecycle."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)

        # Initially not running
        assert scheduler.scheduler.running is False

        # Start scheduler
        scheduler.start()
        assert scheduler.scheduler.running is True

        # Add jobs
        org_id = uuid4()
        job_id_1 = scheduler.add_full_sync_job(org_id)
        job_id_2 = scheduler.add_incremental_sync_job(org_id)

        # Verify jobs exist
        jobs = scheduler.list_jobs()
        assert len(jobs) == 2

        # Pause a job
        scheduler.pause_job(job_id_1)

        # Resume job
        scheduler.resume_job(job_id_1)

        # Remove a job
        scheduler.remove_job(job_id_2)
        jobs = scheduler.list_jobs()
        assert len(jobs) == 1

        # Stop scheduler
        scheduler.stop()
        assert scheduler.scheduler.running is False

    def test_multiple_organizations(self):
        """Test scheduler managing jobs for multiple organizations."""
        db = Mock(spec=Session)
        scheduler = SyncScheduler(db)
        scheduler.start()

        org_ids = [uuid4() for _ in range(3)]

        # Add jobs for each organization
        job_ids = []
        for org_id in org_ids:
            job_id = scheduler.add_full_sync_job(org_id)
            job_ids.append(job_id)

        # Verify all jobs exist
        jobs = scheduler.list_jobs()
        assert len(jobs) == 3

        # Verify job config
        for job_id in job_ids:
            config = scheduler.jobs_config[job_id]
            assert config["type"] == "full_sync"

        scheduler.stop()


class TestRetryScheduling:
    """Tests for retry job scheduling and execution."""

    def test_retry_manager_exponential_progression(self):
        """Test that retry delays increase exponentially."""
        manager = RetryManager(base_delay=100)

        delays = [manager.calculate_backoff(i) for i in range(4)]

        # Verify exponential growth
        assert delays == [100, 200, 400, 800]

    def test_retry_manager_max_attempts(self):
        """Test retry manager respects max attempts."""
        manager = RetryManager(max_retries=2)

        assert manager.should_retry(0) is True
        assert manager.should_retry(1) is True
        assert manager.should_retry(2) is False

    def test_retry_info_complete(self):
        """Test retry info contains all required fields."""
        manager = RetryManager(max_retries=3, base_delay=60)

        for attempt in range(3):
            info = manager.get_retry_info(attempt)
            assert "should_retry" in info
            assert "next_retry_at" in info
            assert "delay_seconds" in info
            assert "attempt_number" in info
            assert "max_attempts" in info

    def test_retry_message_formatting(self):
        """Test retry message formatting for readability."""
        manager = RetryManager(max_retries=3, base_delay=60)

        msg = manager.format_retry_message(0)
        assert "Retry 1/3" in msg

        msg = manager.format_retry_message(1)
        assert "Retry 2/3" in msg

        msg = manager.format_retry_message(3)
        assert "Max retries" in msg
