"""Tests for currency management service.

Tests for CurrencyManager including CRUD operations, activation/deactivation,
and organization filtering.
"""

import pytest
from uuid import uuid4

from backend.currency.manager import CurrencyManager


class TestCurrencyManager:
    """Tests for CurrencyManager."""

    def setup_method(self):
        """Set up for each test."""
        self.manager = CurrencyManager()
        self.org_id = uuid4()
        self.other_org_id = uuid4()

    def test_add_currency(self):
        """Test adding a currency."""
        currency = self.manager.add_currency(
            organization_id=self.org_id,
            code="USD",
            name="United States Dollar",
            symbol="$",
            decimal_places=2
        )

        assert currency.code == "USD"
        assert currency.name == "United States Dollar"
        assert currency.symbol == "$"
        assert currency.decimal_places == 2
        assert currency.is_active is True

    def test_get_currency(self):
        """Test retrieving a currency."""
        # Add a currency
        added = self.manager.add_currency(
            organization_id=self.org_id,
            code="EUR",
            name="Euro",
            symbol="€"
        )

        # Retrieve it
        retrieved = self.manager.get_currency(self.org_id, "EUR")

        assert retrieved is not None
        assert retrieved.code == "EUR"
        assert retrieved.symbol == "€"

    def test_get_currency_not_found(self):
        """Test retrieving a non-existent currency."""
        currency = self.manager.get_currency(self.org_id, "XYZ")
        assert currency is None

    def test_get_organization_currencies(self):
        """Test getting all currencies for an organization."""
        # Add multiple currencies
        self.manager.add_currency(
            self.org_id, "USD", "United States Dollar", "$"
        )
        self.manager.add_currency(
            self.org_id, "EUR", "Euro", "€"
        )
        self.manager.add_currency(
            self.org_id, "GBP", "British Pound", "£"
        )

        # Get currencies
        currencies = self.manager.get_organization_currencies(self.org_id)

        assert len(currencies) == 3
        assert currencies[0].code == "EUR"  # Alphabetically sorted
        assert currencies[1].code == "GBP"
        assert currencies[2].code == "USD"

    def test_organization_currency_isolation(self):
        """Test that currencies are isolated between organizations."""
        # Add USD to org 1
        self.manager.add_currency(
            self.org_id, "USD", "United States Dollar", "$"
        )

        # Add EUR to org 2
        self.manager.add_currency(
            self.other_org_id, "EUR", "Euro", "€"
        )

        # Check org 1 only has USD
        org1_currencies = self.manager.get_organization_currencies(self.org_id)
        assert len(org1_currencies) == 1
        assert org1_currencies[0].code == "USD"

        # Check org 2 only has EUR
        org2_currencies = self.manager.get_organization_currencies(self.other_org_id)
        assert len(org2_currencies) == 1
        assert org2_currencies[0].code == "EUR"

    def test_add_duplicate_currency(self):
        """Test adding duplicate currency raises error."""
        self.manager.add_currency(
            self.org_id, "USD", "United States Dollar", "$"
        )

        with pytest.raises(ValueError, match="already exists"):
            self.manager.add_currency(
                self.org_id, "USD", "United States Dollar", "$"
            )

    def test_activate_currency(self):
        """Test activating a currency."""
        # Add and deactivate
        currency = self.manager.add_currency(
            self.org_id, "USD", "United States Dollar", "$"
        )
        currency.is_active = False

        # Activate it
        activated = self.manager.activate_currency(self.org_id, "USD")
        assert activated.is_active is True

    def test_deactivate_currency(self):
        """Test deactivating a currency."""
        # Add currency
        self.manager.add_currency(
            self.org_id, "USD", "United States Dollar", "$"
        )

        # Deactivate it
        deactivated = self.manager.deactivate_currency(self.org_id, "USD")
        assert deactivated.is_active is False

    def test_deactivate_and_include_inactive(self):
        """Test that deactivated currencies can be included."""
        # Add two currencies
        self.manager.add_currency(
            self.org_id, "USD", "United States Dollar", "$"
        )
        self.manager.add_currency(
            self.org_id, "EUR", "Euro", "€"
        )

        # Deactivate one
        self.manager.deactivate_currency(self.org_id, "USD")

        # Without inactive - only EUR
        active = self.manager.get_organization_currencies(self.org_id)
        assert len(active) == 1
        assert active[0].code == "EUR"

        # With inactive - both
        all_currencies = self.manager.get_organization_currencies(
            self.org_id, include_inactive=True
        )
        assert len(all_currencies) == 2

    def test_activate_nonexistent_currency(self):
        """Test activating non-existent currency raises error."""
        with pytest.raises(ValueError, match="not found"):
            self.manager.activate_currency(self.org_id, "XYZ")

    def test_deactivate_nonexistent_currency(self):
        """Test deactivating non-existent currency raises error."""
        with pytest.raises(ValueError, match="not found"):
            self.manager.deactivate_currency(self.org_id, "XYZ")

    def test_invalid_currency_code(self):
        """Test adding currency with invalid code raises error."""
        with pytest.raises(ValueError, match="Invalid currency code"):
            self.manager.add_currency(
                self.org_id, "XYZ", "Invalid", "$"
            )

    def test_set_default_currency(self):
        """Test setting default currency."""
        # Add currency
        self.manager.add_currency(
            self.org_id, "USD", "United States Dollar", "$"
        )

        # Set as default
        default = self.manager.set_default_currency(self.org_id, "USD")
        assert default.code == "USD"

    def test_set_default_nonexistent_currency(self):
        """Test setting non-existent currency as default raises error."""
        with pytest.raises(ValueError, match="not found"):
            self.manager.set_default_currency(self.org_id, "XYZ")

    def test_get_all_supported_currencies(self):
        """Test getting all supported currency codes."""
        supported = self.manager.get_all_supported_currencies()

        assert "USD" in supported
        assert "EUR" in supported
        assert "GBP" in supported
        assert "JPY" in supported
        assert len(supported) >= 17  # At least 17 currencies

    def test_get_currency_by_code_valid(self):
        """Test getting currency by valid code."""
        code = self.manager.get_currency_by_code("USD")
        assert code == "USD"

    def test_get_currency_by_code_invalid(self):
        """Test getting currency by invalid code."""
        code = self.manager.get_currency_by_code("XYZ")
        assert code is None
