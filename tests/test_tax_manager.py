"""Tests for tax management service.

Tests for TaxManager including CRUD operations, activation/deactivation,
and organization filtering.
"""

import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal

from backend.tax.manager import TaxManager


class TestTaxManager:
    """Tests for TaxManager."""

    def setup_method(self):
        """Set up for each test."""
        self.manager = TaxManager()
        self.org_id = uuid4()
        self.other_org_id = uuid4()
        self.tax_type_id = uuid4()

    def test_add_tax_type(self):
        """Test adding a tax type."""
        tax_type = self.manager.add_tax_type(
            organization_id=self.org_id,
            code="income_tax",
            name="Income Tax",
            tax_type_category="Direct"
        )

        assert tax_type.code == "income_tax"
        assert tax_type.name == "Income Tax"
        assert tax_type.tax_type_category == "Direct"
        assert tax_type.is_active is True

    def test_get_tax_type(self):
        """Test retrieving a tax type."""
        # Add it
        self.manager.add_tax_type(
            self.org_id, "sales_tax", "Sales Tax", "Indirect"
        )

        # Retrieve it
        retrieved = self.manager.get_tax_type(self.org_id, "sales_tax")

        assert retrieved is not None
        assert retrieved.code == "sales_tax"

    def test_get_tax_type_not_found(self):
        """Test retrieving non-existent tax type."""
        retrieved = self.manager.get_tax_type(self.org_id, "nonexistent")
        assert retrieved is None

    def test_add_duplicate_tax_type(self):
        """Test adding duplicate tax type raises error."""
        self.manager.add_tax_type(
            self.org_id, "vat", "VAT", "Indirect"
        )

        with pytest.raises(ValueError, match="already exists"):
            self.manager.add_tax_type(
                self.org_id, "vat", "VAT", "Indirect"
            )

    def test_get_organization_tax_types(self):
        """Test getting all tax types for an organization."""
        # Add multiple
        self.manager.add_tax_type(self.org_id, "income_tax", "Income Tax", "Direct")
        self.manager.add_tax_type(self.org_id, "sales_tax", "Sales Tax", "Indirect")
        self.manager.add_tax_type(self.org_id, "payroll_tax", "Payroll Tax", "Payroll")

        # Get them
        types = self.manager.get_organization_tax_types(self.org_id)

        assert len(types) == 3
        # Should be sorted by code
        assert types[0].code == "income_tax"
        assert types[1].code == "payroll_tax"
        assert types[2].code == "sales_tax"

    def test_organization_tax_type_isolation(self):
        """Test tax types are isolated between organizations."""
        # Add to org 1
        self.manager.add_tax_type(self.org_id, "income_tax", "Income Tax", "Direct")

        # Add to org 2
        self.manager.add_tax_type(self.other_org_id, "sales_tax", "Sales Tax", "Indirect")

        # Each org should only see its own
        org1_types = self.manager.get_organization_tax_types(self.org_id)
        org2_types = self.manager.get_organization_tax_types(self.other_org_id)

        assert len(org1_types) == 1
        assert org1_types[0].code == "income_tax"

        assert len(org2_types) == 1
        assert org2_types[0].code == "sales_tax"

    def test_activate_tax_type(self):
        """Test activating a tax type."""
        # Add and deactivate
        tax_type = self.manager.add_tax_type(
            self.org_id, "withholding_tax", "Withholding Tax", "Payroll"
        )
        tax_type.is_active = False

        # Activate
        activated = self.manager.activate_tax_type(self.org_id, "withholding_tax")
        assert activated.is_active is True

    def test_deactivate_tax_type(self):
        """Test deactivating a tax type."""
        # Add
        self.manager.add_tax_type(
            self.org_id, "property_tax", "Property Tax", "Direct"
        )

        # Deactivate
        deactivated = self.manager.deactivate_tax_type(self.org_id, "property_tax")
        assert deactivated.is_active is False

    def test_deactivate_and_include_inactive(self):
        """Test filtering inactive tax types."""
        # Add two
        self.manager.add_tax_type(self.org_id, "income_tax", "Income Tax", "Direct")
        self.manager.add_tax_type(self.org_id, "sales_tax", "Sales Tax", "Indirect")

        # Deactivate one
        self.manager.deactivate_tax_type(self.org_id, "income_tax")

        # Without inactive - only sales tax
        active = self.manager.get_organization_tax_types(self.org_id)
        assert len(active) == 1
        assert active[0].code == "sales_tax"

        # With inactive - both
        all_types = self.manager.get_organization_tax_types(
            self.org_id, include_inactive=True
        )
        assert len(all_types) == 2

    def test_activate_nonexistent_tax_type(self):
        """Test activating non-existent tax type raises error."""
        with pytest.raises(ValueError, match="not found"):
            self.manager.activate_tax_type(self.org_id, "nonexistent")

    def test_deactivate_nonexistent_tax_type(self):
        """Test deactivating non-existent tax type raises error."""
        with pytest.raises(ValueError, match="not found"):
            self.manager.deactivate_tax_type(self.org_id, "nonexistent")

    def test_invalid_tax_type_code(self):
        """Test adding tax type with invalid code raises error."""
        with pytest.raises(ValueError, match="at least 3 characters"):
            self.manager.add_tax_type(
                self.org_id, "ab", "Invalid Code", "Direct"
            )

    def test_set_tax_rate(self):
        """Test setting a tax rate."""
        effective_date = date(2025, 1, 1)

        rate = self.manager.set_tax_rate(
            organization_id=self.org_id,
            tax_type_id=self.tax_type_id,
            jurisdiction="US Federal",
            rate=Decimal("0.15"),
            effective_date=effective_date
        )

        assert rate.rate == Decimal("0.15")
        assert rate.jurisdiction == "US Federal"
        assert rate.effective_date == effective_date

    def test_get_current_rate(self):
        """Test getting current tax rate."""
        # Set a rate
        self.manager.set_tax_rate(
            self.org_id, self.tax_type_id, "California",
            Decimal("0.0725"), date(2025, 1, 1)
        )

        # Get it
        rate = self.manager.get_current_rate(
            self.org_id, self.tax_type_id, "California"
        )

        assert rate is not None
        assert float(rate.rate) == 0.0725

    def test_get_current_rate_not_found(self):
        """Test getting non-existent rate returns None."""
        rate = self.manager.get_current_rate(
            self.org_id, self.tax_type_id, "Nonexistent"
        )
        assert rate is None

    def test_get_current_rate_with_expiration(self):
        """Test current rate respects expiration dates."""
        old_date = date(2024, 1, 1)
        new_date = date(2025, 1, 1)

        # Set old rate that expires
        self.manager.set_tax_rate(
            self.org_id, self.tax_type_id, "State",
            Decimal("0.05"), old_date, expiration_date=date(2024, 12, 31)
        )

        # Set new rate
        self.manager.set_tax_rate(
            self.org_id, self.tax_type_id, "State",
            Decimal("0.06"), new_date
        )

        # Should get new rate
        rate = self.manager.get_current_rate(
            self.org_id, self.tax_type_id, "State", as_of_date=date(2025, 6, 1)
        )

        assert float(rate.rate) == 0.06

    def test_get_rate_history(self):
        """Test getting rate history for a date range."""
        # Set multiple rates
        self.manager.set_tax_rate(
            self.org_id, self.tax_type_id, "Federal",
            Decimal("0.15"), date(2024, 1, 1)
        )
        self.manager.set_tax_rate(
            self.org_id, self.tax_type_id, "Federal",
            Decimal("0.16"), date(2025, 1, 1)
        )
        self.manager.set_tax_rate(
            self.org_id, self.tax_type_id, "Federal",
            Decimal("0.17"), date(2026, 1, 1)
        )

        # Get history for 2 years
        history = self.manager.get_rate_history(
            self.org_id, self.tax_type_id, "Federal",
            date(2024, 1, 1), date(2025, 12, 31)
        )

        assert len(history) == 2
        assert float(history[0].rate) == 0.15
        assert float(history[1].rate) == 0.16

    def test_invalid_rate_value(self):
        """Test invalid rate values raise error."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            self.manager.set_tax_rate(
                self.org_id, self.tax_type_id, "Invalid",
                Decimal("1.5"), date(2025, 1, 1)
            )

    def test_validate_tax_type_code(self):
        """Test tax type code validation."""
        assert self.manager.validate_tax_type_code("income_tax") is True
        assert self.manager.validate_tax_type_code("sales_tax") is True
        assert self.manager.validate_tax_type_code("ab") is False
        assert self.manager.validate_tax_type_code("") is False
