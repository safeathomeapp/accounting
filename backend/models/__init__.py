"""
Module: models
Purpose: Database ORM models using SQLAlchemy
Dependencies: SQLAlchemy, pydantic

This module defines all SQLAlchemy models that map to database tables.

Models defined:
- Organization: Practice/organization information
- AccountingPlatform: Xero/QB configuration
- Client: Customers/contacts
- ClientAssignment: User-to-client workflow assignments
- Transaction: Financial transactions
- Account: Chart of accounts
- OAuthToken: OAuth token storage
- AIAnalysisResult: AI analysis results
- SyncHistory: Synchronization tracking
- AuditLog: Change audit trail

Platform: Platform-agnostic (works with Xero and QuickBooks)

Author: Claude Code
Created: November 23, 2025
Last Modified: November 23, 2025
"""

from sqlalchemy.orm import declarative_base

# Base class for all models
# All SQLAlchemy models inherit from this
Base = declarative_base()

# Import all models
# This allows: from backend.models import Base, Organization, Client, etc.
from backend.models.organization import Organization
from backend.models.accounting_platform import AccountingPlatform
from backend.models.client import Client
from backend.models.transaction import Transaction
from backend.models.account import Account
from backend.models.oauth_token import OAuthToken
from backend.models.ai_analysis import AIAnalysisResult
from backend.models.sync_history import SyncHistory
from backend.models.audit_log import AuditLog
from backend.models.user import User
from backend.models.currency import Currency, ExchangeRate, ConversionHistory, CurrencyCode, RateSource
from backend.models.tax import (
    TaxType, TaxRate, TaxLiability, TaxAdjustment, TaxComplianceLog,
    TaxTypeCode, TaxPeriod, TaxLiabilityStatus, TaxAdjustmentType
)
from backend.models.analytics import (
    Forecast, FinancialMetric, TrendAnalysis, KPI, DashboardWidget,
    ForecastType, ForecastMethod, MetricType, TrendDirection
)
from backend.models.document import (
    DocumentInboxItem, DocumentOCRResult, DocumentDraft, DocumentDraftLine
)
from backend.models.client_assignment import ClientAssignment

# Canonical mapping layer models are imported directly from backend.canonical.models
# to avoid circular imports (canonical models import Base from this package).

# Export all models for easy importing
__all__ = [
    "Base",
    "Organization",
    "AccountingPlatform",
    "Client",
    "Transaction",
    "Account",
    "OAuthToken",
    "AIAnalysisResult",
    "SyncHistory",
    "AuditLog",
    "User",
    "Currency",
    "ExchangeRate",
    "ConversionHistory",
    "CurrencyCode",
    "RateSource",
    "TaxType",
    "TaxRate",
    "TaxLiability",
    "TaxAdjustment",
    "TaxComplianceLog",
    "TaxTypeCode",
    "TaxPeriod",
    "TaxLiabilityStatus",
    "TaxAdjustmentType",
    "Forecast",
    "FinancialMetric",
    "TrendAnalysis",
    "KPI",
    "DashboardWidget",
    "ForecastType",
    "ForecastMethod",
    "MetricType",
    "TrendDirection",
    "DocumentInboxItem",
    "DocumentOCRResult",
    "DocumentDraft",
    "DocumentDraftLine",
    "ClientAssignment",
]
