from datetime import date
from decimal import Decimal
from uuid import uuid4

from backend.models.document import DocumentDraft, DocumentInboxItem
from backend.services.claude_ocr import ClaudeOCRError
from backend.services.document_processing import process_inbox_item


class _FakeQuery:
    def __init__(self, inbox_item):
        self._inbox_item = inbox_item

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return []

    def first(self):
        return self._inbox_item


class _FakeSession:
    def __init__(self, inbox_item):
        self.inbox_item = inbox_item
        self.added = []
        self.flush_calls = 0
        self.commit_calls = 0

    def query(self, model):
        items = self.inbox_item if model is DocumentInboxItem else None
        return _FakeQuery(items)

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flush_calls += 1

    def commit(self):
        self.commit_calls += 1


def _build_inbox_item(*, client_id=True):
    return DocumentInboxItem(
        id=uuid4(),
        org_id=uuid4(),
        uploaded_by_user_id=uuid4(),
        client_id=uuid4() if client_id else None,
        file_name="invoice.pdf",
        mime_type="application/pdf",
        file_path="C:/tmp/invoice.pdf",
        checksum_hash="abc123",
        status="uploaded",
        source_type="upload",
    )


def _build_draft_data():
    return {
        "doc_type": "invoice",
        "counterparty_name": "Harbor Supply Co.",
        "doc_date": date(2026, 3, 1),
        "due_date": date(2026, 3, 31),
        "currency": "GBP",
        "invoice_no": "INV-1001",
        "totals": {
            "net": Decimal("100.00"),
            "vat": Decimal("20.00"),
            "gross": Decimal("120.00"),
        },
        "lines": [
            {
                "line_no": 1,
                "description": "Consulting services",
                "qty": Decimal("1.00"),
                "unit_price": Decimal("100.00"),
                "net": Decimal("100.00"),
                "vat": Decimal("20.00"),
                "gross": Decimal("120.00"),
                "vat_code": "VAT20",
                "nominal_code": "4000",
                "confidence": Decimal("0.90"),
            }
        ],
        "raw_text": "Invoice text",
        "confidence": Decimal("0.90"),
        "vendor": {"name": "Harbor Supply Co."},
        "customer": {"name": "Client Ltd"},
    }


def test_process_inbox_item_requires_client_scope(monkeypatch):
    inbox_item = _build_inbox_item(client_id=False)
    db = _FakeSession(inbox_item)

    monkeypatch.setattr("backend.services.document_processing.os.path.exists", lambda path: True)

    result = process_inbox_item(db, str(inbox_item.id))

    assert result.success is False
    assert result.http_status == 409
    assert result.error_code == "missing_client_id"
    assert inbox_item.status == "error"


def test_process_inbox_item_creates_or_updates_ocr_and_draft(monkeypatch):
    inbox_item = _build_inbox_item()
    db = _FakeSession(inbox_item)

    class OCRStub:
        def extract_document(self, file_path, mime_type=None):
            return _build_draft_data()

    monkeypatch.setattr("backend.services.document_processing.os.path.exists", lambda path: True)
    monkeypatch.setattr(
        "backend.services.document_processing.build_suggestion_payload",
        lambda *args, **kwargs: {
            "contact": {
                "suggested_id": str(uuid4()),
                "suggested_name": "Harbor Supply Co.",
                "confidence": "high",
                "reasons": ["matched known supplier alias for this client"],
            },
            "nominal_account": {
                "suggested_id": str(uuid4()),
                "suggested_code": "4000",
                "suggested_name": "Office Supplies",
                "confidence": "high",
                "reasons": ["prior accounting pattern found for matched contact"],
            },
            "document_type": {
                "suggested_value": "bill",
                "confidence": "medium",
                "reasons": ["pattern matched current document type"],
            },
            "tax_code": {
                "suggested_value": "VAT20",
                "confidence": "high",
                "reasons": ["prior accounting pattern found for matched contact"],
            },
        },
    )

    result = process_inbox_item(
        db,
        str(inbox_item.id),
        actor_user_id=str(uuid4()),
        allow_mock_fallback=False,
        ocr_service=OCRStub(),
    )

    assert result.success is True
    assert result.processing_mode == "processed"
    assert result.final_inbox_status == "drafted"
    assert inbox_item.status == "drafted"
    assert result.ocr_result is not None
    assert result.ocr_result.raw_text == "Invoice text"
    assert result.draft is not None
    assert result.draft.doc_type_guess == "invoice"
    assert result.draft.totals_guess == {"net": "100.00", "vat": "20.00", "gross": "120.00"}
    assert len(result.draft.lines) == 1
    assert result.draft.draft_json["suggestions"]["contact"]["confidence"] == "high"
    assert result.draft.draft_json["suggestions"]["tax_code"]["suggested_value"] == "VAT20"


