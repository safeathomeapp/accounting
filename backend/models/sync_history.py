"""
Module: sync_history
Purpose: Synchronization history tracking ORM model
Dependencies: SQLAlchemy
Platform: Universal

The SyncHistory model tracks all data synchronization events with accounting platforms.
Provides complete audit trail and troubleshooting information.

Relationships:
- Many-to-one: organization (which organization was synced)
- Many-to-one: accounting_platform (which platform was synced)

Author: Claude Code
Created: November 23, 2025
Last Modified: November 23, 2025
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.models import Base


class SyncHistory(Base):
    """
    Represents a synchronization event with an accounting platform.

    Complete audit trail of all data syncs with performance metrics
    and error information for troubleshooting.

    Attributes:
        id (UUID): Primary key
        organization_id (UUID): Organization being synced
        platform_id (UUID): Which platform (Xero, QB, etc.)
        sync_type (str): 'full' (all data) or 'incremental' (since last sync)
        sync_status (str): 'started', 'completed', 'failed'
        records_synced (int): Total records synced
        records_created (int): New records created
        records_updated (int): Existing records updated
        records_failed (int): Records that failed
        started_at (DateTime): When sync started
        completed_at (DateTime): When sync completed
        duration_seconds (int): How long sync took
        error_message (str): Error message if sync_status='failed'
        error_details (dict): Detailed error information (JSON)
        created_at (DateTime): When record was created

    Relationships:
        organization: The organization
        platform: The accounting platform

    Note:
        - One record per sync event
        - Full history preserved for debugging
        - Performance metrics help identify slow syncs
        - Error details enable quick troubleshooting

    Example:
        >>> from backend.models import SyncHistory
        >>> sync = SyncHistory(
        ...     organization_id=org_uuid,
        ...     platform_id=platform_uuid,
        ...     sync_type="incremental",
        ...     sync_status="started",
        ...     started_at=datetime.now()
        ... )
        >>> db.add(sync)
        >>> # ... perform sync ...
        >>> sync.sync_status = "completed"
        >>> sync.completed_at = datetime.now()
        >>> sync.records_created = 5
        >>> sync.records_updated = 12
        >>> db.commit()
    """

    __tablename__ = "sync_history"

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
    platform_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounting_platforms.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Sync Metadata
    # Type: full (all data) or incremental (since last sync)
    sync_type = Column(String(50), nullable=False)
    # Status: started, completed, failed
    sync_status = Column(String(50), nullable=False, index=True)

    # Record Counts
    # Total records synced
    records_synced = Column(Integer, default=0, nullable=False)
    # New records created
    records_created = Column(Integer, default=0, nullable=False)
    # Existing records updated
    records_updated = Column(Integer, default=0, nullable=False)
    # Records that failed to sync
    records_failed = Column(Integer, default=0, nullable=False)

    # Timing
    # When sync started
    started_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        index=True
    )
    # When sync completed (null if still running)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    # How long sync took in seconds
    duration_seconds = Column(Integer, nullable=True)

    # Error Handling
    # Error message (if sync_status='failed')
    error_message = Column(Text, nullable=True)
    # Detailed error information as JSON
    error_details = Column(JSONB, nullable=True)

    # Record Timestamp
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )

    # Relationships
    organization = relationship(
        "Organization",
        back_populates="sync_history",
        lazy="select"
    )
    platform = relationship(
        "AccountingPlatform",
        back_populates="sync_history",
        lazy="select"
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<SyncHistory("
            f"id={self.id}, "
            f"status={self.sync_status}, "
            f"records={self.records_synced}, "
            f"started={self.started_at}"
            f")>"
        )
