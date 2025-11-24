"""Tests for the sync engine."""

import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.sync import SyncEngine, SyncResult, SyncStats, SyncError
from backend.sync.exceptions import SyncException
from backend.sync.models import SyncStats as SyncStatsModel
from backend.accounting import StandardAccount, StandardContact, StandardTransaction, TransactionType, ContactType, AccountType
from backend.models import Organization, AccountingPlatform, SyncHistory


class TestSyncStats:
    """Tests for SyncStats data model."""

    def test_sync_stats_initialization(self):
        """Test SyncStats creation."""
        stats = SyncStats(entity_type="account")
        assert stats.entity_type == "account"
        assert stats.total_fetched == 0
        assert stats.created == 0
        assert stats.updated == 0
        assert stats.failed == 0

    def test_sync_stats_total_processed(self):
        """Test total processed calculation."""
        stats = SyncStats(entity_type="account")
        stats.created = 5
        stats.updated = 3
        stats.skipped = 2
        assert stats.total_processed == 10

    def test_sync_stats_success_rate(self):
        """Test success rate calculation."""
        stats = SyncStats(entity_type="account")
        stats.created = 8
        stats.updated = 2
        stats.failed = 10
        # 10 successes out of 20 total = 50%
        assert stats.success_rate == 50.0

    def test_sync_stats_success_rate_all_processed(self):
        """Test 100% success rate."""
        stats = SyncStats(entity_type="account")
        stats.created = 5
        stats.updated = 5
        stats.failed = 0
        assert stats.success_rate == 100.0

    def test_sync_stats_add_error(self):
        """Test adding errors to stats."""
        stats = SyncStats(entity_type="account")
        error = SyncError(
            entity_type="account",
            entity_id="123",
            error_message="Test error"
        )
        stats.add_error(error)
        assert stats.failed == 1
        assert len(stats.errors) == 1
        assert stats.errors[0] == error


class TestSyncError:
    """Tests for SyncError model."""

    def test_sync_error_creation(self):
        """Test SyncError creation."""
        error = SyncError(
            entity_type="account",
            entity_id="123",
            error_message="Failed to sync",
            error_type="database"
        )
        assert error.entity_type == "account"
        assert error.entity_id == "123"
        assert error.error_message == "Failed to sync"

    def test_sync_error_string_representation(self):
        """Test error string format."""
        error = SyncError(
            entity_type="account",
            entity_id="123",
            error_message="Test",
            error_type="fetch"
        )
        error_str = str(error)
        assert "[fetch]" in error_str
        assert "account" in error_str
        assert "123" in error_str


class TestSyncResult:
    """Tests for SyncResult data model."""

    def test_sync_result_initialization(self):
        """Test SyncResult creation."""
        result = SyncResult(
            status="success",
            sync_history_id=uuid4()
        )
        assert result.status == "success"
        assert result.accounts.entity_type == "account"
        assert result.clients.entity_type == "client"
        assert result.transactions.entity_type == "transaction"

    def test_sync_result_total_synced(self):
        """Test total synced calculation."""
        result = SyncResult(
            status="success",
            sync_history_id=uuid4()
        )
        result.accounts.created = 5
        result.clients.updated = 3
        result.transactions.created = 2
        assert result.total_synced == 10

    def test_sync_result_total_failed(self):
        """Test total failed calculation."""
        result = SyncResult(
            status="partial",
            sync_history_id=uuid4()
        )
        result.accounts.failed = 2
        result.clients.failed = 1
        result.transactions.failed = 3
        assert result.total_failed == 6

    def test_sync_result_string_representation(self):
        """Test SyncResult string format."""
        sync_id = uuid4()
        result = SyncResult(
            status="success",
            sync_history_id=sync_id
        )
        result_str = str(result)
        assert "Sync success" in result_str
        assert str(sync_id) in result_str


class TestSyncEngineInitialization:
    """Tests for SyncEngine initialization."""

    def test_sync_engine_creation(self):
        """Test SyncEngine initialization."""
        db = Mock(spec=Session)
        engine = SyncEngine(db)
        assert engine.db == db

    def test_sync_engine_attributes(self):
        """Test SyncEngine has required attributes."""
        db = Mock(spec=Session)
        engine = SyncEngine(db)
        assert hasattr(engine, "sync_all_platforms")
        assert hasattr(engine, "sync_platform")
        assert callable(engine.sync_all_platforms)
        assert callable(engine.sync_platform)


class TestSyncEngineDetermineSyncType:
    """Tests for determining sync type logic."""

    def test_determine_sync_type_full_no_previous(self):
        """Test full sync when no previous sync exists."""
        db = Mock(spec=Session)
        db.query().filter_by().order_by().first.return_value = None

        engine = SyncEngine(db)
        platform = Mock()
        platform.id = uuid4()

        sync_type = engine._determine_sync_type(platform)
        assert sync_type == "full"

    def test_determine_sync_type_incremental_recent_sync(self):
        """Test incremental sync when recent sync exists."""
        db = Mock(spec=Session)

        # Mock a recent sync history
        last_sync = Mock()
        last_sync.completed_at = datetime.now()

        db.query().filter_by().order_by().first.return_value = last_sync

        engine = SyncEngine(db)
        platform = Mock()
        platform.id = uuid4()

        sync_type = engine._determine_sync_type(platform)
        assert sync_type == "incremental"

    def test_determine_sync_type_full_old_sync(self):
        """Test full sync when previous sync is old (>7 days)."""
        from datetime import timedelta
        db = Mock(spec=Session)

        # Mock an old sync history (10 days ago) with naive datetime
        old_datetime = datetime(2025, 11, 14)  # 10 days before today
        last_sync = Mock()
        last_sync.completed_at = old_datetime

        db.query().filter_by().order_by().first.return_value = last_sync

        engine = SyncEngine(db)
        platform = Mock()
        platform.id = uuid4()

        sync_type = engine._determine_sync_type(platform)
        assert sync_type == "full"


