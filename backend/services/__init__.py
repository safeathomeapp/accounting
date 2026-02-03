"""
Backend services module.

Contains service classes for external integrations:
- claude_ocr: Claude Vision OCR for document extraction
- mobile_auth: Mobile authentication services
"""

from backend.services.claude_ocr import (
    ClaudeOCRService,
    ClaudeOCRError,
    extract_document,
    get_claude_ocr_service,
)

__all__ = [
    "ClaudeOCRService",
    "ClaudeOCRError",
    "extract_document",
    "get_claude_ocr_service",
]
