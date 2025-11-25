"""Tax management service.

Manages tax types and rates for organizations.
"""

from uuid import UUID
from datetime import date
from decimal import Decimal
from typing import List, Optional

from backend.models.tax import TaxType, TaxRate


class TaxManager:
    """Manages tax types and rates for an organization."""

    def __init__(self):
        """Initialize tax manager."""
        self.tax_types = {}  # In-memory storage: (org_id, code) -> TaxType
        self.tax_rates = {}  # In-memory storage: (org_id, type_id, jurisdiction, date) -> TaxRate

    def add_tax_type(
        self,
        organization_id: UUID,
        code: str,
        name: str,
        tax_type_category: str,
        description: Optional[str] = None
    ) -> TaxType:
        """Add a new tax type to the organization.

        Args:
            organization_id: Organization UUID
            code: Tax type code (income_tax, sales_tax, etc.)
            name: Human-readable tax type name
            tax_type_category: Category (Direct, Indirect, Payroll)
            description: Optional description

        Returns:
            Created TaxType object

        Raises:
            ValueError: If tax type already exists
        """
        # Validate code
        if not code or len(code) < 3:
            raise ValueError("Tax type code must be at least 3 characters")

        # Check if tax type already exists
        org_types = self.get_organization_tax_types(organization_id)
        if any(t.code == code for t in org_types):
            raise ValueError(f"Tax type {code} already exists for organization")

        # Create tax type
        tax_type = TaxType(
            organization_id=organization_id,
            code=code,
            name=name,
            tax_type_category=tax_type_category,
            description=description,
            is_active=True
        )

        # Store it
        key = (organization_id, code)
        self.tax_types[key] = tax_type

        return tax_type

    def get_tax_type(
        self,
        organization_id: UUID,
        code: str
    ) -> Optional[TaxType]:
        """Get a tax type for an organization.

        Args:
            organization_id: Organization UUID
            code: Tax type code

        Returns:
            TaxType object or None if not found
        """
        key = (organization_id, code)
        return self.tax_types.get(key)

    def get_organization_tax_types(
        self,
        organization_id: UUID,
        include_inactive: bool = False
    ) -> List[TaxType]:
        """Get all tax types for an organization.

        Args:
            organization_id: Organization UUID
            include_inactive: Include inactive tax types

        Returns:
            List of TaxType objects
        """
        types = [
            t for (org_id, _), t in self.tax_types.items()
            if org_id == organization_id
        ]

        if not include_inactive:
            types = [t for t in types if t.is_active]

        return sorted(types, key=lambda t: t.code)

    def activate_tax_type(
        self,
        organization_id: UUID,
        code: str
    ) -> TaxType:
        """Activate a tax type.

        Args:
            organization_id: Organization UUID
            code: Tax type code

        Returns:
            Updated TaxType object

        Raises:
            ValueError: If tax type not found
        """
        tax_type = self.get_tax_type(organization_id, code)
        if not tax_type:
            raise ValueError(f"Tax type {code} not found")

        tax_type.is_active = True
        return tax_type

    def deactivate_tax_type(
        self,
        organization_id: UUID,
        code: str
    ) -> TaxType:
        """Deactivate a tax type.

        Args:
            organization_id: Organization UUID
            code: Tax type code

        Returns:
            Updated TaxType object

        Raises:
            ValueError: If tax type not found
        """
        tax_type = self.get_tax_type(organization_id, code)
        if not tax_type:
            raise ValueError(f"Tax type {code} not found")

        tax_type.is_active = False
        return tax_type

    def set_tax_rate(
        self,
        organization_id: UUID,
        tax_type_id: UUID,
        jurisdiction: str,
        rate: Decimal,
        effective_date: date,
        expiration_date: Optional[date] = None
    ) -> TaxRate:
        """Set a tax rate for a jurisdiction.

        Args:
            organization_id: Organization UUID
            tax_type_id: Tax type UUID
            jurisdiction: Jurisdiction code/name
            rate: Tax rate as decimal (e.g., 0.15 for 15%)
            effective_date: When rate becomes effective
            expiration_date: When rate expires (optional)

        Returns:
            Created TaxRate object

        Raises:
            ValueError: If rate is invalid
        """
        # Validate rate
        if rate < 0 or rate > 1:
            raise ValueError("Tax rate must be between 0 and 1")

        # Create tax rate
        tax_rate = TaxRate(
            organization_id=organization_id,
            tax_type_id=tax_type_id,
            jurisdiction=jurisdiction,
            rate=rate,
            effective_date=effective_date,
            expiration_date=expiration_date,
            is_active=True
        )

        # Store it
        key = (organization_id, tax_type_id, jurisdiction, effective_date)
        self.tax_rates[key] = tax_rate

        return tax_rate

    def get_current_rate(
        self,
        organization_id: UUID,
        tax_type_id: UUID,
        jurisdiction: str,
        as_of_date: Optional[date] = None
    ) -> Optional[TaxRate]:
        """Get the current tax rate for a jurisdiction.

        Args:
            organization_id: Organization UUID
            tax_type_id: Tax type UUID
            jurisdiction: Jurisdiction code
            as_of_date: Date to check rate for (defaults to today)

        Returns:
            TaxRate object or None if not found
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Find all matching rates
        matching_rates = [
            rate for (org_id, type_id, juris, eff_date), rate in self.tax_rates.items()
            if org_id == organization_id
            and type_id == tax_type_id
            and juris == jurisdiction
            and eff_date <= as_of_date
            and (rate.expiration_date is None or rate.expiration_date >= as_of_date)
        ]

        if not matching_rates:
            return None

        # Return most recent rate
        matching_rates.sort(key=lambda r: r.effective_date, reverse=True)
        return matching_rates[0]

    def get_rate_history(
        self,
        organization_id: UUID,
        tax_type_id: UUID,
        jurisdiction: str,
        start_date: date,
        end_date: date
    ) -> List[TaxRate]:
        """Get tax rate history for a date range.

        Args:
            organization_id: Organization UUID
            tax_type_id: Tax type UUID
            jurisdiction: Jurisdiction code
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of TaxRate objects sorted by effective_date
        """
        matching_rates = [
            rate for (org_id, type_id, juris, eff_date), rate in self.tax_rates.items()
            if org_id == organization_id
            and type_id == tax_type_id
            and juris == jurisdiction
            and start_date <= eff_date <= end_date
        ]

        # Sort by effective date
        matching_rates.sort(key=lambda r: r.effective_date)
        return matching_rates

    def validate_tax_type_code(self, code: str) -> bool:
        """Validate tax type code format.

        Args:
            code: Tax type code to validate

        Returns:
            True if valid, False otherwise
        """
        if not code or len(code) < 3:
            return False
        if not code.replace("_", "").isalnum():
            return False
        return True
