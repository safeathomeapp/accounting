"""API routes for manual sync triggers."""

import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Organization, AccountingPlatform
from backend.sync import SyncEngine
from backend.sync.exceptions import SyncException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/all")
def sync_all_platforms(
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Sync all active platforms for an organization.

    Args:
        org_id: Organization UUID
        db: Database session

    Returns:
        SyncResult with status and statistics

    Example:
        POST /sync/all?org_id=123e4567-e89b-12d3-a456-426614174000
    """
    logger.info(f"Sync request: all platforms for org {org_id}")

    try:
        engine = SyncEngine(db)
        result = engine.sync_all_platforms(org_id)

        return {
            "status": result.status,
            "sync_history_id": str(result.sync_history_id),
            "duration_seconds": result.duration_seconds,
            "accounts": {
                "total_fetched": result.accounts.total_fetched,
                "created": result.accounts.created,
                "updated": result.accounts.updated,
                "failed": result.accounts.failed,
                "success_rate": result.accounts.success_rate
            },
            "clients": {
                "total_fetched": result.clients.total_fetched,
                "created": result.clients.created,
                "updated": result.clients.updated,
                "failed": result.clients.failed,
                "success_rate": result.clients.success_rate
            },
            "transactions": {
                "total_fetched": result.transactions.total_fetched,
                "created": result.transactions.created,
                "updated": result.transactions.updated,
                "failed": result.transactions.failed,
                "success_rate": result.transactions.success_rate
            },
            "total_synced": result.total_synced,
            "total_failed": result.total_failed,
            "errors": [str(e) for e in result.errors]
        }

    except SyncException as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error during sync: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Sync failed with unexpected error")


@router.post("/platform/{platform_name}")
def sync_platform(
    org_id: UUID,
    platform_name: str,
    db: Session = Depends(get_db)
):
    """
    Sync a specific platform for an organization.

    Args:
        org_id: Organization UUID
        platform_name: Platform name ('xero', 'quickbooks')
        db: Database session

    Returns:
        SyncResult with status and statistics

    Example:
        POST /sync/platform/xero?org_id=123e4567-e89b-12d3-a456-426614174000
    """
    logger.info(f"Sync request: {platform_name} for org {org_id}")

    try:
        engine = SyncEngine(db)
        result = engine.sync_platform(org_id, platform_name)

        return {
            "status": result.status,
            "platform": platform_name,
            "sync_history_id": str(result.sync_history_id),
            "duration_seconds": result.duration_seconds,
            "accounts": {
                "total_fetched": result.accounts.total_fetched,
                "created": result.accounts.created,
                "updated": result.accounts.updated,
                "failed": result.accounts.failed,
                "success_rate": result.accounts.success_rate
            },
            "clients": {
                "total_fetched": result.clients.total_fetched,
                "created": result.clients.created,
                "updated": result.clients.updated,
                "failed": result.clients.failed,
                "success_rate": result.clients.success_rate
            },
            "transactions": {
                "total_fetched": result.transactions.total_fetched,
                "created": result.transactions.created,
                "updated": result.transactions.updated,
                "failed": result.transactions.failed,
                "success_rate": result.transactions.success_rate
            },
            "total_synced": result.total_synced,
            "total_failed": result.total_failed,
            "errors": [str(e) for e in result.errors]
        }

    except SyncException as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error during sync: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Sync failed with unexpected error")


@router.get("/status")
def get_sync_status(
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get sync status for an organization.

    Returns the most recent sync result for each platform.

    Args:
        org_id: Organization UUID
        db: Database session

    Returns:
        Sync status for each platform
    """
    from backend.models import SyncHistory

    logger.info(f"Status request for org {org_id}")

    try:
        # Get platforms for organization
        platforms = db.query(AccountingPlatform).filter_by(
            organization_id=org_id
        ).all()

        if not platforms:
            raise HTTPException(status_code=404, detail="No platforms configured")

        status = {
            "organization_id": str(org_id),
            "platforms": {}
        }

        for platform in platforms:
            # Get last sync for this platform
            last_sync = db.query(SyncHistory).filter_by(
                platform_id=platform.id,
                sync_status="completed"
            ).order_by(SyncHistory.completed_at.desc()).first()

            platform_status = {
                "platform_name": platform.platform_name,
                "is_active": platform.is_active
            }

            if last_sync:
                platform_status.update({
                    "last_sync_id": str(last_sync.id),
                    "last_sync_at": last_sync.completed_at.isoformat() if last_sync.completed_at else None,
                    "sync_type": last_sync.sync_type,
                    "records_synced": last_sync.records_synced,
                    "records_created": last_sync.records_created,
                    "records_updated": last_sync.records_updated,
                    "records_failed": last_sync.records_failed,
                    "duration_seconds": last_sync.duration_seconds
                })
            else:
                platform_status["last_sync_at"] = None
                platform_status["message"] = "Never synced"

            status["platforms"][platform.platform_name] = platform_status

        return status

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting sync status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get sync status")


@router.get("/history")
def get_sync_history(
    org_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get sync history for an organization.

    Returns recent sync operations ordered by date descending.

    Args:
        org_id: Organization UUID
        limit: Number of records to return (1-100, default 10)
        db: Database session

    Returns:
        List of sync history records
    """
    from backend.models import SyncHistory

    logger.info(f"History request for org {org_id}, limit={limit}")

    try:
        # Get sync history for organization
        syncs = db.query(SyncHistory).filter_by(
            organization_id=org_id
        ).order_by(SyncHistory.started_at.desc()).limit(limit).all()

        if not syncs:
            return {
                "organization_id": str(org_id),
                "total": 0,
                "syncs": []
            }

        return {
            "organization_id": str(org_id),
            "total": len(syncs),
            "syncs": [
                {
                    "sync_id": str(sync.id),
                    "platform": sync.platform.platform_name if sync.platform else "unknown",
                    "sync_type": sync.sync_type,
                    "status": sync.sync_status,
                    "started_at": sync.started_at.isoformat(),
                    "completed_at": sync.completed_at.isoformat() if sync.completed_at else None,
                    "duration_seconds": sync.duration_seconds,
                    "records": {
                        "synced": sync.records_synced,
                        "created": sync.records_created,
                        "updated": sync.records_updated,
                        "failed": sync.records_failed
                    },
                    "error_message": sync.error_message
                }
                for sync in syncs
            ]
        }

    except Exception as e:
        logger.error(f"Error getting sync history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get sync history")
