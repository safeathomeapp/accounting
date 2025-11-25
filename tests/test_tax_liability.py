"""Tests for tax liability management service.

Tests for TaxLiabilityManager including CRUD operations, payment tracking,
and liability status management.
"""

import pytest
from uuid import uuid4
from datetime import date, timedelta
from decimal import Decimal

from backend.tax.liability import TaxLiabilityManager
from backend.models.tax import TaxPeriod, TaxLiabilityStatus


class TestTaxLiabilityManager:
    """Tests for TaxLiabilityManager."""

    def setup_method(self):
        """Set up for each test."""
        self.manager = TaxLiabilityManager()
        self.org_id = uuid4()
        self.tax_type_id = uuid4()
        self.due_date = date.today() + timedelta(days=90)  # Future date

    def test_create_liability(self):
        """Test creating a tax liability."""
        liability = self.manager.create_liability(
            organization_id=self.org_id,
            tax_type_id=self.tax_type_id,
            period=TaxPeriod.Q1,
            tax_year=2025,
            calculated_amount=Decimal("5000"),
            due_date=self.due_date
        )

        assert liability.calculated_amount == Decimal("5000")
        assert liability.paid_amount == Decimal("0")
        assert liability.balance == Decimal("5000")
        assert liability.status == TaxLiabilityStatus.PENDING
        assert liability.period == TaxPeriod.Q1
        assert liability.tax_year == 2025

    def test_get_liability(self):
        """Test retrieving a liability."""
        # Create it
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("10000"), self.due_date
        )

        # Retrieve it
        retrieved = self.manager.get_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1, 2025
        )

        assert retrieved is not None
        assert retrieved.calculated_amount == Decimal("10000")

    def test_get_liability_not_found(self):
        """Test retrieving non-existent liability."""
        retrieved = self.manager.get_liability(
            self.org_id, self.tax_type_id, TaxPeriod.MONTHLY, 2025
        )
        assert retrieved is None

    def test_create_duplicate_liability(self):
        """Test creating duplicate liability raises error."""
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000"), self.due_date
        )

        with pytest.raises(ValueError, match="already exists"):
            self.manager.create_liability(
                self.org_id, self.tax_type_id, TaxPeriod.Q1,
                2025, Decimal("6000"), self.due_date
            )

    def test_record_payment(self):
        """Test recording a payment."""
        # Create liability
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000"), self.due_date
        )

        # Record payment
        liability = self.manager.record_payment(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("2000")
        )

        assert liability.paid_amount == Decimal("2000")
        assert liability.balance == Decimal("3000")
        assert liability.status == TaxLiabilityStatus.PENDING

    def test_record_payment_full_payment(self):
        """Test recording payment that completes liability."""
        # Create liability
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000"), self.due_date
        )

        # Pay full amount
        liability = self.manager.record_payment(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000")
        )

        assert liability.balance == Decimal("0")
        assert liability.status == TaxLiabilityStatus.PAID

    def test_record_payment_overdue(self):
        """Test payment status becomes overdue if past due date."""
        # Create liability with past due date
        past_due = date.today() - timedelta(days=10)
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000"), past_due
        )

        # Record partial payment
        liability = self.manager.record_payment(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("2000")
        )

        assert liability.balance == Decimal("3000")
        assert liability.status == TaxLiabilityStatus.OVERDUE

    def test_record_payment_invalid_amount(self):
        """Test recording invalid payment amount raises error."""
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000"), self.due_date
        )

        with pytest.raises(ValueError, match="must be positive"):
            self.manager.record_payment(
                self.org_id, self.tax_type_id, TaxPeriod.Q1,
                2025, Decimal("-100")
            )

    def test_get_organization_liabilities(self):
        """Test getting all liabilities for organization."""
        # Create multiple
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000"), date(2025, 3, 31)
        )
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.ANNUAL,
            2025, Decimal("20000"), date(2025, 12, 31)
        )

        # Get them
        liabilities = self.manager.get_organization_liabilities(self.org_id)

        assert len(liabilities) == 2
        # Should be sorted by due date
        assert liabilities[0].period == TaxPeriod.Q1
        assert liabilities[1].period == TaxPeriod.ANNUAL

    def test_get_organization_liabilities_by_year(self):
        """Test filtering liabilities by tax year."""
        # Create liabilities for different years
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.ANNUAL,
            2024, Decimal("10000"), date(2024, 12, 31)
        )
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.ANNUAL,
            2025, Decimal("15000"), date(2025, 12, 31)
        )

        # Filter by year
        liabilities_2025 = self.manager.get_organization_liabilities(
            self.org_id, tax_year=2025
        )

        assert len(liabilities_2025) == 1
        assert liabilities_2025[0].tax_year == 2025

    def test_get_organization_liabilities_by_status(self):
        """Test filtering liabilities by status."""
        # Create and pay one
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000"), self.due_date
        )
        self.manager.record_payment(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000")
        )

        # Create unpaid one
        other_tax_type = uuid4()
        self.manager.create_liability(
            self.org_id, other_tax_type, TaxPeriod.MONTHLY,
            2025, Decimal("2000"), self.due_date
        )

        # Filter by status
        paid = self.manager.get_organization_liabilities(
            self.org_id, status=TaxLiabilityStatus.PAID
        )
        pending = self.manager.get_organization_liabilities(
            self.org_id, status=TaxLiabilityStatus.PENDING
        )

        assert len(paid) == 1
        assert len(pending) == 1

    def test_get_quarterly_liability(self):
        """Test getting quarterly liability."""
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000"), self.due_date
        )

        liability = self.manager.get_quarterly_liability(
            self.org_id, self.tax_type_id, 2025, 1
        )

        assert liability is not None
        assert liability.period == TaxPeriod.Q1

    def test_get_annual_liability(self):
        """Test getting annual liability."""
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.ANNUAL,
            2025, Decimal("20000"), date(2025, 12, 31)
        )

        liability = self.manager.get_annual_liability(
            self.org_id, self.tax_type_id, 2025
        )

        assert liability is not None
        assert liability.period == TaxPeriod.ANNUAL
        assert liability.tax_year == 2025

    def test_calculate_balance(self):
        """Test calculating liability balance."""
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000"), self.due_date
        )

        self.manager.record_payment(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("1500")
        )

        balance = self.manager.calculate_balance(
            self.org_id, self.tax_type_id, TaxPeriod.Q1, 2025
        )

        assert balance == Decimal("3500")

    def test_get_overdue_liabilities(self):
        """Test getting overdue liabilities."""
        # Create overdue
        past_due = date.today() - timedelta(days=5)
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000"), past_due
        )

        # Create future
        future_due = date.today() + timedelta(days=30)
        other_tax_type = uuid4()
        self.manager.create_liability(
            self.org_id, other_tax_type, TaxPeriod.Q1,
            2025, Decimal("3000"), future_due
        )

        # Get overdue
        overdue = self.manager.get_overdue_liabilities(self.org_id)

        assert len(overdue) == 1
        assert overdue[0].calculated_amount == Decimal("5000")

    def test_get_upcoming_liabilities(self):
        """Test getting upcoming liabilities within timeframe."""
        # Create upcoming (in 15 days)
        upcoming = date.today() + timedelta(days=15)
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000"), upcoming
        )

        # Create far future (in 60 days)
        far_future = date.today() + timedelta(days=60)
        other_tax_type = uuid4()
        self.manager.create_liability(
            self.org_id, other_tax_type, TaxPeriod.Q1,
            2025, Decimal("3000"), far_future
        )

        # Get upcoming in 30 days
        upcoming_liabilities = self.manager.get_upcoming_liabilities(
            self.org_id, days=30
        )

        assert len(upcoming_liabilities) == 1
        assert upcoming_liabilities[0].calculated_amount == Decimal("5000")

    def test_update_liability_status(self):
        """Test updating liability status."""
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000"), self.due_date
        )

        liability = self.manager.update_liability_status(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, TaxLiabilityStatus.ADJUSTED
        )

        assert liability.status == TaxLiabilityStatus.ADJUSTED

    def test_get_liability_summary(self):
        """Test getting liability summary for year."""
        # Create two liabilities
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000"), date(2025, 3, 31)
        )

        other_tax_type = uuid4()
        self.manager.create_liability(
            self.org_id, other_tax_type, TaxPeriod.Q1,
            2025, Decimal("3000"), date(2025, 3, 31)
        )

        # Pay one partially
        self.manager.record_payment(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("2000")
        )

        # Get summary
        summary = self.manager.get_liability_summary(self.org_id, 2025)

        assert summary["total_calculated"] == Decimal("8000")
        assert summary["total_paid"] == Decimal("2000")
        assert summary["total_balance"] == Decimal("6000")

    def test_invalid_quarter(self):
        """Test invalid quarter number raises error."""
        with pytest.raises(ValueError, match="between 1 and 4"):
            self.manager.get_quarterly_liability(
                self.org_id, self.tax_type_id, 2025, 5
            )

    def test_negative_amount_error(self):
        """Test negative amount raises error."""
        with pytest.raises(ValueError, match="cannot be negative"):
            self.manager.create_liability(
                self.org_id, self.tax_type_id, TaxPeriod.Q1,
                2025, Decimal("-1000"), self.due_date
            )

    def test_record_payment_nonexistent_liability(self):
        """Test recording payment on nonexistent liability raises error."""
        with pytest.raises(ValueError, match="not found"):
            self.manager.record_payment(
                self.org_id, self.tax_type_id, TaxPeriod.Q1,
                2025, Decimal("1000")
            )

    def test_organization_isolation(self):
        """Test liabilities are isolated between organizations."""
        other_org = uuid4()

        # Add to org 1
        self.manager.create_liability(
            self.org_id, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("5000"), self.due_date
        )

        # Add to org 2
        self.manager.create_liability(
            other_org, self.tax_type_id, TaxPeriod.Q1,
            2025, Decimal("3000"), self.due_date
        )

        # Each org should only see its own
        org1_liabilities = self.manager.get_organization_liabilities(self.org_id)
        org2_liabilities = self.manager.get_organization_liabilities(other_org)

        assert len(org1_liabilities) == 1
        assert org1_liabilities[0].calculated_amount == Decimal("5000")

        assert len(org2_liabilities) == 1
        assert org2_liabilities[0].calculated_amount == Decimal("3000")
