"""Integration tests for tax API routes and workflows.

Tests for complete tax compliance workflows including creating tax types,
setting rates, calculating taxes, managing liabilities, and compliance reporting.
"""

import pytest
from uuid import uuid4
from datetime import date, timedelta
from decimal import Decimal

from backend.tax import TaxManager, TaxCalculator, TaxLiabilityManager, TaxComplianceReporter
from backend.models.tax import TaxPeriod, TaxLiabilityStatus


class TestTaxComplianceWorkflow:
    """Integration tests for complete tax compliance workflows."""

    def setup_method(self):
        """Set up for each test."""
        self.org_id = uuid4()
        self.tax_manager = TaxManager()
        self.calculator = TaxCalculator()
        self.liability_manager = TaxLiabilityManager()
        self.compliance_reporter = TaxComplianceReporter()

    def test_complete_quarterly_tax_workflow(self):
        """Test complete quarterly tax workflow: setup, calculation, liability, payment."""
        # 1. Create tax type
        tax_type = self.tax_manager.add_tax_type(
            self.org_id, "income_tax", "Income Tax", "Direct"
        )

        # 2. Set tax rate
        rate = self.tax_manager.set_tax_rate(
            self.org_id, tax_type.id, "Federal",
            Decimal("0.15"), date(2025, 1, 1)
        )

        # 3. Calculate tax
        gross_income = Decimal("100000")
        brackets = [(Decimal("inf"), Decimal("0.15"))]
        taxable, tax_owed = self.calculator.calculate_income_tax(
            gross_income, brackets
        )

        # 4. Create liability
        liability = self.liability_manager.create_liability(
            self.org_id, tax_type.id, TaxPeriod.Q1, 2025,
            tax_owed, date(2025, 4, 15)
        )

        assert liability.calculated_amount == Decimal("15000")
        assert liability.status == TaxLiabilityStatus.PENDING

        # 5. Record payment
        liability = self.liability_manager.record_payment(
            self.org_id, tax_type.id, TaxPeriod.Q1, 2025,
            Decimal("15000")
        )

        assert liability.balance == Decimal("0")
        assert liability.status == TaxLiabilityStatus.PAID

    def test_multi_period_liability_tracking(self):
        """Test tracking liabilities across multiple periods."""
        tax_type = self.tax_manager.add_tax_type(
            self.org_id, "sales_tax", "Sales Tax", "Indirect"
        )

        # Create liabilities for Q1, Q2, Q3
        periods = [
            (TaxPeriod.Q1, date(2025, 4, 15), Decimal("5000")),
            (TaxPeriod.Q2, date(2025, 7, 15), Decimal("6000")),
            (TaxPeriod.Q3, date(2025, 10, 15), Decimal("5500"))
        ]

        liabilities = []
        for period, due_date, amount in periods:
            liability = self.liability_manager.create_liability(
                self.org_id, tax_type.id, period, 2025, amount, due_date
            )
            liabilities.append(liability)

        # Get summary
        summary = self.liability_manager.get_liability_summary(self.org_id, 2025)

        assert summary["total_calculated"] == Decimal("16500")
        assert summary["total_paid"] == Decimal("0")
        assert summary["total_balance"] == Decimal("16500")

        # Pay Q1
        self.liability_manager.record_payment(
            self.org_id, tax_type.id, TaxPeriod.Q1, 2025, Decimal("5000")
        )

        # Check updated summary
        summary = self.liability_manager.get_liability_summary(self.org_id, 2025)
        assert summary["total_paid"] == Decimal("5000")
        assert summary["total_balance"] == Decimal("11500")

    def test_progressive_tax_calculation_with_multiple_brackets(self):
        """Test calculating progressive income tax with multiple brackets."""
        # US federal tax brackets for 2025
        brackets = [
            (Decimal("11600"), Decimal("0.10")),
            (Decimal("47150"), Decimal("0.12")),
            (Decimal("100525"), Decimal("0.22")),
            (Decimal("191950"), Decimal("0.24")),
            (Decimal("243725"), Decimal("0.32")),
            (Decimal("609350"), Decimal("0.35")),
            (Decimal("inf"), Decimal("0.37"))
        ]

        income = Decimal("150000")
        taxable, tax = self.calculator.calculate_income_tax(income, brackets)

        assert taxable == income
        # 11600*0.10 + (47150-11600)*0.12 + (100525-47150)*0.22 + (191950-100525)*0.24 + (150000-191950 capped)
        # = 1160 + 4266 + 11742.50 + 21846 + 0 = 29042.50
        assert tax == Decimal("29042.50")

    def test_withholding_tax_with_allowances(self):
        """Test withholding tax calculation with allowances."""
        gross = Decimal("5000")
        rate = Decimal("0.20")
        allowances = 2
        allowance_amount = Decimal("200")

        base, withholding = self.calculator.calculate_withholding_tax(
            gross, rate, allowances, allowance_amount
        )

        assert base == Decimal("4600")  # 5000 - (2 * 200)
        assert withholding == Decimal("920")  # 4600 * 0.20

    def test_multi_jurisdiction_tax_management(self):
        """Test managing tax rates across multiple jurisdictions."""
        tax_type = self.tax_manager.add_tax_type(
            self.org_id, "sales_tax", "Sales Tax", "Indirect"
        )

        jurisdictions = [
            ("California", Decimal("0.0725")),
            ("Texas", Decimal("0.0625")),
            ("Florida", Decimal("0.06")),
            ("New York", Decimal("0.04"))
        ]

        for jurisdiction, rate_value in jurisdictions:
            self.tax_manager.set_tax_rate(
                self.org_id, tax_type.id, jurisdiction,
                rate_value, date(2025, 1, 1)
            )

        # Verify all rates are stored
        for jurisdiction, expected_rate in jurisdictions:
            rate = self.tax_manager.get_current_rate(
                self.org_id, tax_type.id, jurisdiction
            )
            assert rate is not None
            assert rate.rate == expected_rate

    def test_compliance_checklist_with_reporting(self):
        """Test creating compliance checklist and generating reports."""
        # Create Q1 compliance checklist
        items = [
            {
                "item_id": "q1_filing",
                "description": "File Q1 tax return",
                "due_date": date(2025, 4, 15),
                "notes": "Federal quarterly filing"
            },
            {
                "item_id": "q1_payment",
                "description": "Pay Q1 tax",
                "due_date": date(2025, 4, 20),
                "notes": None
            },
            {
                "item_id": "q1_reconciliation",
                "description": "Reconcile Q1 accounts",
                "due_date": date(2025, 5, 1),
                "notes": None
            }
        ]

        self.compliance_reporter.create_compliance_checklist(
            self.org_id, TaxPeriod.Q1, 2025, items
        )

        # Mark some items complete
        self.compliance_reporter.mark_checklist_item_complete(
            self.org_id, TaxPeriod.Q1, 2025, "q1_filing"
        )
        self.compliance_reporter.mark_checklist_item_complete(
            self.org_id, TaxPeriod.Q1, 2025, "q1_payment"
        )

        # Generate report
        report = self.compliance_reporter.generate_compliance_report(
            self.org_id, TaxPeriod.Q1, 2025
        )

        assert report["is_compliant"] is False  # 2/3 = 66%
        assert report["checklist_status"]["completion_percentage"] == pytest.approx(66.66, 0.1)

    def test_annual_compliance_summary_across_quarters(self):
        """Test generating annual compliance summary."""
        # Create checklists for all quarters
        due_months = {1: 4, 2: 7, 3: 10, 4: 1}  # Q1->April, Q2->July, Q3->Oct, Q4->Jan(next year)

        for quarter, period in enumerate([TaxPeriod.Q1, TaxPeriod.Q2, TaxPeriod.Q3, TaxPeriod.Q4], 1):
            items = [
                {
                    "item_id": f"q{quarter}_filing",
                    "description": f"File Q{quarter} return",
                    "due_date": date(2025, due_months[quarter], 15)
                }
            ]
            self.compliance_reporter.create_compliance_checklist(
                self.org_id, period, 2025, items
            )

        # Complete Q1 and Q2
        for quarter in [1, 2]:
            period = [TaxPeriod.Q1, TaxPeriod.Q2, TaxPeriod.Q3, TaxPeriod.Q4][quarter - 1]
            self.compliance_reporter.mark_checklist_item_complete(
                self.org_id, period, 2025, f"q{quarter}_filing"
            )

        # Get annual summary
        summary = self.compliance_reporter.get_annual_compliance_summary(
            self.org_id, 2025
        )

        assert summary["is_fully_compliant"] is False
        assert summary["overall_completion_percentage"] == 50  # 2/4

    def test_overdue_liability_tracking(self):
        """Test identification and tracking of overdue liabilities."""
        tax_type = self.tax_manager.add_tax_type(
            self.org_id, "payroll_tax", "Payroll Tax", "Payroll"
        )

        # Create past due liability
        past_due = date.today() - timedelta(days=30)
        self.liability_manager.create_liability(
            self.org_id, tax_type.id, TaxPeriod.MONTHLY, 2025,
            Decimal("5000"), past_due
        )

        # Create upcoming liability
        upcoming = date.today() + timedelta(days=15)
        other_type = uuid4()
        self.liability_manager.create_liability(
            self.org_id, other_type, TaxPeriod.MONTHLY, 2025,
            Decimal("3000"), upcoming
        )

        # Get overdue
        overdue = self.liability_manager.get_overdue_liabilities(self.org_id)
        assert len(overdue) == 1

        # Get upcoming
        upcoming_items = self.liability_manager.get_upcoming_liabilities(
            self.org_id, days=30
        )
        assert len(upcoming_items) == 1

    def test_tax_credit_and_deduction_workflow(self):
        """Test applying tax credits and deductions."""
        gross_income = Decimal("100000")
        deductions = Decimal("24000")
        brackets = [(Decimal("inf"), Decimal("0.20"))]

        # Calculate with deductions
        taxable, tax = self.calculator.calculate_income_tax(
            gross_income, brackets, deductions
        )

        assert taxable == Decimal("76000")
        assert tax == Decimal("15200")

        # Apply tax credit
        credit_amount = Decimal("2000")
        tax_after_credit = self.calculator.apply_tax_credit(tax, credit_amount)

        assert tax_after_credit == Decimal("13200")

    def test_multiple_organizations_isolation(self):
        """Test tax data is properly isolated between organizations."""
        org2_id = uuid4()

        # Create tax type for org1
        tax_type1 = self.tax_manager.add_tax_type(
            self.org_id, "income_tax", "Income Tax", "Direct"
        )

        # Create different tax type for org2
        tax_type2 = self.tax_manager.add_tax_type(
            org2_id, "sales_tax", "Sales Tax", "Indirect"
        )

        # Verify each org only sees its own
        org1_types = self.tax_manager.get_organization_tax_types(self.org_id)
        org2_types = self.tax_manager.get_organization_tax_types(org2_id)

        assert len(org1_types) == 1
        assert org1_types[0].code == "income_tax"

        assert len(org2_types) == 1
        assert org2_types[0].code == "sales_tax"

    def test_tax_calculation_precision(self):
        """Test financial calculations maintain decimal precision."""
        # Test with amounts requiring precise rounding
        sale = Decimal("1234.56")
        rate = Decimal("0.0725")

        sale_amount, tax = self.calculator.calculate_sales_tax(sale, rate)

        # Verify decimal precision is maintained
        assert tax == Decimal("89.505600")

        # Test rounding
        rounded = self.calculator.round_tax_amount(tax, 2)
        assert rounded == Decimal("89.51")

    def test_effective_tax_rate_calculation(self):
        """Test effective tax rate calculations."""
        total_tax = Decimal("15000")
        income = Decimal("100000")

        effective_rate = self.calculator.calculate_effective_tax_rate(total_tax, income)

        assert effective_rate == Decimal("0.15")

    def test_rate_history_and_changes(self):
        """Test managing tax rate changes over time."""
        tax_type = self.tax_manager.add_tax_type(
            self.org_id, "income_tax", "Income Tax", "Direct"
        )

        # Set rates for different years
        self.tax_manager.set_tax_rate(
            self.org_id, tax_type.id, "Federal",
            Decimal("0.15"), date(2024, 1, 1)
        )

        self.tax_manager.set_tax_rate(
            self.org_id, tax_type.id, "Federal",
            Decimal("0.16"), date(2025, 1, 1)
        )

        # Get history for 2 year period
        history = self.tax_manager.get_rate_history(
            self.org_id, tax_type.id, "Federal",
            date(2024, 1, 1), date(2025, 12, 31)
        )

        assert len(history) == 2
        assert history[0].rate == Decimal("0.15")
        assert history[1].rate == Decimal("0.16")

    def test_compliance_calendar_generation(self):
        """Test generating compliance calendar."""
        # Create checklists for Q1 and Q2
        for period, due_month in [(TaxPeriod.Q1, 4), (TaxPeriod.Q2, 7)]:
            items = [
                {
                    "item_id": f"filing_{period.value}",
                    "description": f"File {period.value} return",
                    "due_date": date(2025, due_month, 15)
                }
            ]
            self.compliance_reporter.create_compliance_checklist(
                self.org_id, period, 2025, items
            )

        # Get calendar
        calendar = self.compliance_reporter.get_compliance_calendar(
            self.org_id, 2025
        )

        assert len(calendar) >= 2
        # Verify sorted by date
        for i in range(len(calendar) - 1):
            assert calendar[i]["date"] <= calendar[i + 1]["date"]

    def test_quarterly_vs_annual_liability_management(self):
        """Test managing both quarterly and annual liabilities."""
        tax_type = self.tax_manager.add_tax_type(
            self.org_id, "income_tax", "Income Tax", "Direct"
        )

        # Create quarterly liability
        q_liability = self.liability_manager.create_liability(
            self.org_id, tax_type.id, TaxPeriod.Q1, 2025,
            Decimal("5000"), date(2025, 4, 15)
        )

        # Create annual liability
        annual_liability = self.liability_manager.create_liability(
            self.org_id, tax_type.id, TaxPeriod.ANNUAL, 2025,
            Decimal("20000"), date(2026, 1, 15)
        )

        # Verify both exist
        q_retrieved = self.liability_manager.get_quarterly_liability(
            self.org_id, tax_type.id, 2025, 1
        )
        annual_retrieved = self.liability_manager.get_annual_liability(
            self.org_id, tax_type.id, 2025
        )

        assert q_retrieved is not None
        assert annual_retrieved is not None
        assert q_retrieved.period == TaxPeriod.Q1
        assert annual_retrieved.period == TaxPeriod.ANNUAL

    def test_error_handling_invalid_operations(self):
        """Test error handling for invalid operations."""
        # Test invalid rate
        with pytest.raises(ValueError):
            self.tax_manager.set_tax_rate(
                self.org_id, uuid4(), "test",
                Decimal("1.5"), date(2025, 1, 1)
            )

        # Test duplicate tax type
        self.tax_manager.add_tax_type(
            self.org_id, "income_tax", "Income Tax", "Direct"
        )

        with pytest.raises(ValueError):
            self.tax_manager.add_tax_type(
                self.org_id, "income_tax", "Duplicate", "Direct"
            )

        # Test invalid bracket calculation
        with pytest.raises(ValueError):
            self.calculator.calculate_income_tax(
                Decimal("-1000"),
                [(Decimal("inf"), Decimal("0.15"))]
            )
