# Month 2, Week 3: Background Sync Jobs Roadmap

## Overview
Implement automated sync jobs using APScheduler to keep accounting data fresh without manual intervention. This provides continuous data synchronization and sets up foundation for the Week 4 reporting layer.

**Current Status**: Week 2 Complete (222/222 tests passing)
**Target**: 250+ passing tests, automated sync infrastructure

## Architecture

```
FastAPI Application
  ├── SyncScheduler (APScheduler manager)
  │   ├── Schedule full syncs (daily)
  │   ├── Schedule incremental syncs (hourly)
  │   └── Retry failed syncs (with backoff)
  │
  ├── Sync Jobs (async tasks)
  │   ├── sync_all_platforms_job()
  │   ├── sync_platform_job(platform_name)
  │   └── retry_failed_syncs_job()
  │
  └── Job Management Endpoints
      ├── GET /api/v1/sync/jobs (list active jobs)
      ├── POST /api/v1/sync/jobs/{job_id}/pause (pause job)
      ├── POST /api/v1/sync/jobs/{job_id}/resume (resume job)
      └── DELETE /api/v1/sync/jobs/{job_id} (cancel job)
```

## Implementation Steps

### Step 1: APScheduler Setup (40 lines)
**File**: `backend/sync/scheduler.py`

Create SyncScheduler class that manages all sync jobs:

```python
class SyncScheduler:
    def __init__(self, db_session):
        self.scheduler = BackgroundScheduler()
        self.db = db_session

    def start(self):
        """Start the scheduler"""

    def stop(self):
        """Stop the scheduler gracefully"""

    def add_full_sync_job(self, org_id, cron_expression='0 2 * * *'):
        """Schedule daily full sync at 2 AM"""

    def add_incremental_sync_job(self, org_id, cron_expression='0 * * * *'):
        """Schedule hourly incremental sync"""

    def add_retry_job(self, cron_expression='0 3,6,9,12 * * *'):
        """Retry failed syncs 4x per day"""

    def pause_job(self, job_id):
        """Pause a specific job"""

    def resume_job(self, job_id):
        """Resume a paused job"""

    def list_jobs(self):
        """Get all active jobs with status"""
```

**Key Features**:
- Uses `APScheduler.BackgroundScheduler` for async execution
- Configurable cron expressions for flexible scheduling
- Graceful start/stop with proper cleanup
- Error handling and logging

### Step 2: Sync Job Tasks (60 lines)
**File**: `backend/sync/tasks.py`

Create async job functions that are scheduled:

```python
async def sync_all_platforms_job(organization_id: UUID) -> None:
    """Scheduled job to sync all platforms for an organization"""
    # Similar to sync_routes but with job context

async def sync_platform_job(organization_id: UUID, platform_name: str) -> None:
    """Scheduled job to sync specific platform"""

async def retry_failed_syncs_job() -> None:
    """Retry syncs that failed in the last 24 hours"""
    # Query SyncHistory with status='failed'
    # Retry up to 3 times with exponential backoff
```

**Key Features**:
- Async task execution for non-blocking operations
- Job context tracking (start_time, end_time, status)
- Error logging and retry counters
- Status updates to SyncHistory

### Step 3: Retry Logic with Exponential Backoff (50 lines)
**File**: `backend/sync/retry.py`

Create RetryManager for handling sync failures:

```python
class RetryManager:
    def __init__(self, max_retries: int = 3, base_delay: int = 60):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def calculate_backoff(self, attempt: int) -> int:
        """Exponential backoff: base_delay * (2 ^ attempt)"""
        return self.base_delay * (2 ** attempt)

    def should_retry(self, sync_history: SyncHistory) -> bool:
        """Check if sync should be retried"""

    def schedule_retry(self, sync_history: SyncHistory, delay_seconds: int):
        """Schedule retry with delay"""
```

**Key Features**:
- Exponential backoff to avoid thundering herd
- Max 3 retries per failed sync
- Delay tracking in database
- Automatic cleanup of old retried syncs

### Step 4: Job Management Endpoints (80 lines)
**File**: `backend/api/job_routes.py`

Add endpoints for managing background sync jobs:

```python
@router.get("/jobs")
def list_sync_jobs(org_id: UUID, db: Session):
    """List all sync jobs for organization"""
    # Returns: [{"job_id", "type", "status", "next_run", "last_run"}, ...]

@router.post("/jobs/{job_id}/pause")
def pause_sync_job(org_id: UUID, job_id: str, db: Session):
    """Pause a specific sync job"""

@router.post("/jobs/{job_id}/resume")
def resume_sync_job(org_id: UUID, job_id: str, db: Session):
    """Resume a paused job"""

@router.delete("/jobs/{job_id}")
def cancel_sync_job(org_id: UUID, job_id: str, db: Session):
    """Cancel and delete a job"""

@router.get("/jobs/{job_id}/status")
def get_job_status(org_id: UUID, job_id: str, db: Session):
    """Get detailed status of specific job"""
```

