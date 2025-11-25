"""Real-time monitoring and dashboard module.

Provides live sync monitoring, metrics collection, and WebSocket-based
real-time updates for dashboard applications.

Components:
- Models: Database models for monitoring data
- Collector: Metrics collection from sync operations
- WebSocket: Real-time connection management and broadcasting
- Realtime: Real-time event emission system
"""

from .models import SyncJobMetric, DashboardEvent, ErrorLog, EventType, ErrorSeverity
from .collector import MetricsCollector
from .websocket import ConnectionManager, format_ws_message, manager
from .realtime import RealtimeEventBroadcaster, broadcast_job_status

__all__ = [
    # Models
    "SyncJobMetric",
    "DashboardEvent",
    "ErrorLog",
    "EventType",
    "ErrorSeverity",
    # Collector
    "MetricsCollector",
    # WebSocket
    "ConnectionManager",
    "format_ws_message",
    "manager",
    # Realtime Broadcasting
    "RealtimeEventBroadcaster",
    "broadcast_job_status",
]
