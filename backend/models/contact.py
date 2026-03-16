"""
Module: contact
Purpose: Contact ORM model for client's vendors/customers/suppliers
Dependencies: SQLAlchemy
Platform: Universal

The Contact model represents a vendor, customer, or supplier that a Client
deals with. These are the counterparties on invoices and bills.

Domain Model:
- Organization = The accounting firm
- Client = A business whose books the org manages
- Contact = A vendor/customer that the Client transacts with

Example:
- Organization: "Thompson & Associates Accountants"
- Client: "Riverside Construction Ltd" (whose books we manage)
- Contact: "Crouchers Orchards" (vendor that sends invoices to Riverside)

Author: Claude Code
Created: February 2026
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from backend.models import Base


class Contact(Base):
    """
    Represents a vendor, customer, or supplier for a Client.

    These are the counterparties that appear on invoices, bills, and receipts.
    Used for fuzzy matching during OCR extraction and for syncing with
    accounting software contact databases.

    Attributes:
        id (UUID): Primary key
        client_id (UUID): The client this contact belongs to
        organization_id (UUID): Organization scope (denormalized for RLS)
        name (str): Contact name (required)
        contact_type (str): 'vendor', 'customer', 'both'
        email (str): Email address
        phone (str): Phone number
        website (str): Website URL
        address_line1 (str): Address line 1
        address_line2 (str): Address line 2
        city (str): City
        postal_code (str): Postal code
        country (str): Country
        tax_number (str): VAT number / Tax ID
        payment_terms (str): Default payment terms
        default_nominal_code (str): Default expense/revenue account
        notes (str): Internal notes
        platform_id (str): ID from accounting software (if synced)
        platform_name (str): Which platform ('xero', 'quickbooks')
        is_active (bool): Whether contact is active
        created_at (DateTime): Record creation timestamp
        updated_at (DateTime): Record modification timestamp

    Relationships:
        client: The client this contact belongs to
        organization: Organization scope
    """

    __tablename__ = "contacts"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Foreign Keys
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Denormalized for RLS (Row Level Security)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Core Fields
    name = Column(String(255), nullable=False, index=True)
    contact_type = Column(String(50), nullable=False, default="vendor")  # vendor, customer, both

    # Contact Information
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)

    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    # Tax & Accounting
    tax_number = Column(String(50), nullable=True)  # VAT number
    payment_terms = Column(String(50), nullable=True)  # e.g., 'net30'
    default_nominal_code = Column(String(50), nullable=True)  # Default account code
    currency = Column(String(3), nullable=True, default="GBP")

    # Notes
    notes = Column(Text, nullable=True)

    # Platform Sync (for accounting software integration)
    platform_id = Column(String(500), nullable=True)
    platform_name = Column(String(50), nullable=True)  # 'xero', 'quickbooks', etc.
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
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
    client = relationship(
        "Client",
        back_populates="contacts",
        lazy="select"
    )
    organization = relationship(
        "Organization",
        lazy="select"
    )

    # Indexes
    __table_args__ = (
        # Unique constraint per client + platform
        Index(
            "ix_contacts_client_platform",
            "client_id", "platform_name", "platform_id",
            unique=True,
            postgresql_where="platform_id IS NOT NULL"
        ),
        # Name search within client
        Index("ix_contacts_client_name", "client_id", "name"),
    )

    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, name={self.name}, type={self.contact_type})>"
