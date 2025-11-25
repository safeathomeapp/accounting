"""Mobile API Routes for React Native App

This file contains 20 REST API endpoints optimized for mobile apps.

Key Features:
- JWT authentication (token-based, not cookie-based)
- Pagination (return small chunks of data)
- Offline sync queue management
- Push notification management
- Lightweight responses (no unnecessary data)

All endpoints prefix: /api/mobile/

Structure:
1. Authentication (login, logout, refresh)
2. Organization & User (profile, settings)
3. Transactions (list, create, update)
4. Accounts (list, details)
5. Offline Sync (queue management)
6. Push Notifications (device management)
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date
from typing import Optional, List

from backend.database import get_db
from backend.services.mobile_auth import MobileAuthService
from backend.models.mobile_session import MobileSession
from backend.models.offline_sync_queue import OfflineSyncQueueItem
from backend.models.push_notification import PushDeviceToken

# Create router with /api/mobile prefix
router = APIRouter(prefix="/api/mobile", tags=["mobile"])


# ===== REQUEST/RESPONSE MODELS =====
# These define the structure of data sent to/from the mobile app

class LoginRequest(BaseModel):
    """Request to log in"""
    email: str
    password: str
    device_id: str
    device_name: str = None
    device_os: str = None  # "iOS" or "Android"
    app_version: str = None


class LoginResponse(BaseModel):
    """Response after successful login"""
    access_token: str
    refresh_token: str
    user_id: str
    organization_id: str


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token"""
    refresh_token: str
    device_id: str


class TransactionListRequest(BaseModel):
    """Request to list transactions"""
    page: int = 1  # Which page (1, 2, 3...)
    limit: int = 20  # How many per page
    start_date: Optional[date] = None  # Filter by date
    end_date: Optional[date] = None


class CreateTransactionRequest(BaseModel):
    """Request to create a transaction"""
    amount: str  # Use string for decimal precision
    date: date
    description: str
    account_id: UUID
    category_id: Optional[UUID] = None


class CreateOfflineSyncRequest(BaseModel):
    """Request to add item to offline sync queue"""
    action: str  # "create", "update", "delete"
    entity_type: str  # "transaction", "account", etc.
    entity_data: dict  # The actual data


class PushTokenRequest(BaseModel):
    """Request to register device for push notifications"""
    token: str
    token_type: str = "expo"  # "expo", "fcm", "apns"
    device_id: str
    device_name: str = None
    device_os: str = None


# ===== HELPER FUNCTIONS =====

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> tuple[UUID, UUID]:
    """
    Extract user and organization from JWT token.

    This is called on every protected endpoint to verify the user.

    Args:
        authorization: "Bearer <token>" header
        db: Database session

    Returns:
        (user_id, organization_id)

    Raises:
        HTTPException 401 if token invalid
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.replace("Bearer ", "")

    # Verify token and extract payload
    payload = MobileAuthService.verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = UUID(payload["user_id"])
    organization_id = UUID(payload["organization_id"])

    return user_id, organization_id


# ===== AUTHENTICATION ENDPOINTS =====

@router.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Log in to the mobile app.

    Request:
        POST /api/mobile/auth/login
        {
            "email": "user@example.com",
            "password": "password123",
            "device_id": "iPhone_UDID_12345",
            "device_name": "John's iPhone",
            "device_os": "iOS",
            "app_version": "1.0.0"
        }

    Response:
        {
            "access_token": "eyJ0eXA...",
            "refresh_token": "eyJ0eXA...",
            "user_id": "abc123...",
            "organization_id": "def456..."
        }

    Notes:
    - For now, we accept any email/password
    - Later: Integrate with real user authentication
    - Save both tokens locally on the phone
    """
    # TODO: Replace with real user authentication
    # For now, accept any credentials
    user_id = UUID("00000000-0000-0000-0000-000000000001")  # Mock user
    organization_id = UUID("00000000-0000-0000-0000-000000000002")  # Mock org

    # Create JWT tokens and session record
    access_token, refresh_token, session = MobileAuthService.create_session(
        db=db,
        user_id=user_id,
        organization_id=organization_id,
        device_id=request.device_id,
        device_name=request.device_name,
        device_os=request.device_os,
        app_version=request.app_version
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user_id),
        organization_id=str(organization_id)
    )


