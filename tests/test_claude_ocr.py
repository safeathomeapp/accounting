"""Tests for Claude OCR service."""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from backend.services.claude_ocr import (
    ClaudeOCRService,
    ClaudeOCRError,
    extract_document,
    get_claude_ocr_service,
)


class TestClaudeOCRServiceInit:
    """Tests for ClaudeOCRService initialization."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        with patch('backend.services.claude_ocr.anthropic.Anthropic') as mock_anthropic:
            service = ClaudeOCRService(api_key="test-key")
            assert service.api_key == "test-key"
            mock_anthropic.assert_called_once_with(api_key="test-key")

    def test_init_without_api_key_raises_error(self):
        """Test that initialization fails without API key."""
        with patch('backend.services.claude_ocr.settings') as mock_settings:
            mock_settings.claude_api_key = ""
            with pytest.raises(ClaudeOCRError, match="API key not configured"):
                ClaudeOCRService()


class TestClaudeOCRServiceParsing:
    """Tests for parsing helper methods."""

    @pytest.fixture
    def service(self):
        """Create service with mocked anthropic client."""
        with patch('backend.services.claude_ocr.anthropic.Anthropic'):
            with patch('backend.services.claude_ocr.settings') as mock_settings:
                mock_settings.claude_api_key = "test-key"
                mock_settings.claude_model = "claude-sonnet-4-20250514"
                mock_settings.claude_max_tokens = 4096
                return ClaudeOCRService(api_key="test-key")

    def test_parse_decimal_from_string(self, service):
        """Test parsing decimal from string."""
        assert service._parse_decimal("100.50") == Decimal("100.50")
        assert service._parse_decimal("1,234.56") == Decimal("1234.56")
        assert service._parse_decimal("£99.99") == Decimal("99.99")
        assert service._parse_decimal("$500") == Decimal("500.00")

    def test_parse_decimal_from_none(self, service):
        """Test parsing decimal from None."""
        assert service._parse_decimal(None) == Decimal("0.00")
        assert service._parse_decimal(None, "1.00") == Decimal("1.00")

    def test_parse_decimal_from_invalid(self, service):
        """Test parsing decimal from invalid string."""
        assert service._parse_decimal("not a number") == Decimal("0.00")
        assert service._parse_decimal("") == Decimal("0.00")

    def test_parse_date_iso_format(self, service):
        """Test parsing date in ISO format."""
        result = service._parse_date("2025-12-31")
        assert result == date(2025, 12, 31)

    def test_parse_date_uk_format(self, service):
        """Test parsing date in UK format."""
        result = service._parse_date("31/12/2025")
        assert result == date(2025, 12, 31)

    def test_parse_date_none(self, service):
        """Test parsing None date."""
        assert service._parse_date(None) is None
        assert service._parse_date("") is None

    def test_parse_date_invalid(self, service):
        """Test parsing invalid date."""
        assert service._parse_date("not a date") is None


class TestClaudeOCRServiceValidation:
    """Tests for validation and normalization."""

    @pytest.fixture
    def service(self):
        """Create service with mocked anthropic client."""
        with patch('backend.services.claude_ocr.anthropic.Anthropic'):
            with patch('backend.services.claude_ocr.settings') as mock_settings:
                mock_settings.claude_api_key = "test-key"
                mock_settings.claude_model = "claude-sonnet-4-20250514"
                mock_settings.claude_max_tokens = 4096
                return ClaudeOCRService(api_key="test-key")

    def test_validate_and_normalize_complete_data(self, service):
        """Test normalization of complete extracted data."""
        raw_data = {
            "doc_type": "invoice",
            "counterparty_name": "Test Company Ltd",
            "doc_date": "2025-01-15",
            "due_date": "2025-02-15",
            "currency": "GBP",
            "invoice_no": "INV-001",
            "totals": {
                "net": "100.00",
                "vat": "20.00",
                "gross": "120.00",
            },
            "lines": [
                {
                    "line_no": 1,
                    "description": "Consulting",
                    "qty": "1",
                    "unit_price": "100.00",
                    "net": "100.00",
                    "vat": "20.00",
                    "gross": "120.00",
                    "confidence": "0.95",
                }
            ],
        }

        result = service._validate_and_normalize(raw_data)

        assert result["doc_type"] == "invoice"
        assert result["counterparty_name"] == "Test Company Ltd"
        assert result["doc_date"] == date(2025, 1, 15)
        assert result["due_date"] == date(2025, 2, 15)
        assert result["currency"] == "GBP"
        assert result["invoice_no"] == "INV-001"
        assert result["totals"]["net"] == Decimal("100.00")
        assert result["totals"]["vat"] == Decimal("20.00")
        assert result["totals"]["gross"] == Decimal("120.00")
        assert len(result["lines"]) == 1
        assert result["lines"][0]["description"] == "Consulting"

    def test_validate_and_normalize_minimal_data(self, service):
        """Test normalization with minimal data."""
        raw_data = {
            "totals": {"gross": "100.00"},
        }

        result = service._validate_and_normalize(raw_data)

        assert result["doc_type"] == "invoice"  # Default
        assert result["counterparty_name"] == "Unknown"
        assert result["currency"] == "GBP"  # Default
        assert result["totals"]["gross"] == Decimal("100.00")
        # Should create a single line from totals
        assert len(result["lines"]) == 1
        assert result["lines"][0]["description"] == "Document total"

    def test_validate_and_normalize_empty_data(self, service):
        """Test normalization with empty data."""
        result = service._validate_and_normalize({})

        assert result["doc_type"] == "invoice"
        assert result["counterparty_name"] == "Unknown"
        assert result["totals"]["gross"] == Decimal("0.00")


class TestClaudeOCRServiceExtraction:
    """Tests for document extraction."""

    @pytest.fixture
    def service(self):
        """Create service with mocked anthropic client."""
        with patch('backend.services.claude_ocr.anthropic.Anthropic') as mock_anthropic:
            with patch('backend.services.claude_ocr.settings') as mock_settings:
                mock_settings.claude_api_key = "test-key"
                mock_settings.claude_model = "claude-sonnet-4-20250514"
                mock_settings.claude_max_tokens = 4096
                service = ClaudeOCRService(api_key="test-key")
                service._mock_client = mock_anthropic.return_value
                return service

    def test_extract_document_success(self, service, tmp_path):
        """Test successful document extraction."""
        # Create a test image file
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"fake png content")

        # Mock Claude response
        mock_response = Mock()
        mock_response.content = [Mock(text='''
        {
            "doc_type": "invoice",
            "counterparty_name": "ABC Corp",
            "doc_date": "2025-01-20",
            "currency": "GBP",
            "invoice_no": "INV-123",
            "totals": {"net": "500.00", "vat": "100.00", "gross": "600.00"},
            "lines": [
                {"line_no": 1, "description": "Service", "qty": "1", "unit_price": "500.00", "net": "500.00", "vat": "100.00", "gross": "600.00"}
            ]
        }
        ''')]
        service._mock_client.messages.create.return_value = mock_response

        result = service.extract_document(str(test_file))

        assert result["doc_type"] == "invoice"
        assert result["counterparty_name"] == "ABC Corp"
        assert result["totals"]["gross"] == Decimal("600.00")
        assert len(result["lines"]) == 1

    def test_extract_document_file_not_found(self, service):
        """Test extraction with non-existent file."""
        with pytest.raises(ClaudeOCRError, match="File not found"):
            service.extract_document("/nonexistent/file.png")

    def test_extract_document_unsupported_type(self, service, tmp_path):
        """Test extraction with unsupported file type."""
        test_file = tmp_path / "test.xyz"
        test_file.write_bytes(b"some content")

        with pytest.raises(ClaudeOCRError, match="Unsupported file type"):
            service.extract_document(str(test_file))


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_claude_ocr_service_singleton(self):
        """Test that get_claude_ocr_service returns a singleton."""
        with patch('backend.services.claude_ocr.anthropic.Anthropic'):
            with patch('backend.services.claude_ocr.settings') as mock_settings:
                mock_settings.claude_api_key = "test-key"
                mock_settings.claude_model = "claude-sonnet-4-20250514"
                mock_settings.claude_max_tokens = 4096

                # Reset singleton
                import backend.services.claude_ocr as module
                module._service_instance = None

                service1 = get_claude_ocr_service()
                service2 = get_claude_ocr_service()

                assert service1 is service2
