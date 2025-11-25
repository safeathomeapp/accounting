"""Exchange rate management service.

Manages exchange rates including fetching, caching, and historical lookups.
"""

from uuid import UUID
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from backend.models.currency import ExchangeRate, RateSource


class ExchangeRateManager:
    """Manages exchange rates for an organization."""

    def __init__(self):
        """Initialize exchange rate manager."""
        self.rates = {}  # Temporary in-memory storage for testing
        self.cache = {}  # Cache for recent rates
        self.cache_ttl = 3600  # Cache validity in seconds (1 hour)

    def set_rate(
        self,
        organization_id: UUID,
        source_currency: str,
        target_currency: str,
        rate: float,
        effective_date: Optional[datetime] = None,
        source: str = "provider",
        provider: Optional[str] = None
    ) -> ExchangeRate:
        """Set or update an exchange rate.

        Args:
            organization_id: Organization UUID
            source_currency: Source currency code (e.g., 'EUR')
            target_currency: Target currency code (e.g., 'USD')
            rate: Exchange rate (e.g., 1.21 for EUR to USD)
            effective_date: When rate becomes effective (defaults to now)
            source: Source of rate (provider, manual, historical)
            provider: Provider name (e.g., 'fixer.io')

        Returns:
            Created or updated ExchangeRate object
        """
        if effective_date is None:
            effective_date = datetime.now(timezone.utc)

        exchange_rate = ExchangeRate(
            organization_id=organization_id,
            source_currency_code=source_currency,
            target_currency_code=target_currency,
            rate=rate,
            effective_date=effective_date,
            source=source,
            provider=provider
        )

        # Store rate
        key = (organization_id, source_currency, target_currency, effective_date.date())
        self.rates[key] = exchange_rate

        # Update cache
        self._update_cache(
            organization_id, source_currency, target_currency, exchange_rate
        )

        return exchange_rate

    def get_current_rate(
        self,
        organization_id: UUID,
        source_currency: str,
        target_currency: str
    ) -> Optional[ExchangeRate]:
        """Get the current (spot) exchange rate.

        Args:
            organization_id: Organization UUID
            source_currency: Source currency code
            target_currency: Target currency code

        Returns:
            Current ExchangeRate or None if not found
        """
        # Check cache first
        cache_key = (organization_id, source_currency, target_currency, "current")
        if cache_key in self.cache:
            cached_rate, cached_time = self.cache[cache_key]
            if self._is_cache_valid(cached_time):
                return cached_rate

        # Get most recent rate
        matching_rates = [
            (key, rate) for (org_id, src, tgt, date), rate in self.rates.items()
            if org_id == organization_id and src == source_currency and tgt == target_currency
        ]

        if not matching_rates:
            return None

        # Sort by date, get most recent
        matching_rates.sort(key=lambda x: x[0][3], reverse=True)
        most_recent_rate = matching_rates[0][1]

        # Update cache
        self.cache[cache_key] = (most_recent_rate, datetime.now(timezone.utc))

        return most_recent_rate

    def get_historical_rate(
        self,
        organization_id: UUID,
        source_currency: str,
        target_currency: str,
        date: datetime
    ) -> Optional[ExchangeRate]:
        """Get exchange rate for a specific date.

        Args:
            organization_id: Organization UUID
            source_currency: Source currency code
            target_currency: Target currency code
            date: Date to fetch rate for

        Returns:
            ExchangeRate for the given date or None if not found
        """
        key = (organization_id, source_currency, target_currency, date.date())
        return self.rates.get(key)

    def get_rate_history(
        self,
        organization_id: UUID,
        source_currency: str,
        target_currency: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[ExchangeRate]:
        """Get exchange rate history for a date range.

        Args:
            organization_id: Organization UUID
            source_currency: Source currency code
            target_currency: Target currency code
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of ExchangeRate objects in date range, sorted by date
        """
        matching_rates = [
            rate for (org_id, src, tgt, date), rate in self.rates.items()
            if org_id == organization_id
            and src == source_currency
            and tgt == target_currency
            and start_date.date() <= date <= end_date.date()
        ]

        # Sort by date
        matching_rates.sort(key=lambda r: r.effective_date)
        return matching_rates

    def set_manual_rate(
        self,
        organization_id: UUID,
        source_currency: str,
        target_currency: str,
        rate: float,
        effective_date: Optional[datetime] = None
    ) -> ExchangeRate:
        """Set a manually-entered exchange rate.

        Args:
            organization_id: Organization UUID
            source_currency: Source currency code
            target_currency: Target currency code
            rate: Exchange rate
            effective_date: When rate becomes effective (defaults to now)

        Returns:
            Created ExchangeRate object
        """
        return self.set_rate(
            organization_id,
            source_currency,
            target_currency,
            rate,
            effective_date=effective_date,
            source="manual",
            provider=None
        )

    def fetch_rates_from_provider(
        self,
        organization_id: UUID,
        source_currency: str,
        provider: str = "mock"
    ) -> Dict[str, float]:
        """Fetch exchange rates from a provider.

        This is a placeholder for provider integration. In production,
        this would call actual rate provider APIs (fixer.io, etc.)

        Args:
            organization_id: Organization UUID
            source_currency: Source currency code
            provider: Provider name (default: mock)

        Returns:
            Dictionary of {target_currency: rate}
        """
        # Mock provider response
        if provider == "mock":
            return {
                "USD": 1.21,
                "GBP": 0.87,
                "JPY": 145.50,
                "CAD": 1.36,
                "AUD": 1.82
            }
        return {}

    def cache_rates(
        self,
        organization_id: UUID,
        source_currency: str,
        rates: Dict[str, float],
        provider: str = "mock"
    ) -> List[ExchangeRate]:
        """Cache fetched rates for multiple target currencies.

        Args:
            organization_id: Organization UUID
            source_currency: Source currency code
            rates: Dictionary of {target_currency: rate}
            provider: Provider name

        Returns:
            List of created ExchangeRate objects
        """
        created_rates = []
        now = datetime.now(timezone.utc)

        for target_currency, rate in rates.items():
            exchange_rate = self.set_rate(
                organization_id,
                source_currency,
                target_currency,
                rate,
                effective_date=now,
                source="provider",
                provider=provider
            )
            created_rates.append(exchange_rate)

        return created_rates

    def is_rate_stale(
        self,
        organization_id: UUID,
        source_currency: str,
        target_currency: str,
        max_age_hours: int = 24
    ) -> bool:
        """Check if current rate is too old.

        Args:
            organization_id: Organization UUID
            source_currency: Source currency code
            target_currency: Target currency code
            max_age_hours: Maximum age of rate in hours

        Returns:
            True if rate is stale, False otherwise
        """
        rate = self.get_current_rate(
            organization_id, source_currency, target_currency
        )

        if not rate:
            return True

        age = datetime.now(timezone.utc) - rate.effective_date
        max_age = timedelta(hours=max_age_hours)

        return age > max_age

    def _update_cache(
        self,
        organization_id: UUID,
        source_currency: str,
        target_currency: str,
        rate: ExchangeRate
    ) -> None:
        """Update rate cache.

        Args:
            organization_id: Organization UUID
            source_currency: Source currency code
            target_currency: Target currency code
            rate: ExchangeRate object to cache
        """
        cache_key = (organization_id, source_currency, target_currency, "current")
        self.cache[cache_key] = (rate, datetime.now(timezone.utc))

    def _is_cache_valid(self, cached_time: datetime) -> bool:
        """Check if cached rate is still valid.

        Args:
            cached_time: When rate was cached

        Returns:
            True if cache is still valid, False if expired
        """
        age = datetime.now(timezone.utc) - cached_time
        return age < timedelta(seconds=self.cache_ttl)

    def clear_cache(self) -> None:
        """Clear all cached rates."""
        self.cache.clear()
