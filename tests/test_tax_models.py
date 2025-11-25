"""Tests for tax database models.

Tests for TaxType, TaxRate, TaxLiability, TaxAdjustment, and TaxComplianceLog models.
"""

import pytest
from uuid import uuid4
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

from backend.models.tax import (
    TaxType, TaxRate, TaxLiability, TaxAdjustment, TaxComplianceLog,
    TaxTypeCode, TaxPeriod, TaxLiabilityStatus, TaxAdjustmentType
)


class TestTaxTypeModel:
    """Tests for TaxType model."""

    def test_tax_type_creation(self):
        """Test creating a tax type."""
        org_id = uuid4()
        tax_type = TaxType(
            organization_id=org_id,
            code="income_tax",
            name="Income Tax",
            description="Federal income tax",
            tax_type_category="Direct"
        )

        assert tax_type.code == "income_tax"
        assert tax_type.name == "Income Tax"
        assert tax_type.description == "Federal income tax"
        assert tax_type.tax_type_category == "Direct"
        assert tax_type.is_active is True
        assert tax_type.created_at is not None

    def test_tax_type_defaults(self):
        """Test tax type default values."""
        org_id = uuid4()
        tax_type = TaxType(
            organization_id=org_id,
            code="sales_tax",
            name="Sales Tax",
            tax_type_category="Indirect"
        )

        assert tax_type.is_active is True
        assert tax_type.created_at is not None
        assert tax_type.updated_at is not None

    def test_tax_type_deactivation(self):
        """Test deactivating a tax type."""
        org_id = uuid4()
        tax_type = TaxType(
            organization_id=org_id,
            code="vat",
            name="VAT",
            tax_type_category="Indirect",
            is_active=False
        )

        assert tax_type.is_active is False

    def test_tax_type_repr(self):
        """Test tax type string representation."""
        org_id = uuid4()
        tax_type = TaxType(
            organization_id=org_id,
            code="withholding_tax",
            name="Withholding Tax",
            tax_type_category="Payroll"
        )

        assert "withholding_tax" in repr(tax_type)


class TestTaxRateModel:
    """Tests for TaxRate model."""

    def test_tax_rate_creation(self):
        """Test creating a tax rate."""
        org_id = uuid4()
        tax_type_id = uuid4()
        effective_date = date(2025, 1, 1)

        rate = TaxRate(
            organization_id=org_id,
            tax_type_id=tax_type_id,
            jurisdiction="US Federal",
            rate=Decimal("0.1500"),
            effective_date=effective_date
        )

        assert rate.jurisdiction == "US Federal"
        assert float(rate.rate) == 0.15
        assert rate.effective_date == effective_date
        assert rate.is_active is True
        assert rate.expiration_date is None

    def test_tax_rate_with_expiration(self):
        """Test tax rate with expiration date."""
        org_id = uuid4()
        tax_type_id = uuid4()
        effective_date = date(2025, 1, 1)
        expiration_date = date(2025, 12, 31)

        rate = TaxRate(
            organization_id=org_id,
            tax_type_id=tax_type_id,
            jurisdiction="Temporary Rate",
            rate=Decimal("0.0800"),
            effective_date=effective_date,
            expiration_date=expiration_date
        )

        assert rate.expiration_date == expiration_date

    def test_tax_rate_with_high_precision(self):
        """Test tax rate with high precision decimals."""
        org_id = uuid4()
        tax_type_id = uuid4()

        rate = TaxRate(
            organization_id=org_id,
            tax_type_id=tax_type_id,
            jurisdiction="Precise Rate",
            rate=Decimal("0.0850"),
            effective_date=date(2025, 1, 1)
        )

        assert float(rate.rate) == 0.085

    def test_tax_rate_repr(self):
        """Test tax rate string representation."""
        org_id = uuid4()
        tax_type_id = uuid4()

        rate = TaxRate(
            organization_id=org_id,
            tax_type_id=tax_type_id,
            jurisdiction="California",
            rate=Decimal("0.0725"),
            effective_date=date(2025, 1, 1)
        )

        repr_str = repr(rate)
        assert "California" in repr_str
        assert "0.0725" in repr_str


