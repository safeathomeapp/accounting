"""Data quality monitoring and mapping management API endpoints."""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.canonical.models import (
    PlatformTransactionMapping,
    CashflowFact,
    IngestionQuarantine,
    NormalizedTxnType,
    NormalizedTxnStatus,
    CashflowBucket,
    DateSource,
)
from backend.canonical.engine import MappingEngine
from backend.canonical.utils import (
    get_coverage_stats,
    get_coverage_by_platform,
    get_unmapped_types,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data-quality", tags=["data-quality"])


# ============================================================================
# COVERAGE ENDPOINTS
# ============================================================================

@router.get("/orgs/{org_id}/coverage")
async def get_org_coverage(
    org_id: UUID,
    db: Session = Depends(get_db),
) -> Dict:
    """Get mapping coverage statistics for an organization."""
    try:
        overall = get_coverage_stats(db, org_id)
        by_platform = get_coverage_by_platform(db, org_id)

        return {
            "organization_id": str(org_id),
            "overall": overall,
            "by_platform": by_platform,
        }
    except Exception as e:
        logger.error(f"Error getting coverage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve coverage stats")


# ============================================================================
# QUARANTINE ENDPOINTS
# ============================================================================

@router.get("/orgs/{org_id}/quarantine")
async def get_quarantine_entries(
    org_id: UUID,
    resolved: bool = Query(False, description="Include resolved entries"),
    db: Session = Depends(get_db),
) -> Dict:
    """Get quarantined transactions for an organization."""
    try:
        query = db.query(IngestionQuarantine).filter(
            IngestionQuarantine.organization_id == org_id
        )
        if not resolved:
            query = query.filter(IngestionQuarantine.resolved_at == None)

        entries = query.order_by(IngestionQuarantine.quarantined_at.desc()).all()

        return {
            "count": len(entries),
            "entries": [
                {
                    "id": str(e.id),
                    "transaction_id": str(e.transaction_id),
                    "platform_name": e.platform_name,
                    "source_type": e.source_type,
                    "source_status": e.source_status,
                    "reason": e.reason,
                    "quarantined_at": e.quarantined_at.isoformat() if e.quarantined_at else None,
                    "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
                    "resolved_by": e.resolved_by,
                }
                for e in entries
            ],
        }
    except Exception as e:
        logger.error(f"Error getting quarantine entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quarantine entries")


@router.post("/orgs/{org_id}/quarantine/{quarantine_id}/resolve")
async def resolve_quarantine_entry(
    org_id: UUID,
    quarantine_id: UUID,
    db: Session = Depends(get_db),
) -> Dict:
    """Resolve a single quarantine entry by re-attempting mapping."""
    try:
        engine = MappingEngine(db)
        engine.load_mappings()
        fact = engine.resolve_quarantine(quarantine_id, resolved_by="api_user")

        if fact:
            return {
                "resolved": True,
                "fact_id": str(fact.id),
                "bucket": fact.canonical_bucket.value,
            }
        else:
            return {
                "resolved": False,
                "reason": "No matching mapping found or entry already resolved",
            }
    except Exception as e:
        logger.error(f"Error resolving quarantine entry: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve quarantine entry")


@router.post("/orgs/{org_id}/quarantine/resolve-all")
async def resolve_all_quarantine(
    org_id: UUID,
    db: Session = Depends(get_db),
) -> Dict:
    """Attempt to resolve all unresolved quarantine entries for an organization."""
    try:
        engine = MappingEngine(db)
        engine.load_mappings()
        stats = engine.resolve_all_quarantine(org_id=org_id, resolved_by="api_user")
        return stats
    except Exception as e:
        logger.error(f"Error resolving all quarantine: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve quarantine entries")


# ============================================================================
# UNMAPPED TYPES
# ============================================================================

@router.get("/orgs/{org_id}/unmapped-types")
async def get_unmapped_type_list(
    org_id: UUID,
    db: Session = Depends(get_db),
) -> Dict:
    """Get all (platform, type, status) combos that have no active mapping."""
    try:
        unmapped = get_unmapped_types(db, org_id)
        return {
            "count": len(unmapped),
            "unmapped_types": unmapped,
        }
    except Exception as e:
        logger.error(f"Error getting unmapped types: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve unmapped types")


# ============================================================================
# MAPPING MANAGEMENT
# ============================================================================

@router.get("/mappings")
async def list_mappings(
    platform_name: Optional[str] = Query(None, description="Filter by platform"),
    active_only: bool = Query(True, description="Only show active mappings"),
    db: Session = Depends(get_db),
) -> Dict:
    """List all platform transaction mappings."""
    try:
        query = db.query(PlatformTransactionMapping)
        if platform_name:
            query = query.filter(PlatformTransactionMapping.platform_name == platform_name)
        if active_only:
            query = query.filter(PlatformTransactionMapping.is_active == True)

        mappings = query.order_by(
            PlatformTransactionMapping.platform_name,
            PlatformTransactionMapping.source_type,
            PlatformTransactionMapping.source_status,
        ).all()

        return {
            "count": len(mappings),
            "mappings": [
                {
                    "id": m.id,
                    "platform_name": m.platform_name,
                    "source_type": m.source_type,
                    "source_status": m.source_status,
                    "normalized_type": m.normalized_type.value,
                    "normalized_status": m.normalized_status.value,
                    "canonical_bucket": m.canonical_bucket.value,
                    "effective_date_source": m.effective_date_source.value,
                    "priority": m.priority,
                    "is_active": m.is_active,
                }
                for m in mappings
            ],
        }
    except Exception as e:
        logger.error(f"Error listing mappings: {e}")
        raise HTTPException(status_code=500, detail="Failed to list mappings")


@router.post("/mappings")
async def create_mapping(
    platform_name: str,
    source_type: str,
    source_status: str,
    normalized_type: str,
    normalized_status: str,
    canonical_bucket: str,
    effective_date_source: str = "TRANSACTION_DATE",
    priority: int = 0,
    db: Session = Depends(get_db),
) -> Dict:
    """Create a new platform transaction mapping."""
    try:
        mapping = PlatformTransactionMapping(
            platform_name=platform_name,
            source_type=source_type,
            source_status=source_status,
            normalized_type=NormalizedTxnType(normalized_type),
            normalized_status=NormalizedTxnStatus(normalized_status),
            canonical_bucket=CashflowBucket(canonical_bucket),
            effective_date_source=DateSource(effective_date_source),
            priority=priority,
            is_active=True,
        )
        db.add(mapping)
        db.commit()
        db.refresh(mapping)

        logger.info(f"Created mapping {mapping.id}: {platform_name}/{source_type}/{source_status}")
        return {
            "id": mapping.id,
            "platform_name": mapping.platform_name,
            "source_type": mapping.source_type,
            "source_status": mapping.source_status,
            "canonical_bucket": mapping.canonical_bucket.value,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating mapping: {e}")
        raise HTTPException(status_code=500, detail="Failed to create mapping")


@router.put("/mappings/{mapping_id}")
async def update_mapping(
    mapping_id: int,
    normalized_type: Optional[str] = None,
    normalized_status: Optional[str] = None,
    canonical_bucket: Optional[str] = None,
    effective_date_source: Optional[str] = None,
    priority: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
) -> Dict:
    """Update an existing mapping."""
    try:
        mapping = db.query(PlatformTransactionMapping).filter_by(id=mapping_id).first()
        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")

        if normalized_type is not None:
            mapping.normalized_type = NormalizedTxnType(normalized_type)
        if normalized_status is not None:
            mapping.normalized_status = NormalizedTxnStatus(normalized_status)
        if canonical_bucket is not None:
            mapping.canonical_bucket = CashflowBucket(canonical_bucket)
        if effective_date_source is not None:
            mapping.effective_date_source = DateSource(effective_date_source)
        if priority is not None:
            mapping.priority = priority
        if is_active is not None:
            mapping.is_active = is_active

        db.commit()
        logger.info(f"Updated mapping {mapping_id}")
        return {"success": True, "id": mapping_id}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating mapping: {e}")
        raise HTTPException(status_code=500, detail="Failed to update mapping")


@router.delete("/mappings/{mapping_id}")
async def delete_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
) -> Dict:
    """Soft-delete a mapping (set is_active = False)."""
    try:
        mapping = db.query(PlatformTransactionMapping).filter_by(id=mapping_id).first()
        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")

        mapping.is_active = False
        db.commit()
        logger.info(f"Soft-deleted mapping {mapping_id}")
        return {"success": True, "id": mapping_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting mapping: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete mapping")


# ============================================================================
# REBUILD FACTS
# ============================================================================

@router.post("/orgs/{org_id}/rebuild-facts")
async def rebuild_facts(
    org_id: UUID,
    db: Session = Depends(get_db),
) -> Dict:
    """Rebuild all canonical facts for an organization."""
    try:
        engine = MappingEngine(db)
        engine.load_mappings()
        stats = engine.rebuild_facts(org_id=org_id)
        logger.info(f"Rebuilt facts for org {org_id}: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error rebuilding facts: {e}")
        raise HTTPException(status_code=500, detail="Failed to rebuild facts")
