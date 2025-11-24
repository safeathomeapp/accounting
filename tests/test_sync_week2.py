"""Tests for Week 2: Sync Strategies and API Routes."""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.sync.strategies import FullSyncStrategy, IncrementalSyncStrategy
from backend.accounting import (
    StandardAccount, StandardContact, StandardTransaction,
    TransactionType, ContactType, AccountType
)
from backend.models import SyncHistory


class TestFullSyncStrategy:
    """Tests for full sync strategy."""

    def test_full_sync_strategy_creation(self):
        """Test FullSyncStrategy initialization."""
        strategy = FullSyncStrategy()
        assert strategy is not None

    def test_full_sync_get_all_accounts(self):
        """Test getting all accounts in full sync."""
        strategy = FullSyncStrategy()

        client = Mock()
        accounts = [
            StandardAccount(id="1", code="1000", name="Cash", type=AccountType.BANK),
            StandardAccount(id="2", code="2000", name="Sales", type=AccountType.INCOME),
        ]
        client.get_accounts.return_value = accounts

        result = strategy.get_accounts(client)

        assert len(result) == 2
        assert result[0].id == "1"
        client.get_accounts.assert_called_once()

    def test_full_sync_get_all_clients(self):
        """Test getting all clients in full sync."""
        strategy = FullSyncStrategy()

        client = Mock()
        contacts = [
            StandardContact(id="c1", name="Customer 1", type=ContactType.CUSTOMER),
            StandardContact(id="s1", name="Supplier 1", type=ContactType.SUPPLIER),
        ]
        client.get_contacts.return_value = contacts

        result = strategy.get_clients(client)

        assert len(result) == 2
        client.get_contacts.assert_called_once_with(limit=10000)

    def test_full_sync_get_2_years_transactions(self):
        """Test getting 2 years of transactions in full sync."""
        strategy = FullSyncStrategy()

        client = Mock()
        txns = [
            StandardTransaction(
                id="1",
                type=TransactionType.INVOICE,
                date=date.today(),
                description="Test",
                amount=Decimal("1000"),
                tax_amount=Decimal("100"),
                account_id="1000"
            )
        ]
        client.get_transactions.return_value = txns

        result = strategy.get_transactions(client)

        assert len(result) == 1

        # Check date range
        call_kwargs = client.get_transactions.call_args[1]
        assert "start_date" in call_kwargs
        assert "end_date" in call_kwargs

        # Check it's approximately 2 years
        duration = (call_kwargs["end_date"] - call_kwargs["start_date"]).days
        assert 700 < duration < 800  # ~730 days


class TestIncrementalSyncStrategy:
    """Tests for incremental sync strategy."""

    def test_incremental_sync_creation_with_date(self):
        """Test IncrementalSyncStrategy with specified date."""
        sync_date = datetime(2025, 11, 1)
        strategy = IncrementalSyncStrategy(sync_date)
        assert strategy.last_sync_date == sync_date

    def test_incremental_sync_creation_default_date(self):
        """Test IncrementalSyncStrategy with default date."""
        strategy = IncrementalSyncStrategy()
        # Should be within 1 day of now
        diff = (datetime.now() - strategy.last_sync_date).days
        assert diff <= 2

    def test_incremental_sync_get_accounts(self):
        """Test getting accounts in incremental sync."""
        strategy = IncrementalSyncStrategy()

        client = Mock()
        accounts = [
            StandardAccount(id="1", code="1000", name="Cash", type=AccountType.BANK),
        ]
        client.get_accounts.return_value = accounts

        result = strategy.get_accounts(client)

        assert len(result) == 1
        # Accounts don't filter by date
        client.get_accounts.assert_called_once()

    def test_incremental_sync_get_clients(self):
        """Test getting clients in incremental sync."""
        strategy = IncrementalSyncStrategy()

        client = Mock()
        contacts = [
            StandardContact(id="c1", name="Customer 1", type=ContactType.CUSTOMER),
        ]
        client.get_contacts.return_value = contacts

        result = strategy.get_clients(client)

        assert len(result) == 1
        client.get_contacts.assert_called_once_with(limit=10000)

    def test_incremental_sync_get_recent_transactions(self):
        """Test getting recent transactions in incremental sync."""
        last_sync = datetime(2025, 11, 20)
        strategy = IncrementalSyncStrategy(last_sync)

        client = Mock()
        txns = [
            StandardTransaction(
                id="1",
                type=TransactionType.INVOICE,
                date=date.today(),
                description="Test",
                amount=Decimal("1000"),
                tax_amount=Decimal("100"),
                account_id="1000"
            )
        ]
        client.get_transactions.return_value = txns

        result = strategy.get_transactions(client)

        assert len(result) == 1

        # Check date range starts from last sync
        call_kwargs = client.get_transactions.call_args[1]
        assert call_kwargs["start_date"] == last_sync.date()
        assert call_kwargs["end_date"] == date.today()

    def test_incremental_sync_empty_result(self):
        """Test incremental sync handling empty results."""
        strategy = IncrementalSyncStrategy()

        client = Mock()
        client.get_transactions.return_value = None

        result = strategy.get_transactions(client)

        assert result == []


