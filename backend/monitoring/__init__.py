"""Real-time monitoring and dashboard module.

Provides live sync monitoring, metrics collection, and WebSocket-based
real-time updates for dashboard applications.

Components:
- Models: Database models for monitoring data
- Collector: Metrics collection from sync operations
- WebSocket: Real-time updates via WebSocket
- Dashboard: Aggregated dashboard data
"""

from .models import SyncJobMetric, DashboardEvent, ErrorLog, EventType, ErrorSeverity
from .collector import MetricsCollector

__all__ = [
    "SyncJobMetric",
    "DashboardEvent",
    "ErrorLog",
    "EventType",
    "ErrorSeverity",
    "MetricsCollector",
]
