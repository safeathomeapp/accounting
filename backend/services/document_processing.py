"""Shared document-processing orchestration for inbox-item extraction."""

import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.document import (
    DocumentDraft,
    DocumentDraftLine,
    DocumentInboxItem,
    DocumentOCRResult,
)
from backend.services.claude_ocr import ClaudeOCRService, get_claude_ocr_service
from backend.services.client_intelligence import build_suggestion_payload

logger = logging.getLogger(__name__)


@dataclass
class DocumentProcessingResult:
    success: bool
    inbox_item: Optional[DocumentInboxItem]
    draft: Optional[DocumentDraft]
    ocr_result: Optional[DocumentOCRResult]
    processing_mode: str
    final_inbox_status: Optional[str]
    ocr_engine: Optional[str] = None
    extraction_error: Optional[str] = None
    used_mock_fallback: bool = False
    http_status: int = 200
    error_code: Optional[str] = None
    error_message: Optional[str] = None


def _totals_to_str(totals: Dict[str, Decimal]) -> Dict[str, str]:
    return {
        "net": str(totals["net"]),
        "vat": str(totals["vat"]),
        "gross": str(totals["gross"]),
    }


def _build_validation(draft_data: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    totals = draft_data["totals"]
    line_net = sum((line["net"] for line in draft_data["lines"]), Decimal("0.00"))
    line_vat = sum((line["vat"] for line in draft_data["lines"]), Decimal("0.00"))
    line_gross = sum((line["gross"] for line in draft_data["lines"]), Decimal("0.00"))
    expected_gross = totals["net"] + totals["vat"]

    if (expected_gross - totals["gross"]).copy_abs() > Decimal("0.01"):
        issues.append({
            "code": "header_total_mismatch",
            "message": "Header totals do not add up to gross.",
            "details": _totals_to_str(totals),
        })

    if (line_net - totals["net"]).copy_abs() > Decimal("0.01"):
        issues.append({
            "code": "line_net_mismatch",
            "message": "Sum of line net does not match header net.",
            "details": {"lines_net": str(line_net), "header_net": str(totals["net"])},
        })

    if (line_vat - totals["vat"]).copy_abs() > Decimal("0.01"):
        issues.append({
            "code": "line_vat_mismatch",
            "message": "Sum of line VAT does not match header VAT.",
            "details": {"lines_vat": str(line_vat), "header_vat": str(totals["vat"])},
        })

    if (line_gross - totals["gross"]).copy_abs() > Decimal("0.01"):
        issues.append({
            "code": "line_gross_mismatch",
            "message": "Sum of line gross does not match header gross.",
            "details": {"lines_gross": str(line_gross), "header_gross": str(totals["gross"])},
        })

    return {
        "status": "ok" if not issues else "warning",
        "issues": issues,
        "computed": {
            "lines_net": str(line_net),
            "lines_vat": str(line_vat),
            "lines_gross": str(line_gross),
        },
        "header": _totals_to_str(totals),
    }


def _build_draft_json(
    draft_data: Dict[str, Any],
    *,
    suggestion_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
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
                "confidence": str(line.get("confidence")) if line.get("confidence") is not None else None,
            }
            for line in draft_data["lines"]
        ],
        "raw_text": draft_data.get("raw_text"),
        "confidence": str(draft_data.get("confidence")) if draft_data.get("confidence") else None,
        "suggestions": suggestion_payload or {},
    }


def _generate_mock_draft(seed_text: str) -> Dict[str, Any]:
    seed = int(hashlib.sha256(seed_text.encode()).hexdigest()[:8], 16)
    doc_types = ["invoice", "bill", "receipt"]
    counterparties = [
        "Harbor Supply Co.",
        "Summit Office Ltd",
        "Evergreen Logistics",
        "Northwind Industrial",
        "Brightline Services",
    ]
    descriptions = [
        "Consulting services",
        "Monthly hosting",
        "Equipment rental",
        "Office supplies",
        "Implementation support",
    ]

    doc_type = doc_types[seed % len(doc_types)]
    counterparty = counterparties[seed % len(counterparties)]
    doc_number = f"INV-{1000 + (seed % 9000)}"
    doc_date = date.today()
    due_date = doc_date

    line_count = 2 + (seed % 3)
    lines = []
    totals = {"net": Decimal("0.00"), "vat": Decimal("0.00"), "gross": Decimal("0.00")}
    for i in range(line_count):
        qty = Decimal(str(1 + ((seed >> i) % 3)))
        unit_price = Decimal(str(50 + ((seed >> (i + 3)) % 200)))
        net = (qty * unit_price).quantize(Decimal("0.01"))
        vat = (net * Decimal("0.20")).quantize(Decimal("0.01"))
        gross = (net + vat).quantize(Decimal("0.01"))
        totals["net"] += net
        totals["vat"] += vat
        totals["gross"] += gross
        lines.append(
            {
                "line_no": i + 1,
                "description": descriptions[(seed + i) % len(descriptions)],
                "qty": qty,
                "unit_price": unit_price,
                "net": net,
                "vat": vat,
                "gross": gross,
                "vat_code": "VAT20",
                "nominal_code": "4000",
                "confidence": Decimal("0.85"),
            }
        )

    return {
        "doc_type": doc_type,
        "counterparty_name": counterparty,
        "doc_date": doc_date,
        "due_date": due_date,
        "currency": "GBP",
        "invoice_no": doc_number,
        "totals": {key: value.quantize(Decimal("0.01")) for key, value in totals.items()},
        "lines": lines,
        "ocr_engine": "stub-v1",
        "raw_text": f"Mock extraction for testing (seed: {seed_text})",
    }


