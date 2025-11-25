"""Mobile Session & JWT Token Management

This module handles JWT tokens for mobile authentication.

Key Concepts:
- JWT Token: A secure token that proves user identity
- Access Token: Short-lived (15 min), used for API requests
- Refresh Token: Long-lived (7 days), used to get new access token
- Device Fingerprint: Identifies which phone/tablet is using the app

Database Table: mobile_sessions
Stores: Who is logged in, what device, when they logged in, when they'll expire
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID

from backend.models import Base


class MobileSession(Base):
    """
    JWT Session for mobile apps.

    Think of this like a "login record" - when a user logs into the mobile app,
    we create a MobileSession record so we can track:
    - Who logged in
    - When they logged in
    - When their session expires
    - What device they're using

    Example usage:
        session = MobileSession(
            user_id=uuid4(),
            organization_id=uuid4(),
            device_id="iPhone_12345",
            access_token="eyJ0eXA...",
            refresh_token="eyJ0eXA...",
            access_token_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
        )
        db.add(session)
        db.commit()
    """

    __tablename__ = "mobile_sessions"

    # Unique ID for this session
    # Example: "a1b2c3d4-e5f6-4789-0123-456789abcdef"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Which user owns this session
    # Links to User table (we'll add this later)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Which organization this user belongs to
    # Important for multi-tenant: prevent user A from accessing org B's data
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Device identifier
    # Examples: "iPhone_Apple_iPhone14,2", "Android_Pixel_6"
    # This prevents sharing tokens between devices
    device_id = Column(String(255), nullable=False)

    # Device name (for display)
    # Example: "John's iPhone 14"
    device_name = Column(String(255))

    # Device operating system
    # Values: "iOS", "Android"
    device_os = Column(String(50))

    # App version that's running on device
    # Example: "1.0.0"
    app_version = Column(String(50))

    # ===== JWT TOKENS =====

    # Short-lived access token (expires in 15 minutes)
    # This is what the app sends with every request:
    # Header: Authorization: Bearer eyJ0eXA...
    access_token = Column(Text, nullable=False)

    # When this access token expires
    # If expired, app must use refresh_token to get a new one
    access_token_expires_at = Column(DateTime(timezone=True), nullable=False)

    # Long-lived refresh token (expires in 7 days)
    # Used only to request a new access token
    # Securely stored on device
    refresh_token = Column(Text, nullable=False)

    # When this refresh token expires
    # If expired, user must log in again
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=False)

    # ===== SESSION METADATA =====

    # When user logged in
    # Example: 2025-11-25 10:30:45 UTC
    login_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # When user last used the app
    # Gets updated every time they make an API request
    last_activity_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # If user logged out, when did they log out?
    # NULL = still logged in
    # 2025-11-26 10:30:45 = logged out at this time
    logout_at = Column(DateTime(timezone=True))

    # Is this session still active?
    # FALSE = user logged out or tokens expired
    # TRUE = user can still use the app
    is_active = Column(Integer, default=1)  # 1 = true, 0 = false

    # If session was revoked (logged out), why?
    # Examples:
    # - "user_logout": User tapped logout
    # - "token_expired": Refresh token expired
    # - "security_issue": We detected suspicious activity
    revocation_reason = Column(String(100))

    # Last error (for debugging)
    # Example: "IP address changed from 192.168.1.1 to 192.168.1.2"
    last_error = Column(Text)

    # Number of times tokens have been refreshed
    # Useful for analytics: how often is user using app?
    refresh_count = Column(Integer, default=0)

    # Number of API requests made in this session
    # Useful for analytics: how active is user?
    request_count = Column(Integer, default=0)

    def __repr__(self):
        """Human-readable representation for debugging"""
        return f"<MobileSession {self.user_id} on {self.device_name}>"

    def is_access_token_expired(self) -> bool:
        """
        Check if access token has expired.

        Returns:
            True if token expired, False if still valid

        Example:
            session = db.query(MobileSession).first()
            if session.is_access_token_expired():
                # Need to refresh token
                new_token = refresh_access_token(session)
        """
        return datetime.now(timezone.utc) >= self.access_token_expires_at

    def is_refresh_token_expired(self) -> bool:
        """
        Check if refresh token has expired.

        Returns:
            True if token expired, False if still valid

        Example:
            session = db.query(MobileSession).first()
            if session.is_refresh_token_expired():
                # Must log in again
                user_must_login_again()
        """
        return datetime.now(timezone.utc) >= self.refresh_token_expires_at

    def mark_activity(self):
        """
        Update last activity time.

        Call this every time user makes an API request.
        Helps track when user was last active.

        Example:
            session = get_session_from_token(token)
            session.mark_activity()
            db.commit()
        """
        self.last_activity_at = datetime.now(timezone.utc)
        self.request_count += 1

    def increment_refresh_count(self):
        """Increment refresh count when token is refreshed"""
        self.refresh_count += 1

    def revoke(self, reason: str = "user_logout", error: str = None):
        """
        Log user out (revoke their session).

        Args:
            reason: Why session was revoked
            error: Optional error message for debugging

        Example:
            session = get_session_from_token(token)
            session.revoke(reason="token_expired", error="Refresh token expired")
            db.commit()
        """
        self.is_active = 0
        self.logout_at = datetime.now(timezone.utc)
        self.revocation_reason = reason
        if error:
            self.last_error = error
