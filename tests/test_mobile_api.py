"""Tests for Mobile API Routes

Comprehensive test suite for all mobile API endpoints.
Tests cover: authentication, transactions, offline sync, push notifications.

Run with: pytest tests/test_mobile_api.py -v
"""

import pytest
from uuid import uuid4
from datetime import date
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal
from backend.models.mobile_session import MobileSession
from backend.models.offline_sync_queue import OfflineSyncQueueItem
from backend.models.push_notification import PushDeviceToken
from backend.services.mobile_auth import MobileAuthService


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session"""
    return SessionLocal()


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return uuid4()


@pytest.fixture
def test_org_id():
    """Test organization ID"""
    return uuid4()


@pytest.fixture
def test_device_id():
    """Test device ID"""
    return "iPhone_test_12345"


@pytest.fixture
def valid_tokens(db_session, test_user_id, test_org_id, test_device_id):
    """Create valid JWT tokens for testing"""
    access_token, refresh_token, session = MobileAuthService.create_session(
        db=db_session,
        user_id=test_user_id,
        organization_id=test_org_id,
        device_id=test_device_id,
        device_name="Test iPhone",
        device_os="iOS",
        app_version="1.0.0"
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": str(test_user_id),
        "organization_id": str(test_org_id),
        "device_id": test_device_id
    }


# ===== AUTHENTICATION TESTS =====

class TestMobileAuth:
    """Test authentication endpoints"""

    def test_health_check(self, client):
        """Health check should work without auth"""
        response = client.get("/api/mobile/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_login_success(self, client):
        """Test successful login"""
        response = client.post(
            "/api/mobile/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123",
                "device_id": "iPhone_12345",
                "device_name": "Test Device",
                "device_os": "iOS",
                "app_version": "1.0.0"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user_id" in data
        assert "organization_id" in data

    def test_refresh_token_success(self, client, valid_tokens, db_session):
        """Test token refresh"""
        response = client.post(
            "/api/mobile/auth/refresh",
            json={
                "refresh_token": valid_tokens["refresh_token"],
                "device_id": valid_tokens["device_id"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user_id"] == valid_tokens["user_id"]

    def test_logout(self, client, valid_tokens):
        """Test logout"""
        response = client.post(
            "/api/mobile/auth/logout",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"}
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_login_missing_credentials(self, client):
        """Test login with missing email"""
        response = client.post(
            "/api/mobile/auth/login",
            json={"password": "password123", "device_id": "iPhone_12345"}
        )
        # Should fail validation
        assert response.status_code == 422

    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token"""
        response = client.post(
            "/api/mobile/auth/refresh",
            json={
                "refresh_token": "invalid_token",
                "device_id": "iPhone_12345"
            }
        )

        assert response.status_code == 401


# ===== USER & ORGANIZATION TESTS =====

