from decimal import Decimal
from uuid import uuid4

from backend.models.account import Account
from backend.models.client_intelligence import ClientAccountingPattern, ClientSupplierAlias
from backend.models.contact import Contact
from backend.services.client_intelligence import (
    build_suggestion_payload,
    get_accounting_pattern_suggestions,
    match_contact_alias,
    normalize_match_text,
)


class _FakeQuery:
    def __init__(self, items):
        self._items = items

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return list(self._items)

    def first(self):
        return self._items[0] if self._items else None


class _FakeSession:
    def __init__(self, mapping):
        self.mapping = mapping

    def query(self, model):
        return _FakeQuery(self.mapping.get(model, []))


def test_match_contact_alias_returns_exact_client_alias_match():
    organization_id = uuid4()
    client_id = uuid4()
    contact = Contact(
        id=uuid4(),
        organization_id=organization_id,
        client_id=client_id,
        name="Harbor Supply Co.",
        contact_type="vendor",
        is_active=True,
    )
    alias = ClientSupplierAlias(
        id=uuid4(),
        organization_id=organization_id,
        client_id=client_id,
        profile_id=uuid4(),
        contact_id=contact.id,
        alias_text="Harbor Supply Company",
        alias_normalized=normalize_match_text("Harbor Supply Company"),
        source_type="review",
        match_count=4,
        confidence_score=Decimal("0.95"),
        is_active=True,
    )
    alias.contact = contact
    db = _FakeSession({ClientSupplierAlias: [alias]})

    suggestion = match_contact_alias(
        db,
        organization_id=str(organization_id),
        client_id=str(client_id),
        raw_supplier_text="Harbor Supply Company",
    )

    assert suggestion["suggested_id"] == str(contact.id)
    assert suggestion["suggested_name"] == "Harbor Supply Co."
    assert suggestion["confidence"] == "high"
    assert "matched known supplier alias for this client" in suggestion["reasons"]


def test_match_contact_alias_returns_no_match_payload():
    organization_id = uuid4()
    client_id = uuid4()
    db = _FakeSession({})

    suggestion = match_contact_alias(
        db,
        organization_id=str(organization_id),
        client_id=str(client_id),
        raw_supplier_text="Unknown Supplier",
    )

    assert suggestion["suggested_id"] is None
    assert suggestion["confidence"] == "low"
    assert suggestion["reasons"]


def test_get_accounting_pattern_suggestions_uses_contact_pattern():
    organization_id = uuid4()
    client_id = uuid4()
    contact_id = uuid4()
    account = Account(
        id=uuid4(),
        organization_id=organization_id,
        client_id=client_id,
        platform_id="acct-1",
        platform_name="xero",
        code="4000",
        name="Office Supplies",
        account_type="expense",
    )
    pattern = ClientAccountingPattern(
        id=uuid4(),
        organization_id=organization_id,
        client_id=client_id,
        profile_id=uuid4(),
        pattern_type="contact_document_type",
        pattern_key=f"{contact_id}:bill",
        contact_id=contact_id,
        suggested_nominal_account_id=account.id,
        suggested_tax_code="VAT20",
        suggested_document_type="bill",
        usage_count=5,
        success_count=5,
        confidence_score=Decimal("0.92"),
        is_active=True,
    )
    pattern.suggested_nominal_account = account
    db = _FakeSession({ClientAccountingPattern: [pattern]})

    suggestions = get_accounting_pattern_suggestions(
        db,
        organization_id=str(organization_id),
        client_id=str(client_id),
        matched_contact_id=str(contact_id),
        document_type_guess="bill",
        raw_supplier_text="Harbor Supply Co.",
    )

    assert suggestions["nominal_account"]["suggested_id"] == str(account.id)
    assert suggestions["nominal_account"]["suggested_code"] == "4000"
    assert suggestions["tax_code"]["suggested_value"] == "VAT20"
    assert suggestions["document_type"]["suggested_value"] == "bill"
    assert suggestions["nominal_account"]["confidence"] == "high"
    assert "prior accounting pattern found for matched contact" in suggestions["nominal_account"]["reasons"]


def test_build_suggestion_payload_combines_contact_and_pattern_suggestions():
    organization_id = uuid4()
    client_id = uuid4()
    contact = Contact(
        id=uuid4(),
        organization_id=organization_id,
        client_id=client_id,
        name="Harbor Supply Co.",
        contact_type="vendor",
        is_active=True,
    )
    alias = ClientSupplierAlias(
        id=uuid4(),
        organization_id=organization_id,
        client_id=client_id,
        profile_id=uuid4(),
        contact_id=contact.id,
        alias_text="Harbor Supply Co.",
        alias_normalized=normalize_match_text("Harbor Supply Co."),
        source_type="review",
        match_count=2,
        confidence_score=Decimal("0.90"),
        is_active=True,
    )
    alias.contact = contact
    pattern = ClientAccountingPattern(
        id=uuid4(),
        organization_id=organization_id,
        client_id=client_id,
        profile_id=uuid4(),
        pattern_type="contact_document_type",
        pattern_key=f"{contact.id}:bill",
        contact_id=contact.id,
        suggested_nominal_account_id=uuid4(),
        suggested_tax_code="VAT20",
        suggested_document_type="bill",
        usage_count=2,
        success_count=2,
        confidence_score=Decimal("0.88"),
        is_active=True,
    )
    db = _FakeSession({
        ClientSupplierAlias: [alias],
        ClientAccountingPattern: [pattern],
    })

    payload = build_suggestion_payload(
        db,
        organization_id=str(organization_id),
        client_id=str(client_id),
        counterparty_name="Harbor Supply Co.",
        document_type_guess="bill",
        raw_text="Bill text",
    )

    assert payload["contact"]["suggested_id"] == str(contact.id)
    assert payload["document_type"]["suggested_value"] == "bill"
    assert payload["tax_code"]["suggested_value"] == "VAT20"