def test_process_inbox_item_preserves_user_edited_draft(monkeypatch):
    inbox_item = _build_inbox_item()
    inbox_item.draft = DocumentDraft(
        inbox_item_id=inbox_item.id,
        org_id=inbox_item.org_id,
        client_id=inbox_item.client_id,
        status="draft",
        draft_json={"source": "user-edit"},
    )
    db = _FakeSession(inbox_item)

    class OCRStub:
        def __init__(self):
            self.called = False

        def extract_document(self, file_path, mime_type=None):
            self.called = True
            return _build_draft_data()

    ocr_stub = OCRStub()
    monkeypatch.setattr("backend.services.document_processing.os.path.exists", lambda path: True)

    result = process_inbox_item(
        db,
        str(inbox_item.id),
        allow_mock_fallback=False,
        ocr_service=ocr_stub,
    )

    assert result.success is True
    assert result.processing_mode == "preserved_existing_draft"
    assert ocr_stub.called is False
    assert inbox_item.status == "drafted"


def test_process_inbox_item_marks_error_on_ocr_failure_without_mock(monkeypatch):
    inbox_item = _build_inbox_item()
    db = _FakeSession(inbox_item)

    class OCRStub:
        def extract_document(self, file_path, mime_type=None):
            raise ClaudeOCRError("Claude unavailable")

    monkeypatch.setattr("backend.services.document_processing.os.path.exists", lambda path: True)

    result = process_inbox_item(
        db,
        str(inbox_item.id),
        allow_mock_fallback=False,
        ocr_service=OCRStub(),
    )

    assert result.success is False
    assert result.error_code == "ocr_failed"
    assert result.http_status == 422
    assert inbox_item.status == "error"
    assert result.ocr_result is not None
    assert result.ocr_result.layout_json["extraction_error"] == "Claude unavailable"


def test_process_inbox_item_uses_mock_fallback_when_enabled(monkeypatch):
    inbox_item = _build_inbox_item()
    db = _FakeSession(inbox_item)

    class OCRStub:
        def extract_document(self, file_path, mime_type=None):
            raise ClaudeOCRError("Claude unavailable")

    monkeypatch.setattr("backend.services.document_processing.os.path.exists", lambda path: True)

    result = process_inbox_item(
        db,
        str(inbox_item.id),
        allow_mock_fallback=True,
        ocr_service=OCRStub(),
    )

    assert result.success is True
    assert result.used_mock_fallback is True
    assert result.ocr_engine == "stub-v1"
    assert inbox_item.status == "drafted"
    assert result.draft is not None


def test_process_inbox_item_keeps_confirmed_values_while_refreshing_suggestions(monkeypatch):
    inbox_item = _build_inbox_item()
    existing_confirmed_contact_id = uuid4()
    inbox_item.draft = DocumentDraft(
        inbox_item_id=inbox_item.id,
        org_id=inbox_item.org_id,
        client_id=inbox_item.client_id,
        status="draft",
        doc_type_confirmed="bill",
        confirmed_contact_id=existing_confirmed_contact_id,
        draft_json={"source": "claude-ocr"},
    )
    db = _FakeSession(inbox_item)

    class OCRStub:
        def extract_document(self, file_path, mime_type=None):
            return _build_draft_data()

    monkeypatch.setattr("backend.services.document_processing.os.path.exists", lambda path: True)
    monkeypatch.setattr(
        "backend.services.document_processing.build_suggestion_payload",
        lambda *args, **kwargs: {
            "contact": {
                "suggested_id": str(uuid4()),
                "suggested_name": "Harbor Supply Co.",
                "confidence": "high",
                "reasons": ["matched known supplier alias for this client"],
            },
            "nominal_account": {
                "suggested_id": str(uuid4()),
                "suggested_code": "4000",
                "suggested_name": "Office Supplies",
                "confidence": "medium",
                "reasons": ["prior accounting pattern found for matched contact"],
            },
            "document_type": {
                "suggested_value": "bill",
                "confidence": "medium",
                "reasons": ["pattern matched current document type"],
            },
            "tax_code": {
                "suggested_value": "VAT20",
                "confidence": "medium",
                "reasons": ["pattern matched current document type"],
            },
        },
    )

    result = process_inbox_item(
        db,
        str(inbox_item.id),
        allow_mock_fallback=False,
        ocr_service=OCRStub(),
    )

    assert result.success is True
    assert result.draft is not None
    assert result.draft.doc_type_confirmed == "bill"
    assert result.draft.confirmed_contact_id == existing_confirmed_contact_id
    assert result.draft.draft_json["suggestions"]["nominal_account"]["suggested_code"] == "4000"
