"""Handler for synchronizing transactions."""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from backend.accounting.base import AccountingClient, TransactionType
from backend.models import Transaction, Client, Account
from backend.sync.models import SyncStats, SyncError

logger = logging.getLogger(__name__)


class TransactionSyncHandler:
    """Handles synchronization of financial transactions (invoices, bills, etc.)."""

    def __init__(self, db: Session):
        """
        Initialize handler.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def sync_transactions(
        self,
        client: AccountingClient,
        organization_id: UUID,
        sync_type: str = "full"
    ) -> SyncStats:
        """
        Sync transactions from platform to database.

        Args:
            client: Accounting client (XeroClient, QuickBooksClient)
            organization_id: Organization UUID
            sync_type: 'full' or 'incremental'

        Returns:
            SyncStats with sync results
        """
        logger.info(f"Syncing transactions for org {organization_id}, type={sync_type}")

        stats = SyncStats(entity_type="transaction")

        try:
            # Determine date range for fetch
            if sync_type == "incremental":
                # Get last synced transaction date
                last_transaction = self.db.query(Transaction).filter_by(
                    organization_id=organization_id,
                    platform_name=client.PLATFORM_NAME
                ).order_by(Transaction.transaction_date.desc()).first()

                if last_transaction:
                    start_date = last_transaction.transaction_date
                else:
                    # Default to 3 months back if no previous sync
                    start_date = (datetime.now() - timedelta(days=90)).date()
            else:
                # Full sync: get last 2 years of transactions
                start_date = (datetime.now() - timedelta(days=730)).date()

            end_date = datetime.now().date()

            logger.info(f"Fetching transactions from {start_date} to {end_date}")

            # Fetch transactions from platform
            platform_transactions = client.get_transactions(
                start_date=start_date,
                end_date=end_date,
                limit=10000
            )
            stats.total_fetched = len(platform_transactions)

            if stats.total_fetched == 0:
                logger.info("No transactions to sync")
                return stats

            logger.info(f"Fetched {stats.total_fetched} transactions from {client.PLATFORM_NAME}")

            # Process each transaction
            for platform_txn in platform_transactions:
                try:
                    self._sync_single_transaction(
                        client.PLATFORM_NAME,
                        organization_id,
                        platform_txn,
                        stats
                    )
                except Exception as e:
                    logger.error(
                        f"Error syncing transaction {platform_txn.id}: {e}",
                        exc_info=True
                    )
                    error = SyncError(
                        entity_type="transaction",
                        entity_id=platform_txn.id,
                        error_message=str(e),
                        error_type="database"
                    )
                    stats.add_error(error)

            # Commit all changes
            self.db.commit()
            logger.info(f"Transaction sync complete: {stats}")

        except Exception as e:
            logger.error(f"Failed to fetch transactions: {e}", exc_info=True)
            error = SyncError(
                entity_type="transaction",
                error_message=str(e),
                error_type="fetch"
            )
            stats.add_error(error)

        return stats

    def _sync_single_transaction(
        self,
        platform_name: str,
        organization_id: UUID,
        platform_txn,
        stats: SyncStats
    ) -> None:
        """
        Sync a single transaction.

        Args:
            platform_name: Name of platform
            organization_id: Organization UUID
            platform_txn: StandardTransaction from platform
            stats: SyncStats to update
        """
        # Check if transaction already exists
        existing = self.db.query(Transaction).filter_by(
            organization_id=organization_id,
            platform_name=platform_name,
            platform_id=platform_txn.id
        ).first()

        # Map transaction type
        transaction_type_map = {
            "INVOICE": "invoice",
            "BILL": "bill",
            "CREDIT_NOTE": "credit_note",
            "DEPOSIT": "bank_transaction",
            "BANK_TRANSACTION": "bank_transaction",
            TransactionType.INVOICE: "invoice",
            TransactionType.BILL: "bill",
        }
        transaction_type = transaction_type_map.get(
            getattr(platform_txn, 'type', TransactionType.INVOICE),
            "invoice"
        )

        # Resolve client ID if provided
        client_id = None
        if platform_txn.contact_id:
            contact = self.db.query(Client).filter_by(
                organization_id=organization_id,
                platform_name=platform_name,
                platform_id=platform_txn.contact_id
            ).first()
            if contact:
                client_id = contact.id

        # Resolve account ID if provided
        account_id = None
        if hasattr(platform_txn, 'account_id') and platform_txn.account_id:
            account = self.db.query(Account).filter_by(
                organization_id=organization_id,
                platform_name=platform_name,
                platform_id=platform_txn.account_id
            ).first()
            if account:
                account_id = account.id

        if existing:
            # Update existing transaction
            existing.transaction_type = transaction_type
            existing.reference_number = platform_txn.reference or existing.reference_number
            existing.description = platform_txn.description or existing.description
            existing.amount = platform_txn.amount
            existing.tax_amount = platform_txn.tax_amount
            existing.total_amount = platform_txn.amount + platform_txn.tax_amount
            existing.transaction_date = platform_txn.date
            existing.status = platform_txn.status
            existing.client_id = client_id
            existing.account_id = account_id
            existing.last_synced_at = datetime.now()
            self.db.flush()
            stats.updated += 1
            logger.debug(f"Updated transaction {platform_txn.id}")

        else:
            # Create new transaction
            new_txn = Transaction(
                organization_id=organization_id,
                platform_id=platform_txn.id,
                platform_name=platform_name,
                transaction_type=transaction_type,
                reference_number=platform_txn.reference,
                description=platform_txn.description,
                amount=platform_txn.amount,
                tax_amount=platform_txn.tax_amount,
                total_amount=platform_txn.amount + platform_txn.tax_amount,
                currency=getattr(platform_txn, 'currency', 'GBP'),
                transaction_date=platform_txn.date,
                status=platform_txn.status,
                client_id=client_id,
                account_id=account_id,
                last_synced_at=datetime.now(),
                is_reconciled=False
            )
            self.db.add(new_txn)
            self.db.flush()
            stats.created += 1
            logger.debug(f"Created transaction {platform_txn.id}")
