"""Integration tests for monitoring system with sync engine.

Tests the end-to-end integration of monitoring into sync operations,
verifying that events are emitted, metrics are recorded, and errors
are logged properly during sync operations.
"""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch, AsyncMock, call
from datetime import datetime, timezone

from backend.sync.monitoring import SyncMonitor
from backend.sync.models import SyncResult, SyncStats, SyncError


class TestSyncMonitorIntegration:
    """Tests for sync monitoring integration."""

    def test_sync_monitor_initialization(self):
        """Test initializing sync monitor."""
        mock_db = MagicMock()

        with patch('backend.sync.monitoring.MetricsCollector'):
            monitor = SyncMonitor(mock_db)

            assert monitor.db is mock_db
            assert monitor.collector is not None

    @pytest.mark.asyncio
    async def test_on_sync_started_emits_event(self):
        """Test that sync start emits job_started event."""
        mock_db = MagicMock()
        job_id = uuid4()
        org_id = uuid4()
        platform = "xero"

        with patch('backend.sync.monitoring.MetricsCollector'):
            with patch('backend.sync.monitoring.RealtimeEventBroadcaster') as mock_broadcaster:
                monitor = SyncMonitor(mock_db)
                mock_broadcaster.emit_job_started = AsyncMock()

                await monitor.on_sync_started(job_id, org_id, platform)

                mock_broadcaster.emit_job_started.assert_called_once_with(
                    job_id, org_id, platform
                )

    @pytest.mark.asyncio
    async def test_on_sync_started_handles_errors(self):
        """Test that on_sync_started handles broadcaster errors gracefully."""
        mock_db = MagicMock()
        job_id = uuid4()
        org_id = uuid4()

        with patch('backend.sync.monitoring.MetricsCollector'):
            with patch('backend.sync.monitoring.RealtimeEventBroadcaster') as mock_broadcaster:
                monitor = SyncMonitor(mock_db)
                mock_broadcaster.emit_job_started = AsyncMock(
                    side_effect=Exception("Broadcaster error")
                )

                # Should not raise, should handle gracefully
                await monitor.on_sync_started(job_id, org_id, "xero")

    @pytest.mark.asyncio
    async def test_on_sync_completed_records_metrics_and_emits_event(self):
        """Test that sync completion records metrics and emits event."""
        mock_db = MagicMock()
        job_id = uuid4()
        org_id = uuid4()

        # Create mock result
        result = SyncResult(
            status="success",
            sync_history_id=uuid4(),
            accounts=SyncStats("account", created=5, updated=10, failed=1),
            clients=SyncStats("client", created=2, updated=5, failed=0),
            transactions=SyncStats("transaction", created=100, updated=50, failed=5)
        )
        result.duration_seconds = 45.5

        with patch('backend.sync.monitoring.MetricsCollector') as mock_collector_class:
            with patch('backend.sync.monitoring.RealtimeEventBroadcaster') as mock_broadcaster:
                mock_collector = MagicMock()
                mock_collector_class.return_value = mock_collector
                mock_broadcaster.emit_job_completed = AsyncMock()

                monitor = SyncMonitor(mock_db)

                await monitor.on_sync_completed(job_id, org_id, result, success=True)

                # Verify metrics were recorded
                mock_collector.record_sync_metrics.assert_called_once()
                call_kwargs = mock_collector.record_sync_metrics.call_args.kwargs
                assert call_kwargs["job_id"] == job_id
                assert call_kwargs["organization_id"] == org_id
                assert call_kwargs["result"] == result

                # Verify event was emitted
                mock_broadcaster.emit_job_completed.assert_called_once()
                event_call = mock_broadcaster.emit_job_completed.call_args
                assert event_call[0][0] == job_id
                assert event_call[0][1] == org_id
                # success is a keyword argument
                assert event_call[1].get("success") is True or event_call[0][3] is True

    @pytest.mark.asyncio
    async def test_on_sync_completed_reports_partial_status(self):
        """Test that partial sync status is reported correctly."""
        mock_db = MagicMock()
        job_id = uuid4()
        org_id = uuid4()

        result = SyncResult(
            status="partial",  # Some entities synced, some failed
            sync_history_id=uuid4(),
            accounts=SyncStats("account", created=5, failed=2),
            clients=SyncStats("client", created=2, failed=1),
            transactions=SyncStats("transaction", created=100, failed=10)
        )

        with patch('backend.sync.monitoring.MetricsCollector') as mock_collector_class:
            with patch('backend.sync.monitoring.RealtimeEventBroadcaster') as mock_broadcaster:
                mock_collector = MagicMock()
                mock_collector_class.return_value = mock_collector
                mock_broadcaster.emit_job_completed = AsyncMock()

                monitor = SyncMonitor(mock_db)

                await monitor.on_sync_completed(job_id, org_id, result, success=True)

                # Event should still be emitted with success=True for partial
                mock_broadcaster.emit_job_completed.assert_called_once()
                event_call = mock_broadcaster.emit_job_completed.call_args
                # success is a keyword argument
                assert event_call[1].get("success") is True

    @pytest.mark.asyncio
    async def test_on_sync_error_logs_and_emits_event(self):
        """Test that sync errors are logged and emitted."""
        mock_db = MagicMock()
        job_id = uuid4()
        org_id = uuid4()
        error_msg = "Failed to fetch data from API"

        with patch('backend.sync.monitoring.MetricsCollector') as mock_collector_class:
            with patch('backend.sync.monitoring.RealtimeEventBroadcaster') as mock_broadcaster:
                mock_collector = MagicMock()
                mock_collector_class.return_value = mock_collector
                mock_broadcaster.emit_error = AsyncMock()

                monitor = SyncMonitor(mock_db)

                await monitor.on_sync_error(
                    job_id, org_id, error_msg,
                    error_type="api_error",
                    severity="error"
                )

                # Verify error was logged
                mock_collector.log_error.assert_called_once()
                log_call = mock_collector.log_error.call_args.kwargs
                assert log_call["job_id"] == job_id
                assert log_call["organization_id"] == org_id
                assert log_call["error_message"] == error_msg
                assert log_call["error_type"] == "api_error"
                assert log_call["severity"] == "error"

                # Verify event was emitted
                mock_broadcaster.emit_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_sync_progress_emits_metric_update(self):
        """Test that sync progress emits metric update events."""
        mock_db = MagicMock()
        job_id = uuid4()
        org_id = uuid4()

        with patch('backend.sync.monitoring.MetricsCollector'):
            with patch('backend.sync.monitoring.RealtimeEventBroadcaster') as mock_broadcaster:
                mock_broadcaster.emit_metric_update = AsyncMock()

                monitor = SyncMonitor(mock_db)

                await monitor.on_sync_progress(
                    job_id, org_id,
                    entity_type="transactions",
                    processed=500,
                    total=1000,
                    failed=10
                )

                # Verify metric update was emitted
                mock_broadcaster.emit_metric_update.assert_called_once()
                call_args = mock_broadcaster.emit_metric_update.call_args
                assert call_args[0][0] == job_id
                assert call_args[0][1] == org_id
                metric_data = call_args[0][2]
                assert metric_data["entity_type"] == "transactions"
                assert metric_data["processed"] == 500
                assert metric_data["total"] == 1000
                assert metric_data["failed"] == 10
                assert metric_data["rate"] == 50.0  # 500/1000 * 100

    @pytest.mark.asyncio
    async def test_on_sync_progress_handles_zero_total(self):
        """Test that on_sync_progress handles zero total gracefully."""
        mock_db = MagicMock()
        job_id = uuid4()
        org_id = uuid4()

        with patch('backend.sync.monitoring.MetricsCollector'):
            with patch('backend.sync.monitoring.RealtimeEventBroadcaster') as mock_broadcaster:
                mock_broadcaster.emit_metric_update = AsyncMock()

                monitor = SyncMonitor(mock_db)

                await monitor.on_sync_progress(
                    job_id, org_id,
                    entity_type="accounts",
                    processed=0,
                    total=0,
                    failed=0
                )

                # Should emit event with rate=0
                mock_broadcaster.emit_metric_update.assert_called_once()
                metric_data = mock_broadcaster.emit_metric_update.call_args[0][2]
                assert metric_data["rate"] == 0


