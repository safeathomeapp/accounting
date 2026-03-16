"""
Module: document
Purpose: Document ingestion, OCR, and draft models
Dependencies: SQLAlchemy
Platform: Universal

Defines tables for the document review workflow:
- document_inbox_item: uploaded file and metadata
- document_ocr_result: OCR/extraction payload (stubbed for now)
- document_draft: editable draft extracted from OCR
- document_draft_line: line items for the draft
"""

from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    Integer,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.models import Base


class DocumentInboxItem(Base):
    """Uploaded document awaiting OCR and review."""

    __tablename__ = "document_inbox_item"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_type = Column(String(50), nullable=False, default="upload")
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_path = Column(Text, nullable=False)
    checksum_hash = Column(String(64), nullable=False)
    status = Column(String(50), nullable=False, default="uploaded", index=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    ocr_result = relationship(
        "DocumentOCRResult",
        back_populates="inbox_item",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="select",
    )
    draft = relationship(
        "DocumentDraft",
        back_populates="inbox_item",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="select",
    )
    organization = relationship(
        "Organization",
        lazy="select",
    )
    uploaded_by = relationship("User", lazy="select")
    client = relationship("Client", lazy="select")


class DocumentOCRResult(Base):
    """Raw OCR/extraction payload (stubbed)."""

    __tablename__ = "document_ocr_result"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    inbox_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_inbox_item.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ocr_engine = Column(String(50), nullable=False, default="stub")
    raw_text = Column(Text, nullable=False, default="")
    layout_json = Column(JSONB, nullable=True)
    pages = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    inbox_item = relationship("DocumentInboxItem", back_populates="ocr_result", lazy="select")
    organization = relationship("Organization", lazy="select")


class DocumentDraft(Base):
    """Editable draft extracted from OCR."""

    __tablename__ = "document_draft"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    inbox_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_inbox_item.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(String(50), nullable=False, default="draft", index=True)
    doc_type_guess = Column(String(50), nullable=True)
    doc_type_confirmed = Column(String(50), nullable=True)
    counterparty_guess = Column(String(255), nullable=True)
    counterparty_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    doc_date_guess = Column(Date, nullable=True)
    doc_date_confirmed = Column(Date, nullable=True)
    currency_guess = Column(String(3), nullable=True)
    currency_confirmed = Column(String(3), nullable=True)
    invoice_no_guess = Column(String(100), nullable=True)
    invoice_no_confirmed = Column(String(100), nullable=True)
    totals_guess = Column(JSONB, nullable=True)
    totals_confirmed = Column(JSONB, nullable=True)
    draft_json = Column(JSONB, nullable=True)
    validation_json = Column(JSONB, nullable=True)
    last_edited_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    submitted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    inbox_item = relationship("DocumentInboxItem", back_populates="draft", lazy="select")
    lines = relationship(
        "DocumentDraftLine",
        back_populates="draft",
        cascade="all, delete-orphan",
        order_by="DocumentDraftLine.line_no",
        lazy="select",
    )
    organization = relationship("Organization", lazy="select")
    client = relationship("Client", foreign_keys=[client_id], lazy="select")
    counterparty = relationship("Client", foreign_keys=[counterparty_id], lazy="select")
    last_editor = relationship("User", foreign_keys=[last_edited_by], lazy="select")
    submitter = relationship("User", foreign_keys=[submitted_by], lazy="select")


class DocumentDraftLine(Base):
    """Line items for a document draft."""

    __tablename__ = "document_draft_line"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    draft_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_draft.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_no = Column(Integer, nullable=False, default=1)
    description_guess = Column(Text, nullable=True)
    description_confirmed = Column(Text, nullable=True)
    qty = Column(Numeric(15, 2), nullable=False, default=Decimal("1.00"))
    unit_price = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    net = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    vat = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    gross = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    vat_code_guess = Column(String(50), nullable=True)
    vat_code_confirmed = Column(String(50), nullable=True)
    nominal_code_guess = Column(String(50), nullable=True)
    nominal_code_confirmed = Column(String(50), nullable=True)
    confidence = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    draft = relationship("DocumentDraft", back_populates="lines", lazy="select")
    organization = relationship("Organization", lazy="select")
