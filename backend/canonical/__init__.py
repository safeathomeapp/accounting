"""
Canonical Data Mapping Layer.

Provides normalized transaction classification and cashflow fact generation.
This is Layer 2 of the data architecture:

  Layer 1: Platform APIs -> Mappers -> transactions table (raw data)
  Layer 2: transactions -> MappingEngine -> cashflow_facts_v1 (canonical truth)
  Layer 3: cashflow_facts_v1 -> Reports / Analytics / AI
"""

from backend.canonical.models import (
    NormalizedTxnType,
    NormalizedTxnStatus,
    CashflowBucket,
    DateSource,
    PlatformTransactionMapping,
    CashflowFact,
    IngestionQuarantine,
)
from backend.canonical.engine import MappingEngine

__all__ = [
    "NormalizedTxnType",
    "NormalizedTxnStatus",
    "CashflowBucket",
    "DateSource",
    "PlatformTransactionMapping",
    "CashflowFact",
    "IngestionQuarantine",
    "MappingEngine",
]
