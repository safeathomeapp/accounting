"""Tests for currency database models.

Tests for Currency, ExchangeRate, and ConversionHistory models,
including creation, relationships, and constraints.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from backend.models.currency import Currency, ExchangeRate, ConversionHistory, CurrencyCode, RateSource


class TestCurrencyModel:
    """Tests for Currency model."""

    def test_currency_creation(self):
        """Test creating a currency."""
        org_id = uuid4()
        currency = Currency(
            organization_id=org_id,
            code="USD",
            name="United States Dollar",
            symbol="$",
            decimal_places=2
        )

        assert currency.code == "USD"
        assert currency.name == "United States Dollar"
        assert currency.symbol == "$"
        assert currency.decimal_places == 2
        assert currency.organization_id == org_id
        assert currency.is_active is True
        assert currency.created_at is not None

    def test_currency_defaults(self):
        """Test currency default values."""
        org_id = uuid4()
        currency = Currency(
            organization_id=org_id,
            code="EUR",
            name="Euro",
            symbol="€"
        )

        assert currency.decimal_places == 2
        assert currency.is_active is True
        assert currency.created_at is not None
        assert currency.updated_at is not None

    def test_currency_with_different_decimal_places(self):
        """Test currency with different decimal places."""
        org_id = uuid4()

        # JPY uses 0 decimal places
        jpy = Currency(
            organization_id=org_id,
            code="JPY",
            name="Japanese Yen",
            symbol="¥",
            decimal_places=0
        )
        assert jpy.decimal_places == 0

        # BHD uses 3 decimal places
        bhd = Currency(
            organization_id=org_id,
            code="BHD",
            name="Bahraini Dinar",
            symbol="د.ب",
            decimal_places=3
        )
        assert bhd.decimal_places == 3

    def test_currency_inactive(self):
        """Test deactivating a currency."""
        org_id = uuid4()
        currency = Currency(
            organization_id=org_id,
            code="AUD",
            name="Australian Dollar",
            symbol="A$",
            is_active=False
        )

        assert currency.is_active is False

    def test_currency_repr(self):
        """Test currency string representation."""
        org_id = uuid4()
        currency = Currency(
            organization_id=org_id,
            code="GBP",
            name="British Pound",
            symbol="£"
        )

        assert "GBP" in repr(currency)


class TestExchangeRateModel:
    """Tests for ExchangeRate model."""

    def test_exchange_rate_creation(self):
        """Test creating an exchange rate."""
        org_id = uuid4()
        rate_date = datetime.now(timezone.utc)

        rate = ExchangeRate(
            organization_id=org_id,
            source_currency_code="EUR",
            target_currency_code="USD",
            rate=1.21,
            effective_date=rate_date,
            source="provider",
            provider="fixer.io"
        )

        assert rate.source_currency_code == "EUR"
        assert rate.target_currency_code == "USD"
        assert rate.rate == 1.21
        assert rate.effective_date == rate_date
        assert rate.source == "provider"
        assert rate.provider == "fixer.io"
        assert rate.created_at is not None

    def test_exchange_rate_manual_source(self):
        """Test creating a manually-entered exchange rate."""
        org_id = uuid4()
        rate = ExchangeRate(
            organization_id=org_id,
            source_currency_code="USD",
            target_currency_code="CAD",
            rate=1.35,
            effective_date=datetime.now(timezone.utc),
            source="manual",
            provider=None
        )

        assert rate.source == "manual"
        assert rate.provider is None

    def test_exchange_rate_historical_source(self):
        """Test creating a historical exchange rate."""
        org_id = uuid4()
        past_date = datetime.now(timezone.utc) - timedelta(days=30)

        rate = ExchangeRate(
            organization_id=org_id,
            source_currency_code="GBP",
            target_currency_code="USD",
            rate=1.27,
            effective_date=past_date,
            source="historical"
        )

        assert rate.source == "historical"
        assert rate.effective_date < datetime.now(timezone.utc)

    def test_exchange_rate_precision(self):
        """Test exchange rate with high precision."""
        org_id = uuid4()
        rate = ExchangeRate(
            organization_id=org_id,
            source_currency_code="EUR",
            target_currency_code="USD",
            rate=1.2134567890,
            effective_date=datetime.now(timezone.utc),
            source="provider"
        )

        # Float should maintain precision
        assert abs(rate.rate - 1.2134567890) < 0.0000001

    def test_exchange_rate_repr(self):
        """Test exchange rate string representation."""
        org_id = uuid4()
        rate = ExchangeRate(
            organization_id=org_id,
            source_currency_code="EUR",
            target_currency_code="USD",
            rate=1.21,
            effective_date=datetime.now(timezone.utc),
            source="provider"
        )

        repr_str = repr(rate)
        assert "EUR" in repr_str
        assert "USD" in repr_str
        assert "1.21" in repr_str


class TestConversionHistoryModel:
    """Tests for ConversionHistory model."""

    def test_conversion_history_creation(self):
        """Test creating a conversion history record."""
        org_id = uuid4()
        conversion_date = datetime.now(timezone.utc)

        history = ConversionHistory(
            organization_id=org_id,
            source_amount=100.00,
            source_currency_code="EUR",
            target_amount=121.00,
            target_currency_code="USD",
            exchange_rate=1.21,
            conversion_date=conversion_date,
            conversion_method="spot"
        )

        assert history.source_amount == 100.00
        assert history.source_currency_code == "EUR"
        assert history.target_amount == 121.00
        assert history.target_currency_code == "USD"
        assert history.exchange_rate == 1.21
        assert history.conversion_method == "spot"
        assert history.converted_at is not None

    def test_conversion_history_with_transaction(self):
        """Test conversion history linked to a transaction."""
        org_id = uuid4()
        transaction_id = uuid4()

        history = ConversionHistory(
            organization_id=org_id,
            source_amount=1000.00,
            source_currency_code="GBP",
            target_amount=1270.00,
            target_currency_code="USD",
            exchange_rate=1.27,
            conversion_date=datetime.now(timezone.utc),
            conversion_method="spot",
            transaction_id=transaction_id
        )

        assert history.transaction_id == transaction_id

    def test_conversion_history_without_transaction(self):
        """Test conversion history without transaction reference."""
        org_id = uuid4()
        history = ConversionHistory(
            organization_id=org_id,
            source_amount=500.00,
            source_currency_code="JPY",
            target_amount=5.00,
            target_currency_code="USD",
            exchange_rate=0.01,
            conversion_date=datetime.now(timezone.utc),
            conversion_method="historical"
        )

        assert history.transaction_id is None

    def test_conversion_history_historical_method(self):
        """Test conversion history with historical conversion method."""
        org_id = uuid4()
        past_date = datetime.now(timezone.utc) - timedelta(days=60)

        history = ConversionHistory(
            organization_id=org_id,
            source_amount=100.00,
            source_currency_code="EUR",
            target_amount=110.00,
            target_currency_code="USD",
            exchange_rate=1.10,
            conversion_date=past_date,
            conversion_method="historical"
        )

        assert history.conversion_method == "historical"
        assert history.conversion_date == past_date

    def test_conversion_history_repr(self):
        """Test conversion history string representation."""
        org_id = uuid4()
        history = ConversionHistory(
            organization_id=org_id,
            source_amount=100.00,
            source_currency_code="EUR",
            target_amount=121.00,
            target_currency_code="USD",
            exchange_rate=1.21,
            conversion_date=datetime.now(timezone.utc),
            conversion_method="spot"
        )

        repr_str = repr(history)
        assert "EUR" in repr_str
        assert "USD" in repr_str
        assert "100" in repr_str
        assert "121" in repr_str

    def test_conversion_history_timestamps(self):
        """Test conversion history timestamps are set correctly."""
        org_id = uuid4()
        before_creation = datetime.now(timezone.utc)

        history = ConversionHistory(
            organization_id=org_id,
            source_amount=100.00,
            source_currency_code="EUR",
            target_amount=121.00,
            target_currency_code="USD",
            exchange_rate=1.21,
            conversion_date=datetime.now(timezone.utc),
            conversion_method="spot"
        )

        after_creation = datetime.now(timezone.utc)

        assert before_creation <= history.converted_at <= after_creation
        assert before_creation <= history.created_at <= after_creation


class TestCurrencyEnums:
    """Tests for Currency enums."""

    def test_currency_code_enum(self):
        """Test CurrencyCode enum."""
        assert CurrencyCode.USD.value == "USD"
        assert CurrencyCode.EUR.value == "EUR"
        assert CurrencyCode.GBP.value == "GBP"
        assert CurrencyCode.JPY.value == "JPY"

    def test_rate_source_enum(self):
        """Test RateSource enum."""
        assert RateSource.PROVIDER.value == "provider"
        assert RateSource.MANUAL.value == "manual"
        assert RateSource.HISTORICAL.value == "historical"
