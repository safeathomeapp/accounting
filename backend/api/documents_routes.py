"""API routes for document intake, OCR, and draft review."""

import hashlib
import logging
import os
import shutil
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.api.auth_routes import get_current_user
from backend.models.document import (
    DocumentInboxItem,
    DocumentOCRResult,
    DocumentDraft,
    DocumentDraftLine,
)
from backend.models.transaction import Transaction
from backend.config import settings

logger = logging.getLogger(__name__)


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
    counterparty_id: Optional[str] = None
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
    return {
        "id": str(draft.id),
        "inbox_item_id": str(draft.inbox_item_id),
        "status": draft.status,
        "doc_type_guess": draft.doc_type_guess,
        "doc_type_confirmed": draft.doc_type_confirmed,
        "counterparty_guess": draft.counterparty_guess,
        "counterparty_id": str(draft.counterparty_id) if draft.counterparty_id else None,
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
            }
            if inbox_item
            else None
        ),
    }


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


def _generate_mock_draft(seed_text: str) -> Dict[str, Any]:
    """Generate mock draft data when Claude OCR is unavailable (fallback)."""
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
    currency = "GBP"

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

    totals = {k: totals[k].quantize(Decimal("0.01")) for k in totals}

    return {
        "doc_type": doc_type,
        "counterparty_name": counterparty,
        "doc_date": doc_date,
        "due_date": due_date,
        "currency": currency,
        "invoice_no": doc_number,
        "totals": totals,
        "lines": lines,
        "ocr_engine": "stub-v1",
        "raw_text": f"Mock extraction for testing (seed: {seed_text})",
    }


