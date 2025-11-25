"""Tax compliance reporting service.

Manages compliance requirements, checklists, and reporting for organizations.
"""

from uuid import UUID
from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict

from backend.models.tax import TaxLiability, TaxComplianceLog, TaxPeriod


class ComplianceChecklistItem:
    """Represents a compliance checklist item."""

    def __init__(
        self,
        item_id: str,
        description: str,
        due_date: date,
        is_completed: bool = False,
        notes: Optional[str] = None
    ):
        """Initialize checklist item."""
        self.item_id = item_id
        self.description = description
        self.due_date = due_date
        self.is_completed = is_completed
        self.notes = notes


class TaxComplianceReporter:
    """Manages tax compliance reporting for organizations."""

    def __init__(self):
        """Initialize compliance reporter."""
        self.checklists = {}  # (org_id, period, year) -> List[ComplianceChecklistItem]
        self.compliance_logs = {}  # (org_id,) -> List[TaxComplianceLog]

    def create_compliance_checklist(
        self,
        organization_id: UUID,
        period: TaxPeriod,
        tax_year: int,
        items: List[Dict[str, any]]
    ) -> List[ComplianceChecklistItem]:
        """Create a compliance checklist for a period.

        Args:
            organization_id: Organization UUID
            period: Tax period
            tax_year: Tax year
            items: List of dicts with 'item_id', 'description', 'due_date', 'notes'

        Returns:
            List of created ComplianceChecklistItem objects

        Raises:
            ValueError: If checklist already exists
        """
        key = (organization_id, period, tax_year)
        if key in self.checklists:
            raise ValueError(f"Checklist already exists for {period.value} {tax_year}")

        checklist_items = [
            ComplianceChecklistItem(
                item_id=item.get("item_id"),
                description=item.get("description"),
                due_date=item.get("due_date"),
                notes=item.get("notes")
            )
            for item in items
        ]

        self.checklists[key] = checklist_items
        return checklist_items

    def get_compliance_checklist(
        self,
        organization_id: UUID,
        period: TaxPeriod,
        tax_year: int
    ) -> Optional[List[ComplianceChecklistItem]]:
        """Get compliance checklist for a period.

        Args:
            organization_id: Organization UUID
            period: Tax period
            tax_year: Tax year

        Returns:
            List of checklist items or None if not found
        """
        key = (organization_id, period, tax_year)
        return self.checklists.get(key)

    def mark_checklist_item_complete(
        self,
        organization_id: UUID,
        period: TaxPeriod,
        tax_year: int,
        item_id: str,
        notes: Optional[str] = None
    ) -> Optional[ComplianceChecklistItem]:
        """Mark a checklist item as complete.

        Args:
            organization_id: Organization UUID
            period: Tax period
            tax_year: Tax year
            item_id: Item ID
            notes: Optional completion notes

        Returns:
            Updated ComplianceChecklistItem or None if not found
        """
        checklist = self.get_compliance_checklist(organization_id, period, tax_year)
        if not checklist:
            return None

        for item in checklist:
            if item.item_id == item_id:
                item.is_completed = True
                if notes:
                    item.notes = notes
                return item

        return None

    def get_checklist_completion_status(
        self,
        organization_id: UUID,
        period: TaxPeriod,
        tax_year: int
    ) -> Dict[str, any]:
        """Get completion status for a checklist.

        Args:
            organization_id: Organization UUID
            period: Tax period
            tax_year: Tax year

        Returns:
            Dict with total_items, completed_items, completion_percentage, items list
        """
        checklist = self.get_compliance_checklist(organization_id, period, tax_year)
        if not checklist:
            return {
                "total_items": 0,
                "completed_items": 0,
                "completion_percentage": 0,
                "items": []
            }

        completed = sum(1 for item in checklist if item.is_completed)
        total = len(checklist)
        percentage = (completed / total * 100) if total > 0 else 0

        return {
            "total_items": total,
            "completed_items": completed,
            "completion_percentage": percentage,
            "items": [
                {
                    "item_id": item.item_id,
                    "description": item.description,
                    "is_completed": item.is_completed,
                    "due_date": item.due_date
                }
                for item in checklist
            ]
        }

    def get_overdue_compliance_items(
        self,
        organization_id: UUID
    ) -> List[ComplianceChecklistItem]:
        """Get all overdue compliance items.

        Args:
            organization_id: Organization UUID

        Returns:
            List of overdue incomplete items
        """
        today = date.today()
        overdue_items = []

        for (org_id, _, _), checklist in self.checklists.items():
            if org_id == organization_id:
                for item in checklist:
                    if not item.is_completed and item.due_date < today:
                        overdue_items.append(item)

        return sorted(overdue_items, key=lambda i: i.due_date)

    def get_upcoming_compliance_items(
        self,
        organization_id: UUID,
        days: int = 30
    ) -> List[ComplianceChecklistItem]:
        """Get upcoming compliance items due within specified days.

        Args:
            organization_id: Organization UUID
            days: Days to look ahead (default 30)

        Returns:
            List of upcoming items
        """
        from datetime import timedelta

        today = date.today()
        upcoming_date = today + timedelta(days=days)
        upcoming_items = []

        for (org_id, _, _), checklist in self.checklists.items():
            if org_id == organization_id:
                for item in checklist:
                    if (not item.is_completed and
                        today <= item.due_date <= upcoming_date):
                        upcoming_items.append(item)

        return sorted(upcoming_items, key=lambda i: i.due_date)

    def generate_compliance_report(
        self,
        organization_id: UUID,
        period: TaxPeriod,
        tax_year: int
    ) -> Dict[str, any]:
        """Generate a compliance report for a period.

        Args:
            organization_id: Organization UUID
            period: Tax period
            tax_year: Tax year

        Returns:
            Compliance report with status, checklist, and findings
        """
        checklist_status = self.get_checklist_completion_status(
            organization_id, period, tax_year
        )
        overdue_items = self.get_overdue_compliance_items(organization_id)

        return {
            "organization_id": str(organization_id),
            "period": period.value,
            "tax_year": tax_year,
            "report_date": date.today().isoformat(),
            "checklist_status": checklist_status,
            "overdue_items_count": len([i for i in overdue_items if i.due_date < date.today()]),
            "is_compliant": checklist_status["completion_percentage"] == 100,
            "summary": self._generate_summary(checklist_status, overdue_items)
        }

    def _generate_summary(
        self,
        checklist_status: Dict[str, any],
        overdue_items: List[ComplianceChecklistItem]
    ) -> str:
        """Generate a summary text for the compliance report."""
        completion = checklist_status["completion_percentage"]

        if completion == 100:
            summary = "All compliance requirements have been met."
        elif completion >= 75:
            summary = "Most compliance requirements are complete. Review remaining items."
        elif completion >= 50:
            summary = "Approximately half of compliance requirements are complete. Action needed."
        else:
            summary = "Significant compliance work remains. Immediate action required."

        if overdue_items:
            summary += f" WARNING: {len(overdue_items)} items are overdue."

        return summary

    def get_annual_compliance_summary(
        self,
        organization_id: UUID,
        tax_year: int
    ) -> Dict[str, any]:
        """Get annual compliance summary across all periods.

        Args:
            organization_id: Organization UUID
            tax_year: Tax year

        Returns:
            Summary with per-period status
        """
        periods_summary = {}

        for period in [TaxPeriod.Q1, TaxPeriod.Q2, TaxPeriod.Q3, TaxPeriod.Q4, TaxPeriod.MONTHLY, TaxPeriod.ANNUAL]:
            status = self.get_checklist_completion_status(
                organization_id, period, tax_year
            )
            if status["total_items"] > 0:
                periods_summary[period.value] = {
                    "completion_percentage": status["completion_percentage"],
                    "total_items": status["total_items"],
                    "completed_items": status["completed_items"]
                }

        # Calculate overall compliance
        total_items = sum(p["total_items"] for p in periods_summary.values())
        total_completed = sum(p["completed_items"] for p in periods_summary.values())
        overall_percentage = (total_completed / total_items * 100) if total_items > 0 else 0

        return {
            "organization_id": str(organization_id),
            "tax_year": tax_year,
            "overall_completion_percentage": overall_percentage,
            "periods": periods_summary,
            "is_fully_compliant": overall_percentage == 100
        }

    def get_compliance_calendar(
        self,
        organization_id: UUID,
        tax_year: int
    ) -> List[Dict[str, any]]:
        """Get compliance calendar for the year.

        Args:
            organization_id: Organization UUID
            tax_year: Tax year

        Returns:
            Sorted list of compliance events by date
        """
        events = []

        for (org_id, period, year), checklist in self.checklists.items():
            if org_id == organization_id and year == tax_year:
                for item in checklist:
                    events.append({
                        "date": item.due_date.isoformat(),
                        "period": period.value,
                        "item_id": item.item_id,
                        "description": item.description,
                        "is_completed": item.is_completed
                    })

        return sorted(events, key=lambda e: e["date"])

    def log_compliance_event(
        self,
        organization_id: UUID,
        event_type: str,
        description: str
    ) -> TaxComplianceLog:
        """Log a compliance event.

        Args:
            organization_id: Organization UUID
            event_type: Type of event
            description: Event description

        Returns:
            Created TaxComplianceLog object
        """
        log = TaxComplianceLog(
            organization_id=organization_id,
            event_type=event_type,
            event_metadata={"description": description},
            affected_entity_type="organization",
            affected_entity_id=str(organization_id)
        )

        key = organization_id
        if key not in self.compliance_logs:
            self.compliance_logs[key] = []

        self.compliance_logs[key].append(log)
        return log

    def get_compliance_event_log(
        self,
        organization_id: UUID,
        limit: int = 50
    ) -> List[TaxComplianceLog]:
        """Get compliance event log for organization.

        Args:
            organization_id: Organization UUID
            limit: Maximum number of events to return

        Returns:
            List of TaxComplianceLog objects, most recent first
        """
        logs = self.compliance_logs.get(organization_id, [])
        return sorted(logs, key=lambda l: l.created_at, reverse=True)[:limit]
