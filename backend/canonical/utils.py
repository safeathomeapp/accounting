"""Helper functions for canonical mapping coverage and gap analysis."""

import logging
from typing import Dict, List
from uuid import UUID

from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from backend.models import Transaction
from backend.canonical.models import (
    CashflowFact,
    IngestionQuarantine,
    PlatformTransactionMapping,
)

logger = logging.getLogger(__name__)


def get_coverage_stats(db: Session, org_id: UUID) -> Dict:
    """Get mapping coverage statistics for an organization.

    Returns:
        Dict with total, mapped, quarantined, unmapped counts and percentages.
    """
    total = db.query(func.count(Transaction.id)).filter(
        Transaction.organization_id == org_id
    ).scalar() or 0

    mapped = db.query(func.count(CashflowFact.id)).filter(
        CashflowFact.organization_id == org_id
    ).scalar() or 0

    quarantined = db.query(func.count(IngestionQuarantine.id)).filter(
        IngestionQuarantine.organization_id == org_id,
        IngestionQuarantine.resolved_at == None,
    ).scalar() or 0

    unmapped = total - mapped - quarantined
    coverage_pct = round((mapped / total * 100), 2) if total > 0 else 0.0

    return {
        "organization_id": str(org_id),
        "total_transactions": total,
        "mapped_count": mapped,
        "quarantined_count": quarantined,
        "unmapped_count": unmapped,
        "coverage_pct": coverage_pct,
    }


def get_coverage_by_platform(db: Session, org_id: UUID) -> List[Dict]:
    """Get coverage stats broken down by platform."""
    platforms = (
        db.query(distinct(Transaction.platform_name))
        .filter(Transaction.organization_id == org_id)
        .all()
    )

    results = []
    for (platform_name,) in platforms:
        total = db.query(func.count(Transaction.id)).filter(
            Transaction.organization_id == org_id,
            Transaction.platform_name == platform_name,
        ).scalar() or 0

        mapped = (
            db.query(func.count(CashflowFact.id))
            .join(Transaction, CashflowFact.transaction_id == Transaction.id)
            .filter(
                CashflowFact.organization_id == org_id,
                Transaction.platform_name == platform_name,
            )
            .scalar() or 0
        )

        quarantined = db.query(func.count(IngestionQuarantine.id)).filter(
            IngestionQuarantine.organization_id == org_id,
            IngestionQuarantine.platform_name == platform_name,
            IngestionQuarantine.resolved_at == None,
        ).scalar() or 0

        coverage_pct = round((mapped / total * 100), 2) if total > 0 else 0.0

        results.append({
            "platform_name": platform_name,
            "total_transactions": total,
            "mapped_count": mapped,
            "quarantined_count": quarantined,
            "unmapped_count": total - mapped - quarantined,
            "coverage_pct": coverage_pct,
        })

    return results


def get_unmapped_types(db: Session, org_id: UUID) -> List[Dict]:
    """Find all (platform, type, status) combos that have no active mapping.

    Returns:
        List of dicts with platform_name, source_type, source_status, count.
    """
    # Get all distinct combos in transactions for this org
    combos = (
        db.query(
            Transaction.platform_name,
            Transaction.transaction_type,
            Transaction.status,
            func.count(Transaction.id).label("count"),
        )
        .filter(Transaction.organization_id == org_id)
        .group_by(
            Transaction.platform_name,
            Transaction.transaction_type,
            Transaction.status,
        )
        .all()
    )

    # Get all active mappings
    mappings = (
        db.query(PlatformTransactionMapping)
        .filter(PlatformTransactionMapping.is_active == True)
        .all()
    )

    mapped_keys = {
        (m.platform_name.lower(), m.source_type.lower(), m.source_status.lower())
        for m in mappings
    }

    unmapped = []
    for platform, txn_type, status, count in combos:
        key = (
            (platform or "").lower(),
            (txn_type or "").lower(),
            (status or "").lower(),
        )
        if key not in mapped_keys:
            unmapped.append({
                "platform_name": platform or "",
                "source_type": txn_type or "",
                "source_status": status or "",
                "transaction_count": count,
            })

    return sorted(unmapped, key=lambda x: x["transaction_count"], reverse=True)
