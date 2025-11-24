"""
Module: ai_analysis
Purpose: AI analysis results ORM model
Dependencies: SQLAlchemy
Platform: Universal

The AIAnalysisResult model stores all Claude AI analysis results for:
- Transaction categorization
- Anomaly detection
- Business insights
- Communication drafting (emails, etc.)

This provides an audit trail and cost tracking for API usage.

Relationships:
- Many-to-one: organization (analysis for which organization)
- Many-to-one: account (suggested account for categorization)

Author: Claude Code
Created: November 23, 2025
Last Modified: November 23, 2025
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, func, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
import uuid

from backend.models import Base


class AIAnalysisResult(Base):
    """
    Represents a Claude AI analysis result.

    Stores all AI interactions for audit trail, cost tracking, and approval workflow.

    Attributes:
        id (UUID): Primary key
        organization_id (UUID): Organization this analysis is for
        analysis_type (str): Type of analysis
            - 'categorization': Suggest category/account for transaction
            - 'anomaly': Detect unusual transactions
            - 'insight': Generate business insights
            - 'communication': Draft emails/messages
        target_entity_type (str): What was analyzed ('transaction', 'client', 'account')
        target_entity_id (UUID): ID of the entity analyzed (optional)
        prompt_used (str): The prompt sent to Claude (for auditing)
        prompt_tokens (int): Tokens used for prompt
        response_tokens (int): Tokens used for response
        result_text (str): Claude's response (text)
        result_json (dict): Claude's response (structured JSON)
        confidence_score (Decimal): 0.00-1.00 confidence in result
        suggested_category (str): For categorization: suggested category
        suggested_account_id (UUID): For categorization: suggested account
        is_approved (bool): Whether user approved this analysis
        was_used (bool): Whether this analysis was actually applied
        estimated_cost_gbp (Decimal): Estimated cost of this API call
        created_at (DateTime): When analysis was performed
        updated_at (DateTime): When record was last updated

    Relationships:
        organization: The organization
        suggested_account: The suggested account (for categorization)

    Note:
        - Every Claude API call is logged here
        - Cost tracking enables budget monitoring
        - Confidence scores help with decision-making
        - Approval workflow: is_approved=False → user reviews → is_approved=True
        - was_used tracks whether result was actually applied

    Example:
        >>> from backend.models import AIAnalysisResult
        >>> analysis = AIAnalysisResult(
        ...     organization_id=org_uuid,
        ...     analysis_type="categorization",
        ...     target_entity_type="transaction",
        ...     target_entity_id=transaction_uuid,
        ...     result_text="This appears to be a consulting fee...",
        ...     confidence_score=Decimal("0.92"),
        ...     suggested_account_id=account_uuid
        ... )
    """

    __tablename__ = "ai_analysis_results"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Foreign Keys
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    suggested_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True
    )

    # Analysis Scope
    # Type of analysis: categorization, anomaly, insight, communication
    analysis_type = Column(String(50), nullable=False, index=True)
    # What kind of entity was analyzed
    target_entity_type = Column(String(50), nullable=True)
    # ID of the entity (transaction, client, etc.)
    target_entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Prompt & Tokens (for cost tracking and auditing)
    # The exact prompt sent to Claude
    prompt_used = Column(Text, nullable=False)
    # Tokens used for input
    prompt_tokens = Column(Integer, nullable=True)
    # Tokens used for output
    response_tokens = Column(Integer, nullable=True)

    # Analysis Result
    # Claude's response as text
    result_text = Column(Text, nullable=False)
    # Claude's response as structured JSON (for programmatic use)
    result_json = Column(JSONB, nullable=True)
    # Confidence score 0.00-1.00
    confidence_score = Column(
        Numeric(3, 2),
        nullable=True,
        default=Decimal("0.50")
    )

    # Categorization-Specific
    # Suggested category (e.g., "Marketing", "Supplies")
    suggested_category = Column(String(100), nullable=True)
    # Suggested account_id (reference to accounts table)
    suggested_account_id_local = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True
    )

    # Approval Workflow
    # Whether user reviewed and approved this analysis
    is_approved = Column(Boolean, default=False, nullable=False, index=True)
    # Whether this analysis was actually applied/used
    was_used = Column(Boolean, default=False, nullable=False)

    # Cost Tracking
    # Estimated cost of this API call in GBP
    estimated_cost_gbp = Column(Numeric(7, 4), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    organization = relationship(
        "Organization",
        back_populates="ai_analysis_results",
        lazy="select"
    )
    suggested_account = relationship(
        "Account",
        foreign_keys=[suggested_account_id_local],
        lazy="select"
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AIAnalysisResult("
            f"id={self.id}, "
            f"type={self.analysis_type}, "
            f"confidence={self.confidence_score}, "
            f"approved={self.is_approved}"
            f")>"
        )
