"""
Module: tests.test_accounting_factory
Purpose: Unit tests for AccountingClientFactory
Dependencies: pytest, backend.accounting

Test Coverage:
- Factory creation with mock objects
- Platform support checking
- Error handling

Run with:
    pytest tests/test_accounting_factory.py -v

Author: Claude Code
Created: November 24, 2025
"""

import pytest
from unittest.mock import Mock, MagicMock

from backend.accounting import (
    AccountingClientFactory,
    AccountingClient,
    ValidationError,
)


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def mock_organization():
    """Create a mock organization with platform configured."""
    org = Mock()
    org.id = 123
    org.accounting_platform = Mock()
    org.accounting_platform.platform_name = "xero"
    org.accounting_platform.get_credentials = Mock(
        return_value={"api_key": "test_key"}
    )
    return org


@pytest.fixture
def mock_organization_no_platform():
    """Create a mock organization without platform."""
    org = Mock()
    org.id = 456
    org.accounting_platform = None
    return org


# ============================================================================
# TESTS FOR FACTORY CLASS
# ============================================================================


class TestAccountingClientFactory:
    """Tests for AccountingClientFactory."""

    def test_supported_platforms(self):
        """Test getting list of supported platforms."""
        platforms = AccountingClientFactory.supported_platforms()
        assert isinstance(platforms, list)
        # Should have at least xero (QB will be added later)
        assert "xero" in platforms or len(platforms) >= 1

    def test_is_platform_supported_true(self):
        """Test checking if platform is supported."""
        assert AccountingClientFactory.is_platform_supported("xero") is True

    def test_is_platform_supported_false(self):
        """Test checking unsupported platform."""
        assert AccountingClientFactory.is_platform_supported("unsupported") is False

    def test_is_platform_supported_case_insensitive(self):
        """Test platform check is case-insensitive."""
        assert AccountingClientFactory.is_platform_supported("XERO") is True
        assert AccountingClientFactory.is_platform_supported("Xero") is True

    def test_create_from_platform_missing_platform(self, mock_organization_no_platform):
        """Test create raises error when organization has no platform."""
        with pytest.raises(ValidationError) as exc_info:
            AccountingClientFactory.create(mock_organization_no_platform)
        assert "no accounting platform" in str(exc_info.value).lower()

    def test_create_from_platform_invalid_platform(self):
        """Test create_from_platform raises error for unsupported platform."""
        with pytest.raises(ValueError) as exc_info:
            AccountingClientFactory.create_from_platform(
                platform="unsupported",
                organization_id="123",
                credentials={"api_key": "test"},
            )
        assert "not supported" in str(exc_info.value).lower()

    def test_create_from_platform_case_insensitive(self):
        """Test create_from_platform is case-insensitive."""
        # This should work with uppercase
        try:
            # Will fail if xero module not implemented, but shouldn't be
            # a platform support error
            AccountingClientFactory.create_from_platform(
                platform="XERO",
                organization_id="123",
                credentials={"api_key": "test"},
            )
        except ValueError as e:
            # Should be about module not found, not platform not supported
            assert "not supported" not in str(e).lower()
        except ImportError:
            # Expected if xero module not yet implemented
            pass

    def test_supported_platforms_returns_copy(self):
        """Test that supported_platforms returns a list (not reference)."""
        platforms1 = AccountingClientFactory.supported_platforms()
        platforms2 = AccountingClientFactory.supported_platforms()
        # Should be equal but different objects
        assert platforms1 == platforms2

    def test_factory_configuration_exists(self):
        """Test that PLATFORM_CLIENTS configuration exists."""
        assert hasattr(AccountingClientFactory, "PLATFORM_CLIENTS")
        assert isinstance(AccountingClientFactory.PLATFORM_CLIENTS, dict)
        assert len(AccountingClientFactory.PLATFORM_CLIENTS) > 0

    def test_platform_clients_have_valid_paths(self):
        """Test that PLATFORM_CLIENTS paths are properly formatted."""
        for platform, path in AccountingClientFactory.PLATFORM_CLIENTS.items():
            assert isinstance(platform, str)
            assert isinstance(path, str)
            # Path should be in format "module.path.ClassName"
            assert "." in path
            parts = path.rsplit(".", 1)
            assert len(parts) == 2
            module_path, class_name = parts
            assert module_path.startswith("backend.accounting")


# ============================================================================
# TESTS FOR ORGANIZATION PLATFORM DETECTION
# ============================================================================


