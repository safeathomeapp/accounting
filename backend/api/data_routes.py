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
import uuid as uuid_module

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel, Field

from backend.database import get_db, set_tenant_context
from backend.models.organization import Organization
from backend.models.client import Client
from backend.models.transaction import Transaction
from backend.models.account import Account
from backend.api.auth_routes import get_current_user
from backend.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["data"])


# ============================================================================
# PYDANTIC SCHEMAS FOR CRUD
# ============================================================================

class TransactionCreate(BaseModel):
    """Schema for creating a transaction."""
    client_id: Optional[str] = None
    account_id: Optional[str] = None
    transaction_type: str = "invoice"
    reference_number: Optional[str] = None
    description: Optional[str] = None
    amount: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    currency: str = "GBP"
    transaction_date: date
    due_date: Optional[date] = None
    status: str = "draft"
    organization_id: Optional[str] = None


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    client_id: Optional[str] = None
    account_id: Optional[str] = None
    transaction_type: Optional[str] = None
    reference_number: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    transaction_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    is_reconciled: Optional[bool] = None


class BulkDeleteRequest(BaseModel):
    """Schema for bulk delete operations."""
    ids: List[str]


class BulkStatusUpdate(BaseModel):
    """Schema for bulk status update."""
    ids: List[str]
    status: str


class ClientCreate(BaseModel):
    """Schema for creating a client."""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    contact_type: str = "customer"
    industry: Optional[str] = None
    tax_number: Optional[str] = None
    organization_id: Optional[str] = None


class ClientUpdate(BaseModel):
    """Schema for updating a client."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    contact_type: Optional[str] = None
    industry: Optional[str] = None
    tax_number: Optional[str] = None
    is_active: Optional[bool] = None


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
    current_user: User = Depends(get_current_user),
    contact_type: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List clients with optional filtering. Requires authentication."""
    # Set RLS tenant context for this session
    set_tenant_context(db, current_user.organization_id)

    # Now query - RLS will automatically filter to this org's clients
    query = db.query(Client).filter(Client.is_active == True)

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
        "platform_name": client.platform_name,
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


