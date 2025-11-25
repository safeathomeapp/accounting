"""API routes for tax compliance and management."""

import logging
from uuid import UUID
from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.tax import TaxManager, TaxCalculator, TaxLiabilityManager, TaxComplianceReporter
from backend.models.tax import TaxPeriod, TaxLiabilityStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tax", tags=["tax"])

# Initialize services
tax_manager = TaxManager()
tax_calculator = TaxCalculator()
liability_manager = TaxLiabilityManager()
compliance_reporter = TaxComplianceReporter()


# Request/Response Models
class TaxTypeRequest(BaseModel):
    """Request model for creating/managing tax types."""
    code: str = Field(..., description="Tax type code (e.g., income_tax)")
    name: str = Field(..., description="Human-readable tax type name")
    tax_type_category: str = Field(..., description="Category (Direct, Indirect, Payroll)")
    description: Optional[str] = Field(None, description="Optional description")


class TaxRateRequest(BaseModel):
    """Request model for setting tax rates."""
    jurisdiction: str = Field(..., description="Jurisdiction code/name")
    rate: Decimal = Field(..., description="Tax rate as decimal (0.0-1.0)")
    effective_date: date = Field(..., description="When rate becomes effective")
    expiration_date: Optional[date] = Field(None, description="When rate expires")


class TaxCalculationRequest(BaseModel):
    """Request model for tax calculations."""
    gross_income: Decimal = Field(..., description="Gross income")
    deductions: Decimal = Field(default=Decimal("0"), description="Deductions")
    tax_brackets: Optional[List[tuple]] = Field(None, description="Progressive tax brackets")
    rate: Optional[Decimal] = Field(None, description="Flat tax rate")


class LiabilityRequest(BaseModel):
    """Request model for creating tax liabilities."""
    tax_type_id: UUID = Field(..., description="Tax type UUID")
    period: TaxPeriod = Field(..., description="Tax period")
    tax_year: int = Field(..., description="Tax year")
    calculated_amount: Decimal = Field(..., description="Calculated tax amount")
    due_date: date = Field(..., description="Due date for payment")


class PaymentRequest(BaseModel):
    """Request model for recording payments."""
    tax_type_id: UUID = Field(..., description="Tax type UUID")
    period: TaxPeriod = Field(..., description="Tax period")
    tax_year: int = Field(..., description="Tax year")
    payment_amount: Decimal = Field(..., description="Payment amount")


