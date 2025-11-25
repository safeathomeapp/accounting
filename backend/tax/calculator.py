"""Tax calculation engine.

Calculates various types of taxes including income tax, sales tax,
and withholding tax.
"""

from decimal import Decimal
from typing import List, Tuple, Optional


class TaxCalculator:
    """Performs tax calculations."""

    def calculate_income_tax(
        self,
        gross_income: Decimal,
        tax_brackets: List[Tuple[Decimal, Decimal]],
        deductions: Decimal = Decimal("0")
    ) -> Tuple[Decimal, Decimal]:
        """Calculate progressive income tax.

        Args:
            gross_income: Gross income amount
            tax_brackets: List of (threshold, rate) tuples, sorted by threshold
                         Example: [(50000, 0.10), (100000, 0.12), (float('inf'), 0.22)]
            deductions: Total deductions to subtract from income

        Returns:
            Tuple of (taxable_income, tax_amount)

        Raises:
            ValueError: If inputs are invalid
        """
        if gross_income < 0:
            raise ValueError("Gross income cannot be negative")
        if deductions < 0:
            raise ValueError("Deductions cannot be negative")
        if not tax_brackets:
            raise ValueError("Tax brackets cannot be empty")

        # Calculate taxable income
        taxable_income = max(gross_income - deductions, Decimal("0"))

        # Calculate tax using progressive brackets
        tax_amount = Decimal("0")
        previous_threshold = Decimal("0")

        for threshold, rate in tax_brackets:
            if taxable_income <= previous_threshold:
                break

            # Amount in this bracket
            bracket_income = min(taxable_income, threshold) - previous_threshold

            # Tax for this bracket
            tax_amount += bracket_income * Decimal(str(rate))

            previous_threshold = threshold

        return taxable_income, tax_amount

    def calculate_sales_tax(
        self,
        sale_amount: Decimal,
        tax_rate: Decimal
    ) -> Tuple[Decimal, Decimal]:
        """Calculate sales tax.

        Args:
            sale_amount: Sale amount before tax
            tax_rate: Tax rate (e.g., 0.0825 for 8.25%)

        Returns:
            Tuple of (sale_amount, tax_amount)

        Raises:
            ValueError: If inputs are invalid
        """
        if sale_amount < 0:
            raise ValueError("Sale amount cannot be negative")
        if tax_rate < 0 or tax_rate > 1:
            raise ValueError("Tax rate must be between 0 and 1")

        tax_amount = sale_amount * tax_rate

        return sale_amount, tax_amount

    def calculate_withholding_tax(
        self,
        gross_amount: Decimal,
        withholding_rate: Decimal,
        allowances: int = 0,
        allowance_amount: Decimal = Decimal("0")
    ) -> Tuple[Decimal, Decimal]:
        """Calculate withholding tax.

        Args:
            gross_amount: Gross amount subject to withholding
            withholding_rate: Withholding tax rate
            allowances: Number of withholding allowances
            allowance_amount: Amount per allowance (e.g., $87.50)

        Returns:
            Tuple of (withholding_base, withholding_amount)

        Raises:
            ValueError: If inputs are invalid
        """
        if gross_amount < 0:
            raise ValueError("Gross amount cannot be negative")
        if withholding_rate < 0 or withholding_rate > 1:
            raise ValueError("Withholding rate must be between 0 and 1")
        if allowances < 0:
            raise ValueError("Allowances cannot be negative")

        # Calculate withholding base (gross minus allowances)
        total_allowance = Decimal(allowances) * allowance_amount
        withholding_base = max(gross_amount - total_allowance, Decimal("0"))

        # Calculate withholding amount
        withholding_amount = withholding_base * withholding_rate

        return withholding_base, withholding_amount

    def calculate_flat_tax(
        self,
        taxable_amount: Decimal,
        tax_rate: Decimal
    ) -> Tuple[Decimal, Decimal]:
        """Calculate flat tax.

        Args:
            taxable_amount: Amount subject to tax
            tax_rate: Flat tax rate

        Returns:
            Tuple of (taxable_amount, tax_amount)

        Raises:
            ValueError: If inputs are invalid
        """
        if taxable_amount < 0:
            raise ValueError("Taxable amount cannot be negative")
        if tax_rate < 0 or tax_rate > 1:
            raise ValueError("Tax rate must be between 0 and 1")

        tax_amount = taxable_amount * tax_rate

        return taxable_amount, tax_amount

    def apply_tax_credit(
        self,
        calculated_tax: Decimal,
        credit_amount: Decimal
    ) -> Decimal:
        """Apply tax credit to reduce tax liability.

        Args:
            calculated_tax: Original tax calculation
            credit_amount: Credit amount to apply

        Returns:
            Tax after credit
        """
        if calculated_tax < 0:
            raise ValueError("Calculated tax cannot be negative")
        if credit_amount < 0:
            raise ValueError("Credit amount cannot be negative")

        return max(calculated_tax - credit_amount, Decimal("0"))

    def apply_deduction(
        self,
        income: Decimal,
        deduction_amount: Decimal
    ) -> Decimal:
        """Apply deduction to income.

        Args:
            income: Gross income
            deduction_amount: Deduction amount

        Returns:
            Taxable income after deduction
        """
        if income < 0:
            raise ValueError("Income cannot be negative")
        if deduction_amount < 0:
            raise ValueError("Deduction cannot be negative")

        return max(income - deduction_amount, Decimal("0"))

    def calculate_multi_tax(
        self,
        income: Decimal,
        tax_rates: dict
    ) -> dict:
        """Calculate multiple taxes for a single income.

        Args:
            income: Gross income
            tax_rates: Dict of {tax_name: rate}
                      Example: {"federal": 0.15, "state": 0.05}

        Returns:
            Dict of {tax_name: amount}
        """
        if income < 0:
            raise ValueError("Income cannot be negative")

        results = {}

        for tax_name, rate in tax_rates.items():
            if rate < 0 or rate > 1:
                raise ValueError(f"Invalid rate for {tax_name}")

            results[tax_name] = income * Decimal(str(rate))

        return results

    def calculate_effective_tax_rate(
        self,
        total_tax: Decimal,
        income: Decimal
    ) -> Decimal:
        """Calculate effective tax rate.

        Args:
            total_tax: Total tax amount
            income: Total income

        Returns:
            Effective tax rate as decimal (0.15 = 15%)
        """
        if income == 0:
            return Decimal("0")
        if income < 0 or total_tax < 0:
            raise ValueError("Values cannot be negative")

        return total_tax / income

    def round_tax_amount(
        self,
        amount: Decimal,
        decimal_places: int = 2
    ) -> Decimal:
        """Round tax amount to specified decimal places.

        Args:
            amount: Amount to round
            decimal_places: Number of decimal places

        Returns:
            Rounded amount
        """
        if decimal_places < 0:
            raise ValueError("Decimal places must be non-negative")

        quantize_format = Decimal(10) ** -decimal_places
        return amount.quantize(quantize_format)
