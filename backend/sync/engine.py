"""Main sync engine orchestrator."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.accounting.factory import AccountingClientFactory
from backend.models import Organization, SyncHistory, AccountingPlatform
from backend.sync.models import SyncResult, SyncStats, SyncError
from backend.sync.exceptions import SyncException

logger = logging.getLogger(__name__)


class SyncEngine:
    """
    Orchestrates synchronization of data from accounting platforms.

    Manages:
    - Full and incremental syncs
    - Multiple platforms (Xero, QuickBooks)
    - All entity types (accounts, clients, transactions)
    - Complete error handling and audit trail
    """

    def __init__(self, db: Session):
        """
        Initialize sync engine.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def sync_all_platforms(self, organization_id: UUID) -> SyncResult:
        """
        Sync all platforms for an organization.

        Args:
            organization_id: UUID of organization

        Returns:
            SyncResult with overall status and statistics

        Raises:
            SyncException: If critical sync error occurs
        """
        logger.info(f"Starting sync for all platforms, org_id={organization_id}")

        # Get organization
        organization = self.db.query(Organization).filter_by(
            id=organization_id
        ).first()

        if not organization:
            raise SyncException(f"Organization not found: {organization_id}")

        # Get all active platforms for organization
        platforms = self.db.query(AccountingPlatform).filter_by(
            organization_id=organization_id,
            is_active=True
        ).all()

        if not platforms:
            raise SyncException(f"No active platforms configured for org: {organization_id}")

        # Sync each platform
        overall_result = None

        for platform in platforms:
            try:
                result = self.sync_platform(organization_id, platform.platform_name)

                if overall_result is None:
                    overall_result = result
                else:
                    # Aggregate results from multiple platforms
                    overall_result.accounts.created += result.accounts.created
                    overall_result.accounts.updated += result.accounts.updated
                    overall_result.accounts.failed += result.accounts.failed
                    overall_result.clients.created += result.clients.created
                    overall_result.clients.updated += result.clients.updated
                    overall_result.clients.failed += result.clients.failed
                    overall_result.transactions.created += result.transactions.created
                    overall_result.transactions.updated += result.transactions.updated
                    overall_result.transactions.failed += result.transactions.failed
                    overall_result.errors.extend(result.errors)

            except Exception as e:
                logger.error(
                    f"Failed to sync platform {platform.platform_name}: {e}",
                    exc_info=True
                )
                if overall_result:
                    overall_result.errors.append(
                        SyncError(
                            entity_type="platform",
                            entity_id=platform.platform_name,
                            error_message=str(e),
                            error_type="sync"
                        )
                    )

        if overall_result is None:
            raise SyncException("No platforms could be synced")

        logger.info(f"Completed sync for all platforms: {overall_result.status}")
        return overall_result

    def sync_platform(
        self,
        organization_id: UUID,
        platform_name: str
    ) -> SyncResult:
        """
        Sync a specific platform for an organization.

        Args:
            organization_id: UUID of organization
            platform_name: Name of platform ('xero', 'quickbooks')

        Returns:
            SyncResult with status and statistics

        Raises:
            SyncException: If critical error occurs
        """
        logger.info(f"Starting sync for platform {platform_name}, org={organization_id}")

        start_time = datetime.now()

        try:
            # Get organization and platform
            organization = self.db.query(Organization).filter_by(
                id=organization_id
            ).first()

            if not organization:
                raise SyncException(f"Organization not found: {organization_id}")

            platform = self.db.query(AccountingPlatform).filter_by(
                organization_id=organization_id,
                platform_name=platform_name
            ).first()

            if not platform:
                raise SyncException(
                    f"Platform {platform_name} not configured for org {organization_id}"
                )

            # Create sync history record
            sync_history = self._create_sync_history(organization, platform)

            # Determine sync type (full or incremental)
            sync_type = self._determine_sync_type(platform)
            logger.info(f"Using {sync_type} sync strategy for {platform_name}")

            # Create accounting client
            try:
                credentials = platform.get_credentials()
                client = AccountingClientFactory.create_from_platform(
                    platform_name,
                    str(organization_id),
                    credentials
                )
            except Exception as e:
                logger.error(f"Failed to create client for {platform_name}: {e}")
                sync_history.sync_status = "failed"
                sync_history.error_message = f"Failed to create client: {str(e)}"
                self.db.add(sync_history)
                self.db.commit()

                result = SyncResult(
                    status="failed",
                    sync_history_id=sync_history.id,
                    accounts=SyncStats("account"),
                    clients=SyncStats("client"),
                    transactions=SyncStats("transaction")
                )
                result.completed_at = datetime.now()
                result.duration_seconds = (result.completed_at - start_time).total_seconds()
                return result

            # Sync entities (will implement handlers next)
            from backend.sync.handlers import (
                AccountSyncHandler,
                ClientSyncHandler,
                TransactionSyncHandler
            )

            account_handler = AccountSyncHandler(self.db)
            client_handler = ClientSyncHandler(self.db)
            transaction_handler = TransactionSyncHandler(self.db)

            accounts_stats = account_handler.sync_accounts(
                client, organization_id, sync_type
            )
            clients_stats = client_handler.sync_clients(
                client, organization_id, sync_type
            )
            transactions_stats = transaction_handler.sync_transactions(
                client, organization_id, sync_type
            )

            # Create result
            result = SyncResult(
                status="success",
                sync_history_id=sync_history.id,
                accounts=accounts_stats,
                clients=clients_stats,
                transactions=transactions_stats
            )

            # Finalize sync history
            self._finalize_sync_history(sync_history, result, sync_type)

            result.completed_at = datetime.now()
            result.duration_seconds = (result.completed_at - start_time).total_seconds()

            logger.info(
                f"Completed sync for {platform_name}: {result.status}, "
                f"duration={result.duration_seconds:.1f}s"
            )

            return result

        except SyncException as e:
            logger.error(f"Sync exception for {platform_name}: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error during sync: {e}", exc_info=True)
            raise SyncException(f"Unexpected sync error: {str(e)}") from e

    def _determine_sync_type(self, platform: AccountingPlatform) -> str:
        """
        Determine if should do full or incremental sync.

        Args:
            platform: The accounting platform

        Returns:
            'full' or 'incremental'
        """
        # Get most recent sync history
        last_sync = self.db.query(SyncHistory).filter_by(
            platform_id=platform.id,
            sync_status="completed"
        ).order_by(SyncHistory.completed_at.desc()).first()

        if not last_sync:
            # No previous sync, do full
            return "full"

        # If last sync was more than 7 days ago, do full
        if datetime.now(last_sync.completed_at.tzinfo) - last_sync.completed_at > timedelta(days=7):
            return "full"

        # Otherwise incremental
        return "incremental"

    def _create_sync_history(
        self,
        organization: Organization,
        platform: AccountingPlatform
    ) -> SyncHistory:
        """
        Create a new sync history record.

        Args:
            organization: The organization
            platform: The accounting platform

        Returns:
            New SyncHistory object (not yet committed)
        """
        sync_history = SyncHistory(
            organization_id=organization.id,
            platform_id=platform.id,
            sync_type="full",  # Will be updated
            sync_status="started",
            started_at=datetime.now()
        )
        self.db.add(sync_history)
        self.db.flush()  # Get the ID without committing

        return sync_history

    def _finalize_sync_history(
        self,
        sync_history: SyncHistory,
        result: SyncResult,
        sync_type: str
    ) -> None:
        """
        Update sync history record with final result.

        Args:
            sync_history: The sync history record
            result: The sync result
            sync_type: The sync type ('full' or 'incremental')
        """
        sync_history.sync_type = sync_type
        sync_history.sync_status = result.status
        sync_history.completed_at = result.completed_at
        sync_history.duration_seconds = int(result.duration_seconds)

        # Record counts
        sync_history.records_synced = result.total_synced
        sync_history.records_created = (
            result.accounts.created + result.clients.created + result.transactions.created
        )
        sync_history.records_updated = (
            result.accounts.updated + result.clients.updated + result.transactions.updated
        )
        sync_history.records_failed = result.total_failed

        # Error handling
        if result.errors:
            error_messages = [str(e) for e in result.errors]
            sync_history.error_message = "; ".join(error_messages[:5])  # First 5 errors
            sync_history.error_details = {
                "total_errors": len(result.errors),
                "error_summary": [
                    {
                        "entity_type": e.entity_type,
                        "error_type": e.error_type,
                        "message": e.error_message
                    }
                    for e in result.errors[:10]  # First 10 error details
                ]
            }

        self.db.commit()
