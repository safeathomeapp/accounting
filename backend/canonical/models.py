"""SQLAlchemy ORM models for the canonical mapping layer."""

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Date, DateTime,
    Numeric, ForeignKey, Index, func, Enum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.models import Base


# ============================================================================
# Python Enum Classes
# ============================================================================

class NormalizedTxnType(str, enum.Enum):
    SALES_INVOICE = "SALES_INVOICE"
    PURCHASE_INVOICE = "PURCHASE_INVOICE"
    CREDIT_NOTE = "CREDIT_NOTE"
    BANK_PAYMENT = "BANK_PAYMENT"
    BANK_RECEIPT = "BANK_RECEIPT"
    JOURNAL = "JOURNAL"
    TRANSFER = "TRANSFER"
    OTHER = "OTHER"


class NormalizedTxnStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    SENT = "SENT"
    PAID = "PAID"
    VOIDED = "VOIDED"
    UNKNOWN = "UNKNOWN"


class CashflowBucket(str, enum.Enum):
    AR_CURRENT = "AR_CURRENT"
    AR_OVERDUE = "AR_OVERDUE"
    AP_CURRENT = "AP_CURRENT"
    AP_OVERDUE = "AP_OVERDUE"
    CASH_IN = "CASH_IN"
    CASH_OUT = "CASH_OUT"
    NON_CASH = "NON_CASH"
    IGNORE = "IGNORE"


class DateSource(str, enum.Enum):
    DUE_DATE = "DUE_DATE"
    TRANSACTION_DATE = "TRANSACTION_DATE"


# ============================================================================
# ORM Models
# ============================================================================

class PlatformTransactionMapping(Base):
    """
    Maps platform-specific (type, status) pairs to canonical classifications.

    Each row says: "When we see a transaction from <platform_name> with
    <source_type> and <source_status>, classify it as <normalized_type>,
    <normalized_status>, and place it in <canonical_bucket>."
    """
    __tablename__ = "platform_transaction_mapping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform_name = Column(String(50), nullable=False)
    source_type = Column(String(100), nullable=False)
    source_status = Column(String(100), nullable=False)
    normalized_type = Column(
        Enum(NormalizedTxnType, name='normalized_txn_type', create_type=False),
        nullable=False
    )
    normalized_status = Column(
        Enum(NormalizedTxnStatus, name='normalized_txn_status', create_type=False),
        nullable=False
    )
    canonical_bucket = Column(
        Enum(CashflowBucket, name='cashflow_bucket', create_type=False),
        nullable=False
    )
    effective_date_source = Column(
        Enum(DateSource, name='date_source', create_type=False),
        nullable=False, server_default='TRANSACTION_DATE'
    )
    priority = Column(Integer, nullable=False, server_default='0')
    is_active = Column(Boolean, nullable=False, server_default='true')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    # Relationships
    facts = relationship("CashflowFact", back_populates="mapping", lazy="select")

    def __repr__(self):
        return (
            f"<PlatformTransactionMapping("
            f"{self.platform_name}/{self.source_type}/{self.source_status} "
            f"-> {self.canonical_bucket.value})>"
        )


class CashflowFact(Base):
    """
    One row per transaction - the canonical truth for reporting.

    signed_amount is positive for AR/CASH_IN, negative for AP/CASH_OUT.
    effective_date is chosen based on the mapping's date_source preference.
    """
    __tablename__ = "cashflow_facts_v1"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False, unique=True
    )
    mapping_id = Column(
        Integer,
        ForeignKey("platform_transaction_mapping.id"),
        nullable=False
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True
    )
    normalized_type = Column(
        Enum(NormalizedTxnType, name='normalized_txn_type', create_type=False),
        nullable=False
    )
    normalized_status = Column(
        Enum(NormalizedTxnStatus, name='normalized_txn_status', create_type=False),
        nullable=False
    )
    canonical_bucket = Column(
        Enum(CashflowBucket, name='cashflow_bucket', create_type=False),
        nullable=False
    )
    effective_date = Column(Date, nullable=False)
    signed_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, server_default='GBP')
    snapshot_date = Column(Date, nullable=False, default=date.today)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    transaction = relationship("Transaction", lazy="select")
    mapping = relationship("PlatformTransactionMapping", back_populates="facts", lazy="select")

    def __repr__(self):
        return (
            f"<CashflowFact("
            f"txn={self.transaction_id}, "
            f"bucket={self.canonical_bucket.value}, "
            f"amount={self.signed_amount})>"
        )


class IngestionQuarantine(Base):
    """
    Holds transactions that could not be mapped to a canonical bucket.

    When a new mapping is added for the missing (platform, type, status),
    quarantined rows can be resolved and re-processed into facts.
    """
    __tablename__ = "ingestion_quarantine"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    platform_name = Column(String(50), nullable=False)
    source_type = Column(String(100), nullable=False)
    source_status = Column(String(100), nullable=False)
    reason = Column(Text, nullable=False)
    quarantined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(255), nullable=True)

    # Relationships
    transaction = relationship("Transaction", lazy="select")

    def __repr__(self):
        resolved = "resolved" if self.resolved_at else "unresolved"
        return (
            f"<IngestionQuarantine("
            f"txn={self.transaction_id}, "
            f"{self.platform_name}/{self.source_type}/{self.source_status}, "
            f"{resolved})>"
        )