@router.post("/clients")
def create_client(
    data: ClientCreate,
    db: Session = Depends(get_db),
):
    """Create a new client."""
    # Get organization from request or fall back to first active
    if data.organization_id:
        org = db.query(Organization).filter(Organization.id == UUID(data.organization_id)).first()
    else:
        org = db.query(Organization).filter(Organization.is_active == True).first()

    if not org:
        raise HTTPException(status_code=400, detail="No organization found")

    # Create client with generated platform_id
    client = Client(
        organization_id=org.id,
        platform_id=f"local-{uuid_module.uuid4()}",
        platform_name="local",
        name=data.name,
        email=data.email,
        phone=data.phone,
        website=data.website,
        address_line1=data.address_line1,
        address_line2=data.address_line2,
        city=data.city,
        postal_code=data.postal_code,
        country=data.country,
        contact_type=data.contact_type,
        industry=data.industry,
        tax_number=data.tax_number,
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    logger.info(f"Created client {client.id}: {client.name}")

    return {
        "id": str(client.id),
        "message": "Client created successfully",
    }


@router.put("/clients/{client_id}")
def update_client(
    client_id: UUID,
    data: ClientUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing client."""
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Update fields if provided
    if data.name is not None:
        client.name = data.name
    if data.email is not None:
        client.email = data.email
    if data.phone is not None:
        client.phone = data.phone
    if data.website is not None:
        client.website = data.website
    if data.address_line1 is not None:
        client.address_line1 = data.address_line1
    if data.address_line2 is not None:
        client.address_line2 = data.address_line2
    if data.city is not None:
        client.city = data.city
    if data.postal_code is not None:
        client.postal_code = data.postal_code
    if data.country is not None:
        client.country = data.country
    if data.contact_type is not None:
        client.contact_type = data.contact_type
    if data.industry is not None:
        client.industry = data.industry
    if data.tax_number is not None:
        client.tax_number = data.tax_number
    if data.is_active is not None:
        client.is_active = data.is_active

    db.commit()
    db.refresh(client)

    logger.info(f"Updated client {client.id}: {client.name}")

    return {
        "id": str(client.id),
        "message": "Client updated successfully",
    }


@router.delete("/clients/{client_id}")
def delete_client(
    client_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a client (soft delete - sets is_active to False)."""
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Soft delete - set inactive instead of removing
    client.is_active = False
    db.commit()

    logger.info(f"Deleted (deactivated) client {client_id}")

    return {"message": "Client deleted successfully"}


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


@router.post("/transactions")
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
):
    """Create a new transaction."""
    # Get organization from request or fall back to first active
    if data.organization_id:
        org = db.query(Organization).filter(Organization.id == UUID(data.organization_id)).first()
    else:
        org = db.query(Organization).filter(Organization.is_active == True).first()

    if not org:
        raise HTTPException(status_code=400, detail="No organization found")

    # Create transaction with generated platform_id
    txn = Transaction(
        organization_id=org.id,
        platform_id=f"local-{uuid_module.uuid4()}",
        platform_name="local",
        client_id=UUID(data.client_id) if data.client_id else None,
        account_id=UUID(data.account_id) if data.account_id else None,
        transaction_type=data.transaction_type,
        reference_number=data.reference_number,
        description=data.description,
        amount=Decimal(str(data.amount)),
        tax_amount=Decimal(str(data.tax_amount)),
        total_amount=Decimal(str(data.total_amount)),
        currency=data.currency,
        transaction_date=data.transaction_date,
        due_date=data.due_date,
        status=data.status,
    )

    db.add(txn)
    db.commit()
    db.refresh(txn)

    logger.info(f"Created transaction {txn.id}")

    return {
        "id": str(txn.id),
        "message": "Transaction created successfully",
    }


@router.post("/transactions/bulk-delete")
def bulk_delete_transactions(
    data: BulkDeleteRequest,
    db: Session = Depends(get_db),
):
    """Delete multiple transactions."""
    if not data.ids:
        raise HTTPException(status_code=400, detail="No transaction IDs provided")

    deleted_count = 0
    for txn_id in data.ids:
        try:
            txn = db.query(Transaction).filter(Transaction.id == UUID(txn_id)).first()
            if txn:
                db.delete(txn)
                deleted_count += 1
        except Exception as e:
            logger.warning(f"Failed to delete transaction {txn_id}: {e}")

    db.commit()

    logger.info(f"Bulk deleted {deleted_count} transactions")

    return {
        "deleted_count": deleted_count,
        "message": f"Deleted {deleted_count} transactions",
    }


@router.put("/transactions/bulk-status")
def bulk_update_transaction_status(
    data: BulkStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update status for multiple transactions."""
    if not data.ids:
        raise HTTPException(status_code=400, detail="No transaction IDs provided")

    updated_count = 0
    for txn_id in data.ids:
        try:
            txn = db.query(Transaction).filter(Transaction.id == UUID(txn_id)).first()
            if txn:
                txn.status = data.status
                updated_count += 1
        except Exception as e:
            logger.warning(f"Failed to update transaction {txn_id}: {e}")

    db.commit()

    logger.info(f"Bulk updated {updated_count} transactions to status: {data.status}")

    return {
        "updated_count": updated_count,
        "message": f"Updated {updated_count} transactions to {data.status}",
    }


@router.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: UUID,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing transaction."""
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Update fields if provided
    if data.client_id is not None:
        txn.client_id = UUID(data.client_id) if data.client_id else None
    if data.account_id is not None:
        txn.account_id = UUID(data.account_id) if data.account_id else None
    if data.transaction_type is not None:
        txn.transaction_type = data.transaction_type
    if data.reference_number is not None:
        txn.reference_number = data.reference_number
    if data.description is not None:
        txn.description = data.description
    if data.amount is not None:
        txn.amount = Decimal(str(data.amount))
    if data.tax_amount is not None:
        txn.tax_amount = Decimal(str(data.tax_amount))
    if data.total_amount is not None:
        txn.total_amount = Decimal(str(data.total_amount))
    if data.currency is not None:
        txn.currency = data.currency
    if data.transaction_date is not None:
        txn.transaction_date = data.transaction_date
    if data.due_date is not None:
        txn.due_date = data.due_date
    if data.status is not None:
        txn.status = data.status
    if data.is_reconciled is not None:
        txn.is_reconciled = data.is_reconciled

    db.commit()
    db.refresh(txn)

    logger.info(f"Updated transaction {txn.id}")

    return {
        "id": str(txn.id),
        "message": "Transaction updated successfully",
    }


@router.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a transaction."""
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(txn)
    db.commit()

    logger.info(f"Deleted transaction {transaction_id}")

    return {"message": "Transaction deleted successfully"}


# ============================================================================
# ACCOUNTS
# ============================================================================

@router.get("/accounts")
def list_accounts(
    db: Session = Depends(get_db),
    org_id: Optional[UUID] = None,
    client_id: Optional[UUID] = None,
    account_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List accounts with optional filtering by organization, client, or type."""
    query = db.query(Account).filter(Account.is_active == True)

    if org_id:
        query = query.filter(Account.organization_id == org_id)

    if client_id:
        query = query.filter(Account.client_id == client_id)

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
                "client_id": str(a.client_id) if a.client_id else None,
                "platform_name": a.platform_name,
            }
            for a in accounts
        ],
        "count": len(accounts),
        "total": total,
    }


@router.get("/clients/{client_id}/accounts")
def list_client_accounts(
    client_id: UUID,
    db: Session = Depends(get_db),
    account_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
):
    """List all accounts for a specific client (their chart of accounts)."""
    # Verify client exists
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    query = db.query(Account).filter(
        Account.client_id == client_id,
        Account.is_active == True
    )

    if account_type:
        query = query.filter(Account.account_type == account_type)

    total = query.count()
    accounts = query.order_by(Account.code).offset(skip).limit(limit).all()

    # Group accounts by type for easier frontend display
    accounts_by_type = {}
    for a in accounts:
        acc_type = a.account_type or "other"
        if acc_type not in accounts_by_type:
            accounts_by_type[acc_type] = []
        accounts_by_type[acc_type].append({
            "id": str(a.id),
            "code": a.code,
            "name": a.name,
            "account_type": a.account_type,
            "description": a.description,
        })

    return {
        "client": {
            "id": str(client.id),
            "name": client.name,
            "platform_name": client.platform_name,
        },
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
        "accounts_by_type": accounts_by_type,
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
        "client_id": str(account.client_id) if account.client_id else None,
        "client_name": account.client.name if account.client else None,
        "code": account.code,
        "name": account.name,
        "account_type": account.account_type,
        "description": account.description,
        "platform_name": account.platform_name,
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
