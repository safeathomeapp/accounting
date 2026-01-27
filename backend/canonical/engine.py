"""MappingEngine - applies platform transaction mappings to produce canonical facts."""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.models import Transaction
from backend.canonical.models import (
    PlatformTransactionMapping,
    CashflowFact,
    IngestionQuarantine,
    CashflowBucket,
    DateSource,
)

logger = logging.getLogger(__name__)


class MappingEngine:
    """
    Core engine that maps raw transactions to canonical cashflow facts.

    Usage:
        engine = MappingEngine(db)
        engine.load_mappings()
        engine.process_all(org_id=some_uuid)
    """

    def __init__(self, db: Session):
        self.db = db
        self._cache: Dict[Tuple[str, str, str], PlatformTransactionMapping] = {}

    def load_mappings(self) -> int:
        """Load all active mappings into memory cache.

        Returns:
            Number of mappings loaded.
        """
        mappings = (
            self.db.query(PlatformTransactionMapping)
            .filter(PlatformTransactionMapping.is_active == True)
            .order_by(PlatformTransactionMapping.priority.desc())
            .all()
        )

        self._cache.clear()
        for m in mappings:
            key = (m.platform_name.lower(), m.source_type.lower(), m.source_status.lower())
            # Higher priority wins (first match due to desc order)
            if key not in self._cache:
                self._cache[key] = m

        logger.info(f"Loaded {len(self._cache)} active mappings into cache")
        return len(self._cache)

    def lookup_mapping(self, platform_name: str, source_type: str,
                       source_status: str) -> Optional[PlatformTransactionMapping]:
        """Find the mapping for a given platform/type/status combo."""
        key = (platform_name.lower(), source_type.lower(), source_status.lower())
        return self._cache.get(key)

    def compute_signed_amount(self, total_amount: Decimal,
                              bucket: CashflowBucket) -> Decimal:
        """Compute signed amount based on bucket.

        AR/CASH_IN = positive (money coming in)
        AP/CASH_OUT = negative (money going out)
        NON_CASH/IGNORE = zero
        """
        if bucket in (CashflowBucket.AR_CURRENT, CashflowBucket.AR_OVERDUE,
                       CashflowBucket.CASH_IN):
            return abs(total_amount)
        elif bucket in (CashflowBucket.AP_CURRENT, CashflowBucket.AP_OVERDUE,
                         CashflowBucket.CASH_OUT):
            return -abs(total_amount)
        elif bucket in (CashflowBucket.NON_CASH, CashflowBucket.IGNORE):
            return Decimal("0.00")
        return total_amount

    def compute_effective_date(self, txn: Transaction,
                               date_source: DateSource) -> date:
        """Choose effective date based on mapping preference."""
        if date_source == DateSource.DUE_DATE and txn.due_date:
            return txn.due_date
        return txn.transaction_date

    def map_transaction(self, txn: Transaction) -> Optional[CashflowFact]:
        """Map a single transaction to a CashflowFact, or quarantine it.

        Returns:
            CashflowFact if mapped successfully, None if quarantined.
        """
        platform = txn.platform_name or ""
        txn_type = txn.transaction_type or ""
        status = txn.status or ""

        mapping = self.lookup_mapping(platform, txn_type, status)

        if mapping is None:
            self._quarantine_transaction(txn, platform, txn_type, status)
            return None

        effective_dt = self.compute_effective_date(txn, mapping.effective_date_source)
        signed_amt = self.compute_signed_amount(txn.total_amount, mapping.canonical_bucket)

        fact = CashflowFact(
            transaction_id=txn.id,
            mapping_id=mapping.id,
            organization_id=txn.organization_id,
            client_id=txn.client_id,
            normalized_type=mapping.normalized_type,
            normalized_status=mapping.normalized_status,
            canonical_bucket=mapping.canonical_bucket,
            effective_date=effective_dt,
            signed_amount=signed_amt,
            currency=txn.currency or "GBP",
            snapshot_date=date.today(),
        )
        return fact

    def _quarantine_transaction(self, txn: Transaction, platform: str,
                                txn_type: str, status: str) -> IngestionQuarantine:
        """Create a quarantine entry for an unmappable transaction."""
        # Check if already quarantined (unresolved)
        existing = (
            self.db.query(IngestionQuarantine)
            .filter(
                IngestionQuarantine.transaction_id == txn.id,
                IngestionQuarantine.resolved_at == None,
            )
            .first()
        )
        if existing:
            return existing

        entry = IngestionQuarantine(
            transaction_id=txn.id,
            organization_id=txn.organization_id,
            platform_name=platform,
            source_type=txn_type,
            source_status=status,
            reason=f"No mapping for ({platform}, {txn_type}, {status})",
        )
        self.db.add(entry)
        return entry

    def process_all(self, org_id=None, dry_run: bool = False) -> Dict:
        """Process all unmapped transactions into facts or quarantine.

        Args:
            org_id: Optional org UUID to limit scope.
            dry_run: If True, don't commit changes.

        Returns:
            Dict with counts: mapped, quarantined, skipped, errors.
        """
        if not self._cache:
            self.load_mappings()

        # Find transactions that don't yet have a fact row
        query = (
            self.db.query(Transaction)
            .outerjoin(CashflowFact, CashflowFact.transaction_id == Transaction.id)
            .filter(CashflowFact.id == None)
        )
        if org_id:
            query = query.filter(Transaction.organization_id == org_id)

        transactions = query.all()
        logger.info(f"Processing {len(transactions)} unmapped transactions")

        stats = {"mapped": 0, "quarantined": 0, "skipped": 0, "errors": 0, "total": len(transactions)}

        for txn in transactions:
            try:
                fact = self.map_transaction(txn)
                if fact:
                    self.db.add(fact)
                    stats["mapped"] += 1
                else:
                    stats["quarantined"] += 1
            except Exception as e:
                logger.error(f"Error processing transaction {txn.id}: {e}")
                stats["errors"] += 1

        if not dry_run:
            self.db.commit()
            logger.info(f"Processing complete: {stats}")
        else:
            self.db.rollback()
            logger.info(f"Dry run complete: {stats}")

        return stats

    def rebuild_facts(self, org_id=None) -> Dict:
        """Delete all facts (and unresolved quarantine) and regenerate.

        Args:
            org_id: Optional org UUID to limit scope.

        Returns:
            Dict with counts.
        """
        if not self._cache:
            self.load_mappings()

        # Delete existing facts
        fact_query = self.db.query(CashflowFact)
        quarantine_query = self.db.query(IngestionQuarantine).filter(
            IngestionQuarantine.resolved_at == None
        )

        if org_id:
            fact_query = fact_query.filter(CashflowFact.organization_id == org_id)
            quarantine_query = quarantine_query.filter(
                IngestionQuarantine.organization_id == org_id
            )

        deleted_facts = fact_query.delete(synchronize_session=False)
        deleted_quarantine = quarantine_query.delete(synchronize_session=False)
        self.db.commit()

        logger.info(f"Deleted {deleted_facts} facts and {deleted_quarantine} quarantine entries")

        # Rebuild
        stats = self.process_all(org_id=org_id)
        stats["deleted_facts"] = deleted_facts
        stats["deleted_quarantine"] = deleted_quarantine
        return stats

    def resolve_quarantine(self, quarantine_id, resolved_by: str = "system") -> Optional[CashflowFact]:
        """Re-attempt mapping for a quarantined transaction.

        Args:
            quarantine_id: UUID of the quarantine entry.
            resolved_by: Who resolved it (user ID or "system").

        Returns:
            CashflowFact if successfully mapped, None otherwise.
        """
        if not self._cache:
            self.load_mappings()

        entry = self.db.query(IngestionQuarantine).filter_by(id=quarantine_id).first()
        if not entry or entry.resolved_at:
            return None

        txn = self.db.query(Transaction).filter_by(id=entry.transaction_id).first()
        if not txn:
            return None

        fact = self.map_transaction(txn)
        if fact:
            # Mark quarantine as resolved
            entry.resolved_at = datetime.utcnow()
            entry.resolved_by = resolved_by
            self.db.add(fact)
            self.db.commit()
            logger.info(f"Resolved quarantine {quarantine_id} -> fact created")
            return fact

        return None

    def resolve_all_quarantine(self, org_id=None,
                               resolved_by: str = "system") -> Dict:
        """Attempt to resolve all unresolved quarantine entries.

        Returns:
            Dict with resolved and still_quarantined counts.
        """
        if not self._cache:
            self.load_mappings()

        query = self.db.query(IngestionQuarantine).filter(
            IngestionQuarantine.resolved_at == None
        )
        if org_id:
            query = query.filter(IngestionQuarantine.organization_id == org_id)

        entries = query.all()
        stats = {"resolved": 0, "still_quarantined": 0, "errors": 0}

        for entry in entries:
            try:
                txn = self.db.query(Transaction).filter_by(id=entry.transaction_id).first()
                if not txn:
                    stats["errors"] += 1
                    continue

                mapping = self.lookup_mapping(
                    entry.platform_name, entry.source_type, entry.source_status
                )
                if mapping:
                    effective_dt = self.compute_effective_date(txn, mapping.effective_date_source)
                    signed_amt = self.compute_signed_amount(txn.total_amount, mapping.canonical_bucket)

                    fact = CashflowFact(
                        transaction_id=txn.id,
                        mapping_id=mapping.id,
                        organization_id=txn.organization_id,
                        client_id=txn.client_id,
                        normalized_type=mapping.normalized_type,
                        normalized_status=mapping.normalized_status,
                        canonical_bucket=mapping.canonical_bucket,
                        effective_date=effective_dt,
                        signed_amount=signed_amt,
                        currency=txn.currency or "GBP",
                        snapshot_date=date.today(),
                    )
                    self.db.add(fact)
                    entry.resolved_at = datetime.utcnow()
                    entry.resolved_by = resolved_by
                    stats["resolved"] += 1
                else:
                    stats["still_quarantined"] += 1
            except Exception as e:
                logger.error(f"Error resolving quarantine {entry.id}: {e}")
                stats["errors"] += 1

        self.db.commit()
        logger.info(f"Batch resolve complete: {stats}")
        return stats
