"""Organization authorization for multi-tenant analytics.

Enforces organization isolation at repository level with:
- Org ID validation on all operations
- Cross-organization access prevention
- Audit logging of access attempts
"""

from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class OrgAuthError(HTTPException):
    """Raised when organization authorization fails."""
    def __init__(self, org_id: UUID, detail: str = "Organization access denied"):
        super().__init__(status_code=403, detail=detail)


class OrganizationAuthorizer:
    """Enforces organization isolation for data access."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session

    def validate_org_access(
        self,
        requested_org_id: UUID,
        user_org_id: Optional[UUID] = None,
        action: str = "read"
    ) -> UUID:
        """
        Validate organization access.

        Args:
            requested_org_id: Organization being accessed
            user_org_id: User's organization (if None, assumes same as requested)
            action: Type of action (read/write/delete)

        Returns:
            Validated organization ID

        Raises:
            OrgAuthError: If access denied
        """
        if not requested_org_id:
            logger.warning("Access attempt with missing org ID")
            raise OrgAuthError(requested_org_id, "Organization ID required")

        # If user_org_id provided, verify it matches
        if user_org_id and user_org_id != requested_org_id:
            logger.warning(
                f"Cross-org access denied: user_org={user_org_id}, requested_org={requested_org_id}"
            )
            raise OrgAuthError(
                requested_org_id,
                f"Cannot access organization {requested_org_id}"
            )

        logger.info(f"Auth: org {requested_org_id} {action} access granted")
        return requested_org_id

    def validate_entity_org(
        self,
        entity_org_id: UUID,
        requesting_org_id: UUID,
        entity_type: str = "entity"
    ) -> None:
        """
        Validate that entity belongs to requesting organization.

        Args:
            entity_org_id: Organization ID of the entity
            requesting_org_id: Organization making the request
            entity_type: Type of entity for logging

        Raises:
            OrgAuthError: If entity belongs to different organization
        """
        if entity_org_id != requesting_org_id:
            logger.warning(
                f"Unauthorized {entity_type} access: "
                f"entity_org={entity_org_id}, requested_by={requesting_org_id}"
            )
            raise OrgAuthError(
                requesting_org_id,
                f"Cannot access {entity_type} from different organization"
            )
        logger.info(
            f"Auth: {entity_type} ownership verified for org {requesting_org_id}"
        )

    def log_access(
        self,
        org_id: UUID,
        action: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        success: bool = True
    ) -> None:
        """
        Log data access attempt.

        Args:
            org_id: Organization ID
            action: Type of action (read/write/delete)
            resource_type: Type of resource (forecast/metric/etc)
            resource_id: ID of specific resource
            success: Whether access was successful
        """
        status = "SUCCESS" if success else "DENIED"
        resource_str = f" {resource_id}" if resource_id else ""
        logger.info(
            f"[AUDIT] {status}: org={org_id} action={action} "
            f"resource={resource_type}{resource_str}"
        )