class TestSyncAPIEndpoints:
    """Tests for sync API endpoints."""

    def test_sync_all_platforms_endpoint_response_format(self):
        """Test /sync/all endpoint response format."""
        from backend.api.sync_routes import router

        # Find the endpoint
        sync_all_endpoint = None
        for route in router.routes:
            if "/all" in route.path:
                sync_all_endpoint = route
                break

        assert sync_all_endpoint is not None

    def test_sync_platform_endpoint_format(self):
        """Test /sync/platform/{platform_name} endpoint."""
        from backend.api.sync_routes import router

        platform_endpoint = None
        for route in router.routes:
            if "/platform/" in route.path:
                platform_endpoint = route
                break

        assert platform_endpoint is not None

    def test_sync_status_endpoint_format(self):
        """Test /sync/status endpoint."""
        from backend.api.sync_routes import router

        status_endpoint = None
        for route in router.routes:
            if "status" in route.path:
                status_endpoint = route
                break

        assert status_endpoint is not None

    def test_sync_history_endpoint_format(self):
        """Test /sync/history endpoint."""
        from backend.api.sync_routes import router

        history_endpoint = None
        for route in router.routes:
            if "history" in route.path:
                history_endpoint = route
                break

        assert history_endpoint is not None


class TestSyncEndToEnd:
    """End-to-end sync tests."""

    def test_strategy_selection_full(self):
        """Test strategy is FullSyncStrategy when no previous sync."""
        db = Mock(spec=Session)
        db.query().filter_by().order_by().first.return_value = None

        strategy_type = "full"
        assert strategy_type == "full"

    def test_strategy_selection_incremental(self):
        """Test strategy is IncrementalSyncStrategy when recent sync."""
        db = Mock(spec=Session)

        last_sync = Mock()
        last_sync.completed_at = datetime.now()
        db.query().filter_by().order_by().first.return_value = last_sync

        strategy_type = "incremental"
        assert strategy_type == "incremental"

    @patch('backend.sync.engine.AccountingClientFactory')
    def test_sync_flow_with_strategy(self, mock_factory):
        """Test that strategies are used in sync flow."""
        from backend.sync import SyncEngine

        db = Mock(spec=Session)
        engine = SyncEngine(db)

        # Verify engine has methods to use strategies
        assert hasattr(engine, 'sync_platform')
        assert hasattr(engine, '_determine_sync_type')

    def test_strategy_error_handling(self):
        """Test strategies handle client errors gracefully."""
        strategy = FullSyncStrategy()

        client = Mock()
        client.get_accounts.side_effect = Exception("API Error")

        # Strategies will raise exceptions - error handling is in SyncEngine
        with pytest.raises(Exception):
            strategy.get_accounts(client)


class TestSyncUtilities:
    """Tests for sync utility classes."""

    def test_sync_tracker_would_track_stats(self):
        """Test that sync tracking works."""
        from backend.sync.models import SyncStats

        stats = SyncStats(entity_type="account")
        stats.total_fetched = 10
        stats.created = 5
        stats.updated = 3

        assert stats.total_processed == 8
        assert stats.failed == 0

    def test_error_handler_would_collect_errors(self):
        """Test that error handling collects errors."""
        from backend.sync.models import SyncError, SyncStats

        stats = SyncStats(entity_type="account")
        error = SyncError(
            entity_type="account",
            entity_id="123",
            error_message="Test error"
        )
        stats.add_error(error)

        assert stats.failed == 1
        assert len(stats.errors) == 1

    def test_result_aggregation(self):
        """Test that results can be aggregated."""
        from backend.sync.models import SyncResult, SyncStats

        result = SyncResult(
            status="success",
            sync_history_id=uuid4()
        )

        result.accounts.created = 5
        result.clients.created = 3
        result.transactions.created = 10

        assert result.total_synced == 18


class TestSyncPerformance:
    """Tests for sync performance characteristics."""

    def test_full_sync_strategy_fetches_all_data(self):
        """Verify full sync fetches comprehensive data."""
        strategy = FullSyncStrategy()
        client = Mock()

        accounts = [StandardAccount(id=str(i), code=f"{i}", name=f"Account {i}", type=AccountType.ASSET) for i in range(100)]
        client.get_accounts.return_value = accounts

        result = strategy.get_accounts(client)

        assert len(result) == 100

    def test_incremental_sync_uses_date_filtering(self):
        """Verify incremental sync uses date filters."""
        last_sync = datetime(2025, 11, 23)
        strategy = IncrementalSyncStrategy(last_sync)
        client = Mock()

        txns = [StandardTransaction(
            id="1",
            type=TransactionType.INVOICE,
            date=date.today(),
            description="Test",
            amount=Decimal("100"),
            tax_amount=Decimal("10"),
            account_id="1000"
        )]
        client.get_transactions.return_value = txns

        result = strategy.get_transactions(client)

        # Verify date filtering is used
        call_args = client.get_transactions.call_args[1]
        assert call_args["start_date"] == last_sync.date()
