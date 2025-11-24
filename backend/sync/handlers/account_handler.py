"""Handler for synchronizing accounts."""

import logging
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.accounting.base import AccountingClient
from backend.models import Account
from backend.sync.models import SyncStats, SyncError
from backend.sync.exceptions import SyncDatabaseError

logger = logging.getLogger(__name__)


class AccountSyncHandler:
    """Handles synchronization of accounts (chart of accounts)."""

    def __init__(self, db: Session):
        """
        Initialize handler.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def sync_accounts(
        self,
        client: AccountingClient,
        organization_id: UUID,
        sync_type: str = "full"
    ) -> SyncStats:
        """
        Sync accounts from platform to database.

        Args:
            client: Accounting client (XeroClient, QuickBooksClient)
            organization_id: Organization UUID
            sync_type: 'full' or 'incremental' (not used for accounts currently)

        Returns:
            SyncStats with sync results
        """
        logger.info(f"Syncing accounts for org {organization_id}")

        stats = SyncStats(entity_type="account")

        try:
            # Fetch accounts from platform
            platform_accounts = client.get_accounts()
            stats.total_fetched = len(platform_accounts)

            if stats.total_fetched == 0:
                logger.info("No accounts to sync")
                return stats

            logger.info(f"Fetched {stats.total_fetched} accounts from {client.PLATFORM_NAME}")

            # Process each account
            for platform_account in platform_accounts:
                try:
                    self._sync_single_account(
                        client.PLATFORM_NAME,
                        organization_id,
                        platform_account,
                        stats
                    )
                except Exception as e:
                    logger.error(
                        f"Error syncing account {platform_account.id}: {e}",
                        exc_info=True
                    )
                    error = SyncError(
                        entity_type="account",
                        entity_id=platform_account.id,
                        error_message=str(e),
                        error_type="database"
                    )
                    stats.add_error(error)

            # Commit all changes
            self.db.commit()
            logger.info(f"Account sync complete: {stats}")

        except Exception as e:
            logger.error(f"Failed to fetch accounts: {e}", exc_info=True)
            error = SyncError(
                entity_type="account",
                error_message=str(e),
                error_type="fetch"
            )
            stats.add_error(error)

        return stats

    def _sync_single_account(
        self,
        platform_name: str,
        organization_id: UUID,
        platform_account,
        stats: SyncStats
    ) -> None:
        """
        Sync a single account.

        Args:
            platform_name: Name of platform
            organization_id: Organization UUID
            platform_account: StandardAccount from platform
            stats: SyncStats to update
        """
        # Check if account already exists
        existing = self.db.query(Account).filter_by(
            organization_id=organization_id,
            platform_name=platform_name,
            platform_id=platform_account.id
        ).first()

        if existing:
            # Update existing account
            existing.code = platform_account.code or existing.code
            existing.name = platform_account.name or existing.name
            existing.account_type = platform_account.type or existing.account_type
            existing.description = getattr(
                platform_account, 'description', existing.description
            )
            existing.is_active = True
            self.db.flush()
            stats.updated += 1
            logger.debug(f"Updated account {platform_account.id}")

        else:
            # Create new account
            new_account = Account(
                organization_id=organization_id,
                platform_id=platform_account.id,
                platform_name=platform_name,
                code=platform_account.code or "",
                name=platform_account.name or "",
                account_type=platform_account.type,
                description=getattr(platform_account, 'description', None),
                is_active=True
            )
            self.db.add(new_account)
            self.db.flush()
            stats.created += 1
            logger.debug(f"Created account {platform_account.id}")
