"""Tests for tax compliance reporting service.

Tests for TaxComplianceReporter including checklists, reporting,
and compliance tracking.
"""

import pytest
from uuid import uuid4
from datetime import date, timedelta

from backend.tax.compliance import TaxComplianceReporter, ComplianceChecklistItem
from backend.models.tax import TaxPeriod


class TestTaxComplianceReporter:
    """Tests for TaxComplianceReporter."""

    def setup_method(self):
        """Set up for each test."""
        self.reporter = TaxComplianceReporter()
        self.org_id = uuid4()

    def test_create_compliance_checklist(self):
        """Test creating a compliance checklist."""
        items = [
            {
                "item_id": "item1",
                "description": "File quarterly tax return",
                "due_date": date(2025, 4, 15),
                "notes": "Q1 filing"
            },
            {
                "item_id": "item2",
                "description": "Pay quarterly tax",
                "due_date": date(2025, 4, 20),
                "notes": None
            }
        ]

        checklist = self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )

        assert len(checklist) == 2
        assert checklist[0].item_id == "item1"
        assert checklist[0].description == "File quarterly tax return"
        assert checklist[0].is_completed is False

    def test_get_compliance_checklist(self):
        """Test retrieving a checklist."""
        items = [
            {
                "item_id": "item1",
                "description": "File return",
                "due_date": date(2025, 4, 15)
            }
        ]

        self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )

        retrieved = self.reporter.get_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025
        )

        assert retrieved is not None
        assert len(retrieved) == 1
        assert retrieved[0].item_id == "item1"

    def test_get_compliance_checklist_not_found(self):
        """Test retrieving non-existent checklist."""
        retrieved = self.reporter.get_compliance_checklist(
            self.org_id, TaxPeriod.Q2, 2025
        )

        assert retrieved is None

    def test_create_duplicate_checklist(self):
        """Test creating duplicate checklist raises error."""
        items = [
            {
                "item_id": "item1",
                "description": "File return",
                "due_date": date(2025, 4, 15)
            }
        ]

        self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )

        with pytest.raises(ValueError, match="already exists"):
            self.reporter.create_compliance_checklist(
                self.org_id, TaxPeriod.Q1, 2025, items
            )

    def test_mark_checklist_item_complete(self):
        """Test marking a checklist item as complete."""
        items = [
            {
                "item_id": "item1",
                "description": "File return",
                "due_date": date(2025, 4, 15)
            }
        ]

        self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )

        item = self.reporter.mark_checklist_item_complete(
            self.org_id, TaxPeriod.Q1, 2025, "item1",
            notes="Completed on time"
        )

        assert item is not None
        assert item.is_completed is True
        assert item.notes == "Completed on time"

    def test_get_checklist_completion_status(self):
        """Test getting checklist completion status."""
        items = [
            {
                "item_id": "item1",
                "description": "File return",
                "due_date": date(2025, 4, 15)
            },
            {
                "item_id": "item2",
                "description": "Pay tax",
                "due_date": date(2025, 4, 20)
            }
        ]

        self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )

        # Complete one item
        self.reporter.mark_checklist_item_complete(
            self.org_id, TaxPeriod.Q1, 2025, "item1"
        )

        status = self.reporter.get_checklist_completion_status(
            self.org_id, TaxPeriod.Q1, 2025
        )

        assert status["total_items"] == 2
        assert status["completed_items"] == 1
        assert status["completion_percentage"] == 50

    def test_get_checklist_completion_status_100_percent(self):
        """Test completion status when all items complete."""
        items = [
            {
                "item_id": "item1",
                "description": "File return",
                "due_date": date(2025, 4, 15)
            }
        ]

        self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )

        self.reporter.mark_checklist_item_complete(
            self.org_id, TaxPeriod.Q1, 2025, "item1"
        )

        status = self.reporter.get_checklist_completion_status(
            self.org_id, TaxPeriod.Q1, 2025
        )

        assert status["completion_percentage"] == 100

    def test_get_overdue_compliance_items(self):
        """Test getting overdue compliance items."""
        past_due = date.today() - timedelta(days=10)
        upcoming = date.today() + timedelta(days=15)

        items = [
            {
                "item_id": "item1",
                "description": "Overdue filing",
                "due_date": past_due
            },
            {
                "item_id": "item2",
                "description": "Upcoming filing",
                "due_date": upcoming
            }
        ]

        self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )

        overdue = self.reporter.get_overdue_compliance_items(self.org_id)

        assert len(overdue) == 1
        assert overdue[0].item_id == "item1"

    def test_get_overdue_completed_items_excluded(self):
        """Test that completed items are not in overdue list."""
        past_due = date.today() - timedelta(days=10)

        items = [
            {
                "item_id": "item1",
                "description": "Past due but completed",
                "due_date": past_due
            }
        ]

        self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )

        # Mark as complete
        self.reporter.mark_checklist_item_complete(
            self.org_id, TaxPeriod.Q1, 2025, "item1"
        )

        overdue = self.reporter.get_overdue_compliance_items(self.org_id)

        assert len(overdue) == 0

    def test_get_upcoming_compliance_items(self):
        """Test getting upcoming compliance items within timeframe."""
        upcoming_soon = date.today() + timedelta(days=10)
        far_future = date.today() + timedelta(days=60)

        items = [
            {
                "item_id": "item1",
                "description": "Upcoming filing",
                "due_date": upcoming_soon
            },
            {
                "item_id": "item2",
                "description": "Far future filing",
                "due_date": far_future
            }
        ]

        self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )

        upcoming = self.reporter.get_upcoming_compliance_items(
            self.org_id, days=30
        )

        assert len(upcoming) == 1
        assert upcoming[0].item_id == "item1"

    def test_generate_compliance_report(self):
        """Test generating a compliance report."""
        items = [
            {
                "item_id": "item1",
                "description": "File return",
                "due_date": date(2025, 4, 15)
            },
            {
                "item_id": "item2",
                "description": "Pay tax",
                "due_date": date(2025, 4, 20)
            }
        ]

        self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )

        # Complete one
        self.reporter.mark_checklist_item_complete(
            self.org_id, TaxPeriod.Q1, 2025, "item1"
        )

        report = self.reporter.generate_compliance_report(
            self.org_id, TaxPeriod.Q1, 2025
        )

        assert report["period"] == "Q1"
        assert report["tax_year"] == 2025
        assert report["is_compliant"] is False
        assert report["checklist_status"]["completion_percentage"] == 50

    def test_compliance_report_fully_compliant(self):
        """Test compliance report when all items complete."""
        items = [
            {
                "item_id": "item1",
                "description": "File return",
                "due_date": date(2025, 4, 15)
            }
        ]

        self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )

        self.reporter.mark_checklist_item_complete(
            self.org_id, TaxPeriod.Q1, 2025, "item1"
        )

        report = self.reporter.generate_compliance_report(
            self.org_id, TaxPeriod.Q1, 2025
        )

        assert report["is_compliant"] is True

    def test_get_annual_compliance_summary(self):
        """Test getting annual compliance summary."""
        # Create checklists for Q1 and Q2
        due_dates = {
            1: date(2025, 4, 15),   # Q1 due April 15
            2: date(2025, 7, 15)    # Q2 due July 15
        }

        for period, quarter in [(TaxPeriod.Q1, 1), (TaxPeriod.Q2, 2)]:
            items = [
                {
                    "item_id": f"item_{quarter}_1",
                    "description": f"Q{quarter} filing",
                    "due_date": due_dates[quarter]
                }
            ]

            self.reporter.create_compliance_checklist(
                self.org_id, period, 2025, items
            )

        # Complete Q1
        self.reporter.mark_checklist_item_complete(
            self.org_id, TaxPeriod.Q1, 2025, "item_1_1"
        )

        summary = self.reporter.get_annual_compliance_summary(
            self.org_id, 2025
        )

        assert summary["tax_year"] == 2025
        assert "Q1" in summary["periods"]
        assert "Q2" in summary["periods"]
        assert summary["periods"]["Q1"]["completion_percentage"] == 100
        assert summary["periods"]["Q2"]["completion_percentage"] == 0
        assert summary["is_fully_compliant"] is False

    def test_get_compliance_calendar(self):
        """Test getting compliance calendar."""
        items = [
            {
                "item_id": "item1",
                "description": "Q1 filing",
                "due_date": date(2025, 4, 15)
            },
            {
                "item_id": "item2",
                "description": "Q2 filing",
                "due_date": date(2025, 7, 15)
            }
        ]

        self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )

        calendar = self.reporter.get_compliance_calendar(
            self.org_id, 2025
        )

        assert len(calendar) == 2
        assert calendar[0]["date"] == "2025-04-15"
        assert calendar[1]["date"] == "2025-07-15"

    def test_log_compliance_event(self):
        """Test logging a compliance event."""
        log = self.reporter.log_compliance_event(
            self.org_id,
            "filing_completed",
            "Q1 tax return filed"
        )

        assert log is not None
        assert log.event_type == "filing_completed"
        assert log.event_metadata["description"] == "Q1 tax return filed"

    def test_get_compliance_event_log(self):
        """Test retrieving compliance event log."""
        self.reporter.log_compliance_event(
            self.org_id, "filing_completed", "Q1 filed"
        )
        self.reporter.log_compliance_event(
            self.org_id, "payment_made", "Q1 payment"
        )

        logs = self.reporter.get_compliance_event_log(self.org_id)

        assert len(logs) >= 2

    def test_checklist_item_not_found(self):
        """Test marking non-existent item returns None."""
        items = [
            {
                "item_id": "item1",
                "description": "Filing",
                "due_date": date(2025, 4, 15)
            }
        ]

        self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )

        result = self.reporter.mark_checklist_item_complete(
            self.org_id, TaxPeriod.Q1, 2025, "nonexistent"
        )

        assert result is None

    def test_empty_checklist_status(self):
        """Test status of non-existent checklist."""
        status = self.reporter.get_checklist_completion_status(
            self.org_id, TaxPeriod.Q1, 2025
        )

        assert status["total_items"] == 0
        assert status["completed_items"] == 0
        assert status["completion_percentage"] == 0

    def test_compliance_report_summary_logic(self):
        """Test compliance report summary text generation."""
        # Test fully compliant
        items_full = [{"item_id": "i1", "description": "Test", "due_date": date(2025, 4, 15)}]
        self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items_full
        )
        self.reporter.mark_checklist_item_complete(self.org_id, TaxPeriod.Q1, 2025, "i1")

        report = self.reporter.generate_compliance_report(
            self.org_id, TaxPeriod.Q1, 2025
        )

        assert "All compliance requirements" in report["summary"]

    def test_multiple_organizations_isolation(self):
        """Test compliance data is isolated between organizations."""
        other_org = uuid4()

        items = [
            {
                "item_id": "item1",
                "description": "Filing",
                "due_date": date(2025, 4, 15)
            }
        ]

        self.reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )
        self.reporter.create_compliance_checklist(
            other_org, TaxPeriod.Q2, 2025, items
        )

        org1_checklist = self.reporter.get_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025
        )
        org2_checklist = self.reporter.get_compliance_checklist(
            other_org, TaxPeriod.Q2, 2025
        )

        assert org1_checklist is not None
        assert org2_checklist is not None
        assert org1_checklist[0].item_id == org2_checklist[0].item_id  # Same item content
