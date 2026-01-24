"""
API routes for core data entities.

Provides REST endpoints for organizations, clients, transactions, and accounts.
These endpoints serve data from the PostgreSQL database.

Author: Claude Code
Created: January 24, 2026
"""

import logging
from uuid import UUID
from typing import Optional, List
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.database import get_db
from backend.models.organization import Organization
from backend.models.client import Client
from backend.models.transaction import Transaction
from backend.models.account import Account

logger = logging.getLogger(__name__)

router = APIRouter(tags=["data"])


# ============================================================================
# ORGANIZATIONS
# ============================================================================

@router.get("/organizations")
def list_organizations(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List all organizations."""
    organizations = (
        db.query(Organization)
        .filter(Organization.is_active == True)
        .order_by(Organization.name)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "organizations": [
            {
                "id": str(org.id),
                "name": org.name,
                "email": org.email,
                "phone": org.phone,
                "city": org.city,
                "country": org.country,
                "currency": org.currency,
                "is_active": org.is_active,
            }
            for org in organizations
        ],
        "count": len(organizations),
    }


@router.get("/organizations/{org_id}")
def get_organization(
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a single organization by ID."""
    org = db.query(Organization).filter(Organization.id == org_id).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {
        "id": str(org.id),
        "name": org.name,
        "email": org.email,
        "phone": org.phone,
        "address_line1": org.address_line1,
        "address_line2": org.address_line2,
        "city": org.city,
        "postal_code": org.postal_code,
        "country": org.country,
        "timezone": org.timezone,
        "currency": org.currency,
        "is_active": org.is_active,
        "created_at": org.created_at.isoformat() if org.created_at else None,
    }


# ============================================================================
# CLIENTS
# ============================================================================

@router.get("/clients")
def list_clients(
    db: Session = Depends(get_db),
    org_id: Optional[UUID] = None,
    contact_type: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List clients with optional filtering."""
    query = db.query(Client).filter(Client.is_active == True)

    if org_id:
        query = query.filter(Client.organization_id == org_id)

    if contact_type:
        query = query.filter(Client.contact_type == contact_type)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Client.name.ilike(search_term)) |
            (Client.email.ilike(search_term))
        )

    total = query.count()
    clients = query.order_by(Client.name).offset(skip).limit(limit).all()

    return {
        "clients": [
            {
                "id": str(c.id),
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "city": c.city,
                "country": c.country,
                "contact_type": c.contact_type,
                "industry": c.industry,
                "tax_number": c.tax_number,
                "is_active": c.is_active,
            }
            for c in clients
        ],
        "count": len(clients),
        "total": total,
    }


@router.get("/clients/{client_id}")
def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a single client by ID."""
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return {
        "id": str(client.id),
        "organization_id": str(client.organization_id),
        "name": client.name,
        "email": client.email,
        "phone": client.phone,
        "website": client.website,
        "address_line1": client.address_line1,
        "address_line2": client.address_line2,
        "city": client.city,
        "postal_code": client.postal_code,
        "country": client.country,
        "contact_type": client.contact_type,
        "industry": client.industry,
        "tax_number": client.tax_number,
        "is_active": client.is_active,
        "created_at": client.created_at.isoformat() if client.created_at else None,
    }


# ============================================================================
# TRANSACTIONS
# ============================================================================

@router.get("/transactions")
def list_transactions(
    db: Session = Depends(get_db),
    org_id: Optional[UUID] = None,
    client_id: Optional[UUID] = None,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List transactions with optional filtering."""
    query = db.query(Transaction)

    if org_id:
        query = query.filter(Transaction.organization_id == org_id)

    if client_id:
        query = query.filter(Transaction.client_id == client_id)

    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)

    if status:
        query = query.filter(Transaction.status == status)

    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)

    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Transaction.description.ilike(search_term)) |
            (Transaction.reference_number.ilike(search_term))
        )

    total = query.count()
    transactions = (
        query
        .order_by(desc(Transaction.transaction_date))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "transactions": [
            {
                "id": str(t.id),
                "client_id": str(t.client_id) if t.client_id else None,
                "client_name": t.client.name if t.client else None,
                "account_id": str(t.account_id) if t.account_id else None,
                "account_name": t.account.name if t.account else None,
                "transaction_type": t.transaction_type,
                "reference_number": t.reference_number,
                "description": t.description,
                "amount": float(t.amount),
                "tax_amount": float(t.tax_amount),
                "total_amount": float(t.total_amount),
                "currency": t.currency,
                "transaction_date": t.transaction_date.isoformat() if t.transaction_date else None,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "status": t.status,
                "is_reconciled": t.is_reconciled,
            }
            for t in transactions
        ],
        "count": len(transactions),
        "total": total,
    }


@router.get("/transactions/{transaction_id}")
def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a single transaction by ID."""
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return {
        "id": str(txn.id),
        "organization_id": str(txn.organization_id),
        "client_id": str(txn.client_id) if txn.client_id else None,
        "client_name": txn.client.name if txn.client else None,
        "account_id": str(txn.account_id) if txn.account_id else None,
        "account_name": txn.account.name if txn.account else None,
        "transaction_type": txn.transaction_type,
        "reference_number": txn.reference_number,
        "description": txn.description,
        "amount": float(txn.amount),
        "tax_amount": float(txn.tax_amount),
        "total_amount": float(txn.total_amount),
        "currency": txn.currency,
        "transaction_date": txn.transaction_date.isoformat() if txn.transaction_date else None,
        "due_date": txn.due_date.isoformat() if txn.due_date else None,
        "status": txn.status,
        "is_reconciled": txn.is_reconciled,
        "created_at": txn.created_at.isoformat() if txn.created_at else None,
    }


# ============================================================================
# ACCOUNTS
# ============================================================================

@router.get("/accounts")
def list_accounts(
    db: Session = Depends(get_db),
    org_id: Optional[UUID] = None,
    account_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List accounts with optional filtering."""
    query = db.query(Account).filter(Account.is_active == True)

    if org_id:
        query = query.filter(Account.organization_id == org_id)

    if account_type:
        query = query.filter(Account.account_type == account_type)

    total = query.count()
    accounts = query.order_by(Account.code).offset(skip).limit(limit).all()

    return {
        "accounts": [
            {
                "id": str(a.id),
                "code": a.code,
                "name": a.name,
                "account_type": a.account_type,
                "description": a.description,
                "is_active": a.is_active,
            }
            for a in accounts
        ],
        "count": len(accounts),
        "total": total,
    }


@router.get("/accounts/{account_id}")
def get_account(
    account_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a single account by ID."""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return {
        "id": str(account.id),
        "organization_id": str(account.organization_id),
        "code": account.code,
        "name": account.name,
        "account_type": account.account_type,
        "description": account.description,
        "is_active": account.is_active,
        "created_at": account.created_at.isoformat() if account.created_at else None,
    }


# ============================================================================
# DASHBOARD SUMMARY
# ============================================================================

@router.get("/dashboard/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    org_id: Optional[UUID] = None,
):
    """Get dashboard summary statistics."""
    # Get organization (use first if not specified)
    if org_id:
        org = db.query(Organization).filter(Organization.id == org_id).first()
    else:
        org = db.query(Organization).filter(Organization.is_active == True).first()

    if not org:
        raise HTTPException(status_code=404, detail="No organization found")

    org_id = org.id

    # Count clients
    total_clients = (
        db.query(func.count(Client.id))
        .filter(Client.organization_id == org_id)
        .filter(Client.is_active == True)
        .scalar()
    )

    # Count transactions
    total_transactions = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.organization_id == org_id)
        .scalar()
    )

    # Count accounts
    total_accounts = (
        db.query(func.count(Account.id))
        .filter(Account.organization_id == org_id)
        .filter(Account.is_active == True)
        .scalar()
    )

    # Calculate revenue (sum of invoice totals)
    revenue = (
        db.query(func.sum(Transaction.total_amount))
        .filter(Transaction.organization_id == org_id)
        .filter(Transaction.transaction_type == "invoice")
        .scalar()
    ) or Decimal("0.00")

    # Calculate expenses (sum of bill totals)
    expenses = (
        db.query(func.sum(Transaction.total_amount))
        .filter(Transaction.organization_id == org_id)
        .filter(Transaction.transaction_type == "bill")
        .scalar()
    ) or Decimal("0.00")

    # Count by status
    status_counts = (
        db.query(Transaction.status, func.count(Transaction.id))
        .filter(Transaction.organization_id == org_id)
        .group_by(Transaction.status)
        .all()
    )
    status_breakdown = {status: count for status, count in status_counts}

    return {
        "organization": {
            "id": str(org.id),
            "name": org.name,
            "currency": org.currency,
        },
        "totalClients": total_clients,
        "totalTransactions": total_transactions,
        "totalAccounts": total_accounts,
        "revenue": f"£{float(revenue):,.2f}",
        "expenses": f"£{float(expenses):,.2f}",
        "netIncome": f"£{float(revenue - expenses):,.2f}",
        "statusBreakdown": status_breakdown,
        "syncStatus": "Connected",
        "lastSync": org.updated_at.isoformat() if org.updated_at else None,
    }
