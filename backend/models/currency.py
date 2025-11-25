"""Database models for multi-currency support.

Models for managing currencies, exchange rates, and conversion history
to support multi-currency transactions and financial reports.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

import enum

# Import Base class from models
from backend.models import Base


class CurrencyCode(str, enum.Enum):
    """ISO 4217 currency codes."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    CHF = "CHF"
    CNY = "CNY"
    INR = "INR"
    MXN = "MXN"
    BRL = "BRL"
    NZD = "NZD"
    SGD = "SGD"
    HKD = "HKD"
    NOK = "NOK"
    SEK = "SEK"
    ZAR = "ZAR"


class RateSource(str, enum.Enum):
    """Source of exchange rate."""
    PROVIDER = "provider"  # From rate provider API
    MANUAL = "manual"      # Manually entered
    HISTORICAL = "historical"  # Historical lookup


class Currency(Base):
    """Currency definition for an organization.

    Represents a currency that the organization can use for transactions
    and financial reports.
    """
    __tablename__ = "currencies"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False
    )
    organization_id = Column(UUID(as_uuid=True), nullable=False)

    code = Column(String(3), nullable=False)  # USD, EUR, GBP
    name = Column(String(100), nullable=False)  # United States Dollar
    symbol = Column(String(10), nullable=False)  # $
    decimal_places = Column(Integer(), nullable=False, default=2)  # 2 for USD, 0 for JPY

    is_active = Column(Boolean(), nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_currency_org_code"),
    )

    def __init__(self, **kwargs):
        """Initialize currency with defaults."""
        if 'is_active' not in kwargs:
            kwargs['is_active'] = True
        if 'decimal_places' not in kwargs:
            kwargs['decimal_places'] = 2
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.now(timezone.utc)
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.now(timezone.utc)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Currency({self.code})>"


class ExchangeRate(Base):
    """Exchange rate between two currencies.

    Stores current, historical, and manually-set exchange rates.
    """
    __tablename__ = "exchange_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False)

    source_currency_code = Column(String(3), nullable=False)  # EUR
    target_currency_code = Column(String(3), nullable=False)  # USD

    rate = Column(Float(), nullable=False)  # 1.21 (1 EUR = 1.21 USD)
    effective_date = Column(DateTime(timezone=True), nullable=False)  # When rate became effective

    source = Column(String(20), nullable=False)  # provider, manual, historical
    provider = Column(String(100), nullable=True)  # fixer.io, openexchangerates, etc.

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "source_currency_code", "target_currency_code",
            "effective_date", "source",
            name="uq_exchange_rate_org_pair_date_source"
        ),
    )

    def __init__(self, **kwargs):
        """Initialize exchange rate with defaults."""
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.now(timezone.utc)
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.now(timezone.utc)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ExchangeRate({self.source_currency_code}/{self.target_currency_code}={self.rate})>"


class ConversionHistory(Base):
    """Record of a currency conversion.

    Audit trail for all currency conversions performed,
    including amounts, rates, and method used.
    """
    __tablename__ = "conversion_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False)

    source_amount = Column(Float(), nullable=False)
    source_currency_code = Column(String(3), nullable=False)

    target_amount = Column(Float(), nullable=False)
    target_currency_code = Column(String(3), nullable=False)

    exchange_rate = Column(Float(), nullable=False)  # The rate used for conversion
    conversion_date = Column(DateTime(timezone=True), nullable=False)  # Date of the rate used
    conversion_method = Column(String(20), nullable=False)  # spot, historical, manual

    transaction_id = Column(UUID(as_uuid=True), nullable=True)  # Optional reference to transaction

    converted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        """Initialize conversion history with defaults."""
        if 'converted_at' not in kwargs:
            kwargs['converted_at'] = datetime.now(timezone.utc)
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.now(timezone.utc)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ConversionHistory("
            f"{self.source_amount}{self.source_currency_code} → "
            f"{self.target_amount}{self.target_currency_code})>"
        )
