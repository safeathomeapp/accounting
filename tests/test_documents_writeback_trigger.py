from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from fastapi import HTTPException
from backend.api.documents_routes import (
    DraftLinePayload,
    DraftUpdatePayload,
    TotalsPayload,
    submit_draft,
    update_draft,
)
from backend.models.contact import Contact
from backend.models.document import DocumentDraft, DocumentDraftLine, DocumentInboxItem
from backend.models.transaction import Transaction


class _FakeQuery:
    def __init__(self, db, model):
        self.db = db
        self.model = model

    def join(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        if self.model is DocumentDraft:
            return self.db.draft
        if self.model is Transaction:
            return self.db.transaction
        if self.model is Contact:
            return self.db.contact
        return None

    def delete(self):
        self.db.deleted_line_query = True


class _FakeSession:
    def __init__(self, draft, contact=None):
        self.draft = draft
        self.contact = contact
        self.transaction = None
        self.deleted_line_query = False
        self.added = []
        self.commit_calls = 0

    def query(self, model):
        return _FakeQuery(self, model)

    def add(self, obj):
        self.added.append(obj)
        if isinstance(obj, Transaction):
            self.transaction = obj

    def commit(self):
        self.commit_calls += 1

    def refresh(self, obj):
        return None


def _build_payload():
    return DraftUpdatePayload(
        doc_type="bill",
        counterparty_name="Harbor Supply Company",
        confirmed_contact_id=str(uuid4()),
        doc_date=date(2026, 3, 10),
        due_date=date(2026, 3, 31),
        currency="GBP",
        invoice_no="INV-1001",
        totals=TotalsPayload(net=Decimal("100.00"), vat=Decimal("20.00"), gross=Decimal("120.00")),
        lines=[
            DraftLinePayload(
                line_no=1,
                description="Office supplies",
                qty=Decimal("1.00"),
                unit_price=Decimal("100.00"),
                net=Decimal("100.00"),
                vat=Decimal("20.00"),
                gross=Decimal("120.00"),
                vat_code="VAT20",
                nominal_code="4000",
            )
        ],
    )


def _build_draft():
    inbox_item = DocumentInboxItem(
        id=uuid4(),
        org_id=uuid4(),
        client_id=uuid4(),
        uploaded_by_user_id=uuid4(),
        file_name="invoice.pdf",
        mime_type="application/pdf",
        file_path="C:/tmp/invoice.pdf",
        checksum_hash="abc123",
        status="drafted",
        source_type="upload",
    )
    draft = DocumentDraft(
        id=uuid4(),
        inbox_item_id=inbox_item.id,
        org_id=inbox_item.org_id,
        client_id=inbox_item.client_id,
        status="draft",
        counterparty_guess="OCR Supplier Ltd",
        draft_json={
            "header": {"counterparty_name": "OCR Supplier Ltd"},
            "suggestions": {"contact": {"suggested_id": str(uuid4())}},
        },
    )
    draft.lines = [
        DocumentDraftLine(
            line_no=1,
            org_id=inbox_item.org_id,
            description_confirmed="Old line",
            qty=Decimal("1.00"),
            unit_price=Decimal("1.00"),
            net=Decimal("1.00"),
            vat=Decimal("0.20"),
            gross=Decimal("1.20"),
        )
    ]
    draft.inbox_item = inbox_item
    return draft


def test_partial_save_does_not_trigger_writeback(monkeypatch):
    draft = _build_draft()
    payload = _build_payload()
    contact = Contact(
        id=payload.confirmed_contact_id,
        organization_id=draft.org_id,
        client_id=draft.client_id,
        name="Harbor Supply Company",
        contact_type="vendor",
        is_active=True,
    )
    db = _FakeSession(draft, contact=contact)
    current_user = SimpleNamespace(id=uuid4(), organization_id=draft.org_id)
    calls = []

    monkeypatch.setattr(
        "backend.api.documents_routes.record_reviewed_outcome",
        lambda *args, **kwargs: calls.append("called"),
    )

    update_draft(
        str(draft.id),
        payload,
        db=db,
        current_user=current_user,
    )

    assert calls == []
    assert draft.confirmed_contact_id == contact.id
    assert draft.counterparty_guess == "OCR Supplier Ltd"
    assert draft.draft_json["header"]["counterparty_name"] == "OCR Supplier Ltd"
    assert draft.draft_json["review"]["confirmed_counterparty_name"] == payload.counterparty_name
    assert draft.draft_json["suggestions"]["contact"]["suggested_id"] is not None


def test_submit_fails_when_confirmed_contact_is_not_in_client_scope():
    draft = _build_draft()
    db = _FakeSession(draft, contact=None)
    payload = _build_payload()
    current_user = SimpleNamespace(id=uuid4(), organization_id=draft.org_id)

    try:
        submit_draft(
            str(draft.id),
            payload,
            db=db,
            current_user=current_user,
        )
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "Confirmed contact must belong to the current client"
    else:
        raise AssertionError("Expected submit_draft to fail for out-of-scope contact")


def test_successful_submit_triggers_writeback(monkeypatch):
    draft = _build_draft()
    payload = _build_payload()
    contact = Contact(
        id=payload.confirmed_contact_id,
        organization_id=draft.org_id,
        client_id=draft.client_id,
        name="Harbor Supply Company",
        contact_type="vendor",
        is_active=True,
    )
    db = _FakeSession(draft, contact=contact)
    current_user = SimpleNamespace(id=uuid4(), organization_id=draft.org_id)
    calls = []

    monkeypatch.setattr(
        "backend.api.documents_routes.record_reviewed_outcome",
        lambda *args, **kwargs: calls.append(kwargs),
    )

    submit_draft(
        str(draft.id),
        payload,
        db=db,
        current_user=current_user,
    )

    assert len(calls) == 1
    assert calls[0]["draft"] is draft
    assert calls[0]["actor_user_id"] == current_user.id
    assert draft.confirmed_contact_id == contact.id


def test_submit_response_exposes_confirmed_contact_without_legacy_counterparty_id(monkeypatch):
    draft = _build_draft()
    payload = _build_payload()
    contact = Contact(
        id=payload.confirmed_contact_id,
        organization_id=draft.org_id,
        client_id=draft.client_id,
        name="Harbor Supply Company",
        contact_type="vendor",
        is_active=True,
    )
    db = _FakeSession(draft, contact=contact)
    current_user = SimpleNamespace(id=uuid4(), organization_id=draft.org_id)

    monkeypatch.setattr(
        "backend.api.documents_routes.record_reviewed_outcome",
        lambda *args, **kwargs: None,
    )

    response = submit_draft(
        str(draft.id),
        payload,
        db=db,
        current_user=current_user,
    )

    assert response["draft"]["confirmed_contact_id"] == str(contact.id)
    assert response["draft"]["confirmed_contact"]["id"] == str(contact.id)
    assert "counterparty_id" not in response["draft"]
