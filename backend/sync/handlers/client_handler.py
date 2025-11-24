"""Handler for synchronizing clients (customers, suppliers)."""

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from backend.accounting.base import AccountingClient, ContactType
from backend.models import Client
from backend.sync.models import SyncStats, SyncError

logger = logging.getLogger(__name__)


class ClientSyncHandler:
    """Handles synchronization of clients (customers, suppliers, contacts)."""

    def __init__(self, db: Session):
        """
        Initialize handler.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def sync_clients(
        self,
        client: AccountingClient,
        organization_id: UUID,
        sync_type: str = "full"
    ) -> SyncStats:
        """
        Sync clients from platform to database.

        Args:
            client: Accounting client (XeroClient, QuickBooksClient)
            organization_id: Organization UUID
            sync_type: 'full' or 'incremental'

        Returns:
            SyncStats with sync results
        """
        logger.info(f"Syncing clients for org {organization_id}")

        stats = SyncStats(entity_type="client")

        try:
            # Fetch clients from platform (both customers and suppliers)
            platform_clients = client.get_contacts()
            stats.total_fetched = len(platform_clients)

            if stats.total_fetched == 0:
                logger.info("No clients to sync")
                return stats

            logger.info(f"Fetched {stats.total_fetched} clients from {client.PLATFORM_NAME}")

            # Process each client
            for platform_client in platform_clients:
                try:
                    self._sync_single_client(
                        client.PLATFORM_NAME,
                        organization_id,
                        platform_client,
                        stats
                    )
                except Exception as e:
                    logger.error(
                        f"Error syncing client {platform_client.id}: {e}",
                        exc_info=True
                    )
                    error = SyncError(
                        entity_type="client",
                        entity_id=platform_client.id,
                        error_message=str(e),
                        error_type="database"
                    )
                    stats.add_error(error)

            # Commit all changes
            self.db.commit()
            logger.info(f"Client sync complete: {stats}")

        except Exception as e:
            logger.error(f"Failed to fetch clients: {e}", exc_info=True)
            error = SyncError(
                entity_type="client",
                error_message=str(e),
                error_type="fetch"
            )
            stats.add_error(error)

        return stats

    def _sync_single_client(
        self,
        platform_name: str,
        organization_id: UUID,
        platform_client,
        stats: SyncStats
    ) -> None:
        """
        Sync a single client.

        Args:
            platform_name: Name of platform
            organization_id: Organization UUID
            platform_client: StandardContact from platform
            stats: SyncStats to update
        """
        # Check if client already exists
        existing = self.db.query(Client).filter_by(
            organization_id=organization_id,
            platform_name=platform_name,
            platform_id=platform_client.id
        ).first()

        # Map contact type
        contact_type_map = {
            "CUSTOMER": "customer",
            "SUPPLIER": "supplier",
            "EMPLOYEE": "employee",
            ContactType.CUSTOMER: "customer",
            ContactType.SUPPLIER: "supplier",
        }
        contact_type = contact_type_map.get(
            getattr(platform_client, 'type', ContactType.CUSTOMER),
            "customer"
        )

        if existing:
            # Update existing client
            existing.name = platform_client.name or existing.name
            existing.email = platform_client.email or existing.email
            existing.phone = platform_client.phone or existing.phone
            existing.address_line1 = getattr(
                platform_client, 'address_line1', existing.address_line1
            )
            existing.city = getattr(platform_client, 'city', existing.city)
            existing.postal_code = getattr(
                platform_client, 'postal_code', existing.postal_code
            )
            existing.country = getattr(platform_client, 'country', existing.country)
            existing.contact_type = contact_type
            existing.tax_number = platform_client.tax_id or existing.tax_number
            existing.is_active = True
            self.db.flush()
            stats.updated += 1
            logger.debug(f"Updated client {platform_client.id}")

        else:
            # Create new client
            # Build address from parts if available
            address_parts = []
            if hasattr(platform_client, 'address') and platform_client.address:
                address_parts = [platform_client.address]

            new_client = Client(
                organization_id=organization_id,
                platform_id=platform_client.id,
                platform_name=platform_name,
                name=platform_client.name or "",
                email=platform_client.email,
                phone=platform_client.phone,
                address_line1=getattr(platform_client, 'address_line1', None),
                city=getattr(platform_client, 'city', None),
                postal_code=getattr(platform_client, 'postal_code', None),
                country=getattr(platform_client, 'country', None),
                contact_type=contact_type,
                tax_number=platform_client.tax_id,
                is_active=True
            )
            self.db.add(new_client)
            self.db.flush()
            stats.created += 1
            logger.debug(f"Created client {platform_client.id}")
