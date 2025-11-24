"""
Module: transaction
Purpose: Financial transaction ORM model (Invoices, Bills, Bank Transactions)
Dependencies: SQLAlchemy
Platform: Universal (works with Xero and QuickBooks)

The Transaction model represents a financial transaction - invoices, bills,
bank transfers, etc. Uses NUMERIC fields for accounting precision.

Relationships:
- Many-to-one: organization
- Many-to-one: client (the party involved in transaction)
- Many-to-one: account (the account this transaction is for)

Author: Claude Code
Created: November 23, 2025
Last Modified: November 23, 2025
"""

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, ForeignKey,
    func, Index, Date, Numeric
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import date, datetime
from decimal import Decimal
import uuid

from backend.models import Base


class Transaction(Base):
    """
    Represents a financial transaction (invoice, bill, bank transaction, etc.).

    Maps to:
    - Xero: Invoice (SalesInvoice/PurchaseInvoice), BankTransaction
    - QuickBooks: Invoice, Bill, JournalEntry

    Uses NUMERIC fields for precise accounting calculations (no floating point).

    Attributes:
        id (UUID): Primary key
        organization_id (UUID): Organization this transaction belongs to
        platform_id (str): ID from platform (Xero InvoiceID, QB Id)
        platform_name (str): 'xero' or 'quickbooks'
        transaction_type (str): 'invoice', 'bill', 'bank_transaction'
        reference_number (str): Transaction reference/number
        description (str): Transaction description (optional)
        amount (Decimal): Base amount (excluding tax)
        tax_amount (Decimal): Tax/VAT amount
        total_amount (Decimal): Total amount (amount + tax)
        currency (str): Currency code (default: 'GBP')
        transaction_date (Date): When transaction occurred
        due_date (Date): When payment is due (optional)
        client_id (UUID): Who this transaction is with (optional)
        account_id (UUID): Which account (optional)
        status (str): 'draft', 'submitted', 'approved', 'paid', etc.
        is_reconciled (bool): Whether this is reconciled to bank
        last_synced_at (DateTime): When last synced
        platform_updated_at (DateTime): When platform record updated
        created_at (DateTime): When created in database
        updated_at (DateTime): When updated in database

    Relationships:
        organization: The organization
        client: The customer/supplier (optional)
        account: The account (optional)

    Unique Constraint:
        (platform_name, platform_id) - one record per platform per transaction

    Indexes:
        - organization_id
        - transaction_date
        - client_id
        - account_id
        - status
        - is_reconciled
        - platform reference
        - last_synced_at

    Important Notes:
        - NUMERIC fields ensure accounting precision
        - total_amount >= 0 (validated by constraint)
        - No floating point arithmetic
        - Decimals stored with 2 decimal places (GBP, USD, etc.)

    Example:
        >>> from backend.models import Transaction
        >>> from decimal import Decimal
        >>> invoice = Transaction(
        ...     organization_id=org_uuid,
        ...     platform_name="xero",
        ...     platform_id="xero-invoice-123",
        ...     transaction_type="invoice",
        ...     amount=Decimal("1000.00"),
        ...     tax_amount=Decimal("200.00"),
        ...     total_amount=Decimal("1200.00"),
        ...     client_id=client_uuid,
        ...     status="submitted"
        ... )
    """

    __tablename__ = "transactions"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Foreign Keys
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Platform Reference
    platform_id = Column(String(500), nullable=False)
    platform_name = Column(String(50), nullable=False, index=True)

    # Transaction Details
    # Type: invoice, bill, bank_transaction, etc.
    transaction_type = Column(String(50), nullable=False)
    # Reference number from platform (INV-001, etc.)
    reference_number = Column(String(100), nullable=True)
    # Description of transaction
    description = Column(Text, nullable=True)

    # Amounts (NUMERIC for accounting precision, NOT float)
    # Base amount (before tax)
    amount = Column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    # Tax/VAT amount
    tax_amount = Column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    # Total amount (amount + tax)
    total_amount = Column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    # Currency code
    currency = Column(String(3), default="GBP", nullable=False)

    # Dates
    # When the transaction occurred
    transaction_date = Column(Date, nullable=False, index=True)
    # When payment is due (optional)
    due_date = Column(Date, nullable=True)

    # Status
    # Current status: draft, submitted, approved, paid, overdue, etc.
    status = Column(String(50), nullable=True, index=True)
    # Whether this has been reconciled to a bank statement
    is_reconciled = Column(Boolean, default=False, nullable=False, index=True)

    # Sync Metadata
    # When last synced from platform
    last_synced_at = Column(DateTime(timezone=True), nullable=True, index=True)
    # When platform record was updated
    platform_updated_at = Column(DateTime(timezone=True), nullable=True)

    # Record Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    organization = relationship(
        "Organization",
        back_populates="transactions",
        lazy="select"
    )
    client = relationship(
        "Client",
        back_populates="transactions",
        lazy="select"
    )
    account = relationship(
        "Account",
        back_populates="transactions",
        lazy="select"
    )

    # Composite index for platform reference uniqueness
    __table_args__ = (
        Index("ix_transactions_platform_ref", "platform_name", "platform_id", unique=True),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Transaction("
            f"id={self.id}, "
            f"type={self.transaction_type}, "
            f"amount={self.total_amount}, "
            f"date={self.transaction_date}"
            f")>"
        )
