"""Database models for tax compliance and reporting.

Models for managing tax types, rates, liabilities, adjustments,
and compliance tracking across organizations.
"""

from datetime import datetime, timezone, date
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, Date, Text, JSON, Enum, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import enum

from backend.models import Base


class TaxTypeCode(str, enum.Enum):
    """Tax type codes."""
    INCOME_TAX = "income_tax"
    SALES_TAX = "sales_tax"
    VAT = "vat"
    WITHHOLDING_TAX = "withholding_tax"
    PAYROLL_TAX = "payroll_tax"
    PROPERTY_TAX = "property_tax"
    EXCISE_TAX = "excise_tax"
    CUSTOM = "custom"


class TaxPeriod(str, enum.Enum):
    """Tax period types."""
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"
    ANNUAL = "ANNUAL"
    MONTHLY = "MONTHLY"


class TaxLiabilityStatus(str, enum.Enum):
    """Tax liability status."""
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    ADJUSTED = "adjusted"


class TaxAdjustmentType(str, enum.Enum):
    """Type of tax adjustment."""
    CREDIT = "credit"
    DEDUCTION = "deduction"
    PENALTY = "penalty"
    REFUND = "refund"
    ESTIMATED_PAYMENT = "estimated_payment"


class TaxType(Base):
    """Tax type definition for an organization.

    Represents a type of tax that can be configured and tracked.
    """
    __tablename__ = "tax_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False)

    code = Column(String(50), nullable=False)  # income_tax, sales_tax, etc.
    name = Column(String(100), nullable=False)  # Income Tax, Sales Tax
    description = Column(Text(), nullable=True)
    tax_type_category = Column(String(30), nullable=False)  # Direct, Indirect, Payroll

    is_active = Column(Boolean(), nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_tax_type_org_code"),
    )

    def __init__(self, **kwargs):
        """Initialize tax type with defaults."""
        if 'is_active' not in kwargs:
            kwargs['is_active'] = True
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.now(timezone.utc)
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.now(timezone.utc)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        """String representation."""
        return f"<TaxType({self.code})>"


class TaxRate(Base):
    """Exchange rate between two currencies.

    Stores current, historical, and manually-set tax rates with jurisdiction support.
    """
    __tablename__ = "tax_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False)

    tax_type_id = Column(UUID(as_uuid=True), nullable=False)  # Foreign key to TaxType
    jurisdiction = Column(String(100), nullable=False)  # US, CA, UK, etc. or "Federal", "State", etc.

    rate = Column(Numeric(precision=5, scale=4), nullable=False)  # 0.15 (15%), 0.0850 (8.5%)
    effective_date = Column(Date(), nullable=False)
    expiration_date = Column(Date(), nullable=True)  # Null = no expiration

    is_active = Column(Boolean(), nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "tax_type_id", "jurisdiction", "effective_date",
            name="uq_tax_rate_org_type_juris_date"
        ),
    )

    def __init__(self, **kwargs):
        """Initialize tax rate with defaults."""
        if 'is_active' not in kwargs:
            kwargs['is_active'] = True
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.now(timezone.utc)
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.now(timezone.utc)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        """String representation."""
        return f"<TaxRate({self.jurisdiction}: {self.rate})>"


class TaxLiability(Base):
    """Tax liability for a specific period.

    Tracks tax obligations and payments for quarters or annual periods.
    """
    __tablename__ = "tax_liabilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False)

    tax_type_id = Column(UUID(as_uuid=True), nullable=False)  # Foreign key to TaxType
    tax_year = Column(Integer(), nullable=False)  # 2025, 2026, etc.
    period = Column(String(10), nullable=False)  # Q1, Q2, Q3, Q4, ANNUAL, MONTHLY

    calculated_amount = Column(Numeric(precision=12, scale=2), nullable=False)  # Total calculated tax
    paid_amount = Column(Numeric(precision=12, scale=2), nullable=False, default=0)  # Amount already paid
    balance = Column(Numeric(precision=12, scale=2), nullable=False)  # Remaining amount due

    due_date = Column(Date(), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, paid, overdue, adjusted

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "tax_type_id", "tax_year", "period",
            name="uq_tax_liability_org_type_year_period"
        ),
    )

    def __init__(self, **kwargs):
        """Initialize tax liability with defaults."""
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.now(timezone.utc)
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.now(timezone.utc)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        """String representation."""
        return f"<TaxLiability({self.tax_year} {self.period}: {self.calculated_amount})>"


class TaxAdjustment(Base):
    """Tax adjustment, credit, or penalty.

    Records adjustments to tax liabilities including credits, deductions, and penalties.
    """
    __tablename__ = "tax_adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False)

    tax_liability_id = Column(UUID(as_uuid=True), nullable=False)  # Foreign key to TaxLiability
    adjustment_type = Column(String(20), nullable=False)  # credit, deduction, penalty, refund, estimated_payment

    amount = Column(Numeric(precision=12, scale=2), nullable=False)
    reason = Column(String(255), nullable=False)
    description = Column(Text(), nullable=True)

    applied_date = Column(Date(), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        """Initialize tax adjustment with defaults."""
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.now(timezone.utc)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        """String representation."""
        return f"<TaxAdjustment({self.adjustment_type}: {self.amount})>"


class TaxComplianceLog(Base):
    """Audit trail for tax-related events.

    Records all tax calculations, adjustments, and important compliance events.
    """
    __tablename__ = "tax_compliance_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False)

    event_type = Column(String(50), nullable=False)  # calculation, adjustment, payment, rate_change, etc.
    description = Column(Text(), nullable=False)

    affected_entity_id = Column(UUID(as_uuid=True), nullable=True)  # ID of related entity (liability, adjustment, etc.)
    affected_entity_type = Column(String(50), nullable=True)  # Type of entity (TaxLiability, TaxAdjustment, etc.)

    event_metadata = Column(JSON(), nullable=True)  # Additional context as JSON

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        """Initialize tax compliance log with defaults."""
        # Handle metadata -> event_metadata mapping for backward compatibility
        if 'metadata' in kwargs:
            kwargs['event_metadata'] = kwargs.pop('metadata')
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.now(timezone.utc)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        """String representation."""
        return f"<TaxComplianceLog({self.event_type})>"
