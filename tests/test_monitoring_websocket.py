"""Tests for WebSocket connection management and real-time broadcasting.

Note: Tests use mocking for WebSocket connections to test business logic
without requiring a full async WebSocket infrastructure.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from backend.monitoring.websocket import ConnectionManager, format_ws_message
from backend.monitoring.realtime import RealtimeEventBroadcaster


class TestConnectionManager:
    """Tests for WebSocket connection manager."""

    def test_connection_manager_initialization(self):
        """Test initializing connection manager."""
        manager = ConnectionManager()

        assert isinstance(manager.active_connections, dict)
        assert isinstance(manager.all_connections, set)
        assert len(manager.active_connections) == 0
        assert len(manager.all_connections) == 0

    @pytest.mark.asyncio
    async def test_connect_new_organization(self):
        """Test connecting a client to a new organization."""
        manager = ConnectionManager()
        websocket = AsyncMock()
        org_id = str(uuid4())

        await manager.connect(websocket, org_id)

        # Verify connection was accepted and tracked
        websocket.accept.assert_called_once()
        assert org_id in manager.active_connections
        assert websocket in manager.active_connections[org_id]
        assert websocket in manager.all_connections

    @pytest.mark.asyncio
    async def test_connect_multiple_clients_same_org(self):
        """Test multiple clients connecting to same organization."""
        manager = ConnectionManager()
        org_id = str(uuid4())
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await manager.connect(ws1, org_id)
        await manager.connect(ws2, org_id)
        await manager.connect(ws3, org_id)

        assert len(manager.active_connections[org_id]) == 3
        assert len(manager.all_connections) == 3

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self):
        """Test disconnecting a client."""
        manager = ConnectionManager()
        org_id = str(uuid4())
        websocket = AsyncMock()

        await manager.connect(websocket, org_id)
        assert len(manager.all_connections) == 1

        await manager.disconnect(websocket, org_id)
        assert len(manager.all_connections) == 0
        assert org_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_cleans_up_empty_org(self):
        """Test that empty organization groups are cleaned up."""
        manager = ConnectionManager()
        org_id = str(uuid4())
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1, org_id)
        await manager.connect(ws2, org_id)

        await manager.disconnect(ws1, org_id)
        assert org_id in manager.active_connections  # Still has ws2

        await manager.disconnect(ws2, org_id)
        assert org_id not in manager.active_connections  # Now empty

    @pytest.mark.asyncio
    async def test_broadcast_to_organization(self):
        """Test broadcasting message to organization."""
        manager = ConnectionManager()
        org_id = str(uuid4())
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1, org_id)
        await manager.connect(ws2, org_id)

        message = {"type": "test", "data": "test_data"}
        await manager.broadcast_to_organization(org_id, message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_skips_disconnected_clients(self):
        """Test that broadcast handles disconnected clients."""
        manager = ConnectionManager()
        org_id = str(uuid4())
        ws_good = AsyncMock()
        ws_bad = AsyncMock()

        # Make ws_bad fail on send
        ws_bad.send_json.side_effect = Exception("Connection lost")

        await manager.connect(ws_good, org_id)
        await manager.connect(ws_bad, org_id)

        message = {"type": "test", "data": "test_data"}
        await manager.broadcast_to_organization(org_id, message)

        # Both were called, but bad one should be removed
        ws_good.send_json.assert_called_once_with(message)
        ws_bad.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self):
        """Test broadcasting to all organizations."""
        manager = ConnectionManager()
        org1 = str(uuid4())
        org2 = str(uuid4())
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await manager.connect(ws1, org1)
        await manager.connect(ws2, org1)
        await manager.connect(ws3, org2)

        message = {"type": "test", "data": "global"}
        await manager.broadcast_to_all(message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
        ws3.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_connection(self):
        """Test sending message to specific connection."""
        manager = ConnectionManager()
        websocket = AsyncMock()

        message = {"type": "test"}
        result = await manager.send_to_connection(websocket, message)

        assert result is True
        websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_connection_handles_failure(self):
        """Test sending to connection handles failures."""
        manager = ConnectionManager()
        websocket = AsyncMock()
        websocket.send_json.side_effect = Exception("Send failed")

        message = {"type": "test"}
        result = await manager.send_to_connection(websocket, message)

        assert result is False

    def test_get_organization_connection_count(self):
        """Test getting connection count for organization."""
        manager = ConnectionManager()
        org_id = str(uuid4())

        # Create mock connections (don't actually connect)
        ws1, ws2, ws3 = AsyncMock(), AsyncMock(), AsyncMock()
        manager.active_connections[org_id] = {ws1, ws2, ws3}

        assert manager.get_organization_connection_count(org_id) == 3
        assert manager.get_organization_connection_count(str(uuid4())) == 0

    def test_get_total_connection_count(self):
        """Test getting total connection count."""
        manager = ConnectionManager()

        ws1, ws2, ws3 = AsyncMock(), AsyncMock(), AsyncMock()
        manager.all_connections = {ws1, ws2, ws3}

        assert manager.get_total_connection_count() == 3

    def test_get_organizations_with_connections(self):
        """Test getting list of organizations with active connections."""
        manager = ConnectionManager()
        org1, org2, org3 = str(uuid4()), str(uuid4()), str(uuid4())

        ws = AsyncMock()
        manager.active_connections[org1] = {ws}
        manager.active_connections[org2] = {ws}
        manager.active_connections[org3] = {ws}

        orgs = manager.get_organizations_with_connections()
        assert len(orgs) == 3
        assert org1 in orgs
        assert org2 in orgs
        assert org3 in orgs


class TestMessageFormatting:
    """Tests for WebSocket message formatting."""

    def test_format_ws_message_basic(self):
        """Test formatting basic WebSocket message."""
        message = format_ws_message(
            message_type="test",
            data={"key": "value"}
        )

        assert message["type"] == "test"
        assert message["data"] == {"key": "value"}
        assert "timestamp" in message
        assert message["organization_id"] is None
        assert message["job_id"] is None

    def test_format_ws_message_with_ids(self):
        """Test formatting message with organization and job IDs."""
        org_id = uuid4()
        job_id = uuid4()

        message = format_ws_message(
            message_type="metric",
            data={"processed": 100},
            organization_id=org_id,
            job_id=job_id
        )

        assert message["type"] == "metric"
        assert message["organization_id"] == str(org_id)
        assert message["job_id"] == str(job_id)
        assert message["data"]["processed"] == 100

    def test_format_ws_message_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        message = format_ws_message("test", {})

        timestamp = message["timestamp"]
        # Should be valid ISO format
        assert "T" in timestamp
        assert timestamp.endswith("Z") or "+" in timestamp or timestamp.endswith("+00:00")


class TestRealtimeEventBroadcaster:
    """Tests for real-time event broadcaster."""

    @pytest.mark.asyncio
    async def test_emit_job_started(self):
        """Test emitting job started event."""
        job_id = uuid4()
        org_id = uuid4()

        with patch('backend.monitoring.realtime.manager') as mock_manager:
            await RealtimeEventBroadcaster.emit_job_started(
                job_id, org_id, "xero"
            )

            mock_manager.broadcast_to_organization.assert_called_once()
            call_args = mock_manager.broadcast_to_organization.call_args
            assert call_args[0][0] == str(org_id)
            assert call_args[0][1]["type"] == "job_started"
            assert call_args[0][1]["data"]["platform"] == "xero"

    @pytest.mark.asyncio
    async def test_emit_metric_update(self):
        """Test emitting metric update event."""
        job_id = uuid4()
        org_id = uuid4()
        metric_data = {"transactions": 100, "rate": 50.5}

        with patch('backend.monitoring.realtime.manager') as mock_manager:
            await RealtimeEventBroadcaster.emit_metric_update(
                job_id, org_id, metric_data
            )

            mock_manager.broadcast_to_organization.assert_called_once()
            call_args = mock_manager.broadcast_to_organization.call_args
            assert call_args[0][1]["type"] == "metric_update"
            assert call_args[0][1]["data"]["transactions"] == 100

    @pytest.mark.asyncio
    async def test_emit_transaction_count(self):
        """Test emitting transaction count event."""
        job_id = uuid4()
        org_id = uuid4()
        count_data = {"total": 500, "failed": 10}

        with patch('backend.monitoring.realtime.manager') as mock_manager:
            await RealtimeEventBroadcaster.emit_transaction_count(
                job_id, org_id, count_data
            )

            mock_manager.broadcast_to_organization.assert_called_once()
            call_args = mock_manager.broadcast_to_organization.call_args
            assert call_args[0][1]["type"] == "transaction_count"

    @pytest.mark.asyncio
    async def test_emit_error(self):
        """Test emitting error event."""
        job_id = uuid4()
        org_id = uuid4()
        error_data = {"message": "API error"}

        with patch('backend.monitoring.realtime.manager') as mock_manager:
            await RealtimeEventBroadcaster.emit_error(
                job_id, org_id, error_data
            )

            mock_manager.broadcast_to_organization.assert_called_once()
            call_args = mock_manager.broadcast_to_organization.call_args
            assert call_args[0][1]["type"] == "error"
            assert call_args[0][1]["data"]["severity"] == "error"

    @pytest.mark.asyncio
    async def test_emit_job_completed_success(self):
        """Test emitting job completed event (success)."""
        job_id = uuid4()
        org_id = uuid4()
        result_data = {"processed": 1000}

        with patch('backend.monitoring.realtime.manager') as mock_manager:
            await RealtimeEventBroadcaster.emit_job_completed(
                job_id, org_id, result_data, success=True
            )

            call_args = mock_manager.broadcast_to_organization.call_args
            assert call_args[0][1]["type"] == "job_completed"

    @pytest.mark.asyncio
    async def test_emit_job_completed_failure(self):
        """Test emitting job completed event (failure)."""
        job_id = uuid4()
        org_id = uuid4()
        result_data = {"error": "sync failed"}

        with patch('backend.monitoring.realtime.manager') as mock_manager:
            await RealtimeEventBroadcaster.emit_job_completed(
                job_id, org_id, result_data, success=False
            )

            call_args = mock_manager.broadcast_to_organization.call_args
            assert call_args[0][1]["type"] == "job_failed"

    @pytest.mark.asyncio
    async def test_emit_custom_event(self):
        """Test emitting custom event."""
        org_id = uuid4()

        with patch('backend.monitoring.realtime.manager') as mock_manager:
            await RealtimeEventBroadcaster.emit_custom_event(
                "custom_event", org_id, {"key": "value"}
            )

            call_args = mock_manager.broadcast_to_organization.call_args
            assert call_args[0][1]["type"] == "custom_event"

    def test_get_connection_stats(self):
        """Test getting connection statistics."""
        with patch('backend.monitoring.realtime.manager') as mock_manager:
            mock_manager.get_total_connection_count.return_value = 5
            mock_manager.get_organizations_with_connections.return_value = ["org1", "org2"]
            mock_manager.get_organization_connection_count.side_effect = [3, 2]

            stats = RealtimeEventBroadcaster.get_connection_stats()

            assert stats["total_connections"] == 5
            assert stats["organizations_connected"] == 2
            assert "organization_breakdown" in stats

    @pytest.mark.asyncio
    async def test_broadcast_job_status_started(self):
        """Test broadcast_job_status helper for started status."""
        job_id = uuid4()
        org_id = uuid4()

        with patch('backend.monitoring.realtime.RealtimeEventBroadcaster.emit_job_started') as mock_emit:
            from backend.monitoring.realtime import broadcast_job_status
            await broadcast_job_status(job_id, org_id, "started", platform="xero")

            mock_emit.assert_called_once_with(job_id, org_id, "xero")

    @pytest.mark.asyncio
    async def test_broadcast_job_status_completed(self):
        """Test broadcast_job_status helper for completed status."""
        job_id = uuid4()
        org_id = uuid4()

        with patch('backend.monitoring.realtime.RealtimeEventBroadcaster.emit_job_completed') as mock_emit:
            from backend.monitoring.realtime import broadcast_job_status
            await broadcast_job_status(job_id, org_id, "completed", result="success")

            mock_emit.assert_called_once()
