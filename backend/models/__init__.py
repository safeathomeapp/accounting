"""
Module: models
Purpose: Database ORM models using SQLAlchemy
Dependencies: SQLAlchemy, pydantic

This module defines all SQLAlchemy models that map to database tables.

Models defined:
- Organization: Practice/organization information
- AccountingPlatform: Xero/QB configuration
- Client: Customers/contacts
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
]
