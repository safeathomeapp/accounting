"""Analytics and reporting REST API endpoints."""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Account, Transaction, SyncHistory
from backend.reporting.reconciliation import ReconciliationEngine, ReconciliationStatus
from backend.reporting.categorization import CategorizationEngine
from backend.reporting.generators import ReportGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Global instances for reporting engines
_reconciliation_engine: Optional[ReconciliationEngine] = None
_categorization_engine: Optional[CategorizationEngine] = None
_report_generator: Optional[ReportGenerator] = None


def set_reconciliation_engine(engine: ReconciliationEngine) -> None:
    """Set the global reconciliation engine."""
    global _reconciliation_engine
    _reconciliation_engine = engine


def get_reconciliation_engine() -> ReconciliationEngine:
    """Get the global reconciliation engine."""
    if _reconciliation_engine is None:
        raise HTTPException(status_code=500, detail="Reconciliation engine not initialized")
    return _reconciliation_engine


def set_categorization_engine(engine: CategorizationEngine) -> None:
    """Set the global categorization engine."""
    global _categorization_engine
    _categorization_engine = engine


def get_categorization_engine() -> CategorizationEngine:
    """Get the global categorization engine."""
    if _categorization_engine is None:
        raise HTTPException(status_code=500, detail="Categorization engine not initialized")
    return _categorization_engine


def set_report_generator(generator: ReportGenerator) -> None:
    """Set the global report generator."""
    global _report_generator
    _report_generator = generator


def get_report_generator() -> ReportGenerator:
    """Get the global report generator."""
    if _report_generator is None:
        raise HTTPException(status_code=500, detail="Report generator not initialized")
    return _report_generator


# ======================
# FINANCIAL REPORTS
# ======================

@router.get("/reports/profit-loss")
async def get_profit_loss_report(
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    account_ids: Optional[str] = Query(None, description="Comma-separated account IDs"),
    db: Session = Depends(get_db),
) -> Dict:
    """
    Get Profit & Loss report for date range.

    Args:
        start_date: Report period start
        end_date: Report period end
        account_ids: Optional comma-separated list of account UUIDs to include

    Returns:
        P&L report with revenue, expenses, and net income
    """
    try:
        generator = get_report_generator()

        # Parse account IDs if provided
        account_id_list = []
        if account_ids:
            account_id_list = [UUID(aid.strip()) for aid in account_ids.split(",")]

        report = generator.generate_profit_loss(
            start_date=start_date,
            end_date=end_date,
            account_ids=account_id_list if account_id_list else None,
        )

        logger.info(f"Generated P&L report: {start_date} to {end_date}")
        return report.to_dict()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating P&L report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate report")


@router.get("/reports/balance-sheet")
async def get_balance_sheet_report(
    as_of_date: date = Query(..., description="Date for balance sheet"),
    account_ids: Optional[str] = Query(None, description="Comma-separated account IDs"),
    db: Session = Depends(get_db),
) -> Dict:
    """
    Get Balance Sheet as of specific date.

    Args:
        as_of_date: Date for which to generate balance sheet
        account_ids: Optional comma-separated list of account UUIDs

    Returns:
        Balance sheet with assets, liabilities, and equity
    """
    try:
        generator = get_report_generator()

        account_id_list = []
        if account_ids:
            account_id_list = [UUID(aid.strip()) for aid in account_ids.split(",")]

        report = generator.generate_balance_sheet(
            as_of_date=as_of_date,
            account_ids=account_id_list if account_id_list else None,
        )

        logger.info(f"Generated balance sheet as of {as_of_date}")
        return report.to_dict()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating balance sheet: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate report")


@router.get("/reports/cash-flow")
async def get_cash_flow_report(
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    account_ids: Optional[str] = Query(None, description="Comma-separated account IDs"),
    db: Session = Depends(get_db),
) -> Dict:
    """
    Get Cash Flow Statement for date range.

    Args:
        start_date: Report period start
        end_date: Report period end
        account_ids: Optional comma-separated list of account UUIDs

    Returns:
        Cash flow statement with operating, investing, and financing flows
    """
    try:
        generator = get_report_generator()

        account_id_list = []
        if account_ids:
            account_id_list = [UUID(aid.strip()) for aid in account_ids.split(",")]

        report = generator.generate_cash_flow(
            start_date=start_date,
            end_date=end_date,
            account_ids=account_id_list if account_id_list else None,
        )

        logger.info(f"Generated cash flow report: {start_date} to {end_date}")
        return report.to_dict()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating cash flow report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate report")