def _extract_with_claude(file_path: str, mime_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract document data using Claude Vision OCR.

    Args:
        file_path: Path to the document file
        mime_type: MIME type of the file

    Returns:
        Extracted document data

    Raises:
        Exception: If extraction fails
    """
    from backend.services.claude_ocr import extract_document, ClaudeOCRError

    try:
        result = extract_document(file_path, mime_type)
        result["ocr_engine"] = f"claude-{settings.claude_model}"
        result["raw_text"] = result.get("raw_text", "")
        return result
    except ClaudeOCRError as e:
        logger.error(f"Claude OCR failed: {e}")
        raise


def _is_claude_available() -> bool:
    """Check if Claude API is configured and available."""
    return bool(settings.claude_api_key)


@router.post("/inbox/upload")
def upload_document(
    file: UploadFile = File(...),
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
    """
    Extract structured data from an uploaded document using Claude Vision OCR.

    Falls back to mock data if Claude API is not configured or extraction fails.
    """
    inbox_item = db.query(DocumentInboxItem).filter(
        DocumentInboxItem.id == inbox_item_id,
        DocumentInboxItem.org_id == current_user.organization_id,
    ).first()
    if not inbox_item:
        raise HTTPException(status_code=404, detail="Inbox item not found")

    # Try Claude OCR first, fall back to mock
    ocr_engine = "stub-v1"
    extraction_error = None

    if _is_claude_available():
        try:
            logger.info(f"Attempting Claude OCR extraction for inbox item {inbox_item_id}")
            draft_data = _extract_with_claude(inbox_item.file_path, inbox_item.mime_type)
            ocr_engine = draft_data.get("ocr_engine", f"claude-{settings.claude_model}")
            logger.info(f"Claude OCR extraction successful for inbox item {inbox_item_id}")
        except Exception as e:
            extraction_error = str(e)
            logger.warning(f"Claude OCR failed, falling back to mock: {e}")
            draft_data = _generate_mock_draft(str(inbox_item.id))
    else:
        logger.info("Claude API not configured, using mock extraction")
        draft_data = _generate_mock_draft(str(inbox_item.id))

    totals = TotalsPayload(**draft_data["totals"])
    validation = _validate_totals(
        [
            DraftLinePayload(
                line_no=line["line_no"],
                description=line["description"],
                qty=line["qty"],
                unit_price=line["unit_price"],
                net=line["net"],
                vat=line["vat"],
                gross=line["gross"],
                vat_code=line.get("vat_code"),
                nominal_code=line.get("nominal_code"),
                confidence=line.get("confidence"),
            )
            for line in draft_data["lines"]
        ],
        totals,
    )

    # Store OCR result
    raw_text = draft_data.get("raw_text", "")
    existing_ocr = db.query(DocumentOCRResult).filter(
        DocumentOCRResult.inbox_item_id == inbox_item.id
    ).first()
    if existing_ocr:
        existing_ocr.ocr_engine = ocr_engine
        existing_ocr.raw_text = raw_text
        existing_ocr.layout_json = {
            "pages": 1,
            "extraction_source": ocr_engine,
            "extraction_error": extraction_error,
        }
        existing_ocr.pages = 1
    else:
        db.add(DocumentOCRResult(
            inbox_item_id=inbox_item.id,
            org_id=current_user.organization_id,
            ocr_engine=ocr_engine,
            raw_text=raw_text,
            layout_json={
                "pages": 1,
                "extraction_source": ocr_engine,
                "extraction_error": extraction_error,
            },
            pages=1,
        ))

    draft = db.query(DocumentDraft).filter(
        DocumentDraft.inbox_item_id == inbox_item.id
    ).first()
    if not draft:
        draft = DocumentDraft(
            inbox_item_id=inbox_item.id,
            org_id=current_user.organization_id,
            status="draft",
        )
        db.add(draft)
        db.flush()

    draft.doc_type_guess = draft_data["doc_type"]
    draft.counterparty_guess = draft_data["counterparty_name"]
    draft.doc_date_guess = draft_data["doc_date"]
    draft.currency_guess = draft_data["currency"]
    draft.invoice_no_guess = draft_data["invoice_no"]
    draft.totals_guess = {
        "net": str(draft_data["totals"]["net"]),
        "vat": str(draft_data["totals"]["vat"]),
        "gross": str(draft_data["totals"]["gross"]),
    }
    draft.totals_confirmed = draft.totals_guess
    draft.draft_json = {
        "source": "stub",
        "header": {
            "doc_type": draft_data["doc_type"],
            "counterparty_name": draft_data["counterparty_name"],
            "doc_date": draft_data["doc_date"].isoformat() if draft_data["doc_date"] else None,
            "due_date": draft_data["due_date"].isoformat() if draft_data["due_date"] else None,
            "currency": draft_data["currency"],
            "invoice_no": draft_data["invoice_no"],
            "totals": draft.totals_guess,
        },
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
    }
    draft.validation_json = validation
    draft.last_edited_by = current_user.id

    db.query(DocumentDraftLine).filter(DocumentDraftLine.draft_id == draft.id).delete()
    for line in draft_data["lines"]:
        db.add(DocumentDraftLine(
            draft_id=draft.id,
            org_id=current_user.organization_id,
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
        ))

    inbox_item.status = "drafted"
    db.commit()
    db.refresh(draft)

    return {
        "draft": _draft_to_dict(draft, inbox_item),
    }


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

    validation = _validate_totals(payload.lines, payload.totals)

    draft.doc_type_confirmed = payload.doc_type or draft.doc_type_confirmed
    draft.counterparty_guess = payload.counterparty_name or draft.counterparty_guess
    draft.counterparty_id = payload.counterparty_id or draft.counterparty_id
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
            "counterparty_name": payload.counterparty_name,
            "doc_date": payload.doc_date.isoformat() if payload.doc_date else None,
            "due_date": payload.due_date.isoformat() if payload.due_date else None,
            "currency": payload.currency,
            "invoice_no": payload.invoice_no,
            "totals": draft.totals_confirmed,
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

    validation = _validate_totals(payload.lines, payload.totals)

    draft.doc_type_confirmed = payload.doc_type or draft.doc_type_confirmed
    draft.counterparty_guess = payload.counterparty_name or draft.counterparty_guess
    draft.counterparty_id = payload.counterparty_id or draft.counterparty_id
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
            "counterparty_name": payload.counterparty_name,
            "doc_date": payload.doc_date.isoformat() if payload.doc_date else None,
            "due_date": payload.due_date.isoformat() if payload.due_date else None,
            "currency": payload.currency,
            "invoice_no": payload.invoice_no,
            "totals": draft.totals_confirmed,
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

    db.commit()
    db.refresh(draft)

    return {"draft": _draft_to_dict(draft, draft.inbox_item)}
