"""Data models for sync engine."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID


@dataclass
class SyncError:
    """Represents a single error during sync."""

    entity_type: str  # 'account', 'client', 'transaction'
    entity_id: Optional[str] = None  # Platform ID if available
    error_message: str = ""
    error_type: str = ""  # 'fetch', 'parse', 'validation', 'database'
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        """String representation."""
        msg = f"[{self.error_type}] {self.entity_type}"
        if self.entity_id:
            msg += f" ({self.entity_id})"
        msg += f": {self.error_message}"
        return msg


@dataclass
class SyncStats:
    """Statistics for a single entity type sync."""

    entity_type: str  # 'account', 'client', 'transaction'
    total_fetched: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    errors: List[SyncError] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        """Total records processed (created + updated + skipped + failed)."""
        return self.created + self.updated + self.skipped + self.failed

    @property
    def success_rate(self) -> float:
        """Percentage of successfully processed records."""
        if self.total_processed == 0:
            return 0.0
        successful = self.created + self.updated + self.skipped
        return (successful / self.total_processed) * 100

    def add_error(self, error: SyncError) -> None:
        """Add an error to the stats."""
        self.errors.append(error)
        self.failed += 1

    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.entity_type}: "
            f"fetched={self.total_fetched}, "
            f"created={self.created}, "
            f"updated={self.updated}, "
            f"skipped={self.skipped}, "
            f"failed={self.failed} "
            f"({self.success_rate:.1f}% success)"
        )


@dataclass
class SyncResult:
    """Result of a complete sync operation."""

    status: str  # 'success', 'partial', 'failed'
    sync_history_id: UUID
    accounts: SyncStats = field(default_factory=lambda: SyncStats("account"))
    clients: SyncStats = field(default_factory=lambda: SyncStats("client"))
    transactions: SyncStats = field(default_factory=lambda: SyncStats("transaction"))
    errors: List[SyncError] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    @property
    def total_synced(self) -> int:
        """Total records synced across all entities."""
        return (
            self.accounts.total_processed
            + self.clients.total_processed
            + self.transactions.total_processed
        )

    @property
    def total_failed(self) -> int:
        """Total records failed across all entities."""
        return self.accounts.failed + self.clients.failed + self.transactions.failed

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Sync {self.status} (ID: {self.sync_history_id})\n"
            f"  Duration: {self.duration_seconds:.1f}s\n"
            f"  {self.accounts}\n"
            f"  {self.clients}\n"
            f"  {self.transactions}\n"
            f"  Total synced: {self.total_synced}, "
            f"Failed: {self.total_failed}"
        )