@router.post("/auth/refresh", response_model=LoginResponse)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token when it expires.

    Request:
        POST /api/mobile/auth/refresh
        {
            "refresh_token": "eyJ0eXA...",
            "device_id": "iPhone_UDID_12345"
        }

    Response:
        {
            "access_token": "eyJ0eXA...",
            "refresh_token": "eyJ0eXA..." (same as before, might be rotated),
            "user_id": "abc123...",
            "organization_id": "def456..."
        }

    Notes:
    - Called when access token expires (after 15 minutes)
    - Safe to call frequently
    - Prevents user from losing work while using app
    """
    result = MobileAuthService.refresh_access_token(
        db=db,
        refresh_token=request.refresh_token,
        device_id=request.device_id
    )

    if not result:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token, session = result

    return LoginResponse(
        access_token=new_access_token,
        refresh_token=request.refresh_token,  # Refresh token doesn't change
        user_id=str(session.user_id),
        organization_id=str(session.organization_id)
    )


@router.post("/auth/logout")
def logout(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Log out (revoke session).

    Request:
        POST /api/mobile/auth/logout
        Headers: Authorization: Bearer <token>

    Response:
        {"success": true}

    Notes:
    - After logout, user must log in again
    - Device token is revoked immediately
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.replace("Bearer ", "")
    payload = MobileAuthService.verify_access_token(token)

    if payload:
        user_id = UUID(payload["user_id"])
        organization_id = UUID(payload["organization_id"])
        device_id = payload["device_id"]

        MobileAuthService.revoke_session(
            db=db,
            user_id=user_id,
            organization_id=organization_id,
            device_id=device_id
        )

    return {"success": True}


# ===== USER & ORGANIZATION ENDPOINTS =====

@router.get("/user/profile")
def get_user_profile(
    user_org: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile.

    Returns lightweight profile info for display in app.
    """
    user_id, organization_id = user_org

    # TODO: Fetch real user profile from users table
    # For now, return mock data
    return {
        "user_id": str(user_id),
        "email": "user@example.com",
        "organization_id": str(organization_id),
        "organization_name": "My Company"
    }


