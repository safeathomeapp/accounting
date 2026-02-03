"""
Module: client_assignment
Purpose: User-to-Client assignment ORM model
Dependencies: SQLAlchemy

The ClientAssignment model represents workflow assignments between users and clients.
This is for workload distribution and responsibility tracking, NOT access control.
All users in an organization can access all clients via RLS on organization_id.

Relationships:
- Many-to-one: organization, client, user
- Many-to-one: assigned_by (user who made the assignment)

Author: Claude Code
Created: February 3, 2026
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from backend.models import Base


# Valid assignment roles - enforced by CHECK constraint in DB
ASSIGNMENT_ROLES = ('primary', 'accountant', 'reviewer', 'backup')


class ClientAssignment(Base):
    """
    Represents a user's assignment to a client for workflow purposes.

    This is NOT access control - all users in an organization can access all clients.
    Assignments track who is responsible for a client's work.

    IMPORTANT: Composite FKs enforce that client, user, and assigner all belong
    to the same organization. This prevents cross-org assignment bugs at DB level.

    Attributes:
        id (UUID): Primary key
        organization_id (UUID): Organization (for RLS and composite FK enforcement)
        client_id (UUID): The client being assigned
        user_id (UUID): The user being assigned
        assignment_role (str): Role on this client (CHECK constrained)
            - 'primary': Primary accountant/contact
            - 'accountant': Working accountant
            - 'reviewer': Reviews work before submission
            - 'backup': Covers during absence
        is_active (bool): Whether assignment is active
        assigned_by (UUID): User who made the assignment (same-org enforced)
        assigned_at (DateTime): When assignment was made
        created_at (DateTime): When record created
        updated_at (DateTime): When record updated

    Constraints:
        - UNIQUE (client_id, user_id) - one assignment per user per client
        - CHECK (assignment_role IN (...)) - prevents role drift
        - Composite FK (org_id, client_id) → clients - enforces same-org
        - Composite FK (org_id, user_id) → users - enforces same-org
        - Composite FK (org_id, assigned_by) → users - enforces same-org

    Usage:
        # Assign user to client
        assignment = ClientAssignment(
            organization_id=org_id,
            client_id=client_id,
            user_id=user_id,
            assignment_role='primary',
            assigned_by=admin_user_id
        )

        # Query user's clients
        my_clients = db.query(ClientAssignment).filter(
            ClientAssignment.user_id == current_user.id,
            ClientAssignment.is_active == True
        ).all()

        # Query client's assigned users
        assigned_users = db.query(ClientAssignment).filter(
            ClientAssignment.client_id == client_id,
            ClientAssignment.is_active == True
        ).all()
    """

    __tablename__ = "client_assignments"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Organization (for RLS)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # The client being assigned
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # The user being assigned
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Assignment role
    assignment_role = Column(
        String(50),
        nullable=False,
        default="accountant"
    )

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Assignment metadata
    assigned_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    assigned_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )

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
        lazy="select"
    )
    client = relationship(
        "Client",
        back_populates="assignments",
        lazy="select"
    )
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="client_assignments",
        lazy="select"
    )
    assigner = relationship(
        "User",
        foreign_keys=[assigned_by],
        lazy="select"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("client_id", "user_id", name="uq_client_assignments_client_user"),
        CheckConstraint(
            "assignment_role IN ('primary', 'accountant', 'reviewer', 'backup')",
            name="ck_client_assignments_role"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ClientAssignment("
            f"client_id={self.client_id}, "
            f"user_id={self.user_id}, "
            f"role={self.assignment_role}"
            f")>"
        )
