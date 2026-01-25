"""API routes for authentication.

Provides REST endpoints for user login and authentication.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.config import settings
from backend.models.user import User
from backend.models.organization import Organization

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


class RegisterRequest(BaseModel):
    """Registration request model."""
    email: str
    password: str
    name: str


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        email = payload.get("email")
        user_id = payload.get("user_id")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """
    Authenticate user and return JWT token.

    Args:
        request: Login credentials (email and password)
        db: Database session

    Returns:
        JWT token and user information
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()

    # Check if user exists and password is correct
    if not user or not user.check_password(request.password):
        # Fall back to demo mode for test@example.com
        if request.email == "test@example.com" and request.password == "password":
            # Get the first organization for demo mode
            demo_org = db.query(Organization).filter(Organization.is_active == True).first()
            demo_org_id = str(demo_org.id) if demo_org else None
            demo_org_name = demo_org.name if demo_org else "Demo Company"
            # Create demo token
            payload = {
                "email": request.email,
                "user_id": "demo",
                "organization_id": demo_org_id,
                "exp": datetime.utcnow() + timedelta(hours=24),
                "iat": datetime.utcnow(),
            }
            token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
            return LoginResponse(
                token=token,
                user={"email": request.email, "name": demo_org_name, "id": "demo", "organization_id": demo_org_id}
            )
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is disabled")

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create JWT token
    payload = {
        "email": user.email,
        "user_id": str(user.id),
        "organization_id": str(user.organization_id) if user.organization_id else None,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")

    logger.info(f"User logged in: {user.email}")

    return LoginResponse(
        token=token,
        user={
            "email": user.email,
            "name": user.name,
            "id": str(user.id),
            "is_admin": user.is_admin,
            "organization_id": str(user.organization_id) if user.organization_id else None,
        }
    )


@router.post("/register", response_model=LoginResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """
    Register a new user.

    Args:
        request: Registration data
        db: Database session

    Returns:
        JWT token and user information
    """
    # Check if email already exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create a new organization for this user (business)
    organization = Organization(
        name=request.name,  # Business name
        email=request.email,
    )
    db.add(organization)
    db.flush()  # Get the organization ID without committing

    # Create new user linked to the organization
    user = User(
        email=request.email,
        name=request.name,
        organization_id=organization.id,
        is_admin=True,  # First user is admin of their organization
    )
    user.set_password(request.password)

    db.add(user)
    db.commit()
    db.refresh(user)

    # Create JWT token
    payload = {
        "email": user.email,
        "user_id": str(user.id),
        "organization_id": str(user.organization_id),
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")

    logger.info(f"New user registered: {user.email} with organization {organization.id}")

    return LoginResponse(
        token=token,
        user={
            "email": user.email,
            "name": user.name,
            "id": str(user.id),
            "is_admin": user.is_admin,
            "organization_id": str(user.organization_id),
        }
    )


@router.get("/profile")
def get_profile(
    authorization: Optional[str] = Header(None),
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
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        email = payload.get("email")
        user_id = payload.get("user_id")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Handle demo user
    if user_id == "demo":
        return {
            "email": email,
            "name": "Demo User",
            "id": "demo",
            "is_admin": False,
        }

    # Get real user from database
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "email": user.email,
        "name": user.name,
        "id": str(user.id),
        "is_admin": user.is_admin,
    }