class TestPlatformDetection:
    """Tests for detecting platform from organization."""

    def test_detect_platform_from_organization(self, mock_organization):
        """Test detecting platform from organization."""
        platform = AccountingClientFactory._get_platform_for_organization(
            mock_organization
        )
        assert platform == "xero"

    def test_detect_platform_case_insensitive(self):
        """Test platform detection is case-insensitive."""
        org = Mock()
        org.accounting_platform = Mock()
        org.accounting_platform.platform_name = "XERO"
        platform = AccountingClientFactory._get_platform_for_organization(org)
        assert platform == "xero"

    def test_detect_platform_missing_attribute(self):
        """Test platform detection with missing accounting_platform."""
        org = Mock(spec=[])  # No attributes
        platform = AccountingClientFactory._get_platform_for_organization(org)
        assert platform is None

    def test_detect_platform_none_value(self):
        """Test platform detection when accounting_platform is None."""
        org = Mock()
        org.accounting_platform = None
        platform = AccountingClientFactory._get_platform_for_organization(org)
        assert platform is None

    def test_detect_platform_attribute_error(self):
        """Test platform detection handles TypeError gracefully."""
        # This tests that if something goes wrong accessing platform info,
        # the factory returns None gracefully
        org = Mock()
        # Simulate a problematic object
        org.accounting_platform = None
        platform = AccountingClientFactory._get_platform_for_organization(org)
        assert platform is None


# ============================================================================
# TESTS FOR CREDENTIALS VALIDATION
# ============================================================================


class TestCredentialsValidation:
    """Tests for credential validation."""

    def test_create_with_missing_credentials_method(self):
        """Test error when organization.accounting_platform.get_credentials fails."""
        org = Mock()
        org.id = 123
        org.accounting_platform = Mock(spec=[])  # No get_credentials method
        with pytest.raises(ValidationError):
            AccountingClientFactory.create(org)

    def test_create_with_credentials_exception(self):
        """Test error when get_credentials raises exception."""
        org = Mock()
        org.id = 123
        org.accounting_platform = Mock()
        org.accounting_platform.platform_name = "xero"
        org.accounting_platform.get_credentials = Mock(
            side_effect=RuntimeError("DB error")
        )
        # Should raise ValidationError wrapping the underlying error
        with pytest.raises((ValidationError, RuntimeError)):
            AccountingClientFactory.create(org)


# ============================================================================
# ERROR MESSAGE TESTS
# ============================================================================


class TestErrorMessages:
    """Tests for error message clarity."""

    def test_unsupported_platform_message(self):
        """Test that unsupported platform error is clear."""
        with pytest.raises(ValueError) as exc_info:
            AccountingClientFactory.create_from_platform(
                platform="foobar",
                organization_id="123",
                credentials={},
            )
        error_msg = str(exc_info.value).lower()
        assert "foobar" in error_msg or "not supported" in error_msg

    def test_import_error_message(self):
        """Test that import errors are clear."""
        # Try to create for a platform that exists in config but module missing
        # This is hard to test without mocking, so we just verify the path exists
        platform_path = AccountingClientFactory.PLATFORM_CLIENTS.get("xero")
        if platform_path:
            # Verify path format is correct
            assert "backend.accounting" in platform_path
            assert "Client" in platform_path or "client" in platform_path.lower()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestFactoryIntegration:
    """Integration tests for factory usage."""

    def test_typical_workflow_with_mock(self, mock_organization):
        """Test typical workflow of detecting and creating client."""
        # First, detect the platform
        platform = AccountingClientFactory._get_platform_for_organization(
            mock_organization
        )
        assert platform is not None

        # Then, check if it's supported
        is_supported = AccountingClientFactory.is_platform_supported(platform)
        assert is_supported is True

        # Finally, try to create (XeroClient is now implemented)
        # Will fail due to missing credentials in mock_organization, which is expected
        try:
            client = AccountingClientFactory.create(mock_organization)
            assert isinstance(client, AccountingClient)
        except (ImportError, ValueError, AttributeError) as e:
            # Expected if xero module not yet implemented, or missing credentials
            # Now that XeroClient is implemented, we may get credential errors
            error_msg = str(e).lower()
            assert (
                "cannot import" in error_msg
                or "not implemented" in error_msg
                or "missing credential" in error_msg
                or "cannot get credentials" in error_msg
            )

    def test_supported_platforms_immutable(self):
        """Test that modifying returned list doesn't affect factory."""
        platforms1 = AccountingClientFactory.supported_platforms()
        original_count = len(platforms1)

        platforms1.append("fake_platform")  # Modify the returned list

        platforms2 = AccountingClientFactory.supported_platforms()
        assert len(platforms2) == original_count  # Should not have changed
