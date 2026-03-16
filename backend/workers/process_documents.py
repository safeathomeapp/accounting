"""
Worker: process_documents
Purpose: Process pending document inbox items through OCR extraction end-to-end.

Pipeline:
  1. Find DocumentInboxItem rows with status='uploaded'
  2. Run Claude OCR extraction via ClaudeOCRService
  3. Save/update DocumentOCRResult
  4. Create DocumentDraft (skipped if one already exists)
  5. Mark inbox item status='extracted'

Usage:
    python backend/workers/process_documents.py

Safe to run multiple times:
  - Existing OCR result  → updated in-place
  - Existing draft       → skipped (not overwritten)
  - File missing on disk → marked 'error', skipped
  - OCR failure          → marked 'error', skipped
"""

import logging
import os
import sys
from decimal import Decimal
from pathlib import Path

# Ensure project root is importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import settings
from backend.database import SessionLocal
from backend.models.document import DocumentDraft, DocumentInboxItem, DocumentOCRResult
from backend.services.claude_ocr import ClaudeOCRError, ClaudeOCRService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

_TAG = "[WORKER]"


def log(msg: str) -> None:
    print(f"{_TAG} {msg}", flush=True)


# ---------------------------------------------------------------------------
# Helpers — mirror the structure used by the /inbox/{id}/extract API route
# ---------------------------------------------------------------------------

def _totals_to_str(totals: dict) -> dict:
    """Convert Decimal totals to strings for JSONB storage."""
    return {
        "net": str(totals["net"]),
        "vat": str(totals["vat"]),
        "gross": str(totals["gross"]),
    }


def _build_validation(draft_data: dict) -> dict:
    """Basic validation summary: checks that line gross values sum to the header gross."""
    totals = draft_data["totals"]
    lines = draft_data["lines"]
    lines_gross_sum = sum(line["gross"] for line in lines)
    return {
        "totals_match": abs(totals["gross"] - lines_gross_sum) < Decimal("0.02"),
        "line_count": len(lines),
    }


def _build_draft_json(draft_data: dict) -> dict:
    """Build draft_json in the same structure as the API extract endpoint."""
    return {
        "source": "claude-ocr",
        "header": {
            "doc_type": draft_data["doc_type"],
            "counterparty_name": draft_data["counterparty_name"],
            "doc_date": draft_data["doc_date"].isoformat() if draft_data["doc_date"] else None,
            "due_date": draft_data["due_date"].isoformat() if draft_data["due_date"] else None,
            "currency": draft_data["currency"],
            "invoice_no": draft_data["invoice_no"],
            "order_no": draft_data.get("order_no"),
            "payment_terms": draft_data.get("payment_terms"),
            "payment_status": draft_data.get("payment_status"),
            "totals": _totals_to_str(draft_data["totals"]),
        },
        "vendor": draft_data.get("vendor"),
        "customer": draft_data.get("customer"),
        "lines": [
            {
                "line_no": line["line_no"],
                "description": line["description"],
                "qty": str(line["qty"]),
                "unit_price": str(line["unit_price"]),
                "net": str(line["net"]),
                "vat": str(line["vat"]),
                "gross": str(line["gross"]),
                "vat_code": line.get("vat_code"),
                "nominal_code": line.get("nominal_code"),
                "confidence": str(line["confidence"]) if line.get("confidence") is not None else None,
            }
            for line in draft_data["lines"]
        ],
        "raw_text": draft_data.get("raw_text"),
        "confidence": str(draft_data.get("confidence")) if draft_data.get("confidence") else None,
    }


# ---------------------------------------------------------------------------
# Per-item processor
# ---------------------------------------------------------------------------

def _process_item(db, item: DocumentInboxItem, ocr: ClaudeOCRService) -> None:
    item_id = str(item.id)
    log(f"Processing document ID {item_id} ({item.file_name})")

    # 1. Verify the file is present on disk
    if not os.path.exists(item.file_path):
        log(f"ERROR: File not found on disk: {item.file_path} — marking error and skipping")
        item.status = "error"
        db.commit()
        return

    # 2. Run OCR extraction
    ocr_engine = f"claude-{settings.claude_model}"
    extraction_error = None
    try:
        draft_data = ocr.extract_document(item.file_path, item.mime_type)
        log(f"OCR extraction complete")
    except ClaudeOCRError as exc:
        extraction_error = str(exc)
        log(f"ERROR: OCR extraction failed: {exc} — marking error and skipping")
        item.status = "error"
        db.commit()
        return

    # 3. Save OCR result (upsert — update if it already exists)
    existing_ocr = (
        db.query(DocumentOCRResult)
        .filter(DocumentOCRResult.inbox_item_id == item.id)
        .first()
    )
    if existing_ocr:
        log(f"OCR result already exists for {item_id} — updating in-place")
        existing_ocr.ocr_engine = ocr_engine
        existing_ocr.raw_text = draft_data.get("raw_text", "")
        existing_ocr.layout_json = {
            "pages": 1,
            "extraction_source": ocr_engine,
            "extraction_error": extraction_error,
        }
        existing_ocr.pages = 1
    else:
        db.add(
            DocumentOCRResult(
                inbox_item_id=item.id,
                org_id=item.org_id,
                ocr_engine=ocr_engine,
                raw_text=draft_data.get("raw_text", ""),
                layout_json={
                    "pages": 1,
                    "extraction_source": ocr_engine,
                    "extraction_error": extraction_error,
                },
                pages=1,
            )
        )
    db.flush()

    # 4. Create draft (skip if one already exists — do not overwrite human edits)
    existing_draft = (
        db.query(DocumentDraft)
        .filter(DocumentDraft.inbox_item_id == item.id)
        .first()
    )
    if existing_draft:
        log(f"Draft already exists for {item_id} (ID {existing_draft.id}) — skipping creation")
    else:
        totals_str = _totals_to_str(draft_data["totals"])
        draft = DocumentDraft(
            inbox_item_id=item.id,
            org_id=item.org_id,
            client_id=item.client_id,
            status="draft",
            doc_type_guess=draft_data["doc_type"],
            counterparty_guess=draft_data["counterparty_name"],
            doc_date_guess=draft_data["doc_date"],
            currency_guess=draft_data["currency"],
            invoice_no_guess=draft_data["invoice_no"],
            totals_guess=totals_str,
            totals_confirmed=totals_str,
            draft_json=_build_draft_json(draft_data),
            validation_json=_build_validation(draft_data),
        )
        db.add(draft)
        db.flush()
        log(f"Draft created ID {str(draft.id)}")

    # 5. Mark inbox item as processed
    item.status = "extracted"
    db.commit()
    log(f"Document marked processed")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run() -> None:
    db = SessionLocal()
    try:
        pending = (
            db.query(DocumentInboxItem)
            .filter(DocumentInboxItem.status == "uploaded")
            .order_by(DocumentInboxItem.created_at)
            .all()
        )

        log(f"Found {len(pending)} inbox items")

        if not pending:
            return

        # Initialise service once — validates that CLAUDE_API_KEY is present
        try:
            ocr = ClaudeOCRService()
        except ClaudeOCRError as exc:
            log(f"ERROR: Cannot initialise OCR service: {exc}")
            sys.exit(1)

        for item in pending:
            _process_item(db, item, ocr)

    finally:
        db.close()


if __name__ == "__main__":
    run()
