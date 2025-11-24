"""Xero accounting adapter.

This module provides integration with Xero accounting software via OAuth 2.0
and the Xero API. It adapts Xero's data format to the standardized models
defined in the abstraction layer.

Classes:
    XeroClient: Main adapter implementing AccountingClient interface
"""

from .client import XeroClient

__all__ = ["XeroClient"]
