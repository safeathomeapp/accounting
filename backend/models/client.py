"""
Module: client
Purpose: Customer/Contact ORM model
Dependencies: SQLAlchemy
Platform: Universal (works with Xero Contacts and QB Customers)

The Client model represents a customer, supplier, employee, or other contact.
It maps to Xero Contacts and QuickBooks Customers.

Relationships:
- Many-to-one: organization
- One-to-many: transactions (invoices, bills for this client)

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


class Client(Base):
    """
    Represents a customer, supplier, or other contact.

    Maps to:
    - Xero: Contact
    - QuickBooks: Customer (and Vendor)

    A client can be synced from multiple platforms, creating multiple records
    (one per platform instance). Deduplication happens in Phase 2.

    Attributes:
        id (UUID): Primary key, unique in our database
        organization_id (UUID): Organization this client belongs to
        platform_id (str): ID from the platform (Xero ContactID, QB Id)
        platform_name (str): Which platform ('xero', 'quickbooks')
        name (str): Client name (required)
        email (str): Email address (optional)
        phone (str): Phone number (optional)
        website (str): Website URL (optional)
        address_line1 (str): Address line 1 (optional)
        address_line2 (str): Address line 2 (optional)
        city (str): City (optional)
        postal_code (str): Postal code (optional)
        country (str): Country (optional)
        contact_type (str): 'customer', 'supplier', 'employee', 'other'
        industry (str): Industry classification (optional)
        tax_number (str): Tax ID / VAT number (optional)
        is_active (bool): Whether client is active
        last_synced_at (DateTime): When last synced from platform
        platform_updated_at (DateTime): When platform record was last updated
        created_at (DateTime): When created in our database
        updated_at (DateTime): When last updated in our database

    Relationships:
        organization: The organization this client belongs to
        transactions: Invoices/bills related to this client

    Unique Constraint:
        (platform_name, platform_id) - one record per platform per client

    Indexes:
        - organization_id: Find clients for an organization
        - platform_name, platform_id: Find by platform reference
        - email: Quick email lookups
        - is_active: Filter active clients
        - last_synced_at: Track sync status

    Example:
        >>> from backend.models import Client
        >>> customer = Client(
        ...     organization_id=org_uuid,
        ...     platform_name="xero",
        ...     platform_id="xero-contact-123",
        ...     name="Acme Corp",
        ...     email="contact@acme.com",
        ...     contact_type="customer"
        ... )
    """

    __tablename__ = "clients"

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
    # platform_id: Platform's unique identifier (Xero ContactID, QB Id)
    platform_id = Column(String(500), nullable=False)
    # Which platform: 'xero' or 'quickbooks'
    platform_name = Column(String(50), nullable=False, index=True)

    # Contact Information
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)

    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    # Classification
    # Type: customer, supplier, employee, other
    contact_type = Column(String(50), nullable=True)
    # Industry for categorization
    industry = Column(String(100), nullable=True)
    # Tax number / VAT ID
    tax_number = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Sync Metadata
    # When last synced from platform
    last_synced_at = Column(DateTime(timezone=True), nullable=True, index=True)
    # When platform record was last modified
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
        back_populates="clients",
        lazy="select"
    )
    transactions = relationship(
        "Transaction",
        back_populates="client",
        lazy="select"
    )
    accounts = relationship(
        "Account",
        back_populates="client",
        lazy="select"
    )
    assignments = relationship(
        "ClientAssignment",
        back_populates="client",
        lazy="select"
    )
    contacts = relationship(
        "Contact",
        back_populates="client",
        lazy="select",
        cascade="all, delete-orphan"
    )

    # Composite index for platform reference uniqueness
    __table_args__ = (
        Index("ix_clients_platform_reference", "platform_name", "platform_id", unique=True),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Client("
            f"id={self.id}, "
            f"name={self.name}, "
            f"platform={self.platform_name}"
            f")>"
        )
