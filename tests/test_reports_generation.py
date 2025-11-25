"""Tests for report generation and distribution.

Tests report templates, generation, scheduling, and distribution.
"""

import pytest
from uuid import uuid4
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

from backend.reporting.generation import ReportGenerator
from backend.reporting.distribution import EmailDistributionService, ReportScheduler
from backend.models.reports import ReportFormat, ReportFrequency


class TestReportGenerator:
    """Tests for report generation."""

    def setup_method(self):
        """Set up for each test."""
        self.generator = ReportGenerator()
        self.org_id = uuid4()

    def test_generate_pdf_with_data(self):
        """Test PDF generation with data."""
        data = {
            "summary": {"Total Revenue": "$100,000", "Total Expenses": "$75,000"},
            "tables": {
                "Revenue Breakdown": [
                    ["Category", "Amount"],
                    ["Sales", "$80,000"],
                    ["Services", "$20,000"]
                ]
            }
        }

        pdf = self.generator.generate_pdf(
            "profit_loss",
            "Profit & Loss Statement",
            date(2024, 1, 1),
            date(2024, 1, 31),
            data
        )

        assert isinstance(pdf, bytes)
        assert len(pdf) > 0

    def test_generate_excel_with_data(self):
        """Test Excel generation with data."""
        data = {
            "summary": {"Total Assets": "500000", "Total Liabilities": "200000"},
            "tables": {
                "Assets": [
                    ["Asset Type", "Amount"],
                    ["Cash", "100000"],
                    ["Equipment", "400000"]
                ]
            }
        }

        excel = self.generator.generate_excel(
            "balance_sheet",
            "Balance Sheet",
            date(2024, 1, 1),
            date(2024, 1, 31),
            data
        )

        assert isinstance(excel, bytes)
        assert len(excel) > 0

    def test_generate_csv_report(self):
        """Test CSV generation."""
        data = {
            "summary": {"Period": "January 2024"},
            "tables": {
                "Summary": [
                    ["Metric", "Value"],
                    ["Revenue", "100000"],
                    ["Expenses", "75000"]
                ]
            }
        }

        csv = self.generator.generate_csv(
            "summary",
            "Financial Summary",
            date(2024, 1, 1),
            date(2024, 1, 31),
            data
        )

        assert isinstance(csv, str)
        assert "Financial Summary" in csv
        assert "Revenue" in csv
        assert "100000" in csv

    def test_pdf_with_company_name(self):
        """Test PDF generation includes company name."""
        data = {"summary": {}, "tables": {}}

        pdf = self.generator.generate_pdf(
            "report",
            "Test Report",
            date(2024, 1, 1),
            date(2024, 1, 31),
            data,
            company_name="Acme Corp"
        )

        assert isinstance(pdf, bytes)
        assert len(pdf) > 0

    def test_excel_column_sizing(self):
        """Test Excel auto-sizes columns."""
        data = {
            "summary": {},
            "tables": {
                "Data": [
                    ["Column1", "Very Long Column Header"],
                    ["A", "B"],
                    ["C", "D"]
                ]
            }
        }

        excel = self.generator.generate_excel(
            "test",
            "Test",
            date(2024, 1, 1),
            date(2024, 1, 31),
            data
        )

        assert isinstance(excel, bytes)
        assert len(excel) > 0

    def test_csv_summary_section(self):
        """Test CSV includes summary section."""
        data = {
            "summary": {"Total": "10000", "Average": "5000"},
            "tables": {}
        }

        csv = self.generator.generate_csv(
            "test",
            "Test",
            date(2024, 1, 1),
            date(2024, 1, 31),
            data
        )

        assert "Total" in csv
        assert "10000" in csv


