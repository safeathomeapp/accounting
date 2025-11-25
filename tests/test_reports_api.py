"""Tests for report management REST API endpoints.

Integration tests for all report API endpoints including templates, schedules,
generation, and distribution.
"""

import pytest
from uuid import uuid4
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

from backend.main import app
from backend.models.reports import ReportTemplate, ReportSchedule, Report, ReportDistribution, ReportFormat, ReportFrequency
from backend.database import SessionLocal


@pytest.fixture
def client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session."""
    return SessionLocal()


@pytest.fixture
def org_id():
    """Organization ID."""
    return uuid4()


class TestReportTemplatesAPI:
    """Tests for report template endpoints."""

    def test_create_template(self, client, db_session, org_id):
        """Test creating a report template."""
        response = client.post(
            f"/api/reports/orgs/{org_id}/templates",
            json={
                "name": "Monthly P&L",
                "template_type": "profit_loss",
                "include_sections": "summary,details"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Monthly P&L"
        assert data["template_type"] == "profit_loss"
        assert data["is_active"] is True

    def test_list_templates(self, client, db_session, org_id):
        """Test listing templates for organization."""
        # Create template
        client.post(
            f"/api/reports/orgs/{org_id}/templates",
            json={
                "name": "Template 1",
                "template_type": "balance_sheet"
            }
        )

        # List templates
        response = client.get(f"/api/reports/orgs/{org_id}/templates")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(t["name"] == "Template 1" for t in data)

    def test_get_template(self, client, db_session, org_id):
        """Test retrieving a specific template."""
        # Create template
        create_response = client.post(
            f"/api/reports/orgs/{org_id}/templates",
            json={
                "name": "Balance Sheet",
                "template_type": "balance_sheet"
            }
        )
        template_id = create_response.json()["id"]

        # Get template
        response = client.get(
            f"/api/reports/orgs/{org_id}/templates/{template_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Balance Sheet"
        assert data["template_type"] == "balance_sheet"

    def test_get_nonexistent_template(self, client, org_id):
        """Test getting a template that doesn't exist."""
        response = client.get(
            f"/api/reports/orgs/{org_id}/templates/{uuid4()}"
        )

        assert response.status_code == 404


