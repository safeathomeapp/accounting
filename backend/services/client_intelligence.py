"""Read-only client intelligence lookups for document interpretation."""

import re
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.models.account import Account
from backend.models.client_intelligence import (
    ClientAccountingPattern,
    ClientIntelligenceProfile,
    ClientSupplierAlias,
)
from backend.models.contact import Contact


def normalize_match_text(value: Optional[str]) -> str:
    if not value:
        return ""
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def get_client_intelligence_profile(
    db: Session,
    *,
    organization_id: str,
    client_id: str,
) -> Optional[ClientIntelligenceProfile]:
    return db.query(ClientIntelligenceProfile).filter(
        ClientIntelligenceProfile.organization_id == organization_id,
        ClientIntelligenceProfile.client_id == client_id,
    ).first()


def _score_to_confidence(score: Optional[Decimal], *, strong_match: bool = False) -> str:
    if strong_match:
        return "high"
    if score is None:
        return "medium"
    if score >= Decimal("0.85"):
        return "high"
    if score >= Decimal("0.60"):
        return "medium"
    return "low"


def match_contact_alias(
    db: Session,
    *,
    organization_id: str,
    client_id: str,
    raw_supplier_text: Optional[str],
) -> Dict[str, Any]:
    normalized = normalize_match_text(raw_supplier_text)
    base_result = {
        "suggested_id": None,
        "suggested_name": None,
        "confidence": "low",
        "reasons": [],
    }

    if not normalized:
        base_result["reasons"] = ["no counterparty text available from OCR"]
        return base_result

    alias_match = db.query(ClientSupplierAlias).filter(
        ClientSupplierAlias.organization_id == organization_id,
        ClientSupplierAlias.client_id == client_id,
        ClientSupplierAlias.alias_normalized == normalized,
        ClientSupplierAlias.is_active.is_(True),
    ).order_by(
        ClientSupplierAlias.confidence_score.desc(),
        ClientSupplierAlias.match_count.desc(),
        ClientSupplierAlias.created_at.asc(),
    ).first()

    if alias_match and alias_match.contact:
        return {
            "suggested_id": str(alias_match.contact.id),
            "suggested_name": alias_match.contact.name,
            "confidence": "high",
            "reasons": [
                "matched known supplier alias for this client",
                f"alias source: {alias_match.source_type}",
            ],
        }

    contacts = db.query(Contact).filter(
        Contact.organization_id == organization_id,
        Contact.client_id == client_id,
        Contact.is_active.is_(True),
    ).all()
    for contact in contacts:
        if normalize_match_text(contact.name) == normalized:
            return {
                "suggested_id": str(contact.id),
                "suggested_name": contact.name,
                "confidence": "medium",
                "reasons": [
                    "matched exact normalized contact name for this client",
                ],
            }

    profile = get_client_intelligence_profile(
        db,
        organization_id=organization_id,
        client_id=client_id,
    )
    if profile is None:
        base_result["reasons"] = ["no client intelligence profile found", "no exact contact match found"]
    else:
        base_result["reasons"] = ["no client-specific alias or exact contact match found"]
    return base_result


def _pattern_match_score(
    pattern: ClientAccountingPattern,
    *,
    matched_contact_id: Optional[str],
    document_type_guess: Optional[str],
    normalized_counterparty: str,
) -> tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []
    normalized_key = normalize_match_text(pattern.pattern_key)
    normalized_doc_type = normalize_match_text(document_type_guess)

    if matched_contact_id and pattern.contact_id and str(pattern.contact_id) == matched_contact_id:
        score += 4
        reasons.append("prior accounting pattern found for matched contact")

    if pattern.pattern_type == "document_type" and normalized_doc_type and normalized_key == normalized_doc_type:
        score += 3
        reasons.append("pattern matched current document type")

    if pattern.pattern_type in {"counterparty", "contact_name", "supplier_alias"} and normalized_counterparty:
        if normalized_key == normalized_counterparty:
            score += 2
            reasons.append("pattern matched normalized counterparty text")

    if pattern.pattern_type == "contact_document_type" and matched_contact_id and normalized_doc_type:
        expected_key = f"{matched_contact_id}:{normalized_doc_type}"
        if normalize_match_text(pattern.pattern_key) == expected_key:
            score += 5
            reasons.append("pattern matched contact and document type")

    return score, reasons


