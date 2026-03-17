"""
Worker: process_documents
Purpose: Process pending document inbox items through OCR extraction end-to-end.

Pipeline:
  1. Find DocumentInboxItem rows with status='uploaded'
  2. Delegate processing to the shared document orchestration service

Usage:
    python backend/workers/process_documents.py

Safe to run multiple times:
  - Existing OCR result  → updated in-place by the shared service
  - Existing user draft  → preserved by the shared service
  - File missing on disk → marked 'error'
  - OCR failure          → marked 'error'
"""

import logging
import sys
from pathlib import Path

# Ensure project root is importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.database import SessionLocal
from backend.models.document import DocumentInboxItem
from backend.services.document_processing import process_inbox_item

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

_TAG = "[WORKER]"


def log(msg: str) -> None:
    print(f"{_TAG} {msg}", flush=True)


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

        for item in pending:
            item_id = str(item.id)
            log(f"Processing document ID {item_id} ({item.file_name})")
            result = process_inbox_item(
                db,
                item_id,
                allow_mock_fallback=False,
            )
            if result.success:
                log(
                    f"Processed document ID {item_id} "
                    f"(mode={result.processing_mode}, status={result.final_inbox_status})"
                )
            else:
                log(
                    f"ERROR: Failed processing document ID {item_id} "
                    f"({result.error_code}: {result.error_message})"
                )

    finally:
        db.close()


if __name__ == "__main__":
    run()