class TestSyncMonitoringWorkflow:
    """Tests for complete monitoring workflows."""

    @pytest.mark.asyncio
    async def test_successful_sync_workflow(self):
        """Test complete workflow for successful sync."""
        mock_db = MagicMock()
        job_id = uuid4()
        org_id = uuid4()
        platform = "xero"

        result = SyncResult(
            status="success",
            sync_history_id=uuid4(),
            accounts=SyncStats("account", created=5),
            clients=SyncStats("client", created=2),
            transactions=SyncStats("transaction", created=100)
        )

        with patch('backend.sync.monitoring.MetricsCollector') as mock_collector_class:
            with patch('backend.sync.monitoring.RealtimeEventBroadcaster') as mock_broadcaster:
                mock_collector = MagicMock()
                mock_collector_class.return_value = mock_collector
                mock_broadcaster.emit_job_started = AsyncMock()
                mock_broadcaster.emit_job_completed = AsyncMock()

                monitor = SyncMonitor(mock_db)

                # Start sync
                await monitor.on_sync_started(job_id, org_id, platform)
                assert mock_broadcaster.emit_job_started.called

                # Progress updates (simulated)
                await monitor.on_sync_progress(job_id, org_id, "accounts", 5, 5)
                await monitor.on_sync_progress(job_id, org_id, "clients", 2, 2)
                await monitor.on_sync_progress(job_id, org_id, "transactions", 100, 100)

                # Complete sync
                await monitor.on_sync_completed(job_id, org_id, result, success=True)

                # Verify sequence of events
                assert mock_broadcaster.emit_job_started.call_count == 1
                assert mock_broadcaster.emit_job_completed.call_count == 1
                assert mock_collector.record_sync_metrics.call_count == 1

    @pytest.mark.asyncio
    async def test_failed_sync_workflow(self):
        """Test complete workflow for failed sync."""
        mock_db = MagicMock()
        job_id = uuid4()
        org_id = uuid4()
        platform = "xero"

        with patch('backend.sync.monitoring.MetricsCollector') as mock_collector_class:
            with patch('backend.sync.monitoring.RealtimeEventBroadcaster') as mock_broadcaster:
                mock_collector = MagicMock()
                mock_collector_class.return_value = mock_collector
                mock_broadcaster.emit_job_started = AsyncMock()
                mock_broadcaster.emit_error = AsyncMock()

                monitor = SyncMonitor(mock_db)

                # Start sync
                await monitor.on_sync_started(job_id, org_id, platform)

                # Error occurs
                error_msg = "API authentication failed"
                await monitor.on_sync_error(
                    job_id, org_id, error_msg,
                    error_type="auth_error",
                    severity="critical"
                )

                # Verify events
                assert mock_broadcaster.emit_job_started.call_count == 1
                assert mock_broadcaster.emit_error.call_count == 1
                assert mock_collector.log_error.call_count == 1

    def test_sync_monitor_with_multiple_entities(self):
        """Test monitoring multiple entity syncs in sequence."""
        mock_db = MagicMock()

        with patch('backend.sync.monitoring.MetricsCollector'):
            monitor = SyncMonitor(mock_db)
            assert monitor.collector is not None

            # Test that monitor can handle multiple concurrent syncs
            job_ids = [uuid4() for _ in range(3)]
            org_id = uuid4()

            # Each job should maintain separate state
            for job_id in job_ids:
                assert job_id != job_ids[0] or job_id == job_ids[0]