@router.get("/reports/trial-balance")
async def get_trial_balance_report(
    as_of_date: date = Query(..., description="Date for trial balance"),
    account_ids: Optional[str] = Query(None, description="Comma-separated account IDs"),
    db: Session = Depends(get_db),
) -> Dict:
    """
    Get Trial Balance as of specific date.

    Args:
        as_of_date: Date for which to generate trial balance
        account_ids: Optional comma-separated list of account UUIDs

    Returns:
        Trial balance with all accounts and balances
    """
    try:
        generator = get_report_generator()

        account_id_list = []
        if account_ids:
            account_id_list = [UUID(aid.strip()) for aid in account_ids.split(",")]

        report = generator.generate_trial_balance(
            as_of_date=as_of_date,
            account_ids=account_id_list if account_id_list else None,
        )

        logger.info(f"Generated trial balance as of {as_of_date}")
        return report

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating trial balance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate report")


# ======================
# RECONCILIATION ANALYTICS
# ======================

@router.get("/reconciliation/accounts/{account_id}")
async def get_account_reconciliation_status(
    account_id: UUID,
    db: Session = Depends(get_db),
) -> Dict:
    """Get reconciliation status for an account."""
    try:
        engine = get_reconciliation_engine()
        report = engine.get_reconciliation_report()

        logger.info(f"Retrieved reconciliation status for account {account_id}")
        return report

    except Exception as e:
        logger.error(f"Error getting reconciliation status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reconciliation status")


@router.get("/reconciliation/uncleared-transactions")
async def get_uncleared_transactions(
    db: Session = Depends(get_db),
) -> Dict:
    """Get all uncleared transactions across all accounts."""
    try:
        engine = get_reconciliation_engine()
        uncleared = engine.get_uncleared_transactions()

        logger.info(f"Retrieved {len(uncleared)} uncleared transactions")
        return {
            "count": len(uncleared),
            "transactions": uncleared,
        }

    except Exception as e:
        logger.error(f"Error getting uncleared transactions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve uncleared transactions")


@router.get("/reconciliation/discrepancies")
async def get_discrepancy_report(
    discrepancy_type: Optional[str] = Query(None, description="Filter by discrepancy type"),
    min_confidence: float = Query(0.0, description="Minimum confidence threshold"),
    db: Session = Depends(get_db),
) -> Dict:
    """
    Get discrepancy report from last reconciliation.

    Args:
        discrepancy_type: Filter by type (duplicate, round_trip, unusual_amount, timing, unmatched)
        min_confidence: Minimum confidence score (0.0-1.0)

    Returns:
        List of discrepancies from last reconciliation
    """
    try:
        engine = get_reconciliation_engine()
        report = engine.get_reconciliation_report()

        discrepancies = []
        if "discrepancies" in report:
            discrepancies = report["discrepancies"]

        # Filter by type if specified
        if discrepancy_type:
            discrepancies = [d for d in discrepancies if d.get("type") == discrepancy_type]

        # Filter by confidence
        discrepancies = [d for d in discrepancies if d.get("confidence", 0) >= min_confidence]

        logger.info(f"Retrieved {len(discrepancies)} discrepancies (type={discrepancy_type})")
        return {
            "count": len(discrepancies),
            "discrepancies": discrepancies,
        }

    except Exception as e:
        logger.error(f"Error getting discrepancy report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discrepancy report")


# ======================
# CATEGORIZATION ANALYTICS
# ======================

