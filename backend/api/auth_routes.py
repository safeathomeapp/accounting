"""API routes for authentication.

Provides REST endpoints for user login and authentication.
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import jwt

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Login request model."""
    email: str
    password: str


class LoginResponse(BaseModel):
    """Login response model."""
    token: str
    user: Dict[str, Any]


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """
    Authenticate user and return JWT token.

    For now, this is a simple demo implementation that accepts any email/password.
    In production, you would validate against a users table.

    Args:
        request: Login credentials (email and password)
        db: Database session

    Returns:
        JWT token and user information
    """
    # Demo: accept test@example.com with any password
    if request.email != "test@example.com":
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create JWT token
    payload = {
        "email": request.email,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm="HS256"
    )

    user = {
        "email": request.email,
        "name": "Test User",
        "id": "1",
    }

    logger.info(f"User logged in: {request.email}")

    return LoginResponse(token=token, user=user)


@router.get("/profile")
def get_profile(
    authorization: str = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current user profile.

    Args:
        authorization: Bearer token from header
        db: Database session

    Returns:
        User profile information
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"]
        )
        email = payload.get("email")
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    return {
        "email": email,
        "name": "Test User",
        "id": "1",
    }
