"""Tests for exchange rate management service.

Tests for ExchangeRateManager including rate fetching, caching,
historical lookups, and rate staleness detection.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from backend.currency.rates import ExchangeRateManager


class TestExchangeRateManager:
    """Tests for ExchangeRateManager."""

    def setup_method(self):
        """Set up for each test."""
        self.manager = ExchangeRateManager()
        self.org_id = uuid4()

    def test_set_current_rate(self):
        """Test setting a current exchange rate."""
        rate = self.manager.set_rate(
            organization_id=self.org_id,
            source_currency="EUR",
            target_currency="USD",
            rate=1.21,
            source="provider",
            provider="fixer.io"
        )

        assert rate.source_currency_code == "EUR"
        assert rate.target_currency_code == "USD"
        assert rate.rate == 1.21
        assert rate.source == "provider"
        assert rate.provider == "fixer.io"

    def test_get_current_rate(self):
        """Test retrieving the current exchange rate."""
        # Set a rate
        self.manager.set_rate(
            self.org_id, "EUR", "USD", 1.21, source="provider"
        )

        # Retrieve it
        rate = self.manager.get_current_rate(self.org_id, "EUR", "USD")

        assert rate is not None
        assert rate.rate == 1.21

    def test_get_current_rate_not_found(self):
        """Test retrieving non-existent rate returns None."""
        rate = self.manager.get_current_rate(self.org_id, "EUR", "USD")
        assert rate is None

    def test_get_historical_rate(self):
        """Test retrieving a historical exchange rate."""
        past_date = datetime.now(timezone.utc) - timedelta(days=30)

        # Set a historical rate
        self.manager.set_rate(
            self.org_id,
            "GBP",
            "USD",
            1.27,
            effective_date=past_date,
            source="historical"
        )

        # Retrieve it
        rate = self.manager.get_historical_rate(
            self.org_id, "GBP", "USD", past_date
        )

        assert rate is not None
        assert rate.rate == 1.27
        assert rate.source == "historical"

    def test_get_rate_history(self):
        """Test getting rate history for a date range."""
        today = datetime.now(timezone.utc)
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        week_ago = today - timedelta(days=7)

        # Set rates on different dates
        self.manager.set_rate(
            self.org_id, "EUR", "USD", 1.19,
            effective_date=two_days_ago, source="historical"
        )
        self.manager.set_rate(
            self.org_id, "EUR", "USD", 1.20,
            effective_date=yesterday, source="historical"
        )
        self.manager.set_rate(
            self.org_id, "EUR", "USD", 1.21,
            effective_date=today, source="provider"
        )

        # Get history for last 5 days
        history = self.manager.get_rate_history(
            self.org_id, "EUR", "USD",
            week_ago, today
        )

        assert len(history) == 3
        # Should be sorted by date (oldest first)
        assert history[0].rate == 1.19
        assert history[1].rate == 1.20
        assert history[2].rate == 1.21

    def test_set_manual_rate(self):
        """Test setting a manually-entered rate."""
        rate = self.manager.set_manual_rate(
            self.org_id,
            "USD",
            "CAD",
            1.35
        )

        assert rate.source == "manual"
        assert rate.provider is None
        assert rate.rate == 1.35

    def test_fetch_rates_from_provider(self):
        """Test fetching rates from a mock provider."""
        rates = self.manager.fetch_rates_from_provider(
            self.org_id,
            "EUR",
            provider="mock"
        )

        assert "USD" in rates
        assert "GBP" in rates
        assert rates["USD"] == 1.21

    def test_cache_rates(self):
        """Test caching fetched rates."""
        rates_to_cache = {
            "USD": 1.21,
            "GBP": 0.87,
            "JPY": 145.50
        }

        cached = self.manager.cache_rates(
            self.org_id,
            "EUR",
            rates_to_cache,
            provider="fixer.io"
        )

        assert len(cached) == 3
        assert cached[0].source_currency_code == "EUR"
        assert cached[0].source == "provider"
        assert cached[0].provider == "fixer.io"

    def test_rate_staleness_detection(self):
        """Test detecting when rates are stale."""
        old_date = datetime.now(timezone.utc) - timedelta(hours=25)

        # Set an old rate
        self.manager.set_rate(
            self.org_id,
            "EUR",
            "USD",
            1.20,
            effective_date=old_date
        )

        # Check staleness with 24-hour threshold
        is_stale = self.manager.is_rate_stale(
            self.org_id, "EUR", "USD", max_age_hours=24
        )

        assert is_stale is True

    def test_rate_not_stale(self):
        """Test detecting when rates are fresh."""
        recent_date = datetime.now(timezone.utc) - timedelta(hours=1)

        # Set a recent rate
        self.manager.set_rate(
            self.org_id,
            "EUR",
            "USD",
            1.21,
            effective_date=recent_date
        )

        # Check staleness with 24-hour threshold
        is_stale = self.manager.is_rate_stale(
            self.org_id, "EUR", "USD", max_age_hours=24
        )

        assert is_stale is False

    def test_rate_staleness_no_rate(self):
        """Test rate staleness when no rate exists."""
        is_stale = self.manager.is_rate_stale(
            self.org_id, "EUR", "USD"
        )

        assert is_stale is True

    def test_cache_validity(self):
        """Test cache TTL expiration."""
        # Set a rate
        self.manager.set_rate(
            self.org_id, "EUR", "USD", 1.21
        )

        # Get rate (populates cache)
        rate1 = self.manager.get_current_rate(self.org_id, "EUR", "USD")
        assert rate1 is not None

        # Cache should be valid immediately
        cache_key = (self.org_id, "EUR", "USD", "current")
        assert cache_key in self.manager.cache

        # Simulate cache expiration
        cached_rate, cached_time = self.manager.cache[cache_key]
        self.manager.cache[cache_key] = (
            cached_rate,
            datetime.now(timezone.utc) - timedelta(hours=2)
        )

        # Cache should be considered invalid
        is_valid = self.manager._is_cache_valid(
            datetime.now(timezone.utc) - timedelta(hours=2)
        )
        assert is_valid is False

    def test_clear_cache(self):
        """Test clearing the rate cache."""
        # Set and cache a rate
        self.manager.set_rate(
            self.org_id, "EUR", "USD", 1.21
        )
        self.manager.get_current_rate(self.org_id, "EUR", "USD")

        # Cache should have entries
        assert len(self.manager.cache) > 0

        # Clear cache
        self.manager.clear_cache()

        # Cache should be empty
        assert len(self.manager.cache) == 0