### Step 5: Integration with Main App (30 lines)
**File**: `backend/main.py` (modified)

Initialize scheduler on app startup:

```python
scheduler = None

@app.on_event("startup")
async def startup_scheduler():
    global scheduler
    scheduler = SyncScheduler(SessionLocal())

    # Add default jobs for each organization
    orgs = db.query(Organization).filter_by(is_active=True).all()
    for org in orgs:
        scheduler.add_incremental_sync_job(org.id, '0 * * * *')  # hourly
        scheduler.add_full_sync_job(org.id, '0 2 * * 0')  # weekly Sunday 2 AM

    scheduler.start()
    logger.info("Sync scheduler started")

@app.on_event("shutdown")
async def shutdown_scheduler():
    global scheduler
    if scheduler and scheduler.scheduler.running:
        scheduler.stop()
        logger.info("Sync scheduler stopped")
```

### Step 6: Database Schema Updates (SyncHistory)
**File**: `backend/models.py` (modified)

Add fields to SyncHistory for job tracking:

```python
class SyncHistory(Base):
    # Existing fields...

    # New fields for job tracking
    job_id = Column(String(255), nullable=True)  # APScheduler job ID
    retry_count = Column(Integer, default=0)  # Number of retry attempts
    next_retry_at = Column(DateTime, nullable=True)  # When next retry scheduled
    is_scheduled = Column(Boolean, default=True)  # Part of scheduled job
    scheduled_by_job = Column(String(255), nullable=True)  # Which job triggered this
```

### Step 7: Comprehensive Testing (80+ lines)
**File**: `tests/test_sync_week3.py`

Test categories:

1. **SyncScheduler Tests** (15 tests)
   - Initialization and configuration
   - Adding/pausing/resuming jobs
   - Cron expression validation
   - Job listing and status

2. **Job Execution Tests** (20 tests)
   - sync_all_platforms_job execution
   - sync_platform_job execution
   - Job context tracking
   - Error handling during job execution

3. **Retry Logic Tests** (15 tests)
   - Exponential backoff calculation
   - Retry eligibility checking
   - Retry scheduling and execution
   - Max retry limit enforcement

4. **Integration Tests** (15 tests)
   - Scheduler integration with FastAPI
   - Job management endpoints
   - Concurrent job execution
   - Database consistency after retries

5. **Performance Tests** (10 tests)
   - Multiple concurrent syncs
   - Large dataset handling
   - Scheduler memory footprint
   - Job cleanup and resource management

**Target**: 80+ new tests, 300+ total passing

## Key Design Decisions

### 1. Scheduling Strategy
- **Incremental syncs hourly**: Frequent updates for active data
- **Full syncs weekly**: Comprehensive refresh to catch missed changes
- **Retry syncs every 3 hours**: Failed syncs get multiple attempts

### 2. Async Execution
- Jobs run asynchronously to avoid blocking API requests
- Uses Python asyncio for non-blocking I/O
- Proper exception handling with logging

### 3. Database Tracking
- Every scheduled sync is logged in SyncHistory
- Tracks job_id for correlation with APScheduler
- Retry attempts and next_retry_at for recovery workflow

### 4. Graceful Degradation
- If scheduler fails, manual API endpoints still work
- Existing syncs continue even if scheduler has issues
- No data loss, just missed scheduled runs

## Dependencies

```python
# Add to requirements.txt
APScheduler==3.10.4
python-dateutil==2.8.2
```

## Testing Strategy

1. **Unit Tests**: Test each component in isolation
   - SyncScheduler scheduling logic
   - RetryManager backoff calculations
   - Job task execution

2. **Integration Tests**: Test with real database and scheduler
   - Job execution flow
   - Database state after job completion
   - Concurrent job execution

3. **End-to-End Tests**: Full workflow
   - Schedule job → Job runs → Sync completes → History recorded
   - Failed sync → Retry scheduled → Retry runs → Success

## Success Criteria

- All 80+ new tests pass
- Scheduler starts/stops cleanly without resource leaks
- Failed syncs retry with exponential backoff
- Job management endpoints functional
- No blocking operations during job execution
- Clean logging and error tracking
- **Total**: 300+ passing tests

## Next Steps (Week 4)

Once Week 3 is complete, move to **Reporting & Analytics Layer**:
- Financial reports (P&L, Balance Sheet)
- Reconciliation tools
- Transaction categorization
- Analytics dashboards

The background sync jobs will ensure reporting layer has fresh data continuously.
