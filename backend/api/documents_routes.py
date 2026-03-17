"""API routes for document intake, OCR, and draft review."""

import hashlib
import os
import shutil
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.api.auth_routes import get_current_user
from backend.models.document import (
    DocumentInboxItem,
    DocumentDraft,
    DocumentDraftLine,
)
from backend.models.contact import Contact
from backend.models.transaction import Transaction
from backend.services.client_intelligence_writeback import record_reviewed_outcome
from backend.services.document_processing import process_inbox_item


router = APIRouter(prefix="/api", tags=["documents"])

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))


class TotalsPayload(BaseModel):
    net: Decimal = Field(..., ge=Decimal("0"))
    vat: Decimal = Field(..., ge=Decimal("0"))
    gross: Decimal = Field(..., ge=Decimal("0"))


class DraftLinePayload(BaseModel):
    line_no: int = Field(..., ge=1)
    description: Optional[str] = None
    qty: Decimal = Field(..., ge=Decimal("0"))
    unit_price: Decimal = Field(..., ge=Decimal("0"))
    net: Decimal = Field(..., ge=Decimal("0"))
    vat: Decimal = Field(..., ge=Decimal("0"))
    gross: Decimal = Field(..., ge=Decimal("0"))
    vat_code: Optional[str] = None
    nominal_code: Optional[str] = None
    confidence: Optional[Decimal] = None


class DraftUpdatePayload(BaseModel):
    doc_type: Optional[str] = None
    counterparty_name: Optional[str] = None
    confirmed_contact_id: Optional[str] = None
    doc_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = None
    invoice_no: Optional[str] = None
    totals: TotalsPayload
    lines: List[DraftLinePayload]


