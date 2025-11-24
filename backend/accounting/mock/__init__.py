"""TEMPORARY: Mock accounting adapter.

WARNING: This entire module is FOR DEVELOPMENT ONLY.
         Remove the entire backend/accounting/mock/ directory before production.

This module provides a mock implementation of the AccountingClient interface
for testing, development, and demonstrations without requiring real API credentials.

Classes:
    MockClient: Mock adapter implementing AccountingClient interface
"""

from .client import MockClient

__all__ = ["MockClient"]
