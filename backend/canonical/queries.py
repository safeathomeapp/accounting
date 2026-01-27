"""
Centralized query helpers for the canonical facts layer.

All reporting and analytics should use these functions to read from
cashflow_facts_v1 instead of querying the raw transactions table directly.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.canonical.models import CashflowFact, CashflowBucket, NormalizedTxnType

logger = logging.getLogger(__name__)


def get_facts_for_period(
    db: Session,
    org_id: UUID,
    start_date: date,
    end_date: date,
    buckets: Optional[List[CashflowBucket]] = None,
    client_id: Optional[UUID] = None,
) -> List[CashflowFact]:
    """Get all facts for an organization within a date range."""
    query = db.query(CashflowFact).filter(
        CashflowFact.organization_id == org_id,
        CashflowFact.effective_date >= start_date,
        CashflowFact.effective_date <= end_date,
    )
    if buckets:
        query = query.filter(CashflowFact.canonical_bucket.in_(buckets))
    if client_id:
        query = query.filter(CashflowFact.client_id == client_id)
    return query.all()


def get_revenue(db: Session, org_id: UUID, start_date: date, end_date: date) -> Decimal:
    """Sum of all CASH_IN and AR facts (sales invoices) for the period."""
    result = (
        db.query(func.coalesce(func.sum(CashflowFact.signed_amount), 0))
        .filter(
            CashflowFact.organization_id == org_id,
            CashflowFact.effective_date >= start_date,
            CashflowFact.effective_date <= end_date,
            CashflowFact.normalized_type == NormalizedTxnType.SALES_INVOICE,
            CashflowFact.canonical_bucket.in_([
                CashflowBucket.CASH_IN,
                CashflowBucket.AR_CURRENT,
                CashflowBucket.AR_OVERDUE,
            ]),
        )
        .scalar()
    )
    return Decimal(str(result))


def get_expenses(db: Session, org_id: UUID, start_date: date, end_date: date) -> Decimal:
    """Sum of all CASH_OUT and AP facts (purchase invoices) for the period.

    Returns a positive number representing total expenses.
    """
    result = (
        db.query(func.coalesce(func.sum(CashflowFact.signed_amount), 0))
        .filter(
            CashflowFact.organization_id == org_id,
            CashflowFact.effective_date >= start_date,
            CashflowFact.effective_date <= end_date,
            CashflowFact.normalized_type == NormalizedTxnType.PURCHASE_INVOICE,
            CashflowFact.canonical_bucket.in_([
                CashflowBucket.CASH_OUT,
                CashflowBucket.AP_CURRENT,
                CashflowBucket.AP_OVERDUE,
            ]),
        )
        .scalar()
    )
    # signed_amount is negative for AP/CASH_OUT, return absolute value
    return abs(Decimal(str(result)))


def get_cash_movements(db: Session, org_id: UUID,
                       start_date: date, end_date: date) -> Dict:
    """Get cash in and cash out totals for the period."""
    cash_in = (
        db.query(func.coalesce(func.sum(CashflowFact.signed_amount), 0))
        .filter(
            CashflowFact.organization_id == org_id,
            CashflowFact.effective_date >= start_date,
            CashflowFact.effective_date <= end_date,
            CashflowFact.canonical_bucket == CashflowBucket.CASH_IN,
        )
        .scalar()
    )

    cash_out = (
        db.query(func.coalesce(func.sum(CashflowFact.signed_amount), 0))
        .filter(
            CashflowFact.organization_id == org_id,
            CashflowFact.effective_date >= start_date,
            CashflowFact.effective_date <= end_date,
            CashflowFact.canonical_bucket == CashflowBucket.CASH_OUT,
        )
        .scalar()
    )

    cash_in_val = Decimal(str(cash_in))
    cash_out_val = abs(Decimal(str(cash_out)))

    return {
        "cash_in": cash_in_val,
        "cash_out": cash_out_val,
        "net_cash_flow": cash_in_val - cash_out_val,
    }


def get_ar_aging(db: Session, org_id: UUID) -> Dict:
    """Get accounts receivable aging (current vs overdue)."""
    current = (
        db.query(func.coalesce(func.sum(CashflowFact.signed_amount), 0))
        .filter(
            CashflowFact.organization_id == org_id,
            CashflowFact.canonical_bucket == CashflowBucket.AR_CURRENT,
        )
        .scalar()
    )

    overdue = (
        db.query(func.coalesce(func.sum(CashflowFact.signed_amount), 0))
        .filter(
            CashflowFact.organization_id == org_id,
            CashflowFact.canonical_bucket == CashflowBucket.AR_OVERDUE,
        )
        .scalar()
    )

    return {
        "ar_current": Decimal(str(current)),
        "ar_overdue": Decimal(str(overdue)),
        "ar_total": Decimal(str(current)) + Decimal(str(overdue)),
    }


def get_ap_aging(db: Session, org_id: UUID) -> Dict:
    """Get accounts payable aging (current vs overdue)."""
    current = (
        db.query(func.coalesce(func.sum(CashflowFact.signed_amount), 0))
        .filter(
            CashflowFact.organization_id == org_id,
            CashflowFact.canonical_bucket == CashflowBucket.AP_CURRENT,
        )
        .scalar()
    )

    overdue = (
        db.query(func.coalesce(func.sum(CashflowFact.signed_amount), 0))
        .filter(
            CashflowFact.organization_id == org_id,
            CashflowFact.canonical_bucket == CashflowBucket.AP_OVERDUE,
        )
        .scalar()
    )

    # AP amounts are stored negative, return absolute values
    return {
        "ap_current": abs(Decimal(str(current))),
        "ap_overdue": abs(Decimal(str(overdue))),
        "ap_total": abs(Decimal(str(current))) + abs(Decimal(str(overdue))),
    }


def get_summary_by_bucket(db: Session, org_id: UUID,
                          start_date: date, end_date: date) -> List[Dict]:
    """Get fact totals grouped by canonical bucket."""
    results = (
        db.query(
            CashflowFact.canonical_bucket,
            func.count(CashflowFact.id).label("count"),
            func.sum(CashflowFact.signed_amount).label("total"),
        )
        .filter(
            CashflowFact.organization_id == org_id,
            CashflowFact.effective_date >= start_date,
            CashflowFact.effective_date <= end_date,
        )
        .group_by(CashflowFact.canonical_bucket)
        .all()
    )

    return [
        {
            "bucket": row.canonical_bucket.value,
            "count": row.count,
            "total": float(row.total or 0),
        }
        for row in results
    ]