def _safe_upload_path(org_id: str, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    base_name = f"{org_id}_{hashlib.sha256(filename.encode()).hexdigest()[:10]}"
    stored_name = f"{base_name}_{hashlib.sha256(os.urandom(16)).hexdigest()[:10]}{ext}"
    org_dir = os.path.join(UPLOAD_DIR, org_id)
    os.makedirs(org_dir, exist_ok=True)
    return os.path.join(org_dir, stored_name)


def _checksum_for_path(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _draft_to_dict(draft: DocumentDraft, inbox_item: Optional[DocumentInboxItem] = None) -> Dict[str, Any]:
    confirmed_contact = draft.confirmed_contact
    return {
        "id": str(draft.id),
        "inbox_item_id": str(draft.inbox_item_id),
        "client_id": str(draft.client_id) if draft.client_id else None,
        "status": draft.status,
        "doc_type_guess": draft.doc_type_guess,
        "doc_type_confirmed": draft.doc_type_confirmed,
        "counterparty_guess": draft.counterparty_guess,
        "confirmed_counterparty_name": ((draft.draft_json or {}).get("review") or {}).get("confirmed_counterparty_name"),
        "confirmed_contact_id": str(draft.confirmed_contact_id) if draft.confirmed_contact_id else None,
        "confirmed_contact": (
            {
                "id": str(confirmed_contact.id),
                "name": confirmed_contact.name,
                "contact_type": confirmed_contact.contact_type,
            }
            if confirmed_contact
            else None
        ),
        "doc_date_guess": draft.doc_date_guess.isoformat() if draft.doc_date_guess else None,
        "doc_date_confirmed": draft.doc_date_confirmed.isoformat() if draft.doc_date_confirmed else None,
        "currency_guess": draft.currency_guess,
        "currency_confirmed": draft.currency_confirmed,
        "invoice_no_guess": draft.invoice_no_guess,
        "invoice_no_confirmed": draft.invoice_no_confirmed,
        "totals_guess": draft.totals_guess,
        "totals_confirmed": draft.totals_confirmed,
        "draft_json": draft.draft_json,
        "validation_json": draft.validation_json,
        "lines": [
            {
                "id": str(line.id),
                "line_no": line.line_no,
                "description_guess": line.description_guess,
                "description_confirmed": line.description_confirmed,
                "qty": str(line.qty),
                "unit_price": str(line.unit_price),
                "net": str(line.net),
                "vat": str(line.vat),
                "gross": str(line.gross),
                "vat_code_guess": line.vat_code_guess,
                "vat_code_confirmed": line.vat_code_confirmed,
                "nominal_code_guess": line.nominal_code_guess,
                "nominal_code_confirmed": line.nominal_code_confirmed,
                "confidence": str(line.confidence) if line.confidence is not None else None,
            }
            for line in draft.lines
        ],
        "inbox_item": (
            {
                "id": str(inbox_item.id),
                "file_name": inbox_item.file_name,
                "mime_type": inbox_item.mime_type,
                "status": inbox_item.status,
                "file_url": f"/api/inbox/{inbox_item.id}/file",
                "client_id": str(inbox_item.client_id) if inbox_item.client_id else None,
            }
            if inbox_item
            else None
        ),
    }


def _existing_suggestions(draft: DocumentDraft) -> Dict[str, Any]:
    draft_json = draft.draft_json or {}
    suggestions = draft_json.get("suggestions")
    return suggestions if isinstance(suggestions, dict) else {}


def _observed_counterparty_name(draft: DocumentDraft) -> Optional[str]:
    draft_json = draft.draft_json or {}
    header = draft_json.get("header")
    if isinstance(header, dict):
        counterparty_name = header.get("counterparty_name")
        if counterparty_name:
            return counterparty_name
    return draft.counterparty_guess


def _resolve_confirmed_contact(
    db: Session,
    *,
    draft: DocumentDraft,
    organization_id: str,
    requested_contact_id: Optional[str],
) -> Optional[Contact]:
    if not draft.client_id:
        raise HTTPException(status_code=409, detail="Draft is missing client scope")
    if not requested_contact_id:
        return None

    contact = db.query(Contact).filter(
        Contact.id == requested_contact_id,
        Contact.organization_id == organization_id,
        Contact.client_id == draft.client_id,
        Contact.is_active.is_(True),
    ).first()
    if contact is None:
        raise HTTPException(status_code=400, detail="Confirmed contact must belong to the current client")
    return contact


def _validate_totals(lines: List[DraftLinePayload], totals: TotalsPayload) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    line_net = sum((line.net for line in lines), Decimal("0.00"))
    line_vat = sum((line.vat for line in lines), Decimal("0.00"))
    line_gross = sum((line.gross for line in lines), Decimal("0.00"))
    expected_gross = totals.net + totals.vat

    if (expected_gross - totals.gross).copy_abs() > Decimal("0.01"):
        issues.append({
            "code": "header_total_mismatch",
            "message": "Header totals do not add up to gross.",
            "details": {
                "net": str(totals.net),
                "vat": str(totals.vat),
                "gross": str(totals.gross),
            },
        })

    if (line_net - totals.net).copy_abs() > Decimal("0.01"):
        issues.append({
            "code": "line_net_mismatch",
            "message": "Sum of line net does not match header net.",
            "details": {"lines_net": str(line_net), "header_net": str(totals.net)},
        })

    if (line_vat - totals.vat).copy_abs() > Decimal("0.01"):
        issues.append({
            "code": "line_vat_mismatch",
            "message": "Sum of line VAT does not match header VAT.",
            "details": {"lines_vat": str(line_vat), "header_vat": str(totals.vat)},
        })

    if (line_gross - totals.gross).copy_abs() > Decimal("0.01"):
        issues.append({
            "code": "line_gross_mismatch",
            "message": "Sum of line gross does not match header gross.",
            "details": {"lines_gross": str(line_gross), "header_gross": str(totals.gross)},
        })

    return {
        "status": "ok" if not issues else "warning",
        "issues": issues,
        "computed": {
            "lines_net": str(line_net),
            "lines_vat": str(line_vat),
            "lines_gross": str(line_gross),
        },
        "header": {
            "net": str(totals.net),
            "vat": str(totals.vat),
            "gross": str(totals.gross),
        },
    }


@router.post("/inbox/upload")
def upload_document(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    stored_path = _safe_upload_path(str(current_user.organization_id), file.filename)
    with open(stored_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    checksum_hash = _checksum_for_path(stored_path)

    inbox_item = DocumentInboxItem(
        org_id=current_user.organization_id,
        uploaded_by_user_id=current_user.id,
        client_id=client_id,
        source_type="upload",
        file_name=file.filename,
        mime_type=file.content_type,
        file_path=stored_path,
        checksum_hash=checksum_hash,
        status="uploaded",
    )
    db.add(inbox_item)
    db.commit()
    db.refresh(inbox_item)

    return {
        "inbox_item_id": str(inbox_item.id),
        "file_name": inbox_item.file_name,
        "mime_type": inbox_item.mime_type,
        "file_url": f"/api/inbox/{inbox_item.id}/file",
        "client_id": client_id,
    }


@router.get("/inbox/{inbox_item_id}/file")
def get_inbox_file(
    inbox_item_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    inbox_item = db.query(DocumentInboxItem).filter(
        DocumentInboxItem.id == inbox_item_id,
        DocumentInboxItem.org_id == current_user.organization_id,
    ).first()
    if not inbox_item:
        raise HTTPException(status_code=404, detail="Inbox item not found")

    abs_path = os.path.abspath(inbox_item.file_path)
    if not abs_path.startswith(UPLOAD_DIR):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(abs_path, media_type=inbox_item.mime_type, filename=inbox_item.file_name)


@router.post("/inbox/{inbox_item_id}/extract")
def extract_document_endpoint(
    inbox_item_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    result = process_inbox_item(
        db,
        inbox_item_id,
        organization_id=current_user.organization_id,
        actor_user_id=current_user.id,
        allow_mock_fallback=True,
    )
    if not result.success or result.draft is None or result.inbox_item is None:
        raise HTTPException(status_code=result.http_status, detail=result.error_message)

    return {"draft": _draft_to_dict(result.draft, result.inbox_item)}


@router.get("/drafts/{draft_id}")
def get_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    draft = db.query(DocumentDraft).join(DocumentInboxItem).filter(
        DocumentDraft.id == draft_id,
        DocumentDraft.org_id == current_user.organization_id,
        DocumentInboxItem.org_id == current_user.organization_id,
    ).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    return {"draft": _draft_to_dict(draft, draft.inbox_item)}


@router.patch("/drafts/{draft_id}")
def update_draft(
    draft_id: str,
    payload: DraftUpdatePayload,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    draft = db.query(DocumentDraft).join(DocumentInboxItem).filter(
        DocumentDraft.id == draft_id,
        DocumentDraft.org_id == current_user.organization_id,
        DocumentInboxItem.org_id == current_user.organization_id,
    ).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft.status == "submitted":
        raise HTTPException(status_code=400, detail="Draft is already submitted")

    confirmed_contact = _resolve_confirmed_contact(
        db,
        draft=draft,
        organization_id=current_user.organization_id,
        requested_contact_id=payload.confirmed_contact_id,
    )
    validation = _validate_totals(payload.lines, payload.totals)

    draft.doc_type_confirmed = payload.doc_type or draft.doc_type_confirmed
    draft.confirmed_contact_id = confirmed_contact.id if confirmed_contact else None
    draft.confirmed_contact = confirmed_contact
    draft.doc_date_confirmed = payload.doc_date or draft.doc_date_confirmed
    draft.currency_confirmed = payload.currency or draft.currency_confirmed or draft.currency_guess
    draft.invoice_no_confirmed = payload.invoice_no or draft.invoice_no_confirmed
    draft.totals_confirmed = {
        "net": str(payload.totals.net),
        "vat": str(payload.totals.vat),
        "gross": str(payload.totals.gross),
    }
    draft.validation_json = validation
    draft.last_edited_by = current_user.id
    draft.status = "draft"

    draft.draft_json = {
        "source": "user-edit",
        "header": {
            "doc_type": payload.doc_type,
            "counterparty_name": _observed_counterparty_name(draft),
            "doc_date": payload.doc_date.isoformat() if payload.doc_date else None,
            "due_date": payload.due_date.isoformat() if payload.due_date else None,
            "currency": payload.currency,
            "invoice_no": payload.invoice_no,
            "totals": draft.totals_confirmed,
        },
        "review": {
            "confirmed_counterparty_name": payload.counterparty_name,
            "confirmed_contact_id": str(draft.confirmed_contact_id) if draft.confirmed_contact_id else None,
        },
        "lines": [
            {
                "line_no": line.line_no,
                "description": line.description,
                "qty": str(line.qty),
                "unit_price": str(line.unit_price),
                "net": str(line.net),
                "vat": str(line.vat),
                "gross": str(line.gross),
                "vat_code": line.vat_code,
                "nominal_code": line.nominal_code,
                "confidence": str(line.confidence) if line.confidence is not None else None,
            }
            for line in payload.lines
        ],
        "suggestions": _existing_suggestions(draft),
    }

    db.query(DocumentDraftLine).filter(DocumentDraftLine.draft_id == draft.id).delete()
    for line in payload.lines:
        db.add(DocumentDraftLine(
            draft_id=draft.id,
            org_id=current_user.organization_id,
            line_no=line.line_no,
            description_confirmed=line.description,
            qty=line.qty,
            unit_price=line.unit_price,
            net=line.net,
            vat=line.vat,
            gross=line.gross,
            vat_code_confirmed=line.vat_code,
            nominal_code_confirmed=line.nominal_code,
            confidence=line.confidence,
        ))

    db.commit()
    db.refresh(draft)

    return {"draft": _draft_to_dict(draft, draft.inbox_item)}


@router.post("/drafts/{draft_id}/submit")
def submit_draft(
    draft_id: str,
    payload: DraftUpdatePayload,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    draft = db.query(DocumentDraft).join(DocumentInboxItem).filter(
        DocumentDraft.id == draft_id,
        DocumentDraft.org_id == current_user.organization_id,
        DocumentInboxItem.org_id == current_user.organization_id,
    ).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft.status == "submitted":
        raise HTTPException(status_code=400, detail="Draft already submitted")

    confirmed_contact = _resolve_confirmed_contact(
        db,
        draft=draft,
        organization_id=current_user.organization_id,
        requested_contact_id=payload.confirmed_contact_id,
    )
    validation = _validate_totals(payload.lines, payload.totals)

    draft.doc_type_confirmed = payload.doc_type or draft.doc_type_confirmed
    draft.confirmed_contact_id = confirmed_contact.id if confirmed_contact else None
    draft.confirmed_contact = confirmed_contact
    draft.doc_date_confirmed = payload.doc_date or draft.doc_date_confirmed
    draft.currency_confirmed = payload.currency or draft.currency_confirmed or draft.currency_guess
    draft.invoice_no_confirmed = payload.invoice_no or draft.invoice_no_confirmed
    draft.totals_confirmed = {
        "net": str(payload.totals.net),
        "vat": str(payload.totals.vat),
        "gross": str(payload.totals.gross),
    }
    draft.validation_json = validation
    draft.last_edited_by = current_user.id
    draft.submitted_by = current_user.id
    draft.status = "submitted"

    draft.draft_json = {
        "source": "submitted",
        "submitted_at": datetime.utcnow().isoformat(),
        "header": {
            "doc_type": payload.doc_type,
            "counterparty_name": _observed_counterparty_name(draft),
            "doc_date": payload.doc_date.isoformat() if payload.doc_date else None,
            "due_date": payload.due_date.isoformat() if payload.due_date else None,
            "currency": payload.currency,
            "invoice_no": payload.invoice_no,
            "totals": draft.totals_confirmed,
        },
        "review": {
            "confirmed_counterparty_name": payload.counterparty_name,
            "confirmed_contact_id": str(draft.confirmed_contact_id) if draft.confirmed_contact_id else None,
        },
        "lines": [
            {
                "line_no": line.line_no,
                "description": line.description,
                "qty": str(line.qty),
                "unit_price": str(line.unit_price),
                "net": str(line.net),
                "vat": str(line.vat),
                "gross": str(line.gross),
                "vat_code": line.vat_code,
                "nominal_code": line.nominal_code,
                "confidence": str(line.confidence) if line.confidence is not None else None,
            }
            for line in payload.lines
        ],
        "suggestions": _existing_suggestions(draft),
    }

    db.query(DocumentDraftLine).filter(DocumentDraftLine.draft_id == draft.id).delete()
    for line in payload.lines:
        db.add(DocumentDraftLine(
            draft_id=draft.id,
            org_id=current_user.organization_id,
            line_no=line.line_no,
            description_confirmed=line.description,
            qty=line.qty,
            unit_price=line.unit_price,
            net=line.net,
            vat=line.vat,
            gross=line.gross,
            vat_code_confirmed=line.vat_code,
            nominal_code_confirmed=line.nominal_code,
            confidence=line.confidence,
        ))

    if draft.inbox_item:
        draft.inbox_item.status = "submitted"

    # Create or update placeholder internal transaction
    platform_name = "internal"
    platform_id = f"doc-draft-{draft.id}"
    transaction = db.query(Transaction).filter(
        Transaction.organization_id == current_user.organization_id,
        Transaction.platform_name == platform_name,
        Transaction.platform_id == platform_id,
    ).first()
    transaction_type = (payload.doc_type or draft.doc_type_confirmed or "invoice").lower()
    transaction_date = payload.doc_date or draft.doc_date_confirmed or draft.doc_date_guess or date.today()

    if not transaction:
        transaction = Transaction(
            organization_id=current_user.organization_id,
            platform_name=platform_name,
            platform_id=platform_id,
            transaction_type=transaction_type,
            reference_number=payload.invoice_no,
            description=f"Document review draft {draft.id}",
            amount=payload.totals.net,
            tax_amount=payload.totals.vat,
            total_amount=payload.totals.gross,
            currency=payload.currency or draft.currency_confirmed or draft.currency_guess or "GBP",
            transaction_date=transaction_date,
            due_date=payload.due_date,
            status="submitted",
        )
        db.add(transaction)
    else:
        transaction.transaction_type = transaction_type
        transaction.reference_number = payload.invoice_no
        transaction.amount = payload.totals.net
        transaction.tax_amount = payload.totals.vat
        transaction.total_amount = payload.totals.gross
        transaction.currency = payload.currency or transaction.currency
        transaction.transaction_date = transaction_date
        transaction.due_date = payload.due_date
        transaction.status = "submitted"

    record_reviewed_outcome(
        db,
        draft=draft,
        actor_user_id=current_user.id,
    )

    db.commit()
    db.refresh(draft)

    return {"draft": _draft_to_dict(draft, draft.inbox_item)}
