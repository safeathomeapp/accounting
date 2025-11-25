"""Tests for currency conversion service.

Tests for CurrencyConverter including basic conversions, batch conversions,
historical rate lookups, and conversion history tracking.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from backend.currency.converter import CurrencyConverter
from backend.currency.rates import ExchangeRateManager


class TestCurrencyConverter:
    """Tests for CurrencyConverter."""

    def setup_method(self):
        """Set up for each test."""
        self.rate_manager = ExchangeRateManager()
        self.converter = CurrencyConverter(self.rate_manager)
        self.org_id = uuid4()

        # Set up some exchange rates for testing
        self.rate_manager.set_rate(
            self.org_id, "USD", "EUR", 0.92, source="provider"
        )
        self.rate_manager.set_rate(
            self.org_id, "EUR", "USD", 1.09, source="provider"
        )
        self.rate_manager.set_rate(
            self.org_id, "USD", "GBP", 0.79, source="provider"
        )

    def test_basic_conversion_usd_to_eur(self):
        """Test basic currency conversion."""
        converted, rate = self.converter.convert_amount(
            self.org_id, 100.00, "USD", "EUR"
        )

        assert rate == 0.92
        assert converted == 92.00

    def test_basic_conversion_eur_to_usd(self):
        """Test conversion with high precision rate."""
        converted, rate = self.converter.convert_amount(
            self.org_id, 100.00, "EUR", "USD"
        )

        assert rate == 1.09
        assert converted == 109.00

    def test_same_currency_conversion(self):
        """Test converting to same currency returns amount unchanged."""
        converted, rate = self.converter.convert_amount(
            self.org_id, 100.00, "USD", "USD"
        )

        assert rate == 1.0
        assert converted == 100.00

    def test_zero_amount_conversion(self):
        """Test converting zero amount."""
        converted, rate = self.converter.convert_amount(
            self.org_id, 0.0, "USD", "EUR"
        )

        assert converted == 0.0
        assert rate == 0.92

    def test_negative_amount_conversion(self):
        """Test converting negative amount."""
        converted, rate = self.converter.convert_amount(
            self.org_id, -100.00, "USD", "EUR"
        )

        assert converted == -92.00
        assert rate == 0.92

    def test_rounding_accuracy(self):
        """Test that conversion amounts are rounded correctly."""
        # 333.33 USD to EUR at 0.92 = 306.6636 -> rounds to 306.66
        converted, rate = self.converter.convert_amount(
            self.org_id, 333.33, "USD", "EUR", decimal_places=2
        )

        assert converted == 306.66

    def test_missing_rate_error(self):
        """Test that missing rate raises error."""
        with pytest.raises(ValueError, match="No exchange rate found"):
            self.converter.convert_amount(
                self.org_id, 100.00, "USD", "JPY"
            )

    def test_none_amount_error(self):
        """Test that None amount raises error."""
        with pytest.raises(ValueError, match="Amount cannot be None"):
            self.converter.convert_amount(
                self.org_id, None, "USD", "EUR"
            )

    def test_batch_conversion(self):
        """Test batch conversion of multiple amounts."""
        amounts = [
            (100.00, "USD", "EUR"),
            (50.00, "USD", "GBP"),
            (200.00, "EUR", "USD")
        ]

        results = self.converter.batch_convert(
            self.org_id, amounts, "USD"
        )

        assert len(results) == 3
        assert results[0][0] == 92.00      # 100 USD to EUR
        assert results[0][1] == 0.92       # Rate
        assert results[1][0] == 39.50      # 50 USD to GBP
        assert results[1][1] == 0.79       # Rate
        assert results[2][0] == 218.00     # 200 EUR to USD
        assert results[2][1] == 1.09       # Rate

    def test_historical_rate_conversion(self):
        """Test conversion using historical rate."""
        past_date = datetime.now(timezone.utc) - timedelta(days=30)

        # Set historical rate
        self.rate_manager.set_rate(
            self.org_id, "USD", "EUR", 0.87,
            effective_date=past_date, source="historical"
        )

        # Convert using historical rate
        converted, rate = self.converter.convert_amount_at_date(
            self.org_id, 100.00, "USD", "EUR", past_date
        )

        assert rate == 0.87
        assert converted == 87.00

    def test_historical_rate_not_found(self):
        """Test error when historical rate not found."""
        past_date = datetime.now(timezone.utc) - timedelta(days=30)

        with pytest.raises(ValueError, match="No historical rate found"):
            self.converter.convert_amount_at_date(
                self.org_id, 100.00, "USD", "JPY", past_date
            )

    def test_record_conversion_history(self):
        """Test recording conversion to history."""
        now = datetime.now(timezone.utc)
        tx_id = uuid4()

        history = self.converter.record_conversion(
            self.org_id,
            source_amount=100.00,
            source_currency="USD",
            target_amount=92.00,
            target_currency="EUR",
            exchange_rate=0.92,
            conversion_date=now,
            conversion_method="spot",
            transaction_id=tx_id
        )

        assert history.source_amount == 100.00
        assert history.source_currency_code == "USD"
        assert history.target_amount == 92.00
        assert history.target_currency_code == "EUR"
        assert history.exchange_rate == 0.92
        assert history.transaction_id == tx_id

    def test_get_conversion_history(self):
        """Test retrieving conversion history."""
        now = datetime.now(timezone.utc)
        tx_id1 = uuid4()
        tx_id2 = uuid4()

        # Record multiple conversions
        self.converter.record_conversion(
            self.org_id, 100.00, "USD", 92.00, "EUR", 0.92, now,
            transaction_id=tx_id1
        )
        self.converter.record_conversion(
            self.org_id, 200.00, "EUR", 218.00, "USD", 1.09, now,
            transaction_id=tx_id2
        )

        # Get all history
        history = self.converter.get_conversion_history(self.org_id)
        assert len(history) == 2

        # Get history for specific transaction
        tx_history = self.converter.get_conversion_history(
            self.org_id, transaction_id=tx_id1
        )
        assert len(tx_history) == 1
        assert tx_history[0].transaction_id == tx_id1

    def test_validate_conversion(self):
        """Test conversion validation."""
        # Valid conversion
        assert self.converter.validate_conversion(
            100.0, 0.92, 92.0
        ) is True

        # Invalid conversion (too different)
        assert self.converter.validate_conversion(
            100.0, 0.92, 90.0
        ) is False

        # Valid with tolerance
        assert self.converter.validate_conversion(
            100.0, 0.92, 92.005, tolerance=0.01
        ) is True

    def test_convert_with_history(self):
        """Test conversion and history recording in one call."""
        now = datetime.now(timezone.utc)
        tx_id = uuid4()

        converted, history = self.converter.convert_with_history(
            self.org_id,
            100.00,
            "USD",
            "EUR",
            now,
            transaction_id=tx_id
        )

        assert converted == 92.00
        assert history.source_amount == 100.00
        assert history.target_amount == 92.00
        assert history.transaction_id == tx_id
        assert history.conversion_method == "historical"

    def test_rounding_with_different_decimal_places(self):
        """Test rounding with different decimal place requirements."""
        # JPY uses 0 decimal places
        converted, rate = self.converter.convert_amount(
            self.org_id, 100.00, "USD", "EUR",
            decimal_places=0
        )

        # 100 * 0.92 = 92.0, rounded to 0 places = 92
        assert converted == 92.0
