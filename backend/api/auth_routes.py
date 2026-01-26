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


class InviteUserRequest(BaseModel):
    """Invite user to organization request model."""
    email: str
    name: str
    role: str = "viewer"  # admin, manager, accountant, viewer


class UpdateUserRoleRequest(BaseModel):
    """Update user role request model."""
    role: str


# Valid roles for access control
VALID_ROLES = ["admin", "manager", "accountant", "viewer"]

ROLE_DESCRIPTIONS = {
    "admin": "Full access - can manage users, settings, and all data",
    "manager": "Can manage clients, transactions, and view reports",
    "accountant": "Can view and edit transactions and accounts",
    "viewer": "Read-only access to view data",
}


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
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get user from database
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "email": user.email,
        "name": user.name,
        "id": str(user.id),
        "is_admin": user.is_admin,
        "role": getattr(user, 'role', 'viewer'),
    }


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/users")
def list_users(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all users in the current user's organization.

    Args:
        authorization: Bearer token from header
        db: Database session

    Returns:
        List of users in the organization
    """
    current_user = get_current_user(authorization, db)

    # Get all users in the same organization
    users = db.query(User).filter(
        User.organization_id == current_user.organization_id,
        User.is_active == True
    ).order_by(User.created_at.desc()).all()

    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.name,
                "role": getattr(u, 'role', 'viewer'),
                "is_admin": u.is_admin,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
        "total": len(users),
    }


@router.get("/roles")
def list_roles() -> Dict[str, Any]:
    """
    List all available roles and their descriptions.

    Returns:
        List of roles with descriptions
    """
    return {
        "roles": [
            {"id": role, "name": role.title(), "description": desc}
            for role, desc in ROLE_DESCRIPTIONS.items()
        ]
    }


@router.post("/users")
def invite_user(
    request: InviteUserRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Invite a new user to the organization.

    Args:
        request: User invitation data
        authorization: Bearer token from header
        db: Database session

    Returns:
        Created user information
    """
    current_user = get_current_user(authorization, db)

    # Only admins can invite users
    if not current_user.is_admin and getattr(current_user, 'role', 'viewer') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can invite users")

    # Validate role
    if request.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")

    # Check if email already exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user with a temporary password
    import secrets
    temp_password = secrets.token_urlsafe(12)

    user = User(
        email=request.email,
        name=request.name,
        organization_id=current_user.organization_id,
        role=request.role,
        is_admin=(request.role == "admin"),
        is_active=True,
    )
    user.set_password(temp_password)

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"User invited: {user.email} with role {request.role} by {current_user.email}")

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "temp_password": temp_password,  # In production, send this via email
        "message": f"User invited successfully. Temporary password: {temp_password}",
    }


@router.put("/users/{user_id}")
def update_user_role(
    user_id: str,
    request: UpdateUserRoleRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update a user's role.

    Args:
        user_id: ID of the user to update
        request: New role data
        authorization: Bearer token from header
        db: Database session

    Returns:
        Updated user information
    """
    current_user = get_current_user(authorization, db)

    # Only admins can update roles
    if not current_user.is_admin and getattr(current_user, 'role', 'viewer') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can update user roles")

    # Validate role
    if request.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")

    # Find the user
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-demotion from admin
    if str(user.id) == str(current_user.id) and request.role != "admin" and current_user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot demote yourself from admin")

    # Update role
    user.role = request.role
    user.is_admin = (request.role == "admin")

    db.commit()
    db.refresh(user)

    logger.info(f"User role updated: {user.email} to {request.role} by {current_user.email}")

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "is_admin": user.is_admin,
        },
        "message": f"User role updated to {request.role}",
    }


@router.delete("/users/{user_id}")
def remove_user(
    user_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Remove a user from the organization (soft delete).

    Args:
        user_id: ID of the user to remove
        authorization: Bearer token from header
        db: Database session

    Returns:
        Confirmation message
    """
    current_user = get_current_user(authorization, db)

    # Only admins can remove users
    if not current_user.is_admin and getattr(current_user, 'role', 'viewer') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can remove users")

    # Find the user
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-removal
    if str(user.id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    # Soft delete - just deactivate
    user.is_active = False

    db.commit()

    logger.info(f"User removed: {user.email} by {current_user.email}")

    return {
        "message": f"User {user.email} has been removed",
    }
