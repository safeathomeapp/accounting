"""WebSocket connection management for real-time dashboard updates.

Handles WebSocket connections, message broadcasting, and client management
for live monitoring dashboard streaming.
"""

import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime, timezone
import json
from uuid import UUID

from starlette.websockets import WebSocket, WebSocketState

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting.

    Handles:
    - Client connection/disconnection tracking
    - Organization-scoped connection groups
    - Real-time message broadcasting
    - Error handling and reconnection
    """

    def __init__(self):
        """Initialize connection manager."""
        # Structure: org_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Keep track of all connections globally for broadcast
        self.all_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, organization_id: str) -> None:
        """
        Register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            organization_id: UUID of the organization
        """
        try:
            await websocket.accept()

            # Add to organization group
            if organization_id not in self.active_connections:
                self.active_connections[organization_id] = set()

            self.active_connections[organization_id].add(websocket)
            self.all_connections.add(websocket)

            logger.info(
                f"WebSocket connected: org={organization_id}, "
                f"total_connections={len(self.all_connections)}"
            )

        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {e}")
            raise

    async def disconnect(self, websocket: WebSocket, organization_id: str) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            websocket: The WebSocket connection
            organization_id: UUID of the organization
        """
        try:
            # Remove from organization group
            if organization_id in self.active_connections:
                self.active_connections[organization_id].discard(websocket)

                # Clean up empty organization groups
                if not self.active_connections[organization_id]:
                    del self.active_connections[organization_id]

            # Remove from all connections
            self.all_connections.discard(websocket)

            logger.info(
                f"WebSocket disconnected: org={organization_id}, "
                f"total_connections={len(self.all_connections)}"
            )

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    async def broadcast_to_organization(
        self,
        organization_id: str,
        message: Dict[str, Any]
    ) -> None:
        """
        Broadcast a message to all clients in an organization.

        Args:
            organization_id: UUID of the organization
            message: Message dict to broadcast
        """
        if organization_id not in self.active_connections:
            logger.debug(f"No connections for organization {organization_id}")
            return

        disconnected = set()

        for connection in self.active_connections[organization_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            await self.disconnect(connection, organization_id)

    async def broadcast_to_all(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: Message dict to broadcast
        """
        disconnected = set()

        for connection in self.all_connections.copy():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            # Try to find and remove from org-specific groups
            for org_id in list(self.active_connections.keys()):
                await self.disconnect(connection, org_id)

    async def send_to_connection(
        self,
        websocket: WebSocket,
        message: Dict[str, Any]
    ) -> bool:
        """
        Send a message to a specific connection.

        Args:
            websocket: Target WebSocket connection
            message: Message dict to send

        Returns:
            True if successful, False if connection failed
        """
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"Failed to send message to connection: {e}")
            return False

    def get_organization_connection_count(self, organization_id: str) -> int:
        """
        Get the number of active connections for an organization.

        Args:
            organization_id: UUID of the organization

        Returns:
            Number of active WebSocket connections
        """
        return len(self.active_connections.get(organization_id, set()))

    def get_total_connection_count(self) -> int:
        """Get total active connections across all organizations."""
        return len(self.all_connections)

    def get_organizations_with_connections(self) -> list:
        """Get list of organization IDs with active connections."""
        return list(self.active_connections.keys())


# Global connection manager instance
manager = ConnectionManager()


def format_ws_message(
    message_type: str,
    data: Dict[str, Any],
    organization_id: Optional[str] = None,
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format a message for WebSocket transmission.

    Args:
        message_type: Type of message (e.g., 'job_status', 'metric', 'error')
        data: Message payload data
        organization_id: Optional organization UUID
        job_id: Optional job UUID

    Returns:
        Formatted message dict ready for JSON serialization
    """
    return {
        "type": message_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "organization_id": str(organization_id) if organization_id else None,
        "job_id": str(job_id) if job_id else None,
        "data": data,
    }
