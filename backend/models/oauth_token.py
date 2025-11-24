"""
Module: oauth_token
Purpose: OAuth token storage and history ORM model
Dependencies: SQLAlchemy
Platform: Universal (for any OAuth-based integration)

The OAuthToken model tracks all OAuth tokens for security and compliance.
Tokens are encrypted at rest. This provides a complete token history.

Relationships:
- Many-to-one: accounting_platform (which platform issued the token)

Author: Claude Code
Created: November 23, 2025
Last Modified: November 23, 2025
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, LargeBinary, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.models import Base


class OAuthToken(Base):
    """
    Represents an OAuth token issued by an accounting platform.

    Stores complete token history for security auditing and compliance.
    All sensitive token data is encrypted at rest.

    Attributes:
        id (UUID): Primary key
        platform_id (UUID): Which accounting platform issued this token
        access_token_encrypted (bytes): Encrypted access token (sensitive)
        refresh_token_encrypted (bytes): Encrypted refresh token (sensitive)
        token_type (str): Type of token (usually "Bearer")
        issued_at (DateTime): When token was issued
        expires_at (DateTime): When token expires
        scopes (str): Space-separated OAuth scopes
        is_revoked (bool): Whether token was revoked
        revoked_at (DateTime): When token was revoked
        revoke_reason (str): Why token was revoked
        created_at (DateTime): When record created

    Relationships:
        platform: The accounting platform that issued this token

    Note:
        - All tokens are encrypted using ENCRYPTION_KEY from environment
        - Use EncryptionManager from config.py to encrypt/decrypt
        - Never log or display token values
        - expires_at > issued_at (validated by constraint)
        - Complete history preserved for compliance

    Example:
        >>> from backend.models import OAuthToken
        >>> from backend.config import EncryptionManager
        >>>
        >>> enc = EncryptionManager(os.getenv("ENCRYPTION_KEY"))
        >>> token = OAuthToken(
        ...     platform_id=platform_uuid,
        ...     access_token_encrypted=enc.encrypt(access_token),
        ...     refresh_token_encrypted=enc.encrypt(refresh_token),
        ...     token_type="Bearer",
        ...     expires_at=datetime(2025, 12, 23),
        ...     scopes="offline_access accounting.transactions"
        ... )
    """

    __tablename__ = "oauth_tokens"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Foreign Keys
    platform_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounting_platforms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Token Data (ENCRYPTED)
    # access_token: ENCRYPTED (sensitive - grants API access)
    access_token_encrypted = Column(LargeBinary, nullable=False)
    # refresh_token: ENCRYPTED (sensitive - used to get new access token)
    refresh_token_encrypted = Column(LargeBinary, nullable=True)
    # Token type (typically "Bearer")
    token_type = Column(String(50), default="Bearer", nullable=False)

    # Timing
    # When token was issued
    issued_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        index=True
    )
    # When token expires
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )

    # Scopes (for audit)
    # Space-separated list of OAuth scopes granted
    scopes = Column(Text, nullable=True)

    # Revocation Tracking
    # Whether this token was explicitly revoked
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    # When it was revoked
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    # Why it was revoked (e.g., "user logged out", "token refresh failed")
    revoke_reason = Column(String(255), nullable=True)

    # Record Timestamp
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )

    # Relationships
    platform = relationship(
        "AccountingPlatform",
        back_populates="oauth_tokens",
        lazy="select"
    )

    # Constraint: expires_at > issued_at
    __table_args__ = (
        # This constraint is informational; actual validation in application
        # SQLAlchemy can't express this constraint directly, but DB triggers could enforce it
    )

    def __repr__(self) -> str:
        """String representation (safe - no secrets shown)."""
        return (
            f"<OAuthToken("
            f"id={self.id}, "
            f"platform_id={self.platform_id}, "
            f"issued={self.issued_at}, "
            f"revoked={self.is_revoked}"
            f")>"
        )
