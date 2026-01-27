"""
SQLAlchemy event listeners for auto-generating facts on transaction changes.

Listens for after_insert and after_update events on the Transaction model.
This avoids modifying existing sync handler code - facts are generated
as a side effect of any transaction being written.

Usage (register once at app startup):
    from backend.canonical.listeners import register_canonical_listeners
    register_canonical_listeners()
"""

import logging
from sqlalchemy import event
from sqlalchemy.orm import Session

from backend.models.transaction import Transaction
from backend.canonical.models import CashflowFact, IngestionQuarantine

logger = logging.getLogger(__name__)

_engine = None


def _get_engine(session: Session):
    """Lazy-load and cache a MappingEngine instance."""
    global _engine
    if _engine is None:
        from backend.canonical.engine import MappingEngine
        _engine = MappingEngine(session)
        _engine.load_mappings()
    else:
        # Re-bind to current session
        _engine.db = session
    return _engine


def _on_transaction_after_insert(mapper, connection, target):
    """Generate a fact row when a new transaction is inserted."""
    try:
        session = Session.object_session(target)
        if session is None:
            return

        engine = _get_engine(session)
        fact = engine.map_transaction(target)
        if fact:
            session.add(fact)
            logger.debug(f"Auto-generated fact for new transaction {target.id}")
    except Exception as e:
        logger.warning(f"Failed to auto-generate fact for transaction {target.id}: {e}")


def _on_transaction_after_update(mapper, connection, target):
    """Re-generate fact when a transaction is updated (type/status may have changed)."""
    try:
        session = Session.object_session(target)
        if session is None:
            return

        # Delete existing fact for this transaction
        session.query(CashflowFact).filter_by(transaction_id=target.id).delete()

        # Delete unresolved quarantine entry
        session.query(IngestionQuarantine).filter(
            IngestionQuarantine.transaction_id == target.id,
            IngestionQuarantine.resolved_at == None,
        ).delete()

        engine = _get_engine(session)
        fact = engine.map_transaction(target)
        if fact:
            session.add(fact)
            logger.debug(f"Re-generated fact for updated transaction {target.id}")
    except Exception as e:
        logger.warning(f"Failed to re-generate fact for transaction {target.id}: {e}")


def register_canonical_listeners():
    """Register SQLAlchemy event listeners. Call once at app startup."""
    event.listen(Transaction, "after_insert", _on_transaction_after_insert)
    event.listen(Transaction, "after_update", _on_transaction_after_update)
    logger.info("Canonical fact listeners registered on Transaction model")


def unregister_canonical_listeners():
    """Remove listeners (useful for testing)."""
    event.remove(Transaction, "after_insert", _on_transaction_after_insert)
    event.remove(Transaction, "after_update", _on_transaction_after_update)
    logger.info("Canonical fact listeners removed")
