"""
Module: accounting.factory
Purpose: Factory pattern for creating accounting platform clients
Dependencies: AccountingClient (base class)
Platform: Universal (platform-agnostic)

This module implements the Factory Pattern to create the appropriate
platform-specific accounting client based on configuration.

Instead of business logic deciding which platform to use:
  ❌ BAD: if platform == 'xero': XeroClient(...)
  ✅ GOOD: AccountingClientFactory.create(organization)

The factory handles all platform detection and instantiation.

Example:
    from backend.models import Organization
    from backend.accounting.factory import AccountingClientFactory

    # Create the right client for this organization
    organization = Organization.query.first()
    client = AccountingClientFactory.create(organization)

    # Now you can use it without knowing which platform
    accounts = client.get_accounts()

Future Extensions:
    To add a new platform (e.g., Sage):
    1. Create backend.accounting.sage.client.SageClient
    2. Add entry to PLATFORM_CLIENTS dict
    3. That's it! Rest of code unchanged.

Author: Claude Code
Created: November 24, 2025
Last Modified: November 24, 2025
"""

from typing import Dict, Any, Optional
import logging

from backend.accounting.base import AccountingClient, ValidationError

logger = logging.getLogger(__name__)


class AccountingClientFactory:
    """
    Factory for creating accounting platform clients.

    This class implements the Factory Pattern to instantiate the correct
    platform-specific client based on organization configuration.

    Supported Platforms:
    - xero: Xero accounting software (Month 1, Week 3)
    - quickbooks: QuickBooks Online (Month 7, Week 4)

    Future Platforms:
    - sage: Sage 50/Business (Month 12+)
    - freeagent: FreeAgent accounting (Month 12+)

    Usage:
        organization = db.query(Organization).first()
        client = AccountingClientFactory.create(organization)
        transactions = client.get_transactions(start, end)
    """

    # Mapping of platform names to client classes
    # Add new platforms here as they're implemented
    PLATFORM_CLIENTS: Dict[str, str] = {
        "xero": "backend.accounting.xero.client.XeroClient",
        "quickbooks": "backend.accounting.quickbooks.client.QuickBooksClient",
        "mock": "backend.accounting.mock.client.MockClient",  # TEMPORARY: For development/testing only
        # "sage": "backend.accounting.sage.client.SageClient",  # Future
        # "freeagent": "backend.accounting.freeagent.client.FreeAgentClient",  # Future
    }

    @classmethod
    def create(cls, organization: Any) -> AccountingClient:
        """
        Create an accounting client for the organization.

        Determines which platform the organization uses and creates
        the appropriate client instance.

        Args:
            organization: Organization database model with:
                - accounting_platform_id: Which platform
                - accounting_platform.get_credentials(): OAuth/API credentials

        Returns:
            Instantiated AccountingClient (XeroClient, QuickBooksClient, etc.)

        Raises:
            ValueError: If platform not supported
            ValidationError: If credentials invalid

        Example:
            >>> org = db.query(Organization).filter_by(id=123).first()
            >>> client = AccountingClientFactory.create(org)
            >>> print(type(client).__name__)  # "XeroClient" or "QuickBooksClient"
        """
        # Get platform configuration
        platform = cls._get_platform_for_organization(organization)
        if not platform:
            raise ValidationError(
                f"Organization {organization.id} has no accounting platform configured"
            )

        # Get credentials
        try:
            credentials = organization.accounting_platform.get_credentials()
        except AttributeError as e:
            raise ValidationError(
                f"Cannot get credentials from organization: {e}"
            )

        # Create and return client
        return cls._create_client_for_platform(
            platform=platform,
            organization_id=str(organization.id),
            credentials=credentials,
        )

    @classmethod
    def create_from_platform(
        cls,
        platform: str,
        organization_id: str,
        credentials: Dict[str, Any],
    ) -> AccountingClient:
        """
        Create an accounting client directly from platform and credentials.

        Useful for testing or manual instantiation.

        Args:
            platform: Platform name (xero, quickbooks, etc.)
            organization_id: Our internal organization ID
            credentials: Platform-specific credentials dict

        Returns:
            Instantiated AccountingClient

        Raises:
            ValueError: If platform not supported

        Example:
            >>> client = AccountingClientFactory.create_from_platform(
            ...     platform="xero",
            ...     organization_id="123",
            ...     credentials={"client_id": "...", "client_secret": "..."}
            ... )
        """
        return cls._create_client_for_platform(
            platform=platform.lower(),
            organization_id=organization_id,
            credentials=credentials,
        )

    @classmethod
    def _create_client_for_platform(
        cls,
        platform: str,
        organization_id: str,
        credentials: Dict[str, Any],
    ) -> AccountingClient:
        """
        Internal: Create client instance for specific platform.

        Args:
            platform: Platform name (lowercase)
            organization_id: Our internal organization ID
            credentials: Platform-specific credentials

        Returns:
            AccountingClient instance

        Raises:
            ValueError: If platform not found
        """
        platform = platform.lower()

        # Check if platform is supported
        if platform not in cls.PLATFORM_CLIENTS:
            available = ", ".join(cls.PLATFORM_CLIENTS.keys())
            raise ValueError(
                f"Platform '{platform}' not supported. "
                f"Available platforms: {available}"
            )

        # Dynamically import the client class
        try:
            client_class_path = cls.PLATFORM_CLIENTS[platform]
            module_path, class_name = client_class_path.rsplit(".", 1)

            # Import the module
            module = __import__(module_path, fromlist=[class_name])
            client_class = getattr(module, class_name)

            # Create and return instance
            logger.info(
                f"Creating {platform.upper()} client for organization {organization_id}"
            )
            client = client_class(organization_id, credentials)
            return client

        except ImportError as e:
            raise ValueError(
                f"Cannot import {platform} client. Is it implemented yet? "
                f"Error: {e}"
            )
        except AttributeError as e:
            raise ValueError(
                f"Client class not found in {platform} module. Error: {e}"
            )
        except Exception as e:
            raise ValueError(
                f"Error creating {platform} client: {e}"
            )

    @staticmethod
    def _get_platform_for_organization(organization: Any) -> Optional[str]:
        """
        Get the platform name for an organization.

        Args:
            organization: Organization model

        Returns:
            Platform name or None if not configured
        """
        try:
            if hasattr(organization, 'accounting_platform') and organization.accounting_platform:
                platform_name = organization.accounting_platform.platform_name
                return platform_name.lower()
            return None
        except (AttributeError, TypeError):
            return None

    @classmethod
    def supported_platforms(cls) -> list:
        """
        Get list of supported platforms.

        Returns:
            List of supported platform names

        Example:
            >>> platforms = AccountingClientFactory.supported_platforms()
            >>> print(platforms)  # ["xero", "quickbooks"]
        """
        return list(cls.PLATFORM_CLIENTS.keys())

    @classmethod
    def is_platform_supported(cls, platform: str) -> bool:
        """
        Check if a platform is supported.

        Args:
            platform: Platform name to check

        Returns:
            True if platform is supported

        Example:
            >>> if AccountingClientFactory.is_platform_supported("xero"):
            ...     print("Xero is supported!")
        """
        return platform.lower() in cls.PLATFORM_CLIENTS