def get_accounting_pattern_suggestions(
    db: Session,
    *,
    organization_id: str,
    client_id: str,
    matched_contact_id: Optional[str],
    document_type_guess: Optional[str],
    raw_supplier_text: Optional[str],
) -> Dict[str, Any]:
    patterns = db.query(ClientAccountingPattern).filter(
        ClientAccountingPattern.organization_id == organization_id,
        ClientAccountingPattern.client_id == client_id,
        ClientAccountingPattern.is_active.is_(True),
    ).all()

    normalized_counterparty = normalize_match_text(raw_supplier_text)
    ranked_patterns = []
    for pattern in patterns:
        score, reasons = _pattern_match_score(
            pattern,
            matched_contact_id=matched_contact_id,
            document_type_guess=document_type_guess,
            normalized_counterparty=normalized_counterparty,
        )
        if score == 0:
            continue
        ranked_patterns.append((score, reasons, pattern))

    ranked_patterns.sort(
        key=lambda item: (
            item[0],
            item[2].confidence_score if item[2].confidence_score is not None else Decimal("0"),
            item[2].usage_count,
        ),
        reverse=True,
    )

    def _pick_pattern(field_name: str) -> tuple[Optional[ClientAccountingPattern], List[str], str]:
        for score, reasons, pattern in ranked_patterns:
            value = getattr(pattern, field_name)
            if value:
                confidence = _score_to_confidence(pattern.confidence_score, strong_match=score >= 5)
                return pattern, reasons, confidence
        return None, ["no client-specific accounting pattern found"], "low"

    account_pattern, account_reasons, account_confidence = _pick_pattern("suggested_nominal_account_id")
    document_type_pattern, doc_type_reasons, doc_type_confidence = _pick_pattern("suggested_document_type")
    tax_pattern, tax_reasons, tax_confidence = _pick_pattern("suggested_tax_code")

    account: Optional[Account] = None
    if account_pattern and account_pattern.suggested_nominal_account:
        account = account_pattern.suggested_nominal_account

    return {
        "nominal_account": {
            "suggested_id": str(account.id) if account else (
                str(account_pattern.suggested_nominal_account_id) if account_pattern and account_pattern.suggested_nominal_account_id else None
            ),
            "suggested_code": account.code if account else None,
            "suggested_name": account.name if account else None,
            "confidence": account_confidence,
            "reasons": account_reasons if account_pattern else ["no client-specific nominal account suggestion found"],
        },
        "document_type": {
            "suggested_value": document_type_pattern.suggested_document_type if document_type_pattern else None,
            "confidence": doc_type_confidence,
            "reasons": doc_type_reasons if document_type_pattern else ["no client-specific document type suggestion found"],
        },
        "tax_code": {
            "suggested_value": tax_pattern.suggested_tax_code if tax_pattern else None,
            "confidence": tax_confidence,
            "reasons": tax_reasons if tax_pattern else ["no client-specific tax code suggestion found"],
        },
    }


def build_suggestion_payload(
    db: Session,
    *,
    organization_id: str,
    client_id: str,
    counterparty_name: Optional[str],
    document_type_guess: Optional[str],
    raw_text: Optional[str] = None,
) -> Dict[str, Any]:
    _ = raw_text
    contact_suggestion = match_contact_alias(
        db,
        organization_id=organization_id,
        client_id=client_id,
        raw_supplier_text=counterparty_name,
    )
    pattern_suggestions = get_accounting_pattern_suggestions(
        db,
        organization_id=organization_id,
        client_id=client_id,
        matched_contact_id=contact_suggestion["suggested_id"],
        document_type_guess=document_type_guess,
        raw_supplier_text=counterparty_name,
    )
    return {
        "contact": contact_suggestion,
        "nominal_account": pattern_suggestions["nominal_account"],
        "document_type": pattern_suggestions["document_type"],
        "tax_code": pattern_suggestions["tax_code"],
    }