def _should_preserve_existing_draft(draft: Optional[DocumentDraft]) -> bool:
    if not draft:
        return False
    source = (draft.draft_json or {}).get("source")
    return source in {"user-edit", "submitted"} or draft.status == "submitted"


def _load_inbox_item(
    db: Session,
    inbox_item_id: str,
    organization_id: Optional[str] = None,
) -> Optional[DocumentInboxItem]:
    query = db.query(DocumentInboxItem).filter(DocumentInboxItem.id == inbox_item_id)
    if organization_id is not None:
        query = query.filter(DocumentInboxItem.org_id == organization_id)
    return query.first()


def _ensure_error_status(db: Session, inbox_item: DocumentInboxItem) -> None:
    inbox_item.status = "error"
    db.commit()


def _extract_draft_data(
    inbox_item: DocumentInboxItem,
    allow_mock_fallback: bool,
    ocr_service: Optional[ClaudeOCRService],
) -> tuple[Optional[Dict[str, Any]], Optional[str], Optional[str], bool]:
    extraction_error = None
    used_mock_fallback = False

    try:
        service = ocr_service or get_claude_ocr_service()
        draft_data = service.extract_document(inbox_item.file_path, inbox_item.mime_type)
        return draft_data, f"claude-{settings.claude_model}", None, False
    except Exception as exc:
        extraction_error = str(exc)
        if not allow_mock_fallback:
            return None, f"claude-{settings.claude_model}", extraction_error, False
        logger.warning("Claude OCR failed for inbox item %s, using mock fallback: %s", inbox_item.id, exc)
        used_mock_fallback = True
        draft_data = _generate_mock_draft(str(inbox_item.id))
        return draft_data, draft_data.get("ocr_engine", "stub-v1"), extraction_error, used_mock_fallback


def _upsert_ocr_result(
    db: Session,
    inbox_item: DocumentInboxItem,
    ocr_engine: str,
    raw_text: str,
    extraction_error: Optional[str],
) -> DocumentOCRResult:
    ocr_result = inbox_item.ocr_result
    if ocr_result is None:
        ocr_result = DocumentOCRResult(
            inbox_item_id=inbox_item.id,
            org_id=inbox_item.org_id,
        )
        inbox_item.ocr_result = ocr_result
        db.add(ocr_result)

    ocr_result.ocr_engine = ocr_engine
    ocr_result.raw_text = raw_text
    ocr_result.layout_json = {
        "pages": 1,
        "extraction_source": ocr_engine,
        "extraction_error": extraction_error,
    }
    ocr_result.pages = 1
    return ocr_result


def _apply_draft_data(
    db: Session,
    inbox_item: DocumentInboxItem,
    draft_data: Dict[str, Any],
    actor_user_id: Optional[str],
) -> DocumentDraft:
    suggestion_payload = build_suggestion_payload(
        db,
        organization_id=str(inbox_item.org_id),
        client_id=str(inbox_item.client_id),
        counterparty_name=draft_data.get("counterparty_name"),
        document_type_guess=draft_data.get("doc_type"),
        raw_text=draft_data.get("raw_text"),
    )

    draft = inbox_item.draft
    if draft is None:
        draft = DocumentDraft(
            inbox_item_id=inbox_item.id,
            org_id=inbox_item.org_id,
            client_id=inbox_item.client_id,
        )
        inbox_item.draft = draft
        db.add(draft)

    draft.status = "draft"
    draft.client_id = inbox_item.client_id
    draft.doc_type_guess = draft_data["doc_type"]
    draft.counterparty_guess = draft_data["counterparty_name"]
    draft.doc_date_guess = draft_data["doc_date"]
    draft.currency_guess = draft_data["currency"]
    draft.invoice_no_guess = draft_data["invoice_no"]
    draft.totals_guess = _totals_to_str(draft_data["totals"])
    draft.totals_confirmed = draft.totals_guess
    draft.draft_json = _build_draft_json(draft_data, suggestion_payload=suggestion_payload)
    draft.validation_json = _build_validation(draft_data)
    draft.last_edited_by = actor_user_id
    draft.lines = [
        DocumentDraftLine(
            org_id=inbox_item.org_id,
            line_no=line["line_no"],
            description_guess=line["description"],
            description_confirmed=line["description"],
            qty=line["qty"],
            unit_price=line["unit_price"],
            net=line["net"],
            vat=line["vat"],
            gross=line["gross"],
            vat_code_guess=line.get("vat_code"),
            vat_code_confirmed=line.get("vat_code"),
            nominal_code_guess=line.get("nominal_code"),
            nominal_code_confirmed=line.get("nominal_code"),
            confidence=line.get("confidence"),
        )
        for line in draft_data["lines"]
    ]
    db.flush()
    return draft


