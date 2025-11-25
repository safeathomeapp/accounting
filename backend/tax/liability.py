"""Tax liability management service.

Manages tax liabilities, payments, and liability tracking for organizations.
"""

from uuid import UUID
from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict

from backend.models.tax import TaxLiability, TaxPeriod, TaxLiabilityStatus


class TaxLiabilityManager:
    """Manages tax liabilities for organizations."""

    def __init__(self):
        """Initialize liability manager."""
        self.liabilities = {}  # In-memory storage: (org_id, tax_type_id, period, year) -> TaxLiability

    def create_liability(
        self,
        organization_id: UUID,
        tax_type_id: UUID,
        period: TaxPeriod,
        tax_year: int,
        calculated_amount: Decimal,
        due_date: date
    ) -> TaxLiability:
        """Create a new tax liability.

        Args:
            organization_id: Organization UUID
            tax_type_id: Tax type UUID
            period: Tax period (monthly, quarterly, annual, etc.)
            tax_year: Tax year
            calculated_amount: Calculated tax amount
            due_date: Due date for payment

        Returns:
            Created TaxLiability object

        Raises:
            ValueError: If liability already exists or inputs invalid
        """
        if calculated_amount < 0:
            raise ValueError("Calculated amount cannot be negative")

        # Check if liability already exists
        key = (organization_id, tax_type_id, period, tax_year)
        if key in self.liabilities:
            raise ValueError(f"Liability already exists for {period.value} {tax_year}")

        # Create liability
        liability = TaxLiability(
            organization_id=organization_id,
            tax_type_id=tax_type_id,
            calculated_amount=calculated_amount,
            paid_amount=Decimal("0"),
            balance=calculated_amount,
            due_date=due_date,
            status=TaxLiabilityStatus.PENDING,
            period=period,
            tax_year=tax_year
        )

        # Store it
        self.liabilities[key] = liability

        return liability

    def get_liability(
        self,
        organization_id: UUID,
        tax_type_id: UUID,
        period: TaxPeriod,
        tax_year: int
    ) -> Optional[TaxLiability]:
        """Get a tax liability.

        Args:
            organization_id: Organization UUID
            tax_type_id: Tax type UUID
            period: Tax period
            tax_year: Tax year

        Returns:
            TaxLiability object or None if not found
        """
        key = (organization_id, tax_type_id, period, tax_year)
        return self.liabilities.get(key)

    def get_organization_liabilities(
        self,
        organization_id: UUID,
        tax_year: Optional[int] = None,
        status: Optional[TaxLiabilityStatus] = None
    ) -> List[TaxLiability]:
        """Get all liabilities for an organization.

        Args:
            organization_id: Organization UUID
            tax_year: Filter by tax year (optional)
            status: Filter by status (optional)

        Returns:
            List of TaxLiability objects
        """
        liabilities = [
            liability for (org_id, _, _, year), liability in self.liabilities.items()
            if org_id == organization_id
            and (tax_year is None or year == tax_year)
            and (status is None or liability.status == status)
        ]

        return sorted(liabilities, key=lambda l: l.due_date)

    def record_payment(
        self,
        organization_id: UUID,
        tax_type_id: UUID,
        period: TaxPeriod,
        tax_year: int,
        payment_amount: Decimal
    ) -> TaxLiability:
        """Record a payment for a tax liability.

        Args:
            organization_id: Organization UUID
            tax_type_id: Tax type UUID
            period: Tax period
            tax_year: Tax year
            payment_amount: Payment amount

        Returns:
            Updated TaxLiability object

        Raises:
            ValueError: If liability not found or payment invalid
        """
        if payment_amount <= 0:
            raise ValueError("Payment amount must be positive")

        liability = self.get_liability(organization_id, tax_type_id, period, tax_year)
        if not liability:
            raise ValueError(f"Liability not found for {period.value} {tax_year}")

        # Update amounts
        liability.paid_amount += payment_amount
        liability.balance = max(liability.calculated_amount - liability.paid_amount, Decimal("0"))

        # Update status
        if liability.balance == 0:
            liability.status = TaxLiabilityStatus.PAID
        elif date.today() > liability.due_date and liability.balance > 0:
            liability.status = TaxLiabilityStatus.OVERDUE
        else:
            liability.status = TaxLiabilityStatus.PENDING

        return liability

    def get_quarterly_liability(
        self,
        organization_id: UUID,
        tax_type_id: UUID,
        tax_year: int,
        quarter: int
    ) -> Optional[TaxLiability]:
        """Get quarterly liability for a specific quarter.

        Args:
            organization_id: Organization UUID
            tax_type_id: Tax type UUID
            tax_year: Tax year
            quarter: Quarter number (1-4)

        Returns:
            TaxLiability object or None if not found

        Raises:
            ValueError: If quarter invalid
        """
        if quarter < 1 or quarter > 4:
            raise ValueError("Quarter must be between 1 and 4")

        # Map quarter number to TaxPeriod enum
        quarter_map = {
            1: TaxPeriod.Q1,
            2: TaxPeriod.Q2,
            3: TaxPeriod.Q3,
            4: TaxPeriod.Q4
        }

        return self.get_liability(
            organization_id, tax_type_id, quarter_map[quarter], tax_year
        )

    def get_annual_liability(
        self,
        organization_id: UUID,
        tax_type_id: UUID,
        tax_year: int
    ) -> Optional[TaxLiability]:
        """Get annual liability for a specific year.

        Args:
            organization_id: Organization UUID
            tax_type_id: Tax type UUID
            tax_year: Tax year

        Returns:
            TaxLiability object or None if not found
        """
        return self.get_liability(
            organization_id, tax_type_id, TaxPeriod.ANNUAL, tax_year
        )

    def calculate_balance(
        self,
        organization_id: UUID,
        tax_type_id: UUID,
        period: TaxPeriod,
        tax_year: int
    ) -> Decimal:
        """Calculate current balance for a liability.

        Args:
            organization_id: Organization UUID
            tax_type_id: Tax type UUID
            period: Tax period
            tax_year: Tax year

        Returns:
            Current balance

        Raises:
            ValueError: If liability not found
        """
        liability = self.get_liability(organization_id, tax_type_id, period, tax_year)
        if not liability:
            raise ValueError(f"Liability not found for {period.value} {tax_year}")

        return liability.balance

    def get_overdue_liabilities(
        self,
        organization_id: UUID
    ) -> List[TaxLiability]:
        """Get all overdue liabilities for an organization.

        Args:
            organization_id: Organization UUID

        Returns:
            List of overdue TaxLiability objects
        """
        today = date.today()
        liabilities = [
            liability for (org_id, _, _, _), liability in self.liabilities.items()
            if org_id == organization_id
            and liability.due_date < today
            and liability.balance > 0
        ]

        return sorted(liabilities, key=lambda l: l.due_date)

    def get_upcoming_liabilities(
        self,
        organization_id: UUID,
        days: int = 30
    ) -> List[TaxLiability]:
        """Get upcoming liabilities due within specified days.

        Args:
            organization_id: Organization UUID
            days: Number of days to look ahead (default 30)

        Returns:
            List of upcoming TaxLiability objects
        """
        from datetime import timedelta

        today = date.today()
        upcoming_date = today + timedelta(days=days)

        liabilities = [
            liability for (org_id, _, _, _), liability in self.liabilities.items()
            if org_id == organization_id
            and today <= liability.due_date <= upcoming_date
            and liability.balance > 0
        ]

        return sorted(liabilities, key=lambda l: l.due_date)

    def update_liability_status(
        self,
        organization_id: UUID,
        tax_type_id: UUID,
        period: TaxPeriod,
        tax_year: int,
        status: TaxLiabilityStatus
    ) -> TaxLiability:
        """Update the status of a liability.

        Args:
            organization_id: Organization UUID
            tax_type_id: Tax type UUID
            period: Tax period
            tax_year: Tax year
            status: New status

        Returns:
            Updated TaxLiability object

        Raises:
            ValueError: If liability not found
        """
        liability = self.get_liability(organization_id, tax_type_id, period, tax_year)
        if not liability:
            raise ValueError(f"Liability not found for {period.value} {tax_year}")

        liability.status = status
        return liability

    def get_liability_summary(
        self,
        organization_id: UUID,
        tax_year: int
    ) -> Dict[str, Decimal]:
        """Get summary of liabilities for a tax year.

        Args:
            organization_id: Organization UUID
            tax_year: Tax year

        Returns:
            Dict with total_calculated, total_paid, total_balance
        """
        liabilities = self.get_organization_liabilities(
            organization_id, tax_year=tax_year
        )

        total_calculated = sum(
            (l.calculated_amount for l in liabilities),
            Decimal("0")
        )
        total_paid = sum(
            (l.paid_amount for l in liabilities),
            Decimal("0")
        )
        total_balance = sum(
            (l.balance for l in liabilities),
            Decimal("0")
        )

        return {
            "total_calculated": total_calculated,
            "total_paid": total_paid,
            "total_balance": total_balance
        }