class TestReportSchedulesAPI:
    """Tests for report schedule endpoints."""

    @pytest.fixture
    def template_id(self, client, org_id):
        """Create a template for testing."""
        response = client.post(
            f"/api/reports/orgs/{org_id}/templates",
            json={
                "name": "Test Template",
                "template_type": "profit_loss"
            }
        )
        return response.json()["id"]

    def test_create_schedule(self, client, org_id, template_id):
        """Test creating a schedule."""
        response = client.post(
            f"/api/reports/orgs/{org_id}/schedules",
            json={
                "template_id": template_id,
                "name": "Daily P&L",
                "frequency": "daily",
                "format": "pdf",
                "recipient_emails": ["user@example.com"],
                "start_date": str(date.today()),
                "hour_utc": 9
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Daily P&L"
        assert data["frequency"] == "daily"
        assert data["format"] == "pdf"
        assert data["is_active"] is True

    def test_create_schedule_invalid_template(self, client, org_id):
        """Test creating schedule with invalid template."""
        response = client.post(
            f"/api/reports/orgs/{org_id}/schedules",
            json={
                "template_id": str(uuid4()),
                "name": "Test Schedule",
                "frequency": "daily",
                "format": "pdf",
                "recipient_emails": ["user@example.com"],
                "start_date": str(date.today())
            }
        )

        # Should get an error (either 400 validation or 404 not found)
        assert response.status_code in [400, 404]

    def test_list_schedules(self, client, org_id, template_id):
        """Test listing schedules."""
        # Create schedule
        client.post(
            f"/api/reports/orgs/{org_id}/schedules",
            json={
                "template_id": template_id,
                "name": "Test Schedule",
                "frequency": "daily",
                "format": "pdf",
                "recipient_emails": ["user@example.com"],
                "start_date": str(date.today())
            }
        )

        # List schedules
        response = client.get(f"/api/reports/orgs/{org_id}/schedules")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(s["name"] == "Test Schedule" for s in data)

    def test_get_schedule(self, client, org_id, template_id):
        """Test retrieving a specific schedule."""
        # Create schedule
        create_response = client.post(
            f"/api/reports/orgs/{org_id}/schedules",
            json={
                "template_id": template_id,
                "name": "Weekly Report",
                "frequency": "weekly",
                "format": "excel",
                "recipient_emails": ["user@example.com"],
                "start_date": str(date.today())
            }
        )
        schedule_id = create_response.json()["id"]

        # Get schedule
        response = client.get(
            f"/api/reports/orgs/{org_id}/schedules/{schedule_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Weekly Report"
        assert data["frequency"] == "weekly"

    def test_pause_schedule(self, client, org_id, template_id):
        """Test pausing a schedule."""
        # Create schedule
        create_response = client.post(
            f"/api/reports/orgs/{org_id}/schedules",
            json={
                "template_id": template_id,
                "name": "Test Schedule",
                "frequency": "daily",
                "format": "pdf",
                "recipient_emails": ["user@example.com"],
                "start_date": str(date.today())
            }
        )
        schedule_id = create_response.json()["id"]

        # Pause schedule
        response = client.post(
            f"/api/reports/orgs/{org_id}/schedules/{schedule_id}/pause"
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify paused
        get_response = client.get(
            f"/api/reports/orgs/{org_id}/schedules/{schedule_id}"
        )
        assert get_response.json()["is_active"] is False

    def test_resume_schedule(self, client, org_id, template_id):
        """Test resuming a paused schedule."""
        # Create and pause schedule
        create_response = client.post(
            f"/api/reports/orgs/{org_id}/schedules",
            json={
                "template_id": template_id,
                "name": "Test Schedule",
                "frequency": "daily",
                "format": "pdf",
                "recipient_emails": ["user@example.com"],
                "start_date": str(date.today())
            }
        )
        schedule_id = create_response.json()["id"]

        client.post(
            f"/api/reports/orgs/{org_id}/schedules/{schedule_id}/pause"
        )

        # Resume schedule
        response = client.post(
            f"/api/reports/orgs/{org_id}/schedules/{schedule_id}/resume"
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify resumed
        get_response = client.get(
            f"/api/reports/orgs/{org_id}/schedules/{schedule_id}"
        )
        assert get_response.json()["is_active"] is True

    def test_delete_schedule(self, client, org_id, template_id):
        """Test deleting a schedule."""
        # Create schedule
        create_response = client.post(
            f"/api/reports/orgs/{org_id}/schedules",
            json={
                "template_id": template_id,
                "name": "Test Schedule",
                "frequency": "daily",
                "format": "pdf",
                "recipient_emails": ["user@example.com"],
                "start_date": str(date.today())
            }
        )
        schedule_id = create_response.json()["id"]

        # Delete schedule
        response = client.delete(
            f"/api/reports/orgs/{org_id}/schedules/{schedule_id}"
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify deleted
        get_response = client.get(
            f"/api/reports/orgs/{org_id}/schedules/{schedule_id}"
        )
        assert get_response.status_code == 404


class TestReportGenerationAPI:
    """Tests for report generation endpoints."""

    @pytest.fixture
    def template_id(self, client, org_id):
        """Create a template for testing."""
        response = client.post(
            f"/api/reports/orgs/{org_id}/templates",
            json={
                "name": "Test Template",
                "template_type": "profit_loss"
            }
        )
        return response.json()["id"]

    def test_generate_pdf_report(self, client, org_id, template_id):
        """Test generating a PDF report."""
        response = client.post(
            f"/api/reports/orgs/{org_id}/generate",
            json={
                "template_id": template_id,
                "period_start": str(date(2024, 1, 1)),
                "period_end": str(date(2024, 1, 31)),
                "report_format": "pdf"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "profit_loss"
        assert data["format"] == "pdf"
        assert data["status"] == "generated"
        assert data["file_size"] > 0

    def test_generate_excel_report(self, client, org_id, template_id):
        """Test generating an Excel report."""
        response = client.post(
            f"/api/reports/orgs/{org_id}/generate",
            json={
                "template_id": template_id,
                "period_start": str(date(2024, 1, 1)),
                "period_end": str(date(2024, 1, 31)),
                "report_format": "excel"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "excel"
        assert data["file_size"] > 0

    def test_generate_report_different_period(self, client, org_id, template_id):
        """Test generating a report for different period."""
        response = client.post(
            f"/api/reports/orgs/{org_id}/generate",
            json={
                "template_id": template_id,
                "period_start": str(date(2024, 6, 1)),
                "period_end": str(date(2024, 6, 30)),
                "report_format": "pdf"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["period_start"] == "2024-06-01"
        assert data["period_end"] == "2024-06-30"
        assert data["file_size"] > 0

    def test_list_reports(self, client, org_id, template_id):
        """Test listing generated reports."""
        # Generate report
        client.post(
            f"/api/reports/orgs/{org_id}/generate",
            json={
                "template_id": template_id,
                "period_start": str(date(2024, 1, 1)),
                "period_end": str(date(2024, 1, 31))
            }
        )

        # List reports
        response = client.get(f"/api/reports/orgs/{org_id}/reports")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestReportDistributionAPI:
    """Tests for report distribution endpoints."""

    @pytest.fixture
    def template_id(self, client, org_id):
        """Create a template for testing."""
        response = client.post(
            f"/api/reports/orgs/{org_id}/templates",
            json={
                "name": "Test Template",
                "template_type": "balance_sheet"
            }
        )
        return response.json()["id"]

    @pytest.fixture
    def report_id(self, client, org_id, template_id):
        """Generate a report for testing."""
        response = client.post(
            f"/api/reports/orgs/{org_id}/generate",
            json={
                "template_id": template_id,
                "period_start": str(date(2024, 1, 1)),
                "period_end": str(date(2024, 1, 31))
            }
        )
        return response.json()["id"]

    def test_send_report(self, client, org_id, report_id):
        """Test sending a report."""
        response = client.post(
            f"/api/reports/orgs/{org_id}/send",
            json={
                "report_id": report_id,
                "recipient_emails": ["user@example.com"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["sent"] == 1

    def test_send_report_multiple_recipients(self, client, org_id, report_id):
        """Test sending report to multiple recipients."""
        recipients = [
            "user1@example.com",
            "user2@example.com",
            "user3@example.com"
        ]

        response = client.post(
            f"/api/reports/orgs/{org_id}/send",
            json={
                "report_id": report_id,
                "recipient_emails": recipients
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["sent"] == 3
        assert data["total"] == 3

    def test_list_distributions(self, client, org_id, report_id):
        """Test listing report distributions."""
        # Send report
        client.post(
            f"/api/reports/orgs/{org_id}/send",
            json={
                "report_id": report_id,
                "recipient_emails": ["user@example.com"]
            }
        )

        # List distributions
        response = client.get(
            f"/api/reports/orgs/{org_id}/distributions",
            params={"report_id": str(report_id)}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(d["recipient_email"] == "user@example.com" for d in data)


class TestReportAPIIntegration:
    """End-to-end integration tests."""

    def test_complete_report_workflow(self, client, org_id):
        """Test complete report workflow: create template, schedule, generate, send."""
        # 1. Create template
        template_response = client.post(
            f"/api/reports/orgs/{org_id}/templates",
            json={
                "name": "Monthly P&L",
                "template_type": "profit_loss"
            }
        )
        assert template_response.status_code == 200
        template_id = template_response.json()["id"]

        # 2. Create schedule
        schedule_response = client.post(
            f"/api/reports/orgs/{org_id}/schedules",
            json={
                "template_id": template_id,
                "name": "Daily P&L",
                "frequency": "daily",
                "format": "pdf",
                "recipient_emails": ["manager@example.com"],
                "start_date": str(date.today())
            }
        )
        assert schedule_response.status_code == 200
        schedule_id = schedule_response.json()["id"]

        # 3. Generate report
        generate_response = client.post(
            f"/api/reports/orgs/{org_id}/generate",
            json={
                "template_id": template_id,
                "period_start": str(date(2024, 1, 1)),
                "period_end": str(date(2024, 1, 31))
            }
        )
        assert generate_response.status_code == 200
        report_id = generate_response.json()["id"]

        # 4. Send report
        send_response = client.post(
            f"/api/reports/orgs/{org_id}/send",
            json={
                "report_id": report_id,
                "recipient_emails": ["manager@example.com"]
            }
        )
        assert send_response.status_code == 200
        assert send_response.json()["success"] is True

        # 5. Verify schedule can be paused
        pause_response = client.post(
            f"/api/reports/orgs/{org_id}/schedules/{schedule_id}/pause"
        )
        assert pause_response.status_code == 200

    def test_multiple_templates_and_schedules(self, client, org_id):
        """Test creating multiple templates and schedules."""
        # Create 3 templates
        template_ids = []
        for i in range(3):
            response = client.post(
                f"/api/reports/orgs/{org_id}/templates",
                json={
                    "name": f"Template {i+1}",
                    "template_type": ["profit_loss", "balance_sheet", "cash_flow"][i]
                }
            )
            template_ids.append(response.json()["id"])

        # Create schedules for each
        for i, template_id in enumerate(template_ids):
            response = client.post(
                f"/api/reports/orgs/{org_id}/schedules",
                json={
                    "template_id": template_id,
                    "name": f"Schedule {i+1}",
                    "frequency": ["daily", "weekly", "monthly"][i],
                    "format": "pdf",
                    "recipient_emails": ["user@example.com"],
                    "start_date": str(date.today())
                }
            )
            assert response.status_code == 200

        # Verify all templates listed
        templates_response = client.get(f"/api/reports/orgs/{org_id}/templates")
        assert len(templates_response.json()) >= 3

        # Verify all schedules listed
        schedules_response = client.get(f"/api/reports/orgs/{org_id}/schedules")
        assert len(schedules_response.json()) >= 3
