"""
Module: account
Purpose: Chart of accounts ORM model
Dependencies: SQLAlchemy
Platform: Universal (works with Xero and QuickBooks)

The Account model represents a general ledger account from the chart of accounts.
Maps to Xero Accounts and QuickBooks Account objects.

Relationships:
- Many-to-one: organization
- One-to-many: transactions (transactions posted to this account)

Author: Claude Code
Created: November 23, 2025
Last Modified: November 23, 2025
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.models import Base


class Account(Base):
    """
    Represents a general ledger account.

    Maps to:
    - Xero: Account
    - QuickBooks: Account

    Attributes:
        id (UUID): Primary key
        organization_id (UUID): Organization this account belongs to
        platform_id (str): Platform's account ID
        platform_name (str): 'xero' or 'quickbooks'
        code (str): Account code (e.g., "200" for Sales, "4000" for Expenses)
        name (str): Account name (e.g., "Sales Income")
        account_type (str): Type of account
            - 'asset': Cash, Accounts Receivable, etc.
            - 'liability': Accounts Payable, Loans, etc.
            - 'equity': Owner's capital, retained earnings
            - 'income': Sales, service income
            - 'expense': Cost of goods, operating expenses
            - 'bank': Bank/cash accounts (special asset type)
        description (str): Detailed account description (optional)
        is_active (bool): Whether account is active
        created_at (DateTime): When created in database
        updated_at (DateTime): When updated in database

    Relationships:
        organization: The organization
        transactions: Transactions posted to this account

    Unique Constraint:
        (organization_id, code) - one account per code per organization

    Indexes:
        - organization_id
        - account_type
        - code

    Example:
        >>> from backend.models import Account
        >>> sales_account = Account(
        ...     organization_id=org_uuid,
        ...     platform_name="xero",
        ...     platform_id="xero-account-123",
        ...     code="200",
        ...     name="Sales Income",
        ...     account_type="income"
        ... )
    """

    __tablename__ = "accounts"

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

    # Platform Reference
    platform_id = Column(String(500), nullable=False)
    platform_name = Column(String(50), nullable=False, index=True)

    # Account Details
    # Account code (e.g., "200", "4000")
    code = Column(String(50), nullable=False)
    # Account name
    name = Column(String(255), nullable=False, index=True)
    # Account type: asset, liability, equity, income, expense, bank
    account_type = Column(String(50), nullable=True, index=True)
    # Account description
    description = Column(String(500), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

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
        back_populates="accounts",
        lazy="select"
    )
    transactions = relationship(
        "Transaction",
        back_populates="account",
        lazy="select"
    )

    # Unique constraint: code per organization
    __table_args__ = (
        Index("ix_accounts_org_code", "organization_id", "code", unique=True),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Account("
            f"id={self.id}, "
            f"code={self.code}, "
            f"name={self.name}, "
            f"type={self.account_type}"
            f")>"
        )
