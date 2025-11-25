"""Mobile Authentication Service

This service handles:
- Creating JWT tokens when user logs in
- Validating tokens on each API request
- Refreshing expired tokens
- Revoking sessions when user logs out

Key Concepts:
- JWT Token: Cryptographic token that proves user identity
- Access Token: Short-lived (15 min), used for API requests
- Refresh Token: Long-lived (7 days), used to get new access token
"""

import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from backend.models.mobile_session import MobileSession
from backend.config import settings


class MobileAuthService:
    """
    Service for mobile app authentication.

    Handles JWT token creation, validation, and refresh.
    """

    # Secret key for signing tokens (must be kept secret!)
    # In production, this comes from environment variables
    JWT_SECRET = settings.secret_key or "your-secret-key-change-in-production"

    # Algorithm for signing tokens
    JWT_ALGORITHM = "HS256"

    # How long access token is valid (15 minutes)
    ACCESS_TOKEN_EXPIRY_MINUTES = 15

    # How long refresh token is valid (7 days)
    REFRESH_TOKEN_EXPIRY_DAYS = 7

    @staticmethod
    def create_access_token(
        user_id: UUID,
        organization_id: UUID,
        device_id: str,
        expires_in_minutes: int = ACCESS_TOKEN_EXPIRY_MINUTES
    ) -> str:
        """
        Create a JWT access token.

        This token is sent with every API request to prove user identity.

        Args:
            user_id: User's ID
            organization_id: Organization ID
            device_id: Device identifier
            expires_in_minutes: How long token is valid

        Returns:
            JWT token string

        Example:
            token = MobileAuthService.create_access_token(
                user_id=user_id,
                organization_id=org_id,
                device_id="iPhone_12345"
            )
            # Returns: "eyJ0eXAiOiJKV1QiLCJhbGc..."
        """
        # Create expiry time
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

        # Payload is the data inside the token
        payload = {
            "user_id": str(user_id),
            "organization_id": str(organization_id),
            "device_id": device_id,
            "iat": datetime.now(timezone.utc),  # Issued at
            "exp": expires_at,  # Expiration time
            "token_type": "access"
        }

        # Sign the payload with secret key
        # This creates a token that can't be forged
        token = jwt.encode(
            payload,
            MobileAuthService.JWT_SECRET,
            algorithm=MobileAuthService.JWT_ALGORITHM
        )

        return token

    @staticmethod
    def create_refresh_token(
        user_id: UUID,
        organization_id: UUID,
        device_id: str,
        expires_in_days: int = REFRESH_TOKEN_EXPIRY_DAYS
    ) -> str:
        """
        Create a JWT refresh token.

        This token is used ONLY to get a new access token.
        It's stored securely on the phone and not sent with API requests.

        Args:
            user_id: User's ID
            organization_id: Organization ID
            device_id: Device identifier
            expires_in_days: How long token is valid

        Returns:
            JWT token string
        """
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        payload = {
            "user_id": str(user_id),
            "organization_id": str(organization_id),
            "device_id": device_id,
            "iat": datetime.now(timezone.utc),
            "exp": expires_at,
            "token_type": "refresh"
        }

        token = jwt.encode(
            payload,
            MobileAuthService.JWT_SECRET,
            algorithm=MobileAuthService.JWT_ALGORITHM
        )

        return token

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verify and decode a JWT token.

        Call this on every API request to validate the token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload if valid, None if invalid

        Example:
            payload = MobileAuthService.verify_token(token)
            if payload:
                user_id = payload["user_id"]
                # Token is valid, process request
            else:
                # Token is invalid, return 401 Unauthorized
        """
        try:
            # Decode and verify the token
            # If signature is invalid or token expired, this raises an exception
            payload = jwt.decode(
                token,
                MobileAuthService.JWT_SECRET,
                algorithms=[MobileAuthService.JWT_ALGORITHM]
            )
            return payload

        except jwt.ExpiredSignatureError:
            # Token has expired
            return None
        except jwt.InvalidTokenError:
            # Token is invalid (tampered, wrong format, etc.)
            return None

    @staticmethod
    def verify_access_token(token: str) -> Optional[dict]:
        """
        Verify token is an access token (not refresh token).

        Args:
            token: JWT token string

        Returns:
            Decoded payload if valid access token, None otherwise
        """
        payload = MobileAuthService.verify_token(token)
        if payload and payload.get("token_type") == "access":
            return payload
        return None

    @staticmethod
    def verify_refresh_token(token: str) -> Optional[dict]:
        """
        Verify token is a refresh token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload if valid refresh token, None otherwise
        """
        payload = MobileAuthService.verify_token(token)
        if payload and payload.get("token_type") == "refresh":
            return payload
        return None

    @staticmethod
    def create_session(
        db: Session,
        user_id: UUID,
        organization_id: UUID,
        device_id: str,
        device_name: str = None,
        device_os: str = None,
        app_version: str = None
    ) -> Tuple[str, str, MobileSession]:
        """
        Create a new mobile session (user login).

        This creates both access and refresh tokens and saves session to database.

        Args:
            db: Database session
            user_id: User's ID
            organization_id: Organization ID
            device_id: Device identifier
            device_name: Device name (optional, for display)
            device_os: Device OS (optional, "iOS" or "Android")
            app_version: App version (optional)

        Returns:
            Tuple of (access_token, refresh_token, session_object)

        Example:
            access_token, refresh_token, session = MobileAuthService.create_session(
                db=db,
                user_id=user_id,
                organization_id=org_id,
                device_id="iPhone_12345",
                device_name="John's iPhone 14",
                device_os="iOS",
                app_version="1.0.0"
            )
        """
        # Create tokens
        access_token = MobileAuthService.create_access_token(
            user_id=user_id,
            organization_id=organization_id,
            device_id=device_id
        )

        refresh_token = MobileAuthService.create_refresh_token(
            user_id=user_id,
            organization_id=organization_id,
            device_id=device_id
        )

        # Calculate expiry times
        access_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=MobileAuthService.ACCESS_TOKEN_EXPIRY_MINUTES
        )
        refresh_expires_at = datetime.now(timezone.utc) + timedelta(
            days=MobileAuthService.REFRESH_TOKEN_EXPIRY_DAYS
        )

        # Create session record in database
        session = MobileSession(
            user_id=user_id,
            organization_id=organization_id,
            device_id=device_id,
            device_name=device_name,
            device_os=device_os,
            app_version=app_version,
            access_token=access_token,
            access_token_expires_at=access_expires_at,
            refresh_token=refresh_token,
            refresh_token_expires_at=refresh_expires_at
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        return access_token, refresh_token, session

    @staticmethod
    def refresh_access_token(
        db: Session,
        refresh_token: str,
        device_id: str
    ) -> Optional[Tuple[str, MobileSession]]:
        """
        Use refresh token to get a new access token.

        Called when access token expires.

        Args:
            db: Database session
            refresh_token: Refresh token from user
            device_id: Device ID (for security check)

        Returns:
            Tuple of (new_access_token, session) or None if refresh failed

        Example:
            result = MobileAuthService.refresh_access_token(
                db=db,
                refresh_token=refresh_token,
                device_id="iPhone_12345"
            )
            if result:
                new_access_token, session = result
                # Success - use new access token
            else:
                # Failed - ask user to log in again
        """
        # Verify refresh token is valid
        payload = MobileAuthService.verify_refresh_token(refresh_token)
        if not payload:
            return None

        # Device ID must match (prevent token sharing between devices)
        if payload.get("device_id") != device_id:
            return None

        user_id = UUID(payload["user_id"])
        organization_id = UUID(payload["organization_id"])

        # Find existing session
        session = db.query(MobileSession).filter(
            MobileSession.user_id == user_id,
            MobileSession.organization_id == organization_id,
            MobileSession.device_id == device_id,
            MobileSession.is_active == 1
        ).first()

        if not session:
            return None

        # Check if refresh token is expired
        if session.is_refresh_token_expired():
            session.revoke(reason="refresh_token_expired")
            db.commit()
            return None

        # Create new access token
        new_access_token = MobileAuthService.create_access_token(
            user_id=user_id,
            organization_id=organization_id,
            device_id=device_id
        )

        # Update session
        access_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=MobileAuthService.ACCESS_TOKEN_EXPIRY_MINUTES
        )
        session.access_token = new_access_token
        session.access_token_expires_at = access_expires_at
        session.increment_refresh_count()
        session.mark_activity()

        db.commit()
        db.refresh(session)

        return new_access_token, session

    @staticmethod
    def revoke_session(db: Session, user_id: UUID, organization_id: UUID, device_id: str):
        """
        Revoke a session (user logout).

        Args:
            db: Database session
            user_id: User's ID
            organization_id: Organization ID
            device_id: Device ID

        Example:
            MobileAuthService.revoke_session(
                db=db,
                user_id=user_id,
                organization_id=org_id,
                device_id="iPhone_12345"
            )
        """
        session = db.query(MobileSession).filter(
            MobileSession.user_id == user_id,
            MobileSession.organization_id == organization_id,
            MobileSession.device_id == device_id,
            MobileSession.is_active == 1
        ).first()

        if session:
            session.revoke(reason="user_logout")
            db.commit()

    @staticmethod
    def get_session_from_token(
        db: Session,
        access_token: str
    ) -> Optional[MobileSession]:
        """
        Get session record from access token.

        Useful for updating session (activity, request count, etc.)

        Args:
            db: Database session
            access_token: JWT access token

        Returns:
            Session object if found and valid, None otherwise
        """
        # Verify token is valid
        payload = MobileAuthService.verify_access_token(access_token)
        if not payload:
            return None

        user_id = UUID(payload["user_id"])
        organization_id = UUID(payload["organization_id"])
        device_id = payload["device_id"]

        # Find session in database
        session = db.query(MobileSession).filter(
            MobileSession.user_id == user_id,
            MobileSession.organization_id == organization_id,
            MobileSession.device_id == device_id,
            MobileSession.is_active == 1
        ).first()

        return session
