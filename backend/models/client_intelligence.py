"""Client intelligence ORM models.

Additive, client-scoped memory layer for future document interpretation and
review assistance. These tables do not replace the document pipeline; they
sit alongside it as auditable memory.
"""

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.models import Base


class ClientIntelligenceProfile(Base):
    """Anchor profile for one client's additive intelligence state."""

    __tablename__ = "client_intelligence_profile"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    schema_version = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default="active", index=True)
    last_reviewed_document_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    organization = relationship("Organization", lazy="select")
    client = relationship("Client", back_populates="intelligence_profile", lazy="select")
    supplier_aliases = relationship(
        "ClientSupplierAlias",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="select",
    )
    accounting_patterns = relationship(
        "ClientAccountingPattern",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="select",
    )
    events = relationship(
        "ClientIntelligenceEvent",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="select",
    )

    __table_args__ = (
        UniqueConstraint("client_id", name="uq_client_intelligence_profile_client"),
        CheckConstraint("schema_version >= 1", name="ck_client_intelligence_profile_schema_version"),
        Index("ix_client_intelligence_profile_org_client", "organization_id", "client_id"),
    )


class ClientSupplierAlias(Base):
    """Client-scoped supplier alias mapped to a client-owned contact."""

    __tablename__ = "client_supplier_alias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_intelligence_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alias_text = Column(String(255), nullable=False)
    alias_normalized = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)
    match_count = Column(Integer, nullable=False, default=1)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    organization = relationship("Organization", lazy="select")
    client = relationship("Client", back_populates="supplier_aliases", lazy="select")
    profile = relationship("ClientIntelligenceProfile", back_populates="supplier_aliases", lazy="select")
    contact = relationship("Contact", back_populates="supplier_aliases", lazy="select")

    __table_args__ = (
        CheckConstraint("match_count >= 0", name="ck_client_supplier_alias_match_count"),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
            name="ck_client_supplier_alias_confidence",
        ),
        UniqueConstraint(
            "client_id",
            "contact_id",
            "alias_normalized",
            "source_type",
            name="uq_client_supplier_alias_client_contact_alias_source",
        ),
        Index("ix_client_supplier_alias_client_alias", "client_id", "alias_normalized"),
        Index("ix_client_supplier_alias_org_client", "organization_id", "client_id"),
    )


class ClientAccountingPattern(Base):
    """Client-scoped accounting memory for future coding suggestions."""

    __tablename__ = "client_accounting_pattern"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_intelligence_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pattern_type = Column(String(50), nullable=False)
    pattern_key = Column(String(255), nullable=False)
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    suggested_nominal_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    suggested_tax_code = Column(String(50), nullable=True)
    suggested_document_type = Column(String(50), nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    organization = relationship("Organization", lazy="select")
    client = relationship("Client", back_populates="accounting_patterns", lazy="select")
    profile = relationship("ClientIntelligenceProfile", back_populates="accounting_patterns", lazy="select")
    contact = relationship("Contact", back_populates="accounting_patterns", lazy="select")
    suggested_nominal_account = relationship(
        "Account",
        back_populates="client_accounting_patterns",
        lazy="select",
    )

    __table_args__ = (
        CheckConstraint("usage_count >= 0", name="ck_client_accounting_pattern_usage_count"),
        CheckConstraint("success_count >= 0", name="ck_client_accounting_pattern_success_count"),
        CheckConstraint("success_count <= usage_count", name="ck_client_accounting_pattern_success_lte_usage"),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
            name="ck_client_accounting_pattern_confidence",
        ),
        Index("ix_client_accounting_pattern_client_key", "client_id", "pattern_type", "pattern_key"),
        Index("ix_client_accounting_pattern_org_client", "organization_id", "client_id"),
    )


class ClientIntelligenceEvent(Base):
    """Append-only audit log for client intelligence memory changes."""

    __tablename__ = "client_intelligence_event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_intelligence_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(50), nullable=False)
    source_inbox_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_inbox_item.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_draft_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_draft.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    payload_json = Column(JSONB, nullable=True)
    created_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)

    organization = relationship("Organization", lazy="select")
    client = relationship("Client", back_populates="intelligence_events", lazy="select")
    profile = relationship("ClientIntelligenceProfile", back_populates="events", lazy="select")
    source_inbox_item = relationship("DocumentInboxItem", lazy="select")
    source_draft = relationship("DocumentDraft", lazy="select")
    created_by = relationship("User", lazy="select")

    __table_args__ = (
        Index("ix_client_intelligence_event_client_profile_created", "client_id", "profile_id", "created_at"),
        Index("ix_client_intelligence_event_org_client", "organization_id", "client_id"),
    )