def process_inbox_item(
    db: Session,
    inbox_item_id: str,
    *,
    organization_id: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    allow_mock_fallback: bool = False,
    ocr_service: Optional[ClaudeOCRService] = None,
) -> DocumentProcessingResult:
    inbox_item = _load_inbox_item(db, inbox_item_id, organization_id=organization_id)
    if inbox_item is None:
        return DocumentProcessingResult(
            success=False,
            inbox_item=None,
            draft=None,
            ocr_result=None,
            processing_mode="not_found",
            final_inbox_status=None,
            http_status=404,
            error_code="inbox_item_not_found",
            error_message="Inbox item not found",
        )

    if not inbox_item.client_id:
        _ensure_error_status(db, inbox_item)
        return DocumentProcessingResult(
            success=False,
            inbox_item=inbox_item,
            draft=inbox_item.draft,
            ocr_result=inbox_item.ocr_result,
            processing_mode="missing_client",
            final_inbox_status=inbox_item.status,
            http_status=409,
            error_code="missing_client_id",
            error_message="Document extraction requires a client-scoped inbox item",
        )

    if not os.path.exists(inbox_item.file_path):
        _ensure_error_status(db, inbox_item)
        return DocumentProcessingResult(
            success=False,
            inbox_item=inbox_item,
            draft=inbox_item.draft,
            ocr_result=inbox_item.ocr_result,
            processing_mode="missing_file",
            final_inbox_status=inbox_item.status,
            http_status=404,
            error_code="file_not_found",
            error_message="File not found on disk",
        )

    if _should_preserve_existing_draft(inbox_item.draft):
        inbox_item.status = "submitted" if inbox_item.draft and inbox_item.draft.status == "submitted" else "drafted"
        db.commit()
        return DocumentProcessingResult(
            success=True,
            inbox_item=inbox_item,
            draft=inbox_item.draft,
            ocr_result=inbox_item.ocr_result,
            processing_mode="preserved_existing_draft",
            final_inbox_status=inbox_item.status,
        )

    inbox_item.status = "processing"
    db.flush()

    draft_data, ocr_engine, extraction_error, used_mock_fallback = _extract_draft_data(
        inbox_item,
        allow_mock_fallback=allow_mock_fallback,
        ocr_service=ocr_service,
    )

    if draft_data is None or ocr_engine is None:
        ocr_result = _upsert_ocr_result(
            db,
            inbox_item,
            ocr_engine or f"claude-{settings.claude_model}",
            "",
            extraction_error,
        )
        inbox_item.status = "error"
        db.commit()
        return DocumentProcessingResult(
            success=False,
            inbox_item=inbox_item,
            draft=inbox_item.draft,
            ocr_result=ocr_result,
            processing_mode="ocr_failed",
            final_inbox_status=inbox_item.status,
            ocr_engine=ocr_engine,
            extraction_error=extraction_error,
            http_status=422,
            error_code="ocr_failed",
            error_message=extraction_error or "OCR extraction failed",
        )

    ocr_result = _upsert_ocr_result(
        db,
        inbox_item,
        ocr_engine,
        draft_data.get("raw_text", ""),
        extraction_error,
    )
    draft = _apply_draft_data(
        db,
        inbox_item,
        draft_data,
        actor_user_id=actor_user_id,
    )
    inbox_item.status = "drafted"
    db.commit()

    return DocumentProcessingResult(
        success=True,
        inbox_item=inbox_item,
        draft=draft,
        ocr_result=ocr_result,
        processing_mode="processed",
        final_inbox_status=inbox_item.status,
        ocr_engine=ocr_engine,
        extraction_error=extraction_error,
        used_mock_fallback=used_mock_fallback,
    )
