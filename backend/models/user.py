"""
Module: user
Purpose: User ORM model for authentication
Dependencies: SQLAlchemy
Platform: Universal

The User model represents application users for authentication.

Author: Claude Code
Created: January 25, 2026
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import hashlib
import secrets

from backend.models import Base


class User(Base):
    """
    Represents an application user for authentication.

    Attributes:
        id (UUID): Primary key
        email (str): User email (case-insensitive unique)
        password_hash (str): Hashed password
        name (str): User display name
        organization_id (UUID): User's organization (NULL only for pending users)
        status (str): Lifecycle status (pending, active, suspended, disabled)
        is_active (bool): Whether user can login
        is_admin (bool): Whether user has admin privileges
        role (str): RBAC role (admin, manager, accountant, viewer)
        created_at (DateTime): When created
        updated_at (DateTime): When last updated
        last_login (DateTime): When user last logged in

    DB Constraints:
        - Case-insensitive email uniqueness via lower(email) index
        - CHECK: pending users may have NULL org; non-pending must have org
    """

    __tablename__ = "users"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile
    name = Column(String(255), nullable=False)

    # Organization link
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Lifecycle status: pending, active, suspended, disabled
    # pending users have NULL organization_id (registration in progress)
    # non-pending users must have organization_id (DB enforced via CHECK)
    status = Column(String(20), default="pending", nullable=False)

    # Role-based access control
    # Roles: admin, manager, accountant, viewer
    role = Column(String(50), default="viewer", nullable=False)

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
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization", lazy="select")
    client_assignments = relationship(
        "ClientAssignment",
        foreign_keys="ClientAssignment.user_id",
        back_populates="user",
        lazy="select"
    )

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        # Simple SHA256 hash with salt (in production, use bcrypt)
        salt = secrets.token_hex(16)
        hash_input = f"{salt}:{password}"
        password_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        self.password_hash = f"{salt}:{password_hash}"

    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        if not self.password_hash or ":" not in self.password_hash:
            return False
        salt, stored_hash = self.password_hash.split(":", 1)
        hash_input = f"{salt}:{password}"
        computed_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        return computed_hash == stored_hash

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, email={self.email})>"
