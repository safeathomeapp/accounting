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
from backend.services.client_intelligence import (
    build_suggestion_payload,
    get_accounting_pattern_suggestions,
    get_client_intelligence_profile,
    match_contact_alias,
)
from backend.services.client_intelligence_writeback import (
    append_intelligence_event,
    record_reviewed_outcome,
    upsert_accounting_pattern_from_review,
    upsert_supplier_alias_from_review,
)
from backend.services.document_processing import (
    DocumentProcessingResult,
    process_inbox_item,
)

__all__ = [
    "ClaudeOCRService",
    "ClaudeOCRError",
    "DocumentProcessingResult",
    "build_suggestion_payload",
    "append_intelligence_event",
    "extract_document",
    "get_accounting_pattern_suggestions",
    "get_claude_ocr_service",
    "get_client_intelligence_profile",
    "match_contact_alias",
    "process_inbox_item",
    "record_reviewed_outcome",
    "upsert_accounting_pattern_from_review",
    "upsert_supplier_alias_from_review",
]