class TestTaxLiabilityModel:
    """Tests for TaxLiability model."""

    def test_tax_liability_creation(self):
        """Test creating a tax liability."""
        org_id = uuid4()
        tax_type_id = uuid4()
        due_date = date(2025, 4, 15)

        liability = TaxLiability(
            organization_id=org_id,
            tax_type_id=tax_type_id,
            tax_year=2025,
            period="Q1",
            calculated_amount=Decimal("5000.00"),
            paid_amount=Decimal("2500.00"),
            balance=Decimal("2500.00"),
            due_date=due_date,
            status="pending"
        )

        assert liability.tax_year == 2025
        assert liability.period == "Q1"
        assert float(liability.calculated_amount) == 5000.0
        assert float(liability.paid_amount) == 2500.0
        assert float(liability.balance) == 2500.0
        assert liability.status == "pending"

    def test_tax_liability_annual(self):
        """Test annual tax liability."""
        org_id = uuid4()
        tax_type_id = uuid4()

        liability = TaxLiability(
            organization_id=org_id,
            tax_type_id=tax_type_id,
            tax_year=2025,
            period="ANNUAL",
            calculated_amount=Decimal("20000.00"),
            paid_amount=Decimal("0.00"),
            balance=Decimal("20000.00"),
            due_date=date(2026, 1, 15),
            status="pending"
        )

        assert liability.period == "ANNUAL"

    def test_tax_liability_paid(self):
        """Test paid tax liability."""
        org_id = uuid4()
        tax_type_id = uuid4()

        liability = TaxLiability(
            organization_id=org_id,
            tax_type_id=tax_type_id,
            tax_year=2025,
            period="Q2",
            calculated_amount=Decimal("5000.00"),
            paid_amount=Decimal("5000.00"),
            balance=Decimal("0.00"),
            due_date=date(2025, 7, 15),
            status="paid"
        )

        assert liability.status == "paid"
        assert float(liability.balance) == 0.0

    def test_tax_liability_overdue(self):
        """Test overdue tax liability."""
        org_id = uuid4()
        tax_type_id = uuid4()

        liability = TaxLiability(
            organization_id=org_id,
            tax_type_id=tax_type_id,
            tax_year=2024,
            period="Q4",
            calculated_amount=Decimal("10000.00"),
            paid_amount=Decimal("0.00"),
            balance=Decimal("10000.00"),
            due_date=date(2024, 1, 15),
            status="overdue"
        )

        assert liability.status == "overdue"

    def test_tax_liability_repr(self):
        """Test tax liability string representation."""
        org_id = uuid4()
        tax_type_id = uuid4()

        liability = TaxLiability(
            organization_id=org_id,
            tax_type_id=tax_type_id,
            tax_year=2025,
            period="Q3",
            calculated_amount=Decimal("7500.00"),
            paid_amount=Decimal("0.00"),
            balance=Decimal("7500.00"),
            due_date=date(2025, 10, 15),
            status="pending"
        )

        repr_str = repr(liability)
        assert "2025" in repr_str
        assert "Q3" in repr_str


class TestTaxAdjustmentModel:
    """Tests for TaxAdjustment model."""

    def test_tax_adjustment_credit(self):
        """Test creating a tax credit adjustment."""
        org_id = uuid4()
        liability_id = uuid4()
        applied_date = date(2025, 3, 1)

        adjustment = TaxAdjustment(
            organization_id=org_id,
            tax_liability_id=liability_id,
            adjustment_type="credit",
            amount=Decimal("500.00"),
            reason="Q1 estimated payment credit",
            applied_date=applied_date
        )

        assert adjustment.adjustment_type == "credit"
        assert float(adjustment.amount) == 500.0
        assert adjustment.applied_date == applied_date

    def test_tax_adjustment_deduction(self):
        """Test creating a tax deduction adjustment."""
        org_id = uuid4()
        liability_id = uuid4()

        adjustment = TaxAdjustment(
            organization_id=org_id,
            tax_liability_id=liability_id,
            adjustment_type="deduction",
            amount=Decimal("1000.00"),
            reason="Business expense deduction",
            applied_date=date(2025, 3, 1)
        )

        assert adjustment.adjustment_type == "deduction"

    def test_tax_adjustment_penalty(self):
        """Test creating a penalty adjustment."""
        org_id = uuid4()
        liability_id = uuid4()

        adjustment = TaxAdjustment(
            organization_id=org_id,
            tax_liability_id=liability_id,
            adjustment_type="penalty",
            amount=Decimal("250.00"),
            reason="Late filing penalty",
            applied_date=date(2025, 5, 1)
        )

        assert adjustment.adjustment_type == "penalty"

    def test_tax_adjustment_with_description(self):
        """Test adjustment with detailed description."""
        org_id = uuid4()
        liability_id = uuid4()

        adjustment = TaxAdjustment(
            organization_id=org_id,
            tax_liability_id=liability_id,
            adjustment_type="refund",
            amount=Decimal("300.00"),
            reason="Overpayment from prior year",
            description="Refund from 2024 Q4 overpayment",
            applied_date=date(2025, 1, 15)
        )

        assert adjustment.adjustment_type == "refund"
        assert adjustment.description is not None

    def test_tax_adjustment_repr(self):
        """Test tax adjustment string representation."""
        org_id = uuid4()
        liability_id = uuid4()

        adjustment = TaxAdjustment(
            organization_id=org_id,
            tax_liability_id=liability_id,
            adjustment_type="credit",
            amount=Decimal("750.00"),
            reason="Estimated payment",
            applied_date=date(2025, 4, 1)
        )

        repr_str = repr(adjustment)
        assert "credit" in repr_str
        assert "750" in repr_str