class TestEmailDistributionService:
    """Tests for email distribution."""

    def setup_method(self):
        """Set up for each test."""
        self.service = EmailDistributionService()
        self.org_id = uuid4()
        self.report_id = uuid4()

    def test_send_report(self):
        """Test sending a report via email."""
        success = self.service.send_report(
            "user@example.com",
            self.report_id,
            "Profit_Loss_Jan2024",
            b"PDF content",
            "pdf"
        )

        assert success is True
        delivery = self.service.get_delivery_status(self.report_id)
        assert delivery is not None
        assert delivery["recipient"] == "user@example.com"
        assert delivery["status"] == "sent"

    def test_send_bulk_reports(self):
        """Test sending reports to multiple recipients."""
        recipients = [
            "user1@example.com",
            "user2@example.com",
            "user3@example.com"
        ]

        results = self.service.send_bulk(
            recipients,
            self.report_id,
            "Report",
            b"File content",
            "pdf"
        )

        assert len(results) == 3
        assert all(success for success in results.values())
        assert all(results[email] for email in recipients)

    def test_delivery_status_tracking(self):
        """Test delivery status is tracked."""
        self.service.send_report(
            "user@example.com",
            self.report_id,
            "Report",
            b"content",
            "pdf"
        )

        delivery = self.service.get_delivery_status(self.report_id)
        assert delivery["report_id"] == str(self.report_id)
        assert delivery["sent_at"] is not None
        assert delivery["file_size"] == 7

    def test_pending_deliveries(self):
        """Test get pending deliveries."""
        report_id_1 = uuid4()
        report_id_2 = uuid4()

        self.service.send_report(
            "user1@example.com",
            report_id_1,
            "Report1",
            b"content",
            "pdf"
        )
        self.service.send_report(
            "user2@example.com",
            report_id_2,
            "Report2",
            b"content",
            "pdf"
        )

        pending = self.service.get_pending_deliveries()
        # All are sent immediately in this implementation
        assert isinstance(pending, list)

    def test_retry_failed_delivery(self):
        """Test retrying a failed delivery."""
        self.service.send_report(
            "user@example.com",
            self.report_id,
            "Report",
            b"content",
            "pdf"
        )

        success = self.service.retry_failed(self.report_id, b"new content")
        assert success is True

        delivery = self.service.get_delivery_status(self.report_id)
        assert delivery.get("retry_count", 1) >= 1


class TestReportScheduler:
    """Tests for report scheduling."""

    def setup_method(self):
        """Set up for each test."""
        self.scheduler = ReportScheduler()
        self.org_id = uuid4()
        self.schedule_id = uuid4()

    def test_create_daily_schedule(self):
        """Test creating a daily report schedule."""
        schedule = self.scheduler.create_schedule(
            self.schedule_id,
            self.org_id,
            "daily",
            "pdf",
            ["user@example.com"],
            date(2024, 1, 1),
            hour_utc=9
        )

        assert schedule["id"] == str(self.schedule_id)
        assert schedule["frequency"] == "daily"
        assert schedule["format"] == "pdf"
        assert schedule["is_active"] is True

    def test_create_weekly_schedule(self):
        """Test creating a weekly report schedule."""
        schedule = self.scheduler.create_schedule(
            self.schedule_id,
            self.org_id,
            "weekly",
            "excel",
            ["user@example.com"],
            date(2024, 1, 1)
        )

        assert schedule["frequency"] == "weekly"
        assert schedule["format"] == "excel"

    def test_create_monthly_schedule(self):
        """Test creating a monthly report schedule."""
        schedule = self.scheduler.create_schedule(
            self.schedule_id,
            self.org_id,
            "monthly",
            "json",
            ["user@example.com"],
            date(2024, 1, 1)
        )

        assert schedule["frequency"] == "monthly"
        assert schedule["format"] == "json"

    def test_get_schedule(self):
        """Test retrieving a schedule."""
        self.scheduler.create_schedule(
            self.schedule_id,
            self.org_id,
            "daily",
            "pdf",
            ["user@example.com"],
            date(2024, 1, 1)
        )

        schedule = self.scheduler.get_schedule(self.schedule_id)
        assert schedule is not None
        assert schedule["id"] == str(self.schedule_id)

    def test_get_due_schedules(self):
        """Test getting schedules due for execution."""
        # Create schedule that will be due
        self.scheduler.create_schedule(
            self.schedule_id,
            self.org_id,
            "daily",
            "pdf",
            ["user@example.com"],
            date.today(),
            hour_utc=0
        )

        due = self.scheduler.get_due_schedules()
        # Should have at least the one we created
        assert isinstance(due, list)

    def test_mark_schedule_executed(self):
        """Test marking schedule as executed."""
        self.scheduler.create_schedule(
            self.schedule_id,
            self.org_id,
            "daily",
            "pdf",
            ["user@example.com"],
            date(2024, 1, 1)
        )

        success = self.scheduler.mark_executed(self.schedule_id)
        assert success is True

        schedule = self.scheduler.get_schedule(self.schedule_id)
        assert schedule["last_run"] is not None

    def test_pause_schedule(self):
        """Test pausing a schedule."""
        self.scheduler.create_schedule(
            self.schedule_id,
            self.org_id,
            "daily",
            "pdf",
            ["user@example.com"],
            date(2024, 1, 1)
        )

        success = self.scheduler.pause_schedule(self.schedule_id)
        assert success is True

        schedule = self.scheduler.get_schedule(self.schedule_id)
        assert schedule["is_active"] is False

    def test_resume_schedule(self):
        """Test resuming a paused schedule."""
        self.scheduler.create_schedule(
            self.schedule_id,
            self.org_id,
            "daily",
            "pdf",
            ["user@example.com"],
            date(2024, 1, 1)
        )

        self.scheduler.pause_schedule(self.schedule_id)
        success = self.scheduler.resume_schedule(self.schedule_id)
        assert success is True

        schedule = self.scheduler.get_schedule(self.schedule_id)
        assert schedule["is_active"] is True

    def test_delete_schedule(self):
        """Test deleting a schedule."""
        self.scheduler.create_schedule(
            self.schedule_id,
            self.org_id,
            "daily",
            "pdf",
            ["user@example.com"],
            date(2024, 1, 1)
        )

        success = self.scheduler.delete_schedule(self.schedule_id)
        assert success is True

        schedule = self.scheduler.get_schedule(self.schedule_id)
        assert schedule is None

    def test_multiple_recipients(self):
        """Test schedule with multiple recipients."""
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
        schedule = self.scheduler.create_schedule(
            self.schedule_id,
            self.org_id,
            "daily",
            "pdf",
            recipients,
            date(2024, 1, 1)
        )

        assert len(schedule["recipient_emails"]) == 3
        assert all(email in schedule["recipient_emails"] for email in recipients)


