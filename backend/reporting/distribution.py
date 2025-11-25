"""Report distribution service for email delivery.

Handles report email scheduling and delivery tracking.
"""

from datetime import datetime, timezone, timedelta, date
from typing import List, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class EmailDistributionService:
    """Manages report email distribution."""

    def __init__(self):
        """Initialize distribution service."""
        self.deliveries: dict = {}  # In-memory tracking

    def send_report(
        self,
        recipient_email: str,
        report_id: UUID,
        title: str,
        file_bytes: bytes,
        file_extension: str = "pdf",
        subject_template: str = "Financial Report"
    ) -> bool:
        """
        Send report via email.

        Args:
            recipient_email: Recipient email address
            report_id: Report ID
            title: Report title
            file_bytes: Report file content
            file_extension: File extension (pdf, xlsx, csv)
            subject_template: Email subject template

        Returns:
            Success status
        """
        try:
            # In production, use actual email service (SendGrid, SES, etc)
            # For now, log the delivery intent
            subject = subject_template
            filename = f"{title}.{file_extension}"

            delivery_record = {
                "report_id": str(report_id),
                "recipient": recipient_email,
                "subject": subject,
                "filename": filename,
                "file_size": len(file_bytes),
                "sent_at": datetime.now(timezone.utc),
                "status": "sent"
            }

            self.deliveries[str(report_id)] = delivery_record
            logger.info(
                f"Report {report_id} delivered to {recipient_email} "
                f"({len(file_bytes)} bytes)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send report {report_id}: {str(e)}")
            return False

    def send_bulk(
        self,
        recipient_emails: List[str],
        report_id: UUID,
        title: str,
        file_bytes: bytes,
        file_extension: str = "pdf"
    ) -> dict:
        """
        Send report to multiple recipients.

        Args:
            recipient_emails: List of recipient emails
            report_id: Report ID
            title: Report title
            file_bytes: Report file content
            file_extension: File extension

        Returns:
            Delivery results {email: success_bool}
        """
        results = {}
        for email in recipient_emails:
            success = self.send_report(
                email, report_id, title, file_bytes, file_extension
            )
            results[email] = success

        sent_count = sum(1 for v in results.values() if v)
        logger.info(f"Report {report_id} sent to {sent_count}/{len(recipient_emails)} recipients")
        return results

    def get_delivery_status(self, report_id: UUID) -> Optional[dict]:
        """
        Get delivery status for a report.

        Args:
            report_id: Report ID

        Returns:
            Delivery record or None
        """
        return self.deliveries.get(str(report_id))

    def get_pending_deliveries(self) -> List[dict]:
        """
        Get reports pending delivery.

        Returns:
            List of pending delivery records
        """
        return [
            delivery for delivery in self.deliveries.values()
            if delivery.get("status") == "pending"
        ]

    def retry_failed(self, report_id: UUID, file_bytes: bytes) -> bool:
        """
        Retry delivery for failed report.

        Args:
            report_id: Report ID
            file_bytes: Report file content

        Returns:
            Success status
        """
        record = self.get_delivery_status(report_id)
        if not record:
            logger.warning(f"No delivery record found for {report_id}")
            return False

        try:
            success = self.send_report(
                record["recipient"],
                report_id,
                record["filename"],
                file_bytes
            )
            if success:
                record["status"] = "sent"
                record["retry_count"] = record.get("retry_count", 0) + 1
            return success

        except Exception as e:
            logger.error(f"Retry failed for {report_id}: {str(e)}")
            return False


class ReportScheduler:
    """Manages scheduled report generation."""

    def __init__(self):
        """Initialize scheduler."""
        self.schedules: dict = {}
        self.executions: dict = {}

    def create_schedule(
        self,
        schedule_id: UUID,
        organization_id: UUID,
        frequency: str,
        format: str,
        recipient_emails: List[str],
        start_date: date,
        hour_utc: int = 9
    ) -> dict:
        """
        Create report schedule.

        Args:
            schedule_id: Schedule ID
            organization_id: Organization ID
            frequency: "daily", "weekly", "monthly"
            format: "pdf", "excel", "json"
            recipient_emails: List of recipients
            start_date: Schedule start date
            hour_utc: UTC hour to run (0-23)

        Returns:
            Schedule record
        """
        schedule = {
            "id": str(schedule_id),
            "organization_id": str(organization_id),
            "frequency": frequency,
            "format": format,
            "recipient_emails": recipient_emails,
            "start_date": start_date,
            "hour_utc": hour_utc,
            "is_active": True,
            "last_run": None,
            "next_run": self._calculate_next_run(start_date, frequency, hour_utc),
            "created_at": datetime.now(timezone.utc)
        }
        self.schedules[str(schedule_id)] = schedule
        logger.info(f"Created schedule {schedule_id} ({frequency})")
        return schedule

    def get_schedule(self, schedule_id: UUID) -> Optional[dict]:
        """Get schedule by ID."""
        return self.schedules.get(str(schedule_id))

    def get_due_schedules(self) -> List[dict]:
        """Get schedules due for execution."""
        now = datetime.now(timezone.utc)
        return [
            s for s in self.schedules.values()
            if s["is_active"] and s["next_run"] and s["next_run"] <= now
        ]

    def mark_executed(self, schedule_id: UUID) -> bool:
        """
        Mark schedule as executed.

        Args:
            schedule_id: Schedule ID

        Returns:
            Success status
        """
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            return False

        schedule["last_run"] = datetime.now(timezone.utc)
        schedule["next_run"] = self._calculate_next_run(
            date.today(),
            schedule["frequency"],
            schedule["hour_utc"]
        )
        logger.info(f"Marked schedule {schedule_id} as executed")
        return True

    def pause_schedule(self, schedule_id: UUID) -> bool:
        """Pause a schedule."""
        schedule = self.get_schedule(schedule_id)
        if schedule:
            schedule["is_active"] = False
            logger.info(f"Paused schedule {schedule_id}")
            return True
        return False

    def resume_schedule(self, schedule_id: UUID) -> bool:
        """Resume a schedule."""
        schedule = self.get_schedule(schedule_id)
        if schedule:
            schedule["is_active"] = True
            logger.info(f"Resumed schedule {schedule_id}")
            return True
        return False

    def delete_schedule(self, schedule_id: UUID) -> bool:
        """Delete a schedule."""
        if str(schedule_id) in self.schedules:
            del self.schedules[str(schedule_id)]
            logger.info(f"Deleted schedule {schedule_id}")
            return True
        return False

    def _calculate_next_run(self, start_date: date, frequency: str, hour_utc: int) -> datetime:
        """Calculate next run time based on frequency."""
        now = datetime.now(timezone.utc)
        base_time = datetime.combine(
            start_date,
            datetime.min.time().replace(hour=hour_utc),
            tzinfo=timezone.utc
        )

        if frequency == "daily":
            next_run = base_time
            while next_run <= now:
                next_run += timedelta(days=1)
        elif frequency == "weekly":
            next_run = base_time
            while next_run <= now:
                next_run += timedelta(weeks=1)
        elif frequency == "monthly":
            next_run = base_time
            while next_run <= now:
                try:
                    next_run = next_run.replace(month=next_run.month + 1)
                except ValueError:
                    next_run = next_run.replace(month=12, year=next_run.year + 1)
        else:
            next_run = base_time

        return next_run