class TestUserEndpoints:
    """Test user profile endpoints"""

    def test_get_user_profile(self, client, valid_tokens):
        """Test get user profile"""
        response = client.get(
            "/api/mobile/user/profile",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        assert "organization_id" in data

    def test_get_profile_without_auth(self, client):
        """Test profile endpoint requires auth"""
        response = client.get("/api/mobile/user/profile")
        assert response.status_code == 401

    def test_get_org_summary(self, client, valid_tokens):
        """Test get organization summary"""
        response = client.get(
            "/api/mobile/org/summary",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "organization_id" in data
        assert "total_revenue" in data
        assert "net_income" in data


# ===== TRANSACTION TESTS =====

class TestTransactionEndpoints:
    """Test transaction endpoints"""

    def test_list_transactions(self, client, valid_tokens):
        """Test list transactions"""
        response = client.get(
            "/api/mobile/transactions",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"},
            params={"page": 1, "limit": 20}
        )

        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "page" in data
        assert data["page"] == 1

    def test_list_transactions_pagination(self, client, valid_tokens):
        """Test transaction pagination"""
        response = client.get(
            "/api/mobile/transactions",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"},
            params={"page": 2, "limit": 50}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 50
        assert data["page"] == 2

    def test_create_transaction(self, client, valid_tokens):
        """Test create transaction"""
        response = client.post(
            "/api/mobile/transactions",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"},
            json={
                "amount": "50.00",
                "date": str(date.today()),
                "description": "Lunch",
                "account_id": str(uuid4()),
                "category_id": str(uuid4())
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "transaction_id" in data
        assert data["status"] == "created"


# ===== ACCOUNT TESTS =====

class TestAccountEndpoints:
    """Test account endpoints"""

    def test_list_accounts(self, client, valid_tokens):
        """Test list accounts"""
        response = client.get(
            "/api/mobile/accounts",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data

    def test_get_account_details(self, client, valid_tokens):
        """Test get account details"""
        account_id = uuid4()
        response = client.get(
            f"/api/mobile/accounts/{account_id}",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "account_id" in data
        assert "balance" in data


# ===== OFFLINE SYNC TESTS =====

class TestOfflineSyncEndpoints:
    """Test offline sync queue endpoints"""

    def test_get_empty_sync_queue(self, client, valid_tokens):
        """Test get empty sync queue"""
        response = client.get(
            "/api/mobile/sync-queue",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "pending" in data
        assert "failed" in data

    def test_add_to_sync_queue(self, client, valid_tokens, db_session):
        """Test add item to sync queue"""
        response = client.post(
            "/api/mobile/sync-queue",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"},
            json={
                "action": "create",
                "entity_type": "transaction",
                "entity_data": {
                    "amount": "50.00",
                    "description": "Offline transaction"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "create"
        assert data["status"] == "pending"

    def test_sync_queue_endpoint(self, client, valid_tokens):
        """Test sync queue processing"""
        response = client.post(
            "/api/mobile/sync-queue/sync",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "synced" in data
        assert "failed" in data


# ===== PUSH NOTIFICATION TESTS =====

class TestPushNotificationEndpoints:
    """Test push notification endpoints"""

    def test_register_push_device(self, client, valid_tokens):
        """Test register device for push notifications"""
        response = client.post(
            "/api/mobile/notifications/register-device",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"},
            json={
                "token": "exponentPushToken[abc123...]",
                "token_type": "expo",
                "device_id": "iPhone_12345",
                "device_name": "John's iPhone",
                "device_os": "iOS"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_notification_history(self, client, valid_tokens):
        """Test get notification history"""
        response = client.get(
            "/api/mobile/notifications/history",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data


# ===== SYNC STATUS TESTS =====

class TestSyncStatusEndpoints:
    """Test sync status endpoints"""

    def test_get_sync_status(self, client, valid_tokens):
        """Test get sync status"""
        response = client.get(
            "/api/mobile/sync/status",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "last_sync" in data
        assert "pending_items" in data


# ===== INTEGRATION TESTS =====

class TestMobileIntegration:
    """End-to-end integration tests"""

    def test_complete_login_flow(self, client, db_session):
        """Test complete login flow"""
        # 1. Login
        login_response = client.post(
            "/api/mobile/auth/login",
            json={
                "email": "user@example.com",
                "password": "password123",
                "device_id": "iPhone_flow_test",
                "device_name": "Test Device",
                "device_os": "iOS",
                "app_version": "1.0.0"
            }
        )
        assert login_response.status_code == 200
        tokens = login_response.json()

        # 2. Get profile with token
        profile_response = client.get(
            "/api/mobile/user/profile",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert profile_response.status_code == 200

        # 3. Get accounts with token
        accounts_response = client.get(
            "/api/mobile/accounts",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert accounts_response.status_code == 200

        # 4. Logout
        logout_response = client.post(
            "/api/mobile/auth/logout",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert logout_response.status_code == 200

    def test_offline_sync_workflow(self, client, valid_tokens):
        """Test offline sync workflow"""
        # 1. Create offline transaction
        create_response = client.post(
            "/api/mobile/sync-queue",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"},
            json={
                "action": "create",
                "entity_type": "transaction",
                "entity_data": {"amount": "100.00"}
            }
        )
        assert create_response.status_code == 200

        # 2. Check queue
        queue_response = client.get(
            "/api/mobile/sync-queue",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"}
        )
        assert queue_response.status_code == 200
        assert queue_response.json()["pending"] > 0

        # 3. Sync queue
        sync_response = client.post(
            "/api/mobile/sync-queue/sync",
            headers={"Authorization": f"Bearer {valid_tokens['access_token']}"}
        )
        assert sync_response.status_code == 200