class TestTaxComplianceLogModel:
    """Tests for TaxComplianceLog model."""

    def test_compliance_log_calculation(self):
        """Test logging a tax calculation event."""
        org_id = uuid4()
        liability_id = uuid4()

        log = TaxComplianceLog(
            organization_id=org_id,
            event_type="calculation",
            description="Q1 2025 income tax calculation",
            affected_entity_id=liability_id,
            affected_entity_type="TaxLiability",
            metadata={"period": "Q1", "year": 2025}
        )

        assert log.event_type == "calculation"
        assert log.affected_entity_type == "TaxLiability"
        assert log.event_metadata["period"] == "Q1"
        assert log.created_at is not None

    def test_compliance_log_adjustment(self):
        """Test logging a tax adjustment event."""
        org_id = uuid4()
        adjustment_id = uuid4()

        log = TaxComplianceLog(
            organization_id=org_id,
            event_type="adjustment",
            description="Tax credit applied",
            affected_entity_id=adjustment_id,
            affected_entity_type="TaxAdjustment"
        )

        assert log.event_type == "adjustment"

    def test_compliance_log_payment(self):
        """Test logging a payment event."""
        org_id = uuid4()

        log = TaxComplianceLog(
            organization_id=org_id,
            event_type="payment",
            description="Tax payment submitted",
            affected_entity_id=uuid4(),
            affected_entity_type="TaxLiability",
            metadata={"amount": 5000, "method": "EFT"}
        )

        assert log.event_type == "payment"
        assert log.event_metadata["method"] == "EFT"

    def test_compliance_log_rate_change(self):
        """Test logging a tax rate change event."""
        org_id = uuid4()

        log = TaxComplianceLog(
            organization_id=org_id,
            event_type="rate_change",
            description="Sales tax rate updated",
            affected_entity_id=uuid4(),
            affected_entity_type="TaxRate",
            metadata={"old_rate": 0.08, "new_rate": 0.0825}
        )

        assert log.event_type == "rate_change"

    def test_compliance_log_without_entity(self):
        """Test compliance log without affected entity reference."""
        org_id = uuid4()

        log = TaxComplianceLog(
            organization_id=org_id,
            event_type="compliance_check",
            description="Annual tax compliance review completed"
        )

        assert log.affected_entity_id is None
        assert log.affected_entity_type is None

    def test_compliance_log_repr(self):
        """Test compliance log string representation."""
        org_id = uuid4()

        log = TaxComplianceLog(
            organization_id=org_id,
            event_type="calculation",
            description="Annual tax calculation"
        )

        repr_str = repr(log)
        assert "calculation" in repr_str


class TestTaxEnums:
    """Tests for tax enums."""

    def test_tax_type_code_enum(self):
        """Test TaxTypeCode enum."""
        assert TaxTypeCode.INCOME_TAX.value == "income_tax"
        assert TaxTypeCode.SALES_TAX.value == "sales_tax"
        assert TaxTypeCode.VAT.value == "vat"
        assert TaxTypeCode.WITHHOLDING_TAX.value == "withholding_tax"

    def test_tax_period_enum(self):
        """Test TaxPeriod enum."""
        assert TaxPeriod.Q1.value == "Q1"
        assert TaxPeriod.Q2.value == "Q2"
        assert TaxPeriod.Q3.value == "Q3"
        assert TaxPeriod.Q4.value == "Q4"
        assert TaxPeriod.ANNUAL.value == "ANNUAL"

    def test_tax_liability_status_enum(self):
        """Test TaxLiabilityStatus enum."""
        assert TaxLiabilityStatus.PENDING.value == "pending"
        assert TaxLiabilityStatus.PAID.value == "paid"
        assert TaxLiabilityStatus.OVERDUE.value == "overdue"

    def test_tax_adjustment_type_enum(self):
        """Test TaxAdjustmentType enum."""
        assert TaxAdjustmentType.CREDIT.value == "credit"
        assert TaxAdjustmentType.DEDUCTION.value == "deduction"
        assert TaxAdjustmentType.PENALTY.value == "penalty"
        assert TaxAdjustmentType.REFUND.value == "refund"
