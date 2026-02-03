"""
Module: accounting_platform
Purpose: Accounting platform configuration (Xero, QuickBooks)
Dependencies: SQLAlchemy
Platform: Xero (Phase 1), QuickBooks (Phase 2+)

The AccountingPlatform model stores connection details for each accounting platform
an organization uses. OAuth credentials are stored encrypted in the database.

Relationships:
- Many-to-one: organization (each platform belongs to an organization)
- One-to-many: oauth_tokens (token history)
- One-to-many: sync_history (sync tracking)

Author: Claude Code
Created: November 23, 2025
Last Modified: November 23, 2025
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, LargeBinary, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.models import Base


class AccountingPlatform(Base):
    """
    Represents a connection to an accounting platform (Xero or QuickBooks).

    Each organization can have multiple platform connections. This model stores
    OAuth credentials (encrypted), connection status, and synchronization metadata.

    Attributes:
        id (UUID): Primary key
        organization_id (UUID): Foreign key to Organization
        platform_name (str): 'xero' or 'quickbooks'
        platform_version (str): Platform API version
        client_id (str): OAuth client ID (plaintext - needed for OAuth flows)
        client_secret_encrypted (bytes): Encrypted OAuth client secret
        access_token_encrypted (bytes): Encrypted current access token
        refresh_token_encrypted (bytes): Encrypted refresh token
        token_expires_at (DateTime): When access token expires
        tenant_id (str): Xero organization ID (tenant)
        realm_id (str): QuickBooks company/realm ID
        is_active (bool): Whether this connection is active
        connection_status (str): 'pending', 'connected', 'error'
        last_sync_at (DateTime): When last sync occurred
        last_error_message (str): Last error message if connection failed
        created_at (DateTime): When record created
        updated_at (DateTime): When record updated

    Relationships:
        organization: The organization this platform belongs to
        oauth_tokens: Historical OAuth tokens
        sync_history: Synchronization events

    Note:
        - client_id is stored plaintext (needed for OAuth, not sensitive)
        - client_secret_encrypted and tokens are encrypted at rest
        - Use EncryptionManager from config.py to encrypt/decrypt
        - tenant_id (Xero) and realm_id (QB) enable multi-tenant API support

    Example:
        >>> from backend.models import AccountingPlatform
        >>> platform = AccountingPlatform(
        ...     organization_id=org_uuid,
        ...     platform_name="xero",
        ...     client_id="xero-client-id",
        ...     # client_secret would be encrypted before saving
        ... )
    """

    __tablename__ = "accounting_platforms"

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

    # Platform Identification
    platform_name = Column(String(50), nullable=False, index=True)
    # Valid values: 'xero', 'quickbooks'
    platform_version = Column(String(50), nullable=True)

    # Business Client (the managed business whose external system this connects to)
    # Composite FK in DB enforces same-org. Nullable during transition.
    managed_client_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )

    # OAuth Credentials
    # oauth_client_id: plaintext (needed for OAuth flows, not sensitive)
    # NOTE: Renamed from client_id to remove semantic collision with business clients
    oauth_client_id = Column(String(500), nullable=False)
    # client_secret: ENCRYPTED (sensitive - never log or display)
    client_secret_encrypted = Column(LargeBinary, nullable=False)
    # access_token: ENCRYPTED (sensitive - changes frequently)
    access_token_encrypted = Column(LargeBinary, nullable=True)
    # refresh_token: ENCRYPTED (sensitive - used to get new access tokens)
    refresh_token_encrypted = Column(LargeBinary, nullable=True)
    # When access token expires
    token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Platform-Specific IDs
    # Xero: Organization ID (for multi-tenant support)
    tenant_id = Column(String(255), nullable=True, index=True)
    # QuickBooks: Company/Realm ID
    realm_id = Column(String(255), nullable=True, index=True)

    # Connection Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    # Status: pending (not yet authenticated), connected (working), error (failed)
    connection_status = Column(String(50), default="pending", nullable=False, index=True)
    # When was last successful sync
    last_sync_at = Column(DateTime(timezone=True), nullable=True, index=True)
    # If connection_status='error', what was the error?
    last_error_message = Column(String(500), nullable=True)

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
    organization = relationship(
        "Organization",
        back_populates="accounting_platforms",
        lazy="select"
    )
    oauth_tokens = relationship(
        "OAuthToken",
        back_populates="platform",
        cascade="all, delete-orphan",
        lazy="select"
    )
    sync_history = relationship(
        "SyncHistory",
        back_populates="platform",
        cascade="all, delete-orphan",
        lazy="select"
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AccountingPlatform("
            f"id={self.id}, "
            f"platform={self.platform_name}, "
            f"status={self.connection_status}"
            f")>"
        )
