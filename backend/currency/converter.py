"""Currency conversion service.

Handles currency conversions including spot rates, historical rates,
batch conversions, and conversion history tracking.
"""

from uuid import UUID
from datetime import datetime, timezone
from typing import List, Tuple, Optional
from decimal import Decimal, ROUND_HALF_UP
from backend.models.currency import ConversionHistory
from backend.currency.rates import ExchangeRateManager


class CurrencyConverter:
    """Handles currency conversions and conversion history."""

    def __init__(self, rate_manager: ExchangeRateManager):
        """Initialize currency converter.

        Args:
            rate_manager: ExchangeRateManager instance for rate lookups
        """
        self.rate_manager = rate_manager
        self.conversion_history = {}  # In-memory storage for testing

    def convert_amount(
        self,
        organization_id: UUID,
        amount: float,
        from_currency: str,
        to_currency: str,
        decimal_places: int = 2
    ) -> Tuple[float, float]:
        """Convert amount using current (spot) rate.

        Args:
            organization_id: Organization UUID
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            decimal_places: Decimal places for rounding

        Returns:
            Tuple of (converted_amount, rate_used)

        Raises:
            ValueError: If rate not found or invalid amount
        """
        # Validate amount
        if amount is None:
            raise ValueError("Amount cannot be None")

        # Handle same currency conversion
        if from_currency == to_currency:
            return amount, 1.0

        # Get current rate
        rate_obj = self.rate_manager.get_current_rate(
            organization_id, from_currency, to_currency
        )

        if not rate_obj:
            raise ValueError(
                f"No exchange rate found for {from_currency}/{to_currency}"
            )

        rate = rate_obj.rate
        converted = amount * rate

        # Round to decimal places
        converted = self._round_amount(converted, decimal_places)

        return converted, rate

    def convert_amount_at_date(
        self,
        organization_id: UUID,
        amount: float,
        from_currency: str,
        to_currency: str,
        conversion_date: datetime,
        decimal_places: int = 2
    ) -> Tuple[float, float]:
        """Convert amount using historical rate for a specific date.

        Args:
            organization_id: Organization UUID
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            conversion_date: Date to use for rate lookup
            decimal_places: Decimal places for rounding

        Returns:
            Tuple of (converted_amount, rate_used)

        Raises:
            ValueError: If rate not found or invalid amount
        """
        # Validate amount
        if amount is None:
            raise ValueError("Amount cannot be None")

        # Handle same currency conversion
        if from_currency == to_currency:
            return amount, 1.0

        # Get historical rate
        rate_obj = self.rate_manager.get_historical_rate(
            organization_id, from_currency, to_currency, conversion_date
        )

        if not rate_obj:
            raise ValueError(
                f"No historical rate found for {from_currency}/{to_currency} "
                f"on {conversion_date.date()}"
            )

        rate = rate_obj.rate
        converted = amount * rate

        # Round to decimal places
        converted = self._round_amount(converted, decimal_places)

        return converted, rate

    def batch_convert(
        self,
        organization_id: UUID,
        amounts: List[Tuple[float, str, str]],
        target_currency: str,
        decimal_places: int = 2
    ) -> List[Tuple[float, float]]:
        """Convert multiple amounts in batch.

        Args:
            organization_id: Organization UUID
            amounts: List of tuples (amount, from_currency, to_currency) or (amount, from_currency)
            target_currency: Target currency for all conversions
            decimal_places: Decimal places for rounding

        Returns:
            List of tuples (converted_amount, rate_used)

        Raises:
            ValueError: If any rate not found
        """
        results = []

        for item in amounts:
            if len(item) == 3:
                amount, from_currency, to_currency = item
            elif len(item) == 2:
                amount, from_currency = item
                to_currency = target_currency
            else:
                raise ValueError("Invalid amount tuple format")

            converted, rate = self.convert_amount(
                organization_id,
                amount,
                from_currency,
                to_currency,
                decimal_places
            )
            results.append((converted, rate))

        return results

    def record_conversion(
        self,
        organization_id: UUID,
        source_amount: float,
        source_currency: str,
        target_amount: float,
        target_currency: str,
        exchange_rate: float,
        conversion_date: datetime,
        conversion_method: str = "spot",
        transaction_id: Optional[UUID] = None
    ) -> ConversionHistory:
        """Record a currency conversion in history.

        Args:
            organization_id: Organization UUID
            source_amount: Original amount
            source_currency: Original currency code
            target_amount: Converted amount
            target_currency: Target currency code
            exchange_rate: Rate used for conversion
            conversion_date: Date when rate was effective
            conversion_method: Method of conversion (spot, historical, manual)
            transaction_id: Optional transaction UUID for reference

        Returns:
            ConversionHistory object
        """
        history = ConversionHistory(
            organization_id=organization_id,
            source_amount=source_amount,
            source_currency_code=source_currency,
            target_amount=target_amount,
            target_currency_code=target_currency,
            exchange_rate=exchange_rate,
            conversion_date=conversion_date,
            conversion_method=conversion_method,
            transaction_id=transaction_id
        )

        # Store in temporary storage
        key = (
            organization_id,
            source_currency,
            target_currency,
            history.converted_at
        )
        self.conversion_history[key] = history

        return history

    def get_conversion_history(
        self,
        organization_id: UUID,
        transaction_id: Optional[UUID] = None
    ) -> List[ConversionHistory]:
        """Get conversion history for an organization or transaction.

        Args:
            organization_id: Organization UUID
            transaction_id: Optional transaction UUID filter

        Returns:
            List of ConversionHistory objects
        """
        history = [
            h for (org_id, _, _, _), h in self.conversion_history.items()
            if org_id == organization_id
        ]

        if transaction_id:
            history = [h for h in history if h.transaction_id == transaction_id]

        # Sort by conversion date (newest first)
        history.sort(key=lambda h: h.converted_at, reverse=True)
        return history

    def validate_conversion(
        self,
        source_amount: float,
        rate: float,
        target_amount: float,
        tolerance: float = 0.01
    ) -> bool:
        """Validate that a conversion calculation is correct.

        Args:
            source_amount: Original amount
            rate: Exchange rate used
            target_amount: Converted amount
            tolerance: Allowable difference (default 0.01)

        Returns:
            True if conversion is valid, False otherwise
        """
        expected = source_amount * rate
        difference = abs(target_amount - expected)
        return difference <= tolerance

    def _round_amount(self, amount: float, decimal_places: int) -> float:
        """Round amount to specified decimal places.

        Args:
            amount: Amount to round
            decimal_places: Number of decimal places

        Returns:
            Rounded amount
        """
        if decimal_places < 0:
            raise ValueError("decimal_places must be >= 0")

        # Use Decimal for accurate rounding
        quantize_format = Decimal(10) ** -decimal_places
        decimal_amount = Decimal(str(amount))
        rounded = decimal_amount.quantize(quantize_format, rounding=ROUND_HALF_UP)
        return float(rounded)

    def convert_with_history(
        self,
        organization_id: UUID,
        source_amount: float,
        source_currency: str,
        target_currency: str,
        conversion_date: datetime,
        transaction_id: Optional[UUID] = None,
        decimal_places: int = 2
    ) -> Tuple[float, ConversionHistory]:
        """Convert amount and record in history.

        Args:
            organization_id: Organization UUID
            source_amount: Amount to convert
            source_currency: Source currency code
            target_currency: Target currency code
            conversion_date: Date for rate lookup
            transaction_id: Optional transaction reference
            decimal_places: Decimal places for rounding

        Returns:
            Tuple of (converted_amount, ConversionHistory)

        Raises:
            ValueError: If rate not found
        """
        # Get the rate
        rate_obj = self.rate_manager.get_historical_rate(
            organization_id, source_currency, target_currency, conversion_date
        )

        if not rate_obj:
            raise ValueError(
                f"No rate found for {source_currency}/{target_currency} "
                f"on {conversion_date.date()}"
            )

        # Perform conversion
        target_amount, rate = self.convert_amount_at_date(
            organization_id,
            source_amount,
            source_currency,
            target_currency,
            conversion_date,
            decimal_places
        )

        # Record in history
        history = self.record_conversion(
            organization_id,
            source_amount,
            source_currency,
            target_amount,
            target_currency,
            rate,
            conversion_date,
            conversion_method="historical",
            transaction_id=transaction_id
        )

        return target_amount, history