# Tax Type Endpoints
@router.post("/types")
def create_tax_type(
    org_id: UUID,
    request: TaxTypeRequest
):
    """Create a new tax type for an organization."""
    try:
        tax_type = tax_manager.add_tax_type(
            organization_id=org_id,
            code=request.code,
            name=request.name,
            tax_type_category=request.tax_type_category,
            description=request.description
        )

        return {
            "id": str(tax_type.id),
            "code": tax_type.code,
            "name": tax_type.name,
            "category": tax_type.tax_type_category,
            "is_active": tax_type.is_active
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/types")
def get_organization_tax_types(
    org_id: UUID,
    include_inactive: bool = Query(False, description="Include inactive tax types")
):
    """Get all tax types for an organization."""
    types = tax_manager.get_organization_tax_types(org_id, include_inactive)

    return {
        "org_id": str(org_id),
        "count": len(types),
        "tax_types": [
            {
                "id": str(t.id),
                "code": t.code,
                "name": t.name,
                "category": t.tax_type_category,
                "is_active": t.is_active
            }
            for t in types
        ]
    }


@router.post("/types/{tax_type_code}/activate")
def activate_tax_type(
    org_id: UUID,
    tax_type_code: str
):
    """Activate a tax type."""
    try:
        tax_type = tax_manager.activate_tax_type(org_id, tax_type_code)

        return {
            "code": tax_type.code,
            "name": tax_type.name,
            "is_active": tax_type.is_active
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/types/{tax_type_code}/deactivate")
def deactivate_tax_type(
    org_id: UUID,
    tax_type_code: str
):
    """Deactivate a tax type."""
    try:
        tax_type = tax_manager.deactivate_tax_type(org_id, tax_type_code)

        return {
            "code": tax_type.code,
            "name": tax_type.name,
            "is_active": tax_type.is_active
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Tax Rate Endpoints
@router.post("/rates")
def set_tax_rate(
    org_id: UUID,
    tax_type_id: UUID,
    request: TaxRateRequest
):
    """Set a tax rate for a jurisdiction."""
    try:
        rate = tax_manager.set_tax_rate(
            organization_id=org_id,
            tax_type_id=tax_type_id,
            jurisdiction=request.jurisdiction,
            rate=request.rate,
            effective_date=request.effective_date,
            expiration_date=request.expiration_date
        )

        return {
            "jurisdiction": rate.jurisdiction,
            "rate": float(rate.rate),
            "effective_date": rate.effective_date.isoformat(),
            "expiration_date": rate.expiration_date.isoformat() if rate.expiration_date else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rates/{jurisdiction}")
def get_current_rate(
    org_id: UUID,
    tax_type_id: UUID,
    jurisdiction: str,
    as_of_date: Optional[date] = Query(None, description="Date to check rate for")
):
    """Get current tax rate for a jurisdiction."""
    rate = tax_manager.get_current_rate(org_id, tax_type_id, jurisdiction, as_of_date)

    if not rate:
        raise HTTPException(status_code=404, detail=f"No rate found for {jurisdiction}")

    return {
        "jurisdiction": rate.jurisdiction,
        "rate": float(rate.rate),
        "effective_date": rate.effective_date.isoformat()
    }


# Tax Calculator Endpoints
@router.post("/calculate/income-tax")
def calculate_income_tax(
    request: TaxCalculationRequest
):
    """Calculate progressive income tax."""
    try:
        if not request.tax_brackets:
            raise HTTPException(status_code=400, detail="Tax brackets required")

        # Convert bracket tuples to Decimal
        brackets = [
            (Decimal(str(b[0])), Decimal(str(b[1])))
            for b in request.tax_brackets
        ]

        taxable, tax = tax_calculator.calculate_income_tax(
            request.gross_income,
            brackets,
            request.deductions
        )

        return {
            "gross_income": float(request.gross_income),
            "deductions": float(request.deductions),
            "taxable_income": float(taxable),
            "tax_amount": float(tax)
        }
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calculate/sales-tax")
def calculate_sales_tax(
    amount: Decimal,
    rate: Decimal
):
    """Calculate sales tax."""
    try:
        sale_amount, tax = tax_calculator.calculate_sales_tax(amount, rate)

        return {
            "sale_amount": float(sale_amount),
            "tax_rate": float(rate),
            "tax_amount": float(tax),
            "total": float(sale_amount + tax)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calculate/withholding")
def calculate_withholding_tax(
    amount: Decimal,
    rate: Decimal,
    allowances: int = Query(0, description="Number of withholding allowances"),
    allowance_amount: Decimal = Query(Decimal("0"), description="Amount per allowance")
):
    """Calculate withholding tax."""
    try:
        base, withholding = tax_calculator.calculate_withholding_tax(
            amount, rate, allowances, allowance_amount
        )

        return {
            "gross_amount": float(amount),
            "allowances": allowances,
            "withholding_base": float(base),
            "withholding_amount": float(withholding)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Tax Liability Endpoints
@router.post("/liabilities")
def create_liability(
    org_id: UUID,
    request: LiabilityRequest
):
    """Create a new tax liability."""
    try:
        liability = liability_manager.create_liability(
            organization_id=org_id,
            tax_type_id=request.tax_type_id,
            period=request.period,
            tax_year=request.tax_year,
            calculated_amount=request.calculated_amount,
            due_date=request.due_date
        )

        return {
            "period": liability.period.value,
            "tax_year": liability.tax_year,
            "calculated_amount": float(liability.calculated_amount),
            "paid_amount": float(liability.paid_amount),
            "balance": float(liability.balance),
            "status": liability.status.value,
            "due_date": liability.due_date.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/liabilities")
def get_liabilities(
    org_id: UUID,
    tax_year: Optional[int] = Query(None, description="Filter by tax year"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Get all liabilities for an organization."""
    status_enum = None
    if status:
        try:
            status_enum = TaxLiabilityStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    liabilities = liability_manager.get_organization_liabilities(
        org_id, tax_year=tax_year, status=status_enum
    )

    return {
        "org_id": str(org_id),
        "count": len(liabilities),
        "liabilities": [
            {
                "period": l.period.value,
                "tax_year": l.tax_year,
                "calculated": float(l.calculated_amount),
                "paid": float(l.paid_amount),
                "balance": float(l.balance),
                "status": l.status.value,
                "due_date": l.due_date.isoformat()
            }
            for l in liabilities
        ]
    }


@router.post("/liabilities/{period}/{year}/payment")
def record_payment(
    org_id: UUID,
    period: TaxPeriod,
    year: int,
    tax_type_id: UUID,
    amount: Decimal = Query(..., description="Payment amount")
):
    """Record a payment for a liability."""
    try:
        liability = liability_manager.record_payment(
            org_id, tax_type_id, period, year, amount
        )

        return {
            "paid_amount": float(liability.paid_amount),
            "balance": float(liability.balance),
            "status": liability.status.value
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/liabilities/overdue")
def get_overdue_liabilities(org_id: UUID):
    """Get all overdue liabilities for an organization."""
    overdue = liability_manager.get_overdue_liabilities(org_id)

    return {
        "org_id": str(org_id),
        "count": len(overdue),
        "overdue_items": [
            {
                "period": l.period.value,
                "tax_year": l.tax_year,
                "balance": float(l.balance),
                "due_date": l.due_date.isoformat(),
                "days_overdue": (date.today() - l.due_date).days
            }
            for l in overdue
        ]
    }


@router.get("/liabilities/summary/{year}")
def get_liability_summary(org_id: UUID, year: int):
    """Get annual liability summary."""
    summary = liability_manager.get_liability_summary(org_id, year)

    return {
        "org_id": str(org_id),
        "year": year,
        "total_calculated": float(summary["total_calculated"]),
        "total_paid": float(summary["total_paid"]),
        "total_balance": float(summary["total_balance"])
    }


# Compliance Endpoints
@router.post("/compliance/checklist/{period}/{year}")
def create_compliance_checklist(
    org_id: UUID,
    period: TaxPeriod,
    year: int,
    items: List[Dict[str, Any]]
):
    """Create a compliance checklist."""
    try:
        checklist = compliance_reporter.create_compliance_checklist(
            org_id, period, year, items
        )

        return {
            "period": period.value,
            "year": year,
            "item_count": len(checklist),
            "items": [
                {
                    "item_id": item.item_id,
                    "description": item.description,
                    "due_date": item.due_date.isoformat(),
                    "is_completed": item.is_completed
                }
                for item in checklist
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/compliance/checklist/{period}/{year}/{item_id}/complete")
def complete_checklist_item(
    org_id: UUID,
    period: TaxPeriod,
    year: int,
    item_id: str,
    notes: Optional[str] = Query(None, description="Completion notes")
):
    """Mark a checklist item as complete."""
    item = compliance_reporter.mark_checklist_item_complete(
        org_id, period, year, item_id, notes
    )

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return {
        "item_id": item.item_id,
        "description": item.description,
        "is_completed": item.is_completed
    }


@router.get("/compliance/report/{period}/{year}")
def get_compliance_report(org_id: UUID, period: TaxPeriod, year: int):
    """Generate compliance report."""
    report = compliance_reporter.generate_compliance_report(org_id, period, year)

    return report


@router.get("/compliance/summary/{year}")
def get_compliance_summary(org_id: UUID, year: int):
    """Get annual compliance summary."""
    summary = compliance_reporter.get_annual_compliance_summary(org_id, year)

    return summary


@router.get("/compliance/calendar/{year}")
def get_compliance_calendar(org_id: UUID, year: int):
    """Get compliance calendar for the year."""
    calendar = compliance_reporter.get_compliance_calendar(org_id, year)

    return {
        "org_id": str(org_id),
        "year": year,
        "event_count": len(calendar),
        "events": calendar
    }


@router.get("/compliance/health")
def get_tax_compliance_health(org_id: UUID):
    """Get overall tax compliance health status."""
    overdue = liability_manager.get_overdue_liabilities(org_id)
    upcoming = liability_manager.get_upcoming_liabilities(org_id, days=30)

    return {
        "org_id": str(org_id),
        "overdue_liabilities": len(overdue),
        "upcoming_deadlines": len(upcoming),
        "overall_status": "at_risk" if len(overdue) > 0 else "healthy" if len(upcoming) == 0 else "watch"
    }
