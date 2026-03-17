from backend.models import (
    Account,
    Client,
    ClientAccountingPattern,
    ClientIntelligenceEvent,
    ClientIntelligenceProfile,
    ClientSupplierAlias,
    Contact,
)


def test_client_intelligence_models_are_importable():
    assert ClientIntelligenceProfile.__tablename__ == "client_intelligence_profile"
    assert ClientSupplierAlias.__tablename__ == "client_supplier_alias"
    assert ClientAccountingPattern.__tablename__ == "client_accounting_pattern"
    assert ClientIntelligenceEvent.__tablename__ == "client_intelligence_event"


def test_client_relationship_wiring_exists():
    assert "intelligence_profile" in Client.__mapper__.relationships
    assert "supplier_aliases" in Client.__mapper__.relationships
    assert "accounting_patterns" in Client.__mapper__.relationships
    assert "intelligence_events" in Client.__mapper__.relationships


def test_contact_and_account_relationship_wiring_exists():
    assert "supplier_aliases" in Contact.__mapper__.relationships
    assert "accounting_patterns" in Contact.__mapper__.relationships
    assert "client_accounting_patterns" in Account.__mapper__.relationships
