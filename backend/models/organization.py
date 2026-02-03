"""
Module: organization
Purpose: Organization/Practice ORM model
Dependencies: SQLAlchemy
Platform: Universal

The Organization model represents a bookkeeping practice or organization.
Currently designed for single-tenant (one practice), but extensible to multi-tenant in Phase 3.

Relationships:
- One-to-many: accounting_platforms (Xero/QB configurations)
- One-to-many: clients (customers/contacts)
- One-to-many: accounts (chart of accounts)
- One-to-many: transactions (financial transactions)
- One-to-many: ai_analysis_results
- One-to-many: sync_history
- One-to-many: audit_log

Author: Claude Code
Created: November 23, 2025
Last Modified: November 23, 2025
"""

from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.models import Base


class Organization(Base):
    """
    Represents a bookkeeping practice or organization.

    This is the top-level entity. All other data belongs to an organization.

    Attributes:
        id (UUID): Primary key, auto-generated
        name (str): Organization name (required)
        email (str): Organization email (required, unique)
        phone (str): Phone number (optional)
        address_line1 (str): Address line 1 (optional)
        address_line2 (str): Address line 2 (optional)
        city (str): City (optional)
        postal_code (str): Postal code (optional)
        country (str): Country (optional, default: 'UK')
        timezone (str): Timezone (default: 'Europe/London')
        currency (str): Currency code (default: 'GBP')
        is_active (bool): Whether organization is active (default: True)
        created_at (DateTime): When record was created
        updated_at (DateTime): When record was last updated

    Relationships:
        accounting_platforms: Associated accounting platform configurations
        clients: Associated contacts/customers
        accounts: Chart of accounts
        transactions: Financial transactions
        ai_analysis_results: AI analysis results
        sync_history: Synchronization history
        audit_log: Audit trail
        document_inbox_items: Uploaded documents awaiting review

    Example:
        >>> org = Organization(
        ...     name="My Practice",
        ...     email="contact@mypractice.com",
        ...     country="UK",
        ...     timezone="Europe/London"
        ... )
        >>> db.add(org)
        >>> db.commit()
    """

    __tablename__ = "organizations"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Required Fields
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)

    # Optional Contact Info
    phone = Column(String(20), nullable=True)

    # Optional Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)

    # Configuration
    country = Column(String(100), default="UK", nullable=False)
    timezone = Column(String(50), default="Europe/London", nullable=False)
    currency = Column(String(3), default="GBP", nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships (lazy loading, will be populated when accessed)
    accounting_platforms = relationship(
        "AccountingPlatform",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="select"
    )
    clients = relationship(
        "Client",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="select"
    )
    accounts = relationship(
        "Account",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="select"
    )
    transactions = relationship(
        "Transaction",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="select"
    )
    ai_analysis_results = relationship(
        "AIAnalysisResult",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="select"
    )
    sync_history = relationship(
        "SyncHistory",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="select"
    )
    audit_log = relationship(
        "AuditLog",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="select"
    )
    document_inbox_items = relationship(
        "DocumentInboxItem",
        cascade="all, delete-orphan",
        lazy="select"
    )

    def __repr__(self) -> str:
        """String representation of Organization."""
        return f"<Organization(id={self.id}, name={self.name}, email={self.email})>"
