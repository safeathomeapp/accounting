"""
Module: audit_log
Purpose: Audit trail ORM model
Dependencies: SQLAlchemy
Platform: Universal

The AuditLog model tracks all database changes for compliance and security.
Complete change history with old/new values.

Relationships:
- Many-to-one: organization (which organization's data changed)

Author: Claude Code
Created: November 23, 2025
Last Modified: November 23, 2025
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.models import Base


class AuditLog(Base):
    """
    Represents a database change for compliance and auditing.

    Complete change history showing what changed, when, who did it, and the values.
    Essential for regulatory compliance and fraud detection.

    Attributes:
        id (UUID): Primary key
        organization_id (UUID): Which organization's data changed
        table_name (str): Which table was modified
        record_id (str): ID of the record that changed
        operation (str): 'INSERT', 'UPDATE', or 'DELETE'
        old_values (dict): Previous values (as JSON)
        new_values (dict): New values (as JSON)
        changed_by (str): Who made the change (user email, 'system', 'sync', etc.)
        created_at (DateTime): When change occurred

    Relationships:
        organization: Which organization's data changed

    Note:
        - One record per database change
        - old_values is null for INSERT operations
        - new_values is null for DELETE operations
        - Both present for UPDATE operations
        - Complete traceability for compliance
        - Cannot be modified after creation (immutable audit log)

    Example:
        >>> from backend.models import AuditLog
        >>> audit = AuditLog(
        ...     organization_id=org_uuid,
        ...     table_name="transactions",
        ...     record_id=str(transaction_uuid),
        ...     operation="UPDATE",
        ...     old_values={"status": "draft", "amount": "1000.00"},
        ...     new_values={"status": "submitted", "amount": "1000.00"},
        ...     changed_by="user@example.com"
        ... )
    """

    __tablename__ = "audit_log"

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

    # Change Information
    # Which table was modified
    table_name = Column(String(100), nullable=False, index=True)
    # ID of the record that changed
    record_id = Column(String(500), nullable=False)
    # Operation: INSERT, UPDATE, DELETE
    operation = Column(String(10), nullable=False)

    # Change Data
    # Previous values (JSON) - null for INSERT
    old_values = Column(JSONB, nullable=True)
    # New values (JSON) - null for DELETE
    new_values = Column(JSONB, nullable=True)

    # Attribution
    # Who made the change: user email, 'system', 'sync', 'api', etc.
    changed_by = Column(String(100), nullable=False)

    # Timestamp
    # Immutable - when change occurred
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        index=True
    )

    # Relationships
    organization = relationship(
        "Organization",
        back_populates="audit_log",
        lazy="select"
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AuditLog("
            f"id={self.id}, "
            f"table={self.table_name}, "
            f"op={self.operation}, "
            f"by={self.changed_by}"
            f")>"
        )