@router.get("/org/summary")
def get_organization_summary(
    user_org: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get organization summary (financial overview).

    Used for dashboard on mobile app.
    """
    user_id, organization_id = user_org

    # TODO: Calculate actual financial summary
    return {
        "organization_id": str(organization_id),
        "total_revenue": "150000.00",
        "total_expenses": "75000.00",
        "net_income": "75000.00",
        "last_sync": "2025-11-25T10:30:00Z"
    }


# ===== TRANSACTION ENDPOINTS =====

@router.get("/transactions")
def list_transactions(
    page: int = 1,
    limit: int = 20,
    user_org: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List transactions for the user's organization.

    Paginated for mobile (returns 20 per page).

    Query Parameters:
        page: Which page (1, 2, 3...)
        limit: Items per page

    Response:
        {
            "transactions": [
                {
                    "id": "abc123...",
                    "amount": "50.00",
                    "date": "2025-11-25",
                    "description": "Lunch",
                    "account": "Meals"
                }
            ],
            "page": 1,
            "limit": 20,
            "total": 150
        }
    """
    user_id, organization_id = user_org

    # TODO: Fetch from database
    # For now, return mock data
    return {
        "transactions": [
            {
                "id": "abc123",
                "amount": "50.00",
                "date": "2025-11-25",
                "description": "Lunch",
                "account": "Meals"
            }
        ],
        "page": page,
        "limit": limit,
        "total": 150
    }


@router.post("/transactions")
def create_transaction(
    request: CreateTransactionRequest,
    user_org: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new transaction.

    Works online or offline:
    - Online: Sent immediately to server
    - Offline: Queued locally, sent when online

    Request:
        POST /api/mobile/transactions
        Headers: Authorization: Bearer <token>
        {
            "amount": "50.00",
            "date": "2025-11-25",
            "description": "Lunch",
            "account_id": "xyz789...",
            "category_id": "meals123..." (optional)
        }

    Response:
        {
            "transaction_id": "abc123...",
            "status": "created"
        }
    """
    user_id, organization_id = user_org

    # TODO: Create transaction in database
    # For now, return mock response
    return {
        "transaction_id": "abc123...",
        "status": "created"
    }


# ===== ACCOUNT ENDPOINTS =====

@router.get("/accounts")
def list_accounts(
    user_org: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all accounts for the organization.

    Lightweight list for account picker in app.
    """
    user_id, organization_id = user_org

    # TODO: Fetch from database
    return {
        "accounts": [
            {
                "id": "acc1",
                "name": "Checking Account",
                "balance": "5000.00"
            },
            {
                "id": "acc2",
                "name": "Savings Account",
                "balance": "10000.00"
            }
        ]
    }


@router.get("/accounts/{account_id}")
def get_account(
    account_id: UUID,
    user_org: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get account details (balance, transactions, etc).
    """
    user_id, organization_id = user_org

    # TODO: Fetch account details
    return {
        "account_id": str(account_id),
        "name": "Checking Account",
        "balance": "5000.00",
        "last_transaction": "2025-11-25T10:30:00Z"
    }


# ===== OFFLINE SYNC QUEUE ENDPOINTS =====

@router.get("/sync-queue")
def get_sync_queue(
    user_org: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get pending sync queue items.

    Shows user what's waiting to sync.
    """
    user_id, organization_id = user_org

    items = db.query(OfflineSyncQueueItem).filter(
        OfflineSyncQueueItem.organization_id == organization_id,
        OfflineSyncQueueItem.user_id == user_id,
        OfflineSyncQueueItem.status.in_(["pending", "failed"])
    ).all()

    return {
        "pending": len([i for i in items if i.status == "pending"]),
        "failed": len([i for i in items if i.status == "failed"]),
        "items": [i.to_dict() for i in items]
    }


@router.post("/sync-queue")
def add_to_sync_queue(
    request: CreateOfflineSyncRequest,
    user_org: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add item to offline sync queue.

    Called by mobile app for offline operations.
    """
    user_id, organization_id = user_org

    item = OfflineSyncQueueItem(
        organization_id=organization_id,
        user_id=user_id,
        action=request.action,
        entity_type=request.entity_type,
        entity_data=request.entity_data,
        status="pending"
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item.to_dict()


@router.post("/sync-queue/sync")
def sync_queue(
    user_org: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process offline sync queue.

    Called when device comes online.
    Sends all pending items to server.
    """
    user_id, organization_id = user_org

    # TODO: Implement sync logic
    # For now, return mock response
    return {
        "synced": 0,
        "failed": 0,
        "message": "Sync complete"
    }


# ===== PUSH NOTIFICATION ENDPOINTS =====

@router.post("/notifications/register-device")
def register_push_device(
    request: PushTokenRequest,
    user_org: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register device for push notifications.

    Called when app starts up, or when app asks for notification permission.

    Request:
        {
            "token": "exponentPushToken[abc123...]",
            "token_type": "expo",
            "device_id": "iPhone_UDID_12345",
            "device_name": "John's iPhone",
            "device_os": "iOS"
        }
    """
    user_id, organization_id = user_org

    # Check if token already exists
    existing = db.query(PushDeviceToken).filter(
        PushDeviceToken.token == request.token
    ).first()

    if existing:
        existing.is_active = True
        token_record = existing
    else:
        token_record = PushDeviceToken(
            user_id=user_id,
            organization_id=organization_id,
            device_id=request.device_id,
            device_name=request.device_name,
            token=request.token,
            token_type=request.token_type
        )
        db.add(token_record)

    db.commit()
    db.refresh(token_record)

    return {
        "success": True,
        "device_id": str(token_record.id)
    }


@router.get("/notifications/history")
def get_notification_history(
    user_org: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notification history.

    Shows user past notifications.
    """
    user_id, organization_id = user_org

    # TODO: Fetch notifications from database
    return {
        "notifications": []
    }


# ===== SYNC STATUS ENDPOINT =====

@router.get("/sync/status")
def get_sync_status(
    user_org: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current sync status.

    Used for displaying sync indicator in app.

    Response:
        {
            "status": "synced",
            "last_sync": "2025-11-25T10:30:00Z",
            "pending_items": 0
        }
    """
    user_id, organization_id = user_org

    # TODO: Calculate actual status
    return {
        "status": "synced",
        "last_sync": "2025-11-25T10:30:00Z",
        "pending_items": 0
    }


# ===== HEALTH CHECK =====

@router.get("/health")
def health_check():
    """
    Health check endpoint.

    Called by mobile app to verify backend is reachable.
    Doesn't require authentication.
    """
    return {
        "status": "ok",
        "api_version": "1.0.0"
    }
