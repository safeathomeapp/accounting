"""Tests for tax calculation engine.

Tests for TaxCalculator including income, sales, withholding, and flat taxes.
"""

import pytest
from decimal import Decimal

from backend.tax.calculator import TaxCalculator


class TestTaxCalculator:
    """Tests for TaxCalculator."""

    def setup_method(self):
        """Set up for each test."""
        self.calculator = TaxCalculator()

    # Income Tax Tests
    def test_progressive_income_tax_single_bracket(self):
        """Test progressive income tax with single bracket."""
        income = Decimal("50000")
        brackets = [(Decimal("inf"), Decimal("0.15"))]

        taxable, tax = self.calculator.calculate_income_tax(income, brackets)

        assert taxable == Decimal("50000")
        assert tax == Decimal("7500")  # 50000 * 0.15

    def test_progressive_income_tax_multiple_brackets(self):
        """Test progressive income tax with multiple brackets (US-style)."""
        income = Decimal("100000")
        brackets = [
            (Decimal("10000"), Decimal("0.10")),    # 10% up to 10k
            (Decimal("40000"), Decimal("0.12")),    # 12% up to 40k
            (Decimal("85000"), Decimal("0.22")),    # 22% up to 85k
            (Decimal("inf"), Decimal("0.24"))       # 24% above 85k
        ]

        taxable, tax = self.calculator.calculate_income_tax(income, brackets)

        assert taxable == Decimal("100000")
        # 10k*0.10 + 30k*0.12 + 45k*0.22 + 15k*0.24
        # = 1000 + 3600 + 9900 + 3600 = 18100
        assert tax == Decimal("18100")

    def test_income_tax_with_deductions(self):
        """Test income tax calculation with deductions."""
        income = Decimal("100000")
        deductions = Decimal("24000")
        brackets = [(Decimal("inf"), Decimal("0.20"))]

        taxable, tax = self.calculator.calculate_income_tax(income, brackets, deductions)

        assert taxable == Decimal("76000")  # 100000 - 24000
        assert tax == Decimal("15200")  # 76000 * 0.20

    def test_income_tax_zero_income(self):
        """Test income tax with zero income."""
        brackets = [(Decimal("inf"), Decimal("0.15"))]
        taxable, tax = self.calculator.calculate_income_tax(Decimal("0"), brackets)

        assert taxable == Decimal("0")
        assert tax == Decimal("0")

    def test_income_tax_deductions_exceed_income(self):
        """Test income tax when deductions exceed income."""
        income = Decimal("30000")
        deductions = Decimal("50000")
        brackets = [(Decimal("inf"), Decimal("0.15"))]

        taxable, tax = self.calculator.calculate_income_tax(income, brackets, deductions)

        assert taxable == Decimal("0")  # Negative income becomes 0
        assert tax == Decimal("0")

    def test_income_tax_negative_income_error(self):
        """Test negative income raises error."""
        brackets = [(Decimal("inf"), Decimal("0.15"))]
        with pytest.raises(ValueError, match="cannot be negative"):
            self.calculator.calculate_income_tax(Decimal("-1000"), brackets)

    # Sales Tax Tests
    def test_sales_tax_simple(self):
        """Test simple sales tax calculation."""
        amount = Decimal("100")
        rate = Decimal("0.08")

        sale_amount, tax = self.calculator.calculate_sales_tax(amount, rate)

        assert sale_amount == Decimal("100")
        assert tax == Decimal("8")  # 100 * 0.08

    def test_sales_tax_complex_rate(self):
        """Test sales tax with complex rate."""
        amount = Decimal("1234.56")
        rate = Decimal("0.0725")  # 7.25%

        sale_amount, tax = self.calculator.calculate_sales_tax(amount, rate)

        assert sale_amount == Decimal("1234.56")
        assert tax == Decimal("89.505600")  # 1234.56 * 0.0725

    def test_sales_tax_zero_amount(self):
        """Test sales tax with zero amount."""
        sale_amount, tax = self.calculator.calculate_sales_tax(Decimal("0"), Decimal("0.08"))

        assert sale_amount == Decimal("0")
        assert tax == Decimal("0")

    def test_sales_tax_invalid_rate_error(self):
        """Test sales tax with invalid rate raises error."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            self.calculator.calculate_sales_tax(Decimal("100"), Decimal("1.5"))

    # Withholding Tax Tests
    def test_withholding_tax_simple(self):
        """Test simple withholding tax."""
        amount = Decimal("1000")
        rate = Decimal("0.20")

        base, withholding = self.calculator.calculate_withholding_tax(amount, rate)

        assert base == Decimal("1000")
        assert withholding == Decimal("200")  # 1000 * 0.20

    def test_withholding_tax_with_allowances(self):
        """Test withholding tax with allowances."""
        amount = Decimal("2000")
        rate = Decimal("0.20")
        allowances = 2
        allowance_amount = Decimal("100")

        base, withholding = self.calculator.calculate_withholding_tax(
            amount, rate, allowances, allowance_amount
        )

        assert base == Decimal("1800")  # 2000 - (2 * 100)
        assert withholding == Decimal("360")  # 1800 * 0.20

    def test_withholding_tax_allowances_exceed_amount(self):
        """Test withholding tax when allowances exceed amount."""
        amount = Decimal("500")
        rate = Decimal("0.15")
        allowances = 10
        allowance_amount = Decimal("100")

        base, withholding = self.calculator.calculate_withholding_tax(
            amount, rate, allowances, allowance_amount
        )

        assert base == Decimal("0")  # 500 - 1000 = -500, capped at 0
        assert withholding == Decimal("0")

    # Flat Tax Tests
    def test_flat_tax(self):
        """Test flat tax calculation."""
        amount = Decimal("10000")
        rate = Decimal("0.09")

        taxable, tax = self.calculator.calculate_flat_tax(amount, rate)

        assert taxable == Decimal("10000")
        assert tax == Decimal("900")

    # Tax Credit Tests
    def test_apply_tax_credit(self):
        """Test applying tax credit."""
        tax = Decimal("5000")
        credit = Decimal("1500")

        result = self.calculator.apply_tax_credit(tax, credit)

        assert result == Decimal("3500")  # 5000 - 1500

    def test_apply_tax_credit_exceeds_tax(self):
        """Test credit that exceeds tax results in zero."""
        tax = Decimal("1000")
        credit = Decimal("2000")

        result = self.calculator.apply_tax_credit(tax, credit)

        assert result == Decimal("0")  # Can't go negative

    # Deduction Tests
    def test_apply_deduction(self):
        """Test applying deduction."""
        income = Decimal("100000")
        deduction = Decimal("13000")

        result = self.calculator.apply_deduction(income, deduction)

        assert result == Decimal("87000")

    def test_apply_deduction_exceeds_income(self):
        """Test deduction that exceeds income."""
        income = Decimal("50000")
        deduction = Decimal("75000")

        result = self.calculator.apply_deduction(income, deduction)

        assert result == Decimal("0")

    # Multi-Tax Tests
    def test_calculate_multi_tax(self):
        """Test calculating multiple taxes."""
        income = Decimal("100000")
        rates = {
            "federal": Decimal("0.15"),
            "state": Decimal("0.05"),
            "local": Decimal("0.02")
        }

        results = self.calculator.calculate_multi_tax(income, rates)

        assert results["federal"] == Decimal("15000")
        assert results["state"] == Decimal("5000")
        assert results["local"] == Decimal("2000")

    # Effective Tax Rate Tests
    def test_effective_tax_rate(self):
        """Test effective tax rate calculation."""
        total_tax = Decimal("15000")
        income = Decimal("100000")

        rate = self.calculator.calculate_effective_tax_rate(total_tax, income)

        assert rate == Decimal("0.15")  # 15%

    def test_effective_tax_rate_zero_income(self):
        """Test effective tax rate with zero income."""
        rate = self.calculator.calculate_effective_tax_rate(Decimal("1000"), Decimal("0"))

        assert rate == Decimal("0")

    # Rounding Tests
    def test_round_tax_amount_two_places(self):
        """Test rounding to two decimal places."""
        amount = Decimal("123.4567")

        rounded = self.calculator.round_tax_amount(amount, 2)

        assert rounded == Decimal("123.46")

    def test_round_tax_amount_zero_places(self):
        """Test rounding to zero decimal places."""
        amount = Decimal("123.7")

        rounded = self.calculator.round_tax_amount(amount, 0)

        assert rounded == Decimal("124")

    def test_round_tax_amount_four_places(self):
        """Test rounding to four decimal places."""
        amount = Decimal("0.123456")

        rounded = self.calculator.round_tax_amount(amount, 4)

        assert rounded == Decimal("0.1235")

    # Edge Cases
    def test_high_income_progressive_tax(self):
        """Test high income with progressive brackets."""
        income = Decimal("500000")
        brackets = [
            (Decimal("50000"), Decimal("0.10")),
            (Decimal("100000"), Decimal("0.12")),
            (Decimal("200000"), Decimal("0.22")),
            (Decimal("inf"), Decimal("0.37"))
        ]

        taxable, tax = self.calculator.calculate_income_tax(income, brackets)

        # 50k*0.10 + 50k*0.12 + 100k*0.22 + 300k*0.37
        # = 5000 + 6000 + 22000 + 111000 = 144000
        assert tax == Decimal("144000")

    def test_very_small_amounts(self):
        """Test with very small amounts."""
        amount = Decimal("0.01")
        rate = Decimal("0.05")

        sale_amount, tax = self.calculator.calculate_sales_tax(amount, rate)

        assert tax == Decimal("0.0005")
