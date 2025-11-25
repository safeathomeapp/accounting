"""Offline Sync Queue for Mobile Transactions

This module handles transactions created on the mobile app while offline.

Key Concept:
User on airplane creates a transaction on their phone. Phone saves it locally.
When user lands and gets internet, the app automatically syncs it to the server.

This table tracks:
- Transactions waiting to sync
- Sync status (pending, syncing, synced, failed)
- Retry attempts
- Any errors that occurred

Database Table: offline_sync_queue
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, Integer, Text, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID

from backend.models import Base


class OfflineSyncQueueItem(Base):
    """
    Queue item for a transaction created offline.

    Scenario:
    1. User on airplane creates transaction: "Spent $50 on lunch"
    2. Phone saves locally with status="pending"
    3. User lands, opens app
    4. App detects internet connection
    5. App sends transaction to server
    6. Server saves it, updates status="synced"

    This table tracks all those transactions waiting to sync.

    Example:
        item = OfflineSyncQueueItem(
            organization_id=org_id,
            action="create",
            entity_type="transaction",
            entity_data={
                "amount": "50.00",
                "description": "Lunch",
                "category": "Meals"
            },
            status="pending"
        )
        db.add(item)
        db.commit()
    """

    __tablename__ = "offline_sync_queue"

    # Unique ID for this queue item
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Organization this transaction belongs to
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # User who created this transaction
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # ===== WHAT ACTION ARE WE DOING? =====

    # Type of action
    # Values: "create", "update", "delete"
    # Examples:
    # - "create": User created new transaction while offline
    # - "update": User edited existing transaction while offline
    # - "delete": User deleted transaction while offline
    action = Column(String(50), nullable=False, index=True)

    # Type of entity we're syncing
    # Values: "transaction", "account", "contact"
    # For now, we mainly use "transaction"
    entity_type = Column(String(50), nullable=False, index=True)

    # The actual data to sync
    # JSON format: {
    #   "amount": "50.00",
    #   "date": "2025-11-25",
    #   "description": "Lunch",
    #   "category_id": "abc123",
    #   "account_id": "def456"
    # }
    entity_data = Column(JSON, nullable=False)

    # ===== SYNC STATUS =====

    # Current status of this sync item
    # "pending"   = waiting to send (no internet or app closed)
    # "syncing"   = currently sending to server
    # "synced"    = successfully sent and saved
    # "conflict"  = server rejected due to conflict (e.g., account was deleted)
    # "failed"    = tried to send but got error (will retry)
    status = Column(String(50), nullable=False, default="pending", index=True)

    # Number of times we've tried to sync this
    # Starts at 0, incremented each attempt
    # If > 3 attempts, stop trying
    attempt_count = Column(Integer, default=0)

    # When we'll retry (if it failed)
    # Example: transaction failed at 10:30, retry at 10:35 (5 min later)
    next_retry_at = Column(DateTime(timezone=True))

    # Error message if last sync failed
    # Examples:
    # - "Account not found (might have been deleted)"
    # - "Invalid transaction amount"
    # - "Network timeout"
    last_error = Column(Text)

    # ===== TIMESTAMPS =====

    # When user created this transaction locally (on their phone)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # When we first tried to sync it to server
    first_sync_attempt_at = Column(DateTime(timezone=True))

    # When we last tried to sync it
    last_sync_attempt_at = Column(DateTime(timezone=True))

    # When server confirmed receipt (synced)
    synced_at = Column(DateTime(timezone=True))

    # ===== DEBUGGING INFO =====

    # Server-side ID once synced
    # Before sync: NULL
    # After sync: UUID that server assigned
    server_entity_id = Column(UUID(as_uuid=True))

    # Notes for debugging
    # Example: "User was offline for 2 hours when creating this"
    notes = Column(Text)

    def __repr__(self):
        """Human-readable representation"""
        return f"<QueueItem {self.action} {self.entity_type} ({self.status})>"

    @property
    def can_retry(self) -> bool:
        """
        Can we try syncing this again?

        Returns:
            True if we haven't exceeded max retries

        Example:
            item = db.query(OfflineSyncQueueItem).filter_by(status="failed").first()
            if item.can_retry:
                attempt_sync(item)
        """
        max_attempts = 3
        return self.attempt_count < max_attempts

    def mark_syncing(self):
        """
        Mark this as currently syncing.

        Call when you start sending to server.
        """
        self.status = "syncing"
        self.first_sync_attempt_at = self.first_sync_attempt_at or datetime.now(timezone.utc)
        self.last_sync_attempt_at = datetime.now(timezone.utc)
        self.attempt_count += 1

    def mark_synced(self, server_id: str):
        """
        Mark this as successfully synced.

        Call when server confirms receipt.

        Args:
            server_id: The ID that server assigned to this entity
        """
        self.status = "synced"
        self.synced_at = datetime.now(timezone.utc)
        self.server_entity_id = server_id
        self.last_error = None

    def mark_failed(self, error: str, retry_in_seconds: int = 300):
        """
        Mark this as failed (will retry later).

        Call when sync attempt fails but might work later.

        Args:
            error: Error message
            retry_in_seconds: How many seconds until we retry (default: 5 min)

        Example:
            item.mark_failed(
                error="Network timeout",
                retry_in_seconds=300  # Try again in 5 minutes
            )
        """
        self.status = "failed"
        self.last_error = error
        self.next_retry_at = (
            datetime.now(timezone.utc) +
            datetime.timedelta(seconds=retry_in_seconds)
        )

    def mark_conflict(self, error: str):
        """
        Mark as conflict (server rejected it permanently).

        Call when server rejects the data (e.g., account was deleted).
        Don't retry conflicts.

        Args:
            error: Why there's a conflict
        """
        self.status = "conflict"
        self.last_error = error
        # Don't set next_retry_at - won't retry conflicts

    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            "id": str(self.id),
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_data": self.entity_data,
            "status": self.status,
            "attempt_count": self.attempt_count,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat(),
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
        }
