"""Database models for report generation and distribution.

Models for report templates, schedules, and distribution tracking.
"""

from datetime import datetime, timezone, date
from typing import Optional
from uuid import uuid4
import enum

from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, Enum, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from decimal import Decimal

from backend.models import Base


class ReportFormat(str, enum.Enum):
    """Report output formats."""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ReportFrequency(str, enum.Enum):
    """Report scheduling frequency."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    ONCE = "once"


class ReportTemplate(Base):
    """Report template configuration."""
    __tablename__ = "report_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text)
    template_type = Column(String(50), nullable=False)  # "profit_loss", "balance_sheet", etc.

    # Template configuration
    include_sections = Column(String(500))  # JSON: ["summary", "details", "charts"]
    date_range_days = Column(Integer)  # Days back to include in report
    compare_previous = Column(Boolean, default=False)  # Compare to previous period
    include_charts = Column(Boolean, default=True)
    include_summary = Column(Boolean, default=True)

    # Formatting
    company_name_override = Column(String(200))
    logo_url = Column(String(500))
    footer_text = Column(Text)

    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ReportTemplate {self.name}>"


class ReportSchedule(Base):
    """Report generation schedule."""
    __tablename__ = "report_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    frequency = Column(Enum(ReportFrequency), nullable=False)
    format = Column(Enum(ReportFormat), nullable=False)

    # Schedule timing
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)  # None = ongoing
    day_of_week = Column(Integer)  # 0-6 for weekly (Mon=0)
    day_of_month = Column(Integer)  # 1-28 for monthly
    hour_utc = Column(Integer, default=9)  # 0-23 UTC hour to run

    # Distribution
    recipient_emails = Column(String(1000), nullable=False)  # CSV list
    include_body_text = Column(Boolean, default=False)
    subject_template = Column(String(200), default="Financial Report")

    is_active = Column(Boolean, default=True, index=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime, nullable=False, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ReportSchedule {self.name} ({self.frequency.value})>"


class Report(Base):
    """Generated report record."""
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    schedule_id = Column(UUID(as_uuid=True), index=True)  # NULL if manual generation
    template_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    report_type = Column(String(50), nullable=False)  # "profit_loss", "balance_sheet", etc.
    format = Column(Enum(ReportFormat), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Storage
    file_size = Column(Integer)  # bytes
    file_key = Column(String(500))  # S3 key or file path
    file_url = Column(String(500))  # Download URL

    # Metadata
    title = Column(String(200))
    summary = Column(Text)  # Executive summary
    data_points_count = Column(Integer)  # Number of data points in report

    status = Column(String(20), default="generated")  # "generated", "archived", "deleted"
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime)  # Auto-delete after this date

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<Report {self.report_type} ({self.format.value})>"


class ReportDistribution(Base):
    """Report distribution record."""
    __tablename__ = "report_distributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    report_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    schedule_id = Column(UUID(as_uuid=True), index=True)

    recipient_email = Column(String(200), nullable=False)
    status = Column(String(20), default="pending")  # "pending", "sent", "failed", "bounced"
    error_message = Column(Text)

    sent_at = Column(DateTime)
    opened_at = Column(DateTime)  # If tracking enabled

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ReportDistribution {self.recipient_email} ({self.status})>"