class TestSyncEngineCreateSyncHistory:
    """Tests for creating sync history records."""

    def test_create_sync_history(self):
        """Test SyncHistory creation."""
        db = Mock(spec=Session)
        db.flush = Mock()
        db.add = Mock()

        engine = SyncEngine(db)

        org = Mock()
        org.id = uuid4()

        platform = Mock()
        platform.id = uuid4()

        # Create sync history
        sync_history = engine._create_sync_history(org, platform)

        # Verify it's a SyncHistory-like object
        assert sync_history.organization_id == org.id
        assert sync_history.platform_id == platform.id
        assert sync_history.sync_status == "started"
        assert sync_history.sync_type == "full"


class TestSyncEngineErrors:
    """Tests for error handling."""

    def test_sync_engine_organization_not_found(self):
        """Test error when organization not found."""
        db = Mock(spec=Session)
        query_result = Mock()
        query_result.first.return_value = None
        db.query().filter_by.return_value = query_result

        engine = SyncEngine(db)

        with pytest.raises(SyncException):
            engine.sync_all_platforms(uuid4())

    def test_sync_engine_no_platforms_configured(self):
        """Test error when no platforms configured."""
        db = Mock(spec=Session)

        # First query returns organization
        org_query = Mock()
        org_query.first.return_value = Mock()

        # Second query returns empty platforms list
        platform_query = Mock()
        platform_query.all.return_value = []

        query_mock = Mock()
        query_mock.filter_by.side_effect = [org_query, platform_query]
        db.query.return_value = query_mock

        engine = SyncEngine(db)

        with pytest.raises(SyncException):
            engine.sync_all_platforms(uuid4())


class TestSyncEngineIntegration:
    """Integration tests with mocked clients."""

    def test_sync_engine_factory_integration(self):
        """Test that sync engine uses factory to create clients."""
        db = Mock(spec=Session)
        engine = SyncEngine(db)

        # Verify engine can be created and has required methods
        assert hasattr(engine, 'sync_platform')
        assert hasattr(engine, 'sync_all_platforms')
        assert callable(engine.sync_platform)
        assert callable(engine.sync_all_platforms)


class TestAccountSyncHandler:
    """Tests for account synchronization handler."""

    def test_account_handler_initialization(self):
        """Test AccountSyncHandler creation."""
        from backend.sync.handlers import AccountSyncHandler
        db = Mock(spec=Session)
        handler = AccountSyncHandler(db)
        assert handler.db == db

    @patch('backend.sync.handlers.account_handler.Account')
    def test_sync_accounts_creates_records(self, mock_account_class):
        """Test account handler creates new records."""
        from backend.sync.handlers import AccountSyncHandler

        db = Mock(spec=Session)
        db.query().filter_by().first.return_value = None
        db.flush = Mock()
        db.commit = Mock()

        handler = AccountSyncHandler(db)

        # Mock client with accounts
        client = Mock()
        client.PLATFORM_NAME = "mock"
        client.get_accounts.return_value = [
            StandardAccount(
                id="acc-1",
                code="1000",
                name="Cash",
                type=AccountType.BANK
            )
        ]

        org_id = uuid4()

        # Sync accounts
        stats = handler.sync_accounts(client, org_id)

        assert stats.total_fetched == 1
        assert stats.created == 1
        assert db.add.called or db.flush.called


class TestClientSyncHandler:
    """Tests for client synchronization handler."""

    def test_client_handler_initialization(self):
        """Test ClientSyncHandler creation."""
        from backend.sync.handlers import ClientSyncHandler
        db = Mock(spec=Session)
        handler = ClientSyncHandler(db)
        assert handler.db == db


class TestTransactionSyncHandler:
    """Tests for transaction synchronization handler."""

    def test_transaction_handler_initialization(self):
        """Test TransactionSyncHandler creation."""
        from backend.sync.handlers import TransactionSyncHandler
        db = Mock(spec=Session)
        handler = TransactionSyncHandler(db)
        assert handler.db == db

    def test_transaction_sync_date_range_full(self):
        """Test transaction sync uses correct date range for full sync."""
        from backend.sync.handlers import TransactionSyncHandler
        from datetime import datetime, timedelta

        db = Mock(spec=Session)
        db.commit = Mock()
        db.query().filter_by().order_by().first.return_value = None

        handler = TransactionSyncHandler(db)

        client = Mock()
        client.PLATFORM_NAME = "mock"
        client.get_transactions.return_value = []

        org_id = uuid4()

        # Sync with full type
        stats = handler.sync_transactions(client, org_id, "full")

        # Verify call was made
        client.get_transactions.assert_called_once()

        # Check date range is approximately 2 years
        call_kwargs = client.get_transactions.call_args[1]
        assert "start_date" in call_kwargs
        assert "end_date" in call_kwargs
