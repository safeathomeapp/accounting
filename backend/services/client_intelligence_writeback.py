"""Conservative write-back from reviewed document outcomes into client intelligence."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.models.account import Account
from backend.models.client_intelligence import (
    ClientAccountingPattern,
    ClientIntelligenceEvent,
    ClientIntelligenceProfile,
    ClientSupplierAlias,
)
from backend.models.contact import Contact
from backend.models.document import DocumentDraft
from backend.services.client_intelligence import normalize_match_text


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _bump_confidence(
    current: Optional[Decimal],
    *,
    baseline: Decimal,
    increment: Decimal,
) -> Decimal:
    value = current if current is not None else baseline
    if value < baseline:
        value = baseline
    bumped = value + increment
    return min(bumped, Decimal("0.9900"))


def _get_or_create_profile(
    db: Session,
    *,
    organization_id: str,
    client_id: str,
) -> ClientIntelligenceProfile:
    profile = db.query(ClientIntelligenceProfile).filter(
        ClientIntelligenceProfile.organization_id == organization_id,
        ClientIntelligenceProfile.client_id == client_id,
    ).first()
    if profile is not None:
        return profile

    profile = ClientIntelligenceProfile(
        organization_id=organization_id,
        client_id=client_id,
        schema_version=1,
        status="active",
    )
    db.add(profile)
    db.flush()
    return profile


def _append_event(
    db: Session,
    *,
    profile: ClientIntelligenceProfile,
    event_type: str,
    draft: DocumentDraft,
    actor_user_id: Optional[str],
    payload_json: Optional[Dict[str, Any]] = None,
) -> ClientIntelligenceEvent:
    event = ClientIntelligenceEvent(
        organization_id=profile.organization_id,
        client_id=profile.client_id,
        profile_id=profile.id,
        event_type=event_type,
        source_inbox_item_id=draft.inbox_item_id,
        source_draft_id=draft.id,
        payload_json=payload_json,
        created_by_user_id=actor_user_id,
    )
    db.add(event)
    return event


def append_intelligence_event(
    db: Session,
    *,
    profile: ClientIntelligenceProfile,
    event_type: str,
    draft: DocumentDraft,
    actor_user_id: Optional[str],
    payload_json: Optional[Dict[str, Any]] = None,
) -> ClientIntelligenceEvent:
    return _append_event(
        db,
        profile=profile,
        event_type=event_type,
        draft=draft,
        actor_user_id=actor_user_id,
        payload_json=payload_json,
    )


def _load_confirmed_contact(
    db: Session,
    *,
    organization_id: str,
    client_id: str,
    confirmed_contact_id: Optional[str],
) -> Optional[Contact]:
    if not confirmed_contact_id:
        return None
    return db.query(Contact).filter(
        Contact.organization_id == organization_id,
        Contact.client_id == client_id,
        Contact.id == confirmed_contact_id,
        Contact.is_active.is_(True),
    ).first()


def _single_confirmed_line_value(lines: List[Any], attribute: str) -> Optional[str]:
    values = {
        str(getattr(line, attribute)).strip()
        for line in lines
        if getattr(line, attribute) is not None and str(getattr(line, attribute)).strip()
    }
    if len(values) != 1:
        return None
    return next(iter(values))


def _resolve_nominal_account(
    db: Session,
    *,
    organization_id: str,
    client_id: str,
    nominal_code: Optional[str],
) -> Optional[Account]:
    if not nominal_code:
        return None
    return db.query(Account).filter(
        Account.organization_id == organization_id,
        Account.client_id == client_id,
        Account.code == nominal_code,
        Account.is_active.is_(True),
    ).first()


def _draft_suggestions(draft: DocumentDraft) -> Dict[str, Any]:
    draft_json = draft.draft_json or {}
    suggestions = draft_json.get("suggestions")
    return suggestions if isinstance(suggestions, dict) else {}


def _observed_counterparty_text(draft: DocumentDraft) -> Optional[str]:
    draft_json = draft.draft_json or {}
    header = draft_json.get("header") if isinstance(draft_json.get("header"), dict) else {}
    candidate = header.get("counterparty_name") or draft.counterparty_guess
    if candidate is None:
        return None
    candidate = str(candidate).strip()
    return candidate or None


def upsert_supplier_alias_from_review(
    db: Session,
    *,
    profile: ClientIntelligenceProfile,
    draft: DocumentDraft,
    confirmed_contact: Optional[Contact],
    observed_counterparty_text: Optional[str],
    actor_user_id: Optional[str],
) -> Dict[str, Any]:
    if confirmed_contact is None:
        _append_event(
            db,
            profile=profile,
            event_type="alias_learning_skipped",
            draft=draft,
            actor_user_id=actor_user_id,
            payload_json={"reason": "missing_confirmed_contact"},
        )
        return {"updated": False, "reason": "missing_confirmed_contact"}

    normalized = normalize_match_text(observed_counterparty_text)
    if not normalized:
        _append_event(
            db,
            profile=profile,
            event_type="alias_learning_skipped",
            draft=draft,
            actor_user_id=actor_user_id,
            payload_json={"reason": "missing_observed_counterparty_text"},
        )
        return {"updated": False, "reason": "missing_observed_counterparty_text"}

    alias = db.query(ClientSupplierAlias).filter(
        ClientSupplierAlias.organization_id == profile.organization_id,
        ClientSupplierAlias.client_id == profile.client_id,
        ClientSupplierAlias.profile_id == profile.id,
        ClientSupplierAlias.contact_id == confirmed_contact.id,
        ClientSupplierAlias.alias_normalized == normalized,
        ClientSupplierAlias.source_type == "review",
    ).first()

    if alias is None:
        alias = ClientSupplierAlias(
            organization_id=profile.organization_id,
            client_id=profile.client_id,
            profile_id=profile.id,
            contact_id=confirmed_contact.id,
            alias_text=observed_counterparty_text.strip(),
            alias_normalized=normalized,
            source_type="review",
            match_count=1,
            confidence_score=Decimal("0.9500"),
            is_active=True,
        )
        db.add(alias)
        action = "created"
    else:
        alias.alias_text = observed_counterparty_text.strip()
        alias.match_count += 1
        alias.is_active = True
        alias.confidence_score = _bump_confidence(
            alias.confidence_score,
            baseline=Decimal("0.9000"),
            increment=Decimal("0.0200"),
        )
        action = "updated"

    _append_event(
        db,
        profile=profile,
        event_type="alias_confirmed",
        draft=draft,
        actor_user_id=actor_user_id,
        payload_json={
            "action": action,
            "contact_id": str(confirmed_contact.id),
            "alias_text": observed_counterparty_text.strip(),
            "alias_normalized": normalized,
        },
    )
    return {"updated": True, "action": action, "alias": alias}


def upsert_accounting_pattern_from_review(
    db: Session,
    *,
    profile: ClientIntelligenceProfile,
    draft: DocumentDraft,
    confirmed_contact: Optional[Contact],
    confirmed_document_type: Optional[str],
    confirmed_nominal_account: Optional[Account],
    confirmed_tax_code: Optional[str],
    actor_user_id: Optional[str],
) -> Dict[str, Any]:
    document_type = str(confirmed_document_type).strip().lower() if confirmed_document_type else None
    if not document_type:
        _append_event(
            db,
            profile=profile,
            event_type="accounting_pattern_skipped",
            draft=draft,
            actor_user_id=actor_user_id,
            payload_json={"reason": "missing_confirmed_document_type"},
        )
        return {"updated": False, "reason": "missing_confirmed_document_type"}

    if confirmed_nominal_account is None and not confirmed_tax_code:
        _append_event(
            db,
            profile=profile,
            event_type="accounting_pattern_skipped",
            draft=draft,
            actor_user_id=actor_user_id,
            payload_json={"reason": "missing_confirmed_account_and_tax"},
        )
        return {"updated": False, "reason": "missing_confirmed_account_and_tax"}

    if confirmed_contact is not None:
        pattern_type = "contact_document_type"
        pattern_key = f"{confirmed_contact.id}:{document_type}"
    else:
        pattern_type = "document_type"
        pattern_key = document_type

    pattern = db.query(ClientAccountingPattern).filter(
        ClientAccountingPattern.organization_id == profile.organization_id,
        ClientAccountingPattern.client_id == profile.client_id,
        ClientAccountingPattern.profile_id == profile.id,
        ClientAccountingPattern.pattern_type == pattern_type,
        ClientAccountingPattern.pattern_key == pattern_key,
    ).first()

    if pattern is None:
        pattern = ClientAccountingPattern(
            organization_id=profile.organization_id,
            client_id=profile.client_id,
            profile_id=profile.id,
            pattern_type=pattern_type,
            pattern_key=pattern_key,
            contact_id=confirmed_contact.id if confirmed_contact is not None else None,
            suggested_nominal_account_id=confirmed_nominal_account.id if confirmed_nominal_account is not None else None,
            suggested_tax_code=confirmed_tax_code,
            suggested_document_type=document_type,
            usage_count=1,
            success_count=1,
            confidence_score=Decimal("0.9000"),
            is_active=True,
        )
        db.add(pattern)
        action = "created"
    else:
        pattern.contact_id = confirmed_contact.id if confirmed_contact is not None else pattern.contact_id
        pattern.suggested_nominal_account_id = (
            confirmed_nominal_account.id if confirmed_nominal_account is not None else pattern.suggested_nominal_account_id
        )
        pattern.suggested_tax_code = confirmed_tax_code or pattern.suggested_tax_code
        pattern.suggested_document_type = document_type
        pattern.usage_count += 1
        pattern.success_count += 1
        pattern.is_active = True
        pattern.confidence_score = _bump_confidence(
            pattern.confidence_score,
            baseline=Decimal("0.8500"),
            increment=Decimal("0.0200"),
        )
        action = "updated"

    _append_event(
        db,
        profile=profile,
        event_type="accounting_pattern_strengthened",
        draft=draft,
        actor_user_id=actor_user_id,
        payload_json={
            "action": action,
            "pattern_type": pattern_type,
            "pattern_key": pattern_key,
            "contact_id": str(confirmed_contact.id) if confirmed_contact is not None else None,
            "suggested_nominal_account_id": (
                str(confirmed_nominal_account.id) if confirmed_nominal_account is not None else None
            ),
            "suggested_tax_code": confirmed_tax_code,
            "suggested_document_type": document_type,
        },
    )
    return {"updated": True, "action": action, "pattern": pattern}


def _append_correction_events(
    db: Session,
    *,
    profile: ClientIntelligenceProfile,
    draft: DocumentDraft,
    actor_user_id: Optional[str],
    suggestions: Dict[str, Any],
    confirmed_contact: Optional[Contact],
    confirmed_document_type: Optional[str],
    confirmed_nominal_account: Optional[Account],
    confirmed_tax_code: Optional[str],
) -> None:
    comparisons = [
        (
            "contact",
            (suggestions.get("contact") or {}).get("suggested_id"),
            str(confirmed_contact.id) if confirmed_contact is not None else None,
        ),
        (
            "document_type",
            (suggestions.get("document_type") or {}).get("suggested_value"),
            confirmed_document_type.lower() if confirmed_document_type else None,
        ),
        (
            "nominal_account",
            (suggestions.get("nominal_account") or {}).get("suggested_id"),
            str(confirmed_nominal_account.id) if confirmed_nominal_account is not None else None,
        ),
        (
            "tax_code",
            (suggestions.get("tax_code") or {}).get("suggested_value"),
            confirmed_tax_code,
        ),
    ]
    for field_name, suggested_value, confirmed_value in comparisons:
        if not suggested_value or not confirmed_value:
            continue
        if str(suggested_value) == str(confirmed_value):
            continue
        _append_event(
            db,
            profile=profile,
            event_type="correction_observed",
            draft=draft,
            actor_user_id=actor_user_id,
            payload_json={
                "field": field_name,
                "suggested_value": str(suggested_value),
                "confirmed_value": str(confirmed_value),
            },
        )


def record_reviewed_outcome(
    db: Session,
    *,
    draft: DocumentDraft,
    actor_user_id: Optional[str],
) -> Dict[str, Any]:
    if not draft.client_id:
        return {"updated": False, "reason": "missing_client_id"}

    profile = _get_or_create_profile(
        db,
        organization_id=str(draft.org_id),
        client_id=str(draft.client_id),
    )
    profile.last_reviewed_document_at = _utcnow()

    observed_counterparty_text = _observed_counterparty_text(draft)
    confirmed_contact = _load_confirmed_contact(
        db,
        organization_id=str(draft.org_id),
        client_id=str(draft.client_id),
        confirmed_contact_id=str(draft.confirmed_contact_id) if draft.confirmed_contact_id else None,
    )
    confirmed_document_type = draft.doc_type_confirmed or draft.doc_type_guess
    confirmed_nominal_code = _single_confirmed_line_value(draft.lines, "nominal_code_confirmed")
    confirmed_tax_code = _single_confirmed_line_value(draft.lines, "vat_code_confirmed")
    confirmed_nominal_account = _resolve_nominal_account(
        db,
        organization_id=str(draft.org_id),
        client_id=str(draft.client_id),
        nominal_code=confirmed_nominal_code,
    )

    alias_result = upsert_supplier_alias_from_review(
        db,
        profile=profile,
        draft=draft,
        confirmed_contact=confirmed_contact,
        observed_counterparty_text=observed_counterparty_text,
        actor_user_id=actor_user_id,
    )
    pattern_result = upsert_accounting_pattern_from_review(
        db,
        profile=profile,
        draft=draft,
        confirmed_contact=confirmed_contact,
        confirmed_document_type=confirmed_document_type,
        confirmed_nominal_account=confirmed_nominal_account,
        confirmed_tax_code=confirmed_tax_code,
        actor_user_id=actor_user_id,
    )
    _append_correction_events(
        db,
        profile=profile,
        draft=draft,
        actor_user_id=actor_user_id,
        suggestions=_draft_suggestions(draft),
        confirmed_contact=confirmed_contact,
        confirmed_document_type=confirmed_document_type,
        confirmed_nominal_account=confirmed_nominal_account,
        confirmed_tax_code=confirmed_tax_code,
    )
    db.flush()
    return {
        "updated": alias_result.get("updated") or pattern_result.get("updated"),
        "profile_id": str(profile.id),
        "alias": alias_result,
        "accounting_pattern": pattern_result,
    }
