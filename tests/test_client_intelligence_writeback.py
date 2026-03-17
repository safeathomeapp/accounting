from decimal import Decimal
from uuid import uuid4

from backend.models.account import Account
from backend.models.client_intelligence import (
    ClientAccountingPattern,
    ClientIntelligenceEvent,
    ClientIntelligenceProfile,
    ClientSupplierAlias,
)
from backend.models.contact import Contact
from backend.models.document import DocumentDraft, DocumentDraftLine
from backend.services.client_intelligence_writeback import record_reviewed_outcome


class _FakeQuery:
    def __init__(self, items):
        self._items = items

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._items[0] if self._items else None

    def all(self):
        return list(self._items)


class _FakeSession:
    def __init__(self, mapping=None):
        self.mapping = mapping or {}
        self.added = []
        self.flush_calls = 0

    def query(self, model):
        return _FakeQuery(self.mapping.setdefault(model, []))

    def add(self, obj):
        self.added.append(obj)
        self.mapping.setdefault(type(obj), []).append(obj)

    def flush(self):
        self.flush_calls += 1


def _build_draft(*, suggestions=True, tax_code="VAT20", nominal_code="4000"):
    draft = DocumentDraft(
        id=uuid4(),
        inbox_item_id=uuid4(),
        org_id=uuid4(),
        client_id=uuid4(),
        status="submitted",
        doc_type_guess="bill",
        doc_type_confirmed="bill",
        counterparty_guess="Harbor Supply Company",
    )
    draft.lines = [
        DocumentDraftLine(
            line_no=1,
            org_id=draft.org_id,
            description_confirmed="Office supplies",
            qty=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            net=Decimal("100.00"),
            vat=Decimal("20.00"),
            gross=Decimal("120.00"),
            nominal_code_confirmed=nominal_code,
            vat_code_confirmed=tax_code,
        )
    ]
    draft.draft_json = {
        "header": {"counterparty_name": "Harbor Supply Company"},
    }
    if suggestions:
        draft.draft_json["suggestions"] = {
            "contact": {"suggested_id": str(uuid4())},
            "nominal_account": {"suggested_id": str(uuid4())},
            "document_type": {"suggested_value": "invoice"},
            "tax_code": {"suggested_value": "ZERO"},
        }
    return draft


def test_record_reviewed_outcome_upserts_supplier_alias():
    draft = _build_draft()
    contact = Contact(
        id=uuid4(),
        organization_id=draft.org_id,
        client_id=draft.client_id,
        name="Harbor Supply Co.",
        contact_type="vendor",
        is_active=True,
    )
    account = Account(
        id=uuid4(),
        organization_id=draft.org_id,
        client_id=draft.client_id,
        platform_id="acct-1",
        platform_name="xero",
        code="4000",
        name="Office Supplies",
        account_type="expense",
        is_active=True,
    )
    db = _FakeSession({Contact: [contact], Account: [account]})
    draft.confirmed_contact_id = contact.id

    result = record_reviewed_outcome(
        db,
        draft=draft,
        actor_user_id=str(uuid4()),
    )

    aliases = db.mapping[ClientSupplierAlias]
    events = db.mapping[ClientIntelligenceEvent]
    assert result["updated"] is True
    assert len(aliases) == 1
    assert aliases[0].contact_id == contact.id
    assert aliases[0].alias_text == "Harbor Supply Company"
    assert any(event.event_type == "alias_confirmed" for event in events)


def test_record_reviewed_outcome_upserts_accounting_pattern():
    draft = _build_draft()
    account = Account(
        id=uuid4(),
        organization_id=draft.org_id,
        client_id=draft.client_id,
        platform_id="acct-1",
        platform_name="xero",
        code="4000",
        name="Office Supplies",
        account_type="expense",
        is_active=True,
    )
    db = _FakeSession({Account: [account]})

    result = record_reviewed_outcome(
        db,
        draft=draft,
        actor_user_id=str(uuid4()),
    )

    patterns = db.mapping[ClientAccountingPattern]
    events = db.mapping[ClientIntelligenceEvent]
    assert result["updated"] is True
    assert len(patterns) == 1
    assert patterns[0].pattern_type == "document_type"
    assert patterns[0].suggested_nominal_account_id == account.id
    assert patterns[0].suggested_tax_code == "VAT20"
    assert any(event.event_type == "accounting_pattern_strengthened" for event in events)


def test_record_reviewed_outcome_skips_alias_without_confirmed_contact():
    draft = _build_draft()
    account = Account(
        id=uuid4(),
        organization_id=draft.org_id,
        client_id=draft.client_id,
        platform_id="acct-1",
        platform_name="xero",
        code="4000",
        name="Office Supplies",
        account_type="expense",
        is_active=True,
    )
    db = _FakeSession({Account: [account]})

    record_reviewed_outcome(
        db,
        draft=draft,
        actor_user_id=str(uuid4()),
    )

    assert ClientSupplierAlias not in db.mapping or len(db.mapping[ClientSupplierAlias]) == 0
    skip_events = [event for event in db.mapping[ClientIntelligenceEvent] if event.event_type == "alias_learning_skipped"]
    assert len(skip_events) == 1
    assert skip_events[0].payload_json["reason"] == "missing_confirmed_contact"


def test_record_reviewed_outcome_creates_success_and_correction_events():
    draft = _build_draft()
    contact = Contact(
        id=uuid4(),
        organization_id=draft.org_id,
        client_id=draft.client_id,
        name="Harbor Supply Co.",
        contact_type="vendor",
        is_active=True,
    )
    account = Account(
        id=uuid4(),
        organization_id=draft.org_id,
        client_id=draft.client_id,
        platform_id="acct-1",
        platform_name="xero",
        code="4000",
        name="Office Supplies",
        account_type="expense",
        is_active=True,
    )
    db = _FakeSession({Contact: [contact], Account: [account]})
    draft.confirmed_contact_id = contact.id

    record_reviewed_outcome(
        db,
        draft=draft,
        actor_user_id=str(uuid4()),
    )

    event_types = [event.event_type for event in db.mapping[ClientIntelligenceEvent]]
    assert "alias_confirmed" in event_types
    assert "accounting_pattern_strengthened" in event_types
    assert "correction_observed" in event_types


def test_record_reviewed_outcome_does_not_require_suggestions_for_safe_skips():
    draft = _build_draft(suggestions=False, tax_code=None, nominal_code=None)
    db = _FakeSession()

    result = record_reviewed_outcome(
        db,
        draft=draft,
        actor_user_id=str(uuid4()),
    )

    assert result["updated"] is False
    assert len(db.mapping[ClientIntelligenceProfile]) == 1
    event_types = [event.event_type for event in db.mapping[ClientIntelligenceEvent]]
    assert "alias_learning_skipped" in event_types
    assert "accounting_pattern_skipped" in event_types
