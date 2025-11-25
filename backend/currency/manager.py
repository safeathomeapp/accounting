"""Currency management service.

Manages currencies for organizations including creation, activation,
deactivation, and retrieval.
"""

from uuid import UUID
from typing import List, Optional
from backend.models.currency import Currency, CurrencyCode


class CurrencyManager:
    """Manages currencies for an organization."""

    def __init__(self):
        """Initialize currency manager."""
        self.currencies = {}  # Temporary in-memory storage for testing

    def add_currency(
        self,
        organization_id: UUID,
        code: str,
        name: str,
        symbol: str,
        decimal_places: int = 2
    ) -> Currency:
        """Add a new currency to the organization.

        Args:
            organization_id: Organization UUID
            code: ISO 4217 currency code (e.g., 'USD')
            name: Currency name (e.g., 'United States Dollar')
            symbol: Currency symbol (e.g., '$')
            decimal_places: Number of decimal places for rounding

        Returns:
            Created Currency object

        Raises:
            ValueError: If currency already exists or code is invalid
        """
        # Validate currency code
        if not self._is_valid_currency_code(code):
            raise ValueError(f"Invalid currency code: {code}")

        # Check if currency already exists for this organization
        org_currencies = self.get_organization_currencies(organization_id)
        if any(c.code == code for c in org_currencies):
            raise ValueError(f"Currency {code} already exists for organization")

        # Create currency
        currency = Currency(
            organization_id=organization_id,
            code=code,
            name=name,
            symbol=symbol,
            decimal_places=decimal_places,
            is_active=True
        )

        # Store in temporary storage
        key = (organization_id, code)
        self.currencies[key] = currency

        return currency

    def get_currency(
        self,
        organization_id: UUID,
        code: str
    ) -> Optional[Currency]:
        """Get a currency for an organization.

        Args:
            organization_id: Organization UUID
            code: Currency code

        Returns:
            Currency object or None if not found
        """
        key = (organization_id, code)
        return self.currencies.get(key)

    def get_organization_currencies(
        self,
        organization_id: UUID,
        include_inactive: bool = False
    ) -> List[Currency]:
        """Get all currencies for an organization.

        Args:
            organization_id: Organization UUID
            include_inactive: Include deactivated currencies

        Returns:
            List of Currency objects
        """
        currencies = [
            c for (org_id, _), c in self.currencies.items()
            if org_id == organization_id
        ]

        if not include_inactive:
            currencies = [c for c in currencies if c.is_active]

        return sorted(currencies, key=lambda c: c.code)

    def activate_currency(
        self,
        organization_id: UUID,
        code: str
    ) -> Currency:
        """Activate a currency for an organization.

        Args:
            organization_id: Organization UUID
            code: Currency code

        Returns:
            Updated Currency object

        Raises:
            ValueError: If currency not found
        """
        currency = self.get_currency(organization_id, code)
        if not currency:
            raise ValueError(f"Currency {code} not found")

        currency.is_active = True
        return currency

    def deactivate_currency(
        self,
        organization_id: UUID,
        code: str
    ) -> Currency:
        """Deactivate a currency for an organization.

        Args:
            organization_id: Organization UUID
            code: Currency code

        Returns:
            Updated Currency object

        Raises:
            ValueError: If currency not found
        """
        currency = self.get_currency(organization_id, code)
        if not currency:
            raise ValueError(f"Currency {code} not found")

        currency.is_active = False
        return currency

    def set_default_currency(
        self,
        organization_id: UUID,
        code: str
    ) -> Currency:
        """Set the default currency for an organization.

        Note: This is a placeholder for future implementation when
        default currency is added to Organization model.

        Args:
            organization_id: Organization UUID
            code: Currency code

        Returns:
            Currency object

        Raises:
            ValueError: If currency not found
        """
        currency = self.get_currency(organization_id, code)
        if not currency:
            raise ValueError(f"Currency {code} not found")

        return currency

    def get_currency_by_code(self, code: str) -> Optional[str]:
        """Get currency information by code.

        Args:
            code: ISO 4217 currency code

        Returns:
            Currency code if valid, None otherwise
        """
        if self._is_valid_currency_code(code):
            return code
        return None

    def _is_valid_currency_code(self, code: str) -> bool:
        """Check if a currency code is valid.

        Args:
            code: Currency code to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            CurrencyCode(code)
            return True
        except ValueError:
            return False

    def get_all_supported_currencies(self) -> List[str]:
        """Get all supported currency codes.

        Returns:
            List of ISO 4217 currency codes
        """
        return [c.value for c in CurrencyCode]
