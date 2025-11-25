"""Report management REST API endpoints.

Endpoints for creating, managing, and distributing financial reports.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date
from decimal import Decimal

from backend.database import get_db
from backend.models.reports import ReportTemplate, ReportSchedule, Report, ReportDistribution, ReportFormat, ReportFrequency
from backend.reporting.generation import ReportGenerator
from backend.reporting.distribution import EmailDistributionService, ReportScheduler

router = APIRouter(prefix="/api/reports", tags=["reports"])

# Services
generator = ReportGenerator()
distributor = EmailDistributionService()
scheduler = ReportScheduler()


# ==================== REQUEST MODELS ====================

class CreateTemplateRequest(BaseModel):
    """Request model for creating a template."""
    name: str
    template_type: str
    include_sections: str = "summary,details"
    company_name_override: str = None


class CreateScheduleRequest(BaseModel):
    """Request model for creating a schedule."""
    template_id: UUID
    name: str
    frequency: str
    format: str
    recipient_emails: list[str]
    start_date: date
    hour_utc: int = 9


class GenerateReportRequest(BaseModel):
    """Request model for generating a report."""
    template_id: UUID
    period_start: date
    period_end: date
    report_format: str = "pdf"


class SendReportRequest(BaseModel):
    """Request model for sending a report."""
    report_id: UUID
    recipient_emails: list[str]


# ==================== TEMPLATES ====================

@router.post("/orgs/{org_id}/templates")
def create_template(
    org_id: UUID,
    request: CreateTemplateRequest,
    db: Session = Depends(get_db)
):
    """Create a new report template."""
    try:
        template = ReportTemplate(
            organization_id=org_id,
            name=request.name,
            template_type=request.template_type,
            include_sections=request.include_sections,
            company_name_override=request.company_name_override or request.name,
            is_active=True
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        return {
            "id": str(template.id),
            "organization_id": str(template.organization_id),
            "name": template.name,
            "template_type": template.template_type,
            "include_sections": template.include_sections,
            "is_active": template.is_active,
            "created_at": template.created_at.isoformat()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orgs/{org_id}/templates")
def list_templates(
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """List all templates for organization."""
    templates = db.query(ReportTemplate).filter(
        ReportTemplate.organization_id == org_id,
        ReportTemplate.is_active == True
    ).all()

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "template_type": t.template_type,
            "include_sections": t.include_sections,
            "created_at": t.created_at.isoformat()
        }
        for t in templates
    ]


@router.get("/orgs/{org_id}/templates/{template_id}")
def get_template(
    org_id: UUID,
    template_id: UUID,
    db: Session = Depends(get_db)
):
    """Get specific template."""
    template = db.query(ReportTemplate).filter(
        ReportTemplate.id == template_id,
        ReportTemplate.organization_id == org_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "id": str(template.id),
        "name": template.name,
        "template_type": template.template_type,
        "include_sections": template.include_sections,
        "company_name_override": template.company_name_override,
        "is_active": template.is_active
    }


# ==================== SCHEDULES ====================

@router.post("/orgs/{org_id}/schedules")
def create_schedule(
    org_id: UUID,
    request: CreateScheduleRequest,
    db: Session = Depends(get_db)
):
    """Create a new report schedule."""
    try:
        # Verify template exists
        template = db.query(ReportTemplate).filter(
            ReportTemplate.id == request.template_id,
            ReportTemplate.organization_id == org_id
        ).first()

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Create schedule
        schedule_id = scheduler.create_schedule(
            schedule_id=UUID('00000000-0000-0000-0000-000000000001'),  # Placeholder, will override
            organization_id=org_id,
            frequency=request.frequency,
            format=request.format,
            recipient_emails=request.recipient_emails,
            start_date=request.start_date,
            hour_utc=request.hour_utc
        )

        # Persist to database
        db_schedule = ReportSchedule(
            organization_id=org_id,
            template_id=request.template_id,
            name=request.name,
            frequency=ReportFrequency[request.frequency.upper()],
            format=ReportFormat[request.format.upper()],
            recipient_emails=",".join(request.recipient_emails),
            start_date=request.start_date,
            hour_utc=request.hour_utc,
            is_active=True,
            next_run=schedule_id["next_run"]
        )
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)

        return {
            "id": str(db_schedule.id),
            "organization_id": str(db_schedule.organization_id),
            "name": db_schedule.name,
            "frequency": db_schedule.frequency.value,
            "format": db_schedule.format.value,
            "recipient_emails": db_schedule.recipient_emails.split(","),
            "is_active": db_schedule.is_active,
            "next_run": db_schedule.next_run.isoformat(),
            "created_at": db_schedule.created_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orgs/{org_id}/schedules")
def list_schedules(
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """List all schedules for organization."""
    schedules = db.query(ReportSchedule).filter(
        ReportSchedule.organization_id == org_id,
        ReportSchedule.is_active == True
    ).all()

    return [
        {
            "id": str(s.id),
            "name": s.name,
            "frequency": s.frequency.value,
            "format": s.format.value,
            "recipient_emails": s.recipient_emails.split(","),
            "is_active": s.is_active,
            "next_run": s.next_run.isoformat(),
            "last_run": s.last_run.isoformat() if s.last_run else None
        }
        for s in schedules
    ]


@router.get("/orgs/{org_id}/schedules/{schedule_id}")
def get_schedule(
    org_id: UUID,
    schedule_id: UUID,
    db: Session = Depends(get_db)
):
    """Get specific schedule."""
    schedule = db.query(ReportSchedule).filter(
        ReportSchedule.id == schedule_id,
        ReportSchedule.organization_id == org_id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return {
        "id": str(schedule.id),
        "name": schedule.name,
        "frequency": schedule.frequency.value,
        "format": schedule.format.value,
        "recipient_emails": schedule.recipient_emails.split(","),
        "is_active": schedule.is_active,
        "next_run": schedule.next_run.isoformat(),
        "last_run": schedule.last_run.isoformat() if schedule.last_run else None
    }


@router.post("/orgs/{org_id}/schedules/{schedule_id}/pause")
def pause_schedule(
    org_id: UUID,
    schedule_id: UUID,
    db: Session = Depends(get_db)
):
    """Pause a schedule."""
    schedule = db.query(ReportSchedule).filter(
        ReportSchedule.id == schedule_id,
        ReportSchedule.organization_id == org_id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule.is_active = False
    db.commit()

    return {"success": True, "message": "Schedule paused"}


@router.post("/orgs/{org_id}/schedules/{schedule_id}/resume")
def resume_schedule(
    org_id: UUID,
    schedule_id: UUID,
    db: Session = Depends(get_db)
):
    """Resume a paused schedule."""
    schedule = db.query(ReportSchedule).filter(
        ReportSchedule.id == schedule_id,
        ReportSchedule.organization_id == org_id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule.is_active = True
    db.commit()

    return {"success": True, "message": "Schedule resumed"}


@router.delete("/orgs/{org_id}/schedules/{schedule_id}")
def delete_schedule(
    org_id: UUID,
    schedule_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a schedule."""
    schedule = db.query(ReportSchedule).filter(
        ReportSchedule.id == schedule_id,
        ReportSchedule.organization_id == org_id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(schedule)
    db.commit()

    return {"success": True, "message": "Schedule deleted"}


# ==================== REPORT GENERATION ====================

@router.post("/orgs/{org_id}/generate")
def generate_report(
    org_id: UUID,
    request: GenerateReportRequest,
    db: Session = Depends(get_db)
):
    """Generate a report manually."""
    try:
        # Verify template
        template = db.query(ReportTemplate).filter(
            ReportTemplate.id == request.template_id,
            ReportTemplate.organization_id == org_id
        ).first()

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Generate report data (simplified for demo)
        data = {
            "summary": {
                "Period": f"{request.period_start} to {request.period_end}",
                "Organization": template.company_name_override
            },
            "tables": {}
        }

        # Generate in requested format
        if request.report_format == "pdf":
            content = generator.generate_pdf(
                template.template_type,
                template.name,
                request.period_start,
                request.period_end,
                data,
                company_name=template.company_name_override
            )
        elif request.report_format == "excel":
            content = generator.generate_excel(
                template.template_type,
                template.name,
                request.period_start,
                request.period_end,
                data,
                company_name=template.company_name_override
            )
        else:  # csv
            content = generator.generate_csv(
                template.template_type,
                template.name,
                request.period_start,
                request.period_end,
                data
            )
            if isinstance(content, str):
                content = content.encode('utf-8')

        # Store in database
        report = Report(
            organization_id=org_id,
            template_id=request.template_id,
            report_type=template.template_type,
            format=ReportFormat[request.report_format.upper()],
            period_start=request.period_start,
            period_end=request.period_end,
            title=template.name,
            file_size=len(content),
            status="generated"
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return {
            "id": str(report.id),
            "organization_id": str(report.organization_id),
            "report_type": report.report_type,
            "format": report.format.value,
            "period_start": str(report.period_start),
            "period_end": str(report.period_end),
            "file_size": report.file_size,
            "status": report.status,
            "generated_at": report.generated_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid format: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orgs/{org_id}/reports")
def list_reports(
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """List generated reports for organization."""
    reports = db.query(Report).filter(
        Report.organization_id == org_id
    ).order_by(Report.generated_at.desc()).all()

    return [
        {
            "id": str(r.id),
            "report_type": r.report_type,
            "format": r.format.value,
            "period_start": str(r.period_start),
            "period_end": str(r.period_end),
            "file_size": r.file_size,
            "status": r.status,
            "generated_at": r.generated_at.isoformat()
        }
        for r in reports
    ]


# ==================== DISTRIBUTION ====================

@router.post("/orgs/{org_id}/send")
def send_report(
    org_id: UUID,
    request: SendReportRequest,
    db: Session = Depends(get_db)
):
    """Send a generated report."""
    # Verify report exists
    report = db.query(Report).filter(
        Report.id == request.report_id,
        Report.organization_id == org_id
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # For demo, use mock content
    file_bytes = b"Report content"

    # Send to all recipients
    results = distributor.send_bulk(
        request.recipient_emails,
        request.report_id,
        report.title or f"Report_{report.report_type}",
        file_bytes,
        report.format.value
    )

    # Track distributions in database
    for email, success in results.items():
        distribution = ReportDistribution(
            organization_id=org_id,
            report_id=request.report_id,
            recipient_email=email,
            status="sent" if success else "failed"
        )
        db.add(distribution)

    db.commit()

    return {
        "success": all(results.values()),
        "sent": sum(1 for v in results.values() if v),
        "total": len(results),
        "results": results
    }


@router.get("/orgs/{org_id}/distributions")
def list_distributions(
    org_id: UUID,
    report_id: UUID = None,
    db: Session = Depends(get_db)
):
    """List report distributions."""
    query = db.query(ReportDistribution).filter(
        ReportDistribution.organization_id == org_id
    )

    if report_id:
        query = query.filter(ReportDistribution.report_id == report_id)

    distributions = query.all()

    return [
        {
            "id": str(d.id),
            "report_id": str(d.report_id),
            "recipient_email": d.recipient_email,
            "status": d.status,
            "sent_at": d.sent_at.isoformat() if d.sent_at else None,
            "created_at": d.created_at.isoformat()
        }
        for d in distributions
    ]