@router.get("/categorization/suggestions")
async def get_category_suggestions(
    description: str = Query(..., description="Transaction description"),
    amount: float = Query(..., description="Transaction amount"),
    top_k: int = Query(3, description="Number of suggestions to return"),
) -> Dict:
    """
    Get category suggestions for a transaction.

    Args:
        description: Transaction description
        amount: Transaction amount
        top_k: Number of top suggestions to return

    Returns:
        List of category suggestions with confidence scores
    """
    try:
        engine = get_categorization_engine()
        suggestions = engine.suggest_categories(description, Decimal(str(amount)), top_k)

        logger.info(f"Generated {len(suggestions)} suggestions for '{description[:50]}'")
        return {
            "description": description,
            "amount": float(amount),
            "suggestions": [s.to_dict() for s in suggestions],
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting category suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate suggestions")


@router.get("/categorization/auto-categorize")
async def auto_categorize_transaction(
    description: str = Query(..., description="Transaction description"),
    amount: float = Query(..., description="Transaction amount"),
    confidence_threshold: float = Query(0.7, description="Minimum confidence threshold"),
) -> Dict:
    """
    Auto-categorize transaction if confidence exceeds threshold.

    Args:
        description: Transaction description
        amount: Transaction amount
        confidence_threshold: Minimum confidence (0.0-1.0)

    Returns:
        Suggested category if confident, or None
    """
    try:
        engine = get_categorization_engine()
        suggestion = engine.auto_categorize(
            description,
            Decimal(str(amount)),
            confidence_threshold,
        )

        if suggestion:
            logger.info(f"Auto-categorized '{description[:50]}' -> {suggestion.category_name}")
            return {
                "auto_categorized": True,
                "suggestion": suggestion.to_dict(),
            }
        else:
            logger.debug(f"Insufficient confidence for '{description[:50]}'")
            return {
                "auto_categorized": False,
                "suggestion": None,
            }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error auto-categorizing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to auto-categorize")


@router.get("/categorization/statistics")
async def get_categorization_statistics() -> Dict:
    """Get statistics about categories and rules."""
    try:
        engine = get_categorization_engine()
        stats = engine.get_category_stats()

        logger.info("Retrieved categorization statistics")
        return stats

    except Exception as e:
        logger.error(f"Error getting categorization stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


# ======================
# TRANSACTION ANALYTICS
# ======================

@router.get("/transactions/summary")
async def get_transaction_summary(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    account_id: Optional[str] = Query(None, description="Account UUID"),
    db: Session = Depends(get_db),
) -> Dict:
    """
    Get transaction summary for date range.

    Args:
        start_date: Period start date
        end_date: Period end date
        account_id: Optional account UUID to filter

    Returns:
        Transaction counts, amounts, and averages
    """
    try:
        query = db.query(Transaction).filter(
            Transaction.transaction_date.between(start_date, end_date)
        )

        if account_id:
            query = query.filter(Transaction.account_id == UUID(account_id))

        transactions = query.all()

        if not transactions:
            return {
                "period": f"{start_date} to {end_date}",
                "transaction_count": 0,
                "total_amount": 0.0,
                "average_amount": 0.0,
            }

        total = sum(t.amount for t in transactions)

        logger.info(f"Retrieved {len(transactions)} transactions for summary")
        return {
            "period": f"{start_date} to {end_date}",
            "transaction_count": len(transactions),
            "total_amount": float(total),
            "average_amount": float(total / len(transactions)),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting transaction summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve summary")


@router.get("/transactions/by-category")
async def get_transactions_by_category(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db),
) -> Dict:
    """
    Get transaction amounts grouped by category.

    Args:
        start_date: Period start date
        end_date: Period end date

    Returns:
        Transactions grouped and summed by category
    """
    try:
        transactions = db.query(Transaction).filter(
            Transaction.transaction_date.between(start_date, end_date)
        ).all()

        # Group by category
        by_category = {}
        for txn in transactions:
            category = txn.category or "Uncategorized"
            if category not in by_category:
                by_category[category] = {"count": 0, "total": 0.0}
            by_category[category]["count"] += 1
            by_category[category]["total"] += float(txn.amount)

        logger.info(f"Retrieved {len(transactions)} transactions by category")
        return {
            "period": f"{start_date} to {end_date}",
            "by_category": by_category,
        }

    except Exception as e:
        logger.error(f"Error getting transactions by category: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve transactions")


@router.get("/transactions/trending")
async def get_transaction_trends(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
) -> Dict:
    """
    Get transaction trends over specified number of days.

    Args:
        days: Number of days to look back

    Returns:
        Daily transaction counts and totals
    """
    try:
        start_date = date.today() - timedelta(days=days)
        transactions = db.query(Transaction).filter(
            Transaction.transaction_date >= start_date
        ).all()

        # Group by date
        by_date = {}
        for txn in transactions:
            txn_date = txn.transaction_date.isoformat()
            if txn_date not in by_date:
                by_date[txn_date] = {"count": 0, "total": 0.0}
            by_date[txn_date]["count"] += 1
            by_date[txn_date]["total"] += float(txn.amount)

        logger.info(f"Retrieved transaction trends for {days} days ({len(transactions)} transactions)")
        return {
            "days": days,
            "transaction_count": len(transactions),
            "by_date": by_date,
        }

    except Exception as e:
        logger.error(f"Error getting transaction trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trends")


# ======================
# SYNC ANALYTICS
# ======================

@router.get("/sync/statistics")
async def get_sync_statistics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
) -> Dict:
    """
    Get sync job statistics.

    Args:
        days: Number of days to analyze

    Returns:
        Sync statistics including success rate and timing
    """
    try:
        start_date = datetime.now() - timedelta(days=days)

        jobs = db.query(SyncHistory).filter(
            SyncHistory.created_at >= start_date
        ).all()

        if not jobs:
            return {
                "days": days,
                "total_syncs": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
            }

        successful = len([j for j in jobs if j.status == "completed"])
        failed = len([j for j in jobs if j.status == "failed"])

        logger.info(f"Retrieved sync statistics for {days} days ({len(jobs)} total)")
        return {
            "days": days,
            "total_syncs": len(jobs),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(jobs) if jobs else 0.0,
        }

    except Exception as e:
        logger.error(f"Error getting sync statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


# ============================================================================
# Analytics Persistence Endpoints - Forecasts, Metrics, Trends, KPIs, Widgets
# ============================================================================

from backend.models.analytics import Forecast, FinancialMetric, TrendAnalysis, KPI, DashboardWidget
from backend.models.analytics import ForecastType, ForecastMethod, MetricType, TrendDirection
from backend.analytics.repositories import (
    ForecastRepository, MetricRepository, TrendRepository,
    KPIRepository, DashboardWidgetRepository
)


# ---- Forecast Endpoints ----

@router.post("/orgs/{org_id}/forecasts")
def create_forecast(
    org_id: UUID,
    forecast_type: ForecastType,
    method: ForecastMethod,
    period_start: date,
    period_end: date,
    base_value: Decimal,
    forecasted_value: Decimal,
    accuracy_score: float = 0.0,
    db: Session = Depends(get_db)
):
    """Create a new forecast."""
    try:
        repo = ForecastRepository(db)
        forecast = Forecast(
            organization_id=org_id,
            forecast_type=forecast_type,
            method=method,
            period_start=period_start,
            period_end=period_end,
            forecast_date=datetime.now().date(),
            base_value=base_value,
            forecasted_value=forecasted_value,
            accuracy_score=accuracy_score
        )
        created = repo.create(forecast)
        logger.info(f"Created forecast {created.id} for org {org_id}")
        return {
            "id": str(created.id),
            "organization_id": str(created.organization_id),
            "type": created.forecast_type.value,
            "method": created.method.value,
            "value": str(created.forecasted_value),
            "accuracy": created.accuracy_score
        }
    except Exception as e:
        logger.error(f"Error creating forecast: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orgs/{org_id}/forecasts")
def list_forecasts(
    org_id: UUID,
    forecast_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List forecasts for organization."""
    try:
        repo = ForecastRepository(db)
        type_filter = ForecastType(forecast_type) if forecast_type else None
        forecasts = repo.get_by_org(org_id, forecast_type=type_filter)
        return {
            "count": len(forecasts),
            "forecasts": [{
                "id": str(f.id),
                "type": f.forecast_type.value,
                "value": str(f.forecasted_value),
                "accuracy": f.accuracy_score
            } for f in forecasts]
        }
    except Exception as e:
        logger.error(f"Error listing forecasts: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/forecasts/{forecast_id}")
def get_forecast(forecast_id: UUID, db: Session = Depends(get_db)):
    """Get specific forecast."""
    try:
        repo = ForecastRepository(db)
        forecast = repo.get_by_id(forecast_id)
        if not forecast:
            raise HTTPException(status_code=404, detail="Forecast not found")
        return {
            "id": str(forecast.id),
            "type": forecast.forecast_type.value,
            "value": str(forecast.forecasted_value),
            "accuracy": forecast.accuracy_score
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving forecast: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ---- Metric Endpoints ----

@router.post("/orgs/{org_id}/metrics")
def create_metric(
    org_id: UUID,
    metric_type: MetricType,
    period_date: date,
    metric_value: Decimal,
    benchmark_value: Optional[Decimal] = None,
    db: Session = Depends(get_db)
):
    """Create a new financial metric."""
    try:
        repo = MetricRepository(db)
        vs_benchmark = (metric_value - benchmark_value) if benchmark_value else None
        metric = FinancialMetric(
            organization_id=org_id,
            metric_type=metric_type,
            period_date=period_date,
            metric_value=metric_value,
            benchmark_value=benchmark_value,
            vs_benchmark=vs_benchmark
        )
        created = repo.create(metric)
        logger.info(f"Created metric {created.id} for org {org_id}")
        return {
            "id": str(created.id),
            "type": created.metric_type.value,
            "value": str(created.metric_value),
            "benchmark": str(created.benchmark_value) if created.benchmark_value else None
        }
    except Exception as e:
        logger.error(f"Error creating metric: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orgs/{org_id}/metrics")
def list_metrics(
    org_id: UUID,
    metric_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """List metrics for organization."""
    try:
        repo = MetricRepository(db)
        if metric_type and start_date and end_date:
            type_enum = MetricType(metric_type)
            metrics = repo.get_history(org_id, type_enum, start_date, end_date)
        else:
            metrics = repo.get_by_org(org_id, start_date, end_date)
        return {
            "count": len(metrics),
            "metrics": [{
                "id": str(m.id),
                "type": m.metric_type.value,
                "value": str(m.metric_value),
                "date": m.period_date.isoformat()
            } for m in metrics]
        }
    except Exception as e:
        logger.error(f"Error listing metrics: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ---- Trend Endpoints ----

@router.post("/orgs/{org_id}/trends")
def create_trend(
    org_id: UUID,
    metric_type: str,
    direction: TrendDirection,
    strength: float,
    analysis_start: date,
    analysis_end: date,
    db: Session = Depends(get_db)
):
    """Create a new trend analysis."""
    try:
        repo = TrendRepository(db)
        trend = TrendAnalysis(
            organization_id=org_id,
            metric_type=metric_type,
            trend_direction=direction,
            strength=strength,
            analysis_period_start=analysis_start,
            analysis_period_end=analysis_end
        )
        created = repo.create(trend)
        logger.info(f"Created trend {created.id} for org {org_id}")
        return {
            "id": str(created.id),
            "metric": created.metric_type,
            "direction": created.trend_direction.value,
            "strength": created.strength
        }
    except Exception as e:
        logger.error(f"Error creating trend: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orgs/{org_id}/trends")
def list_trends(
    org_id: UUID,
    direction: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List trends for organization."""
    try:
        repo = TrendRepository(db)
        if direction:
            dir_enum = TrendDirection(direction)
            trends = repo.get_by_direction(org_id, dir_enum)
        else:
            trends = repo.get_by_org(org_id)
        return {
            "count": len(trends),
            "trends": [{
                "id": str(t.id),
                "metric": t.metric_type,
                "direction": t.trend_direction.value,
                "strength": t.strength
            } for t in trends]
        }
    except Exception as e:
        logger.error(f"Error listing trends: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ---- KPI Endpoints ----

@router.post("/orgs/{org_id}/kpis")
def create_kpi(
    org_id: UUID,
    name: str,
    code: str,
    period_date: date,
    current_value: Decimal,
    target_value: Optional[Decimal] = None,
    unit: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new KPI."""
    try:
        repo = KPIRepository(db)
        kpi = KPI(
            organization_id=org_id,
            name=name,
            code=code,
            period_date=period_date,
            current_value=current_value,
            target_value=target_value,
            unit=unit
        )
        created = repo.create(kpi)
        logger.info(f"Created KPI {created.id} ({code}) for org {org_id}")
        return {
            "id": str(created.id),
            "name": created.name,
            "code": created.code,
            "value": str(created.current_value),
            "target": str(created.target_value) if created.target_value else None,
            "unit": created.unit
        }
    except Exception as e:
        logger.error(f"Error creating KPI: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orgs/{org_id}/kpis")
def list_kpis(
    org_id: UUID,
    period_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """List KPIs for organization."""
    try:
        repo = KPIRepository(db)
        kpis = repo.get_by_org(org_id, period_date)
        return {
            "count": len(kpis),
            "kpis": [{
                "id": str(k.id),
                "name": k.name,
                "code": k.code,
                "value": str(k.current_value),
                "target": str(k.target_value) if k.target_value else None
            } for k in kpis]
        }
    except Exception as e:
        logger.error(f"Error listing KPIs: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/kpis/{code}/history")
def get_kpi_history(
    code: str,
    org_id: UUID,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """Get KPI history for date range."""
    try:
        repo = KPIRepository(db)
        history = repo.get_history(org_id, code, start_date, end_date)
        return {
            "code": code,
            "count": len(history),
            "history": [{
                "date": k.period_date.isoformat(),
                "value": str(k.current_value),
                "target": str(k.target_value) if k.target_value else None
            } for k in history]
        }
    except Exception as e:
        logger.error(f"Error retrieving KPI history: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ---- Dashboard Widget Endpoints ----

@router.post("/orgs/{org_id}/widgets")
def create_widget(
    org_id: UUID,
    title: str,
    widget_type: str,
    data_source: str,
    position: int = 0,
    is_pinned: bool = False,
    db: Session = Depends(get_db)
):
    """Create a dashboard widget."""
    try:
        repo = DashboardWidgetRepository(db)
        widget = DashboardWidget(
            organization_id=org_id,
            title=title,
            widget_type=widget_type,
            data_source=data_source,
            position=position,
            is_pinned=is_pinned
        )
        created = repo.create(widget)
        logger.info(f"Created widget {created.id} for org {org_id}")
        return {
            "id": str(created.id),
            "title": created.title,
            "type": created.widget_type,
            "source": created.data_source,
            "position": created.position,
            "pinned": created.is_pinned
        }
    except Exception as e:
        logger.error(f"Error creating widget: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orgs/{org_id}/widgets")
def list_widgets(
    org_id: UUID,
    pinned_only: bool = False,
    db: Session = Depends(get_db)
):
    """List dashboard widgets for organization."""
    try:
        repo = DashboardWidgetRepository(db)
        if pinned_only:
            widgets = repo.get_pinned(org_id)
        else:
            widgets = repo.get_by_org(org_id)
        return {
            "count": len(widgets),
            "widgets": [{
                "id": str(w.id),
                "title": w.title,
                "type": w.widget_type,
                "source": w.data_source,
                "position": w.position,
                "pinned": w.is_pinned
            } for w in widgets]
        }
    except Exception as e:
        logger.error(f"Error listing widgets: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/widgets/{widget_id}/position")
def update_widget_position(
    widget_id: UUID,
    org_id: UUID,
    position: int,
    db: Session = Depends(get_db)
):
    """Update widget position on dashboard."""
    try:
        repo = DashboardWidgetRepository(db)
        success = repo.update_position(org_id, widget_id, position)
        if not success:
            raise HTTPException(status_code=404, detail="Widget not found")
        logger.info(f"Updated widget {widget_id} position to {position}")
        return {"success": True, "position": position}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating widget position: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/widgets/{widget_id}")
def delete_widget(widget_id: UUID, db: Session = Depends(get_db)):
    """Delete (soft delete) a dashboard widget."""
    try:
        repo = DashboardWidgetRepository(db)
        success = repo.delete(widget_id)
        if not success:
            raise HTTPException(status_code=404, detail="Widget not found")
        logger.info(f"Deleted widget {widget_id}")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting widget: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