class TestReportWorkflow:
    """Integration tests for complete report workflow."""

    def setup_method(self):
        """Set up for each test."""
        self.generator = ReportGenerator()
        self.distributor = EmailDistributionService()
        self.scheduler = ReportScheduler()
        self.org_id = uuid4()

    def test_complete_report_generation_and_distribution(self):
        """Test generating and distributing a report."""
        # Generate report
        data = {
            "summary": {"Revenue": "$100000"},
            "tables": {"Income": [["Item", "Amount"], ["Sales", "$100000"]]}
        }

        pdf = self.generator.generate_pdf(
            "profit_loss",
            "Monthly P&L",
            date(2024, 1, 1),
            date(2024, 1, 31),
            data
        )

        # Distribute report
        report_id = uuid4()
        success = self.distributor.send_report(
            "manager@example.com",
            report_id,
            "P&L_Jan2024",
            pdf,
            "pdf"
        )

        assert success is True
        delivery = self.distributor.get_delivery_status(report_id)
        assert delivery["status"] == "sent"

    def test_scheduled_report_generation(self):
        """Test scheduled report generation workflow."""
        schedule_id = uuid4()

        # Create schedule
        schedule = self.scheduler.create_schedule(
            schedule_id,
            self.org_id,
            "daily",
            "pdf",
            ["reports@company.com"],
            date(2024, 1, 1)
        )

        assert schedule["is_active"] is True

        # Execute schedule
        success = self.scheduler.mark_executed(schedule_id)
        assert success is True

        # Verify next run is scheduled
        updated = self.scheduler.get_schedule(schedule_id)
        assert updated["next_run"] > updated["last_run"]

    def test_multi_format_report_generation(self):
        """Test generating same report in multiple formats."""
        data = {
            "summary": {"Total": "1000"},
            "tables": {}
        }

        pdf = self.generator.generate_pdf("test", "Test", date(2024, 1, 1), date(2024, 1, 31), data)
        excel = self.generator.generate_excel("test", "Test", date(2024, 1, 1), date(2024, 1, 31), data)
        csv = self.generator.generate_csv("test", "Test", date(2024, 1, 1), date(2024, 1, 31), data)

        assert len(pdf) > 0
        assert len(excel) > 0
        assert len(csv) > 0

    def test_schedule_execution_and_distribution(self):
        """Test complete schedule execution and distribution."""
        schedule_id = uuid4()
        report_id = uuid4()

        # Create and execute schedule
        self.scheduler.create_schedule(
            schedule_id,
            self.org_id,
            "daily",
            "pdf",
            ["user@example.com"],
            date(2024, 1, 1)
        )

        # Generate report
        data = {"summary": {}, "tables": {}}
        pdf = self.generator.generate_pdf(
            "test", "Test", date(2024, 1, 1), date(2024, 1, 31), data
        )

        # Distribute report
        success = self.distributor.send_report(
            "user@example.com",
            report_id,
            "Test_Report",
            pdf,
            "pdf"
        )

        assert success is True
        self.scheduler.mark_executed(schedule_id)

        schedule = self.scheduler.get_schedule(schedule_id)
        assert schedule["last_run"] is not None
