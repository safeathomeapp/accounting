"""Account reconciliation engine with discrepancy detection."""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


@dataclass
class DiscrepancyItem:
    """A potential discrepancy in reconciliation."""

    id: UUID = field(default_factory=uuid4)
    discrepancy_type: str = ""  # duplicate, round_trip, unusual_amount, timing
    description: str = ""
    items: List[str] = field(default_factory=list)  # Transaction IDs involved
    amount: Decimal = Decimal("0.00")
    confidence: float = 0.5  # 0.0-1.0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "type": self.discrepancy_type,
            "description": self.description,
            "items": self.items,
            "amount": float(self.amount),
            "confidence": round(self.confidence, 3),
        }


@dataclass
class ReconciliationStatus:
    """Status of account reconciliation."""

    account_id: UUID
    reconciliation_date: date
    system_balance: Decimal = Decimal("0.00")
    reconciled_balance: Decimal = Decimal("0.00")
    variance: Decimal = Decimal("0.00")
    is_reconciled: bool = False
    cleared_transaction_count: int = 0
    total_transaction_count: int = 0
    discrepancies: List[DiscrepancyItem] = field(default_factory=list)
    last_reconciled_at: Optional[datetime] = None
    reconciled_by: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "account_id": str(self.account_id),
            "reconciliation_date": self.reconciliation_date.isoformat(),
            "system_balance": float(self.system_balance),
            "reconciled_balance": float(self.reconciled_balance),
            "variance": float(self.variance),
            "is_reconciled": self.is_reconciled,
            "cleared_transaction_count": self.cleared_transaction_count,
            "total_transaction_count": self.total_transaction_count,
            "discrepancy_count": len(self.discrepancies),
            "discrepancies": [d.to_dict() for d in self.discrepancies],
            "last_reconciled_at": (
                self.last_reconciled_at.isoformat() if self.last_reconciled_at else None
            ),
            "reconciled_by": self.reconciled_by,
        }


class ReconciliationEngine:
    """Engine for account reconciliation and discrepancy detection."""

    def __init__(self):
        """Initialize reconciliation engine."""
        self.transaction_cache: Dict[str, Dict] = {}
        self.reconciliation_history: List[ReconciliationStatus] = []

    def add_transaction(
        self,
        transaction_id: str,
        amount: Decimal,
        date_posted: date,
        description: str,
    ) -> None:
        """
        Add a transaction to the cache.

        Args:
            transaction_id: Unique transaction ID
            amount: Transaction amount
            date_posted: Date transaction posted
            description: Transaction description
        """
        self.transaction_cache[transaction_id] = {
            "id": transaction_id,
            "amount": amount,
            "date": date_posted,
            "description": description,
            "cleared": False,
        }

    def calculate_system_balance(
        self,
        start_balance: Decimal = Decimal("0.00"),
    ) -> Decimal:
        """
        Calculate system balance from all transactions.

        Args:
            start_balance: Starting balance

        Returns:
            Calculated balance
        """
        balance = start_balance
        for txn in self.transaction_cache.values():
            balance += txn["amount"]
        return balance

    def reconcile_account(
        self,
        account_id: UUID,
        reconciliation_date: date,
        bank_balance: Decimal,
        cleared_transaction_ids: Optional[List[str]] = None,
        reconciled_by: Optional[str] = None,
    ) -> ReconciliationStatus:
        """
        Reconcile an account by matching cleared transactions.

        Algorithm:
        1. Calculate system balance (all transactions)
        2. Calculate reconciled balance (cleared transactions)
        3. Compare to bank balance
        4. Flag variances as discrepancies
        5. Detect other discrepancies (duplicates, round-trips, etc.)

        Args:
            account_id: Account UUID
            reconciliation_date: Date of reconciliation
            bank_balance: Balance per bank statement
            cleared_transaction_ids: List of transaction IDs that cleared
            reconciled_by: User performing reconciliation

        Returns:
            ReconciliationStatus with full reconciliation details
        """
        if cleared_transaction_ids is None:
            cleared_transaction_ids = []

        logger.info(
            f"Reconciling account {account_id} as of {reconciliation_date}, "
            f"bank balance: {bank_balance}"
        )

        # Calculate system balance
        system_balance = self.calculate_system_balance()

        # Calculate reconciled balance (cleared transactions only)
        reconciled_balance = Decimal("0.00")
        for txn_id in cleared_transaction_ids:
            if txn_id in self.transaction_cache:
                reconciled_balance += self.transaction_cache[txn_id]["amount"]
                self.transaction_cache[txn_id]["cleared"] = True

        # Calculate variance
        variance = bank_balance - reconciled_balance

        # Create status
        status = ReconciliationStatus(
            account_id=account_id,
            reconciliation_date=reconciliation_date,
            system_balance=system_balance,
            reconciled_balance=reconciled_balance,
            variance=variance,
            is_reconciled=(variance == Decimal("0.00")),
            cleared_transaction_count=len(cleared_transaction_ids),
            total_transaction_count=len(self.transaction_cache),
            last_reconciled_at=datetime.now(timezone.utc),
            reconciled_by=reconciled_by,
        )

        # Detect discrepancies
        status.discrepancies = self.detect_discrepancies()

        # Save to history
        self.reconciliation_history.append(status)

        logger.info(
            f"Reconciliation complete: variance={variance}, "
            f"is_reconciled={status.is_reconciled}"
        )

        return status

    def detect_discrepancies(self) -> List[DiscrepancyItem]:
        """
        Detect potential discrepancies in transactions.

        Finds:
        - Duplicate amounts on same day
        - Round-trip transactions (matching debit/credit pairs)
        - Unusual amounts (very large or very small)
        - Timing issues (future-dated transactions)

        Returns:
            List of DiscrepancyItem
        """
        discrepancies: List[DiscrepancyItem] = []

        # Check for duplicate amounts
        amount_map: Dict[Decimal, List[str]] = {}
        for txn_id, txn in self.transaction_cache.items():
            amount = abs(txn["amount"])
            if amount not in amount_map:
                amount_map[amount] = []
            amount_map[amount].append(txn_id)

        for amount, txn_ids in amount_map.items():
            if len(txn_ids) >= 2:
                # Check if they're on the same date
                dates = [self.transaction_cache[tid]["date"] for tid in txn_ids]
                if all(d == dates[0] for d in dates):
                    discrepancies.append(
                        DiscrepancyItem(
                            discrepancy_type="duplicate",
                            description=f"Found {len(txn_ids)} transactions with same amount on {dates[0]}",
                            items=txn_ids,
                            amount=amount,
                            confidence=0.8,
                        )
                    )

        # Check for round-trip transactions (matching +/- pairs)
        txn_list = list(self.transaction_cache.items())
        for i, (id1, txn1) in enumerate(txn_list):
            for id2, txn2 in txn_list[i + 1 :]:
                # Check if amounts cancel out
                if (
                    txn1["amount"] + txn2["amount"] == Decimal("0.00")
                    and abs((txn1["date"] - txn2["date"]).days) <= 3
                ):
                    discrepancies.append(
                        DiscrepancyItem(
                            discrepancy_type="round_trip",
                            description=f"Found matching debit/credit pair: {txn1['description']} / {txn2['description']}",
                            items=[id1, id2],
                            amount=txn1["amount"],
                            confidence=0.7,
                        )
                    )

        # Check for unusual amounts (very large or very small)
        if self.transaction_cache:
            amounts = [abs(t["amount"]) for t in self.transaction_cache.values()]
            avg_amount = sum(amounts) / len(amounts) if amounts else Decimal("0")

            for txn_id, txn in self.transaction_cache.items():
                abs_amount = abs(txn["amount"])
                if avg_amount > 0 and abs_amount > avg_amount * Decimal("2.5"):
                    discrepancies.append(
                        DiscrepancyItem(
                            discrepancy_type="unusual_amount",
                            description=f"Unusually large amount: {abs_amount} (avg: {avg_amount})",
                            items=[txn_id],
                            amount=abs_amount,
                            confidence=0.6,
                        )
                    )

        # Check for future-dated transactions
        for txn_id, txn in self.transaction_cache.items():
            if txn["date"] > date.today():
                discrepancies.append(
                    DiscrepancyItem(
                        discrepancy_type="timing",
                        description=f"Future-dated transaction: {txn['date']}",
                        items=[txn_id],
                        amount=txn["amount"],
                        confidence=0.9,
                    )
                )

        # Remove duplicate discrepancies (by items)
        unique_discrepancies = []
        seen_items = set()
        for disc in discrepancies:
            items_key = tuple(sorted(disc.items))
            if items_key not in seen_items:
                unique_discrepancies.append(disc)
                seen_items.add(items_key)

        logger.info(f"Detected {len(unique_discrepancies)} discrepancies")
        return unique_discrepancies

    def bank_reconciliation(
        self,
        account_id: UUID,
        bank_statement: List[Dict],
        reconciliation_date: date,
        date_variance_days: int = 3,
        amount_variance: Decimal = Decimal("0.01"),
    ) -> ReconciliationStatus:
        """
        Match bank statement to account transactions with fuzzy matching.

        Uses three-level matching:
        1. Exact match (date + amount)
        2. Date variance ±N days
        3. Amount variance ±$X

        Args:
            account_id: Account UUID
            bank_statement: List of dicts with date, amount, description
            reconciliation_date: Date of reconciliation
            date_variance_days: Allow date variance (default 3 days)
            amount_variance: Allow amount variance (default $0.01)

        Returns:
            ReconciliationStatus with bank-matched reconciliation
        """
        logger.info(
            f"Performing bank reconciliation for {account_id} with "
            f"{len(bank_statement)} statement items"
        )

        matched_txn_ids = []
        unmatched_items = []

        for stmt_item in bank_statement:
            stmt_date = stmt_item.get("date")
            stmt_amount = Decimal(str(stmt_item.get("amount", 0)))
            stmt_desc = stmt_item.get("description", "")

            matched = False

            # Try exact match first
            for txn_id, txn in self.transaction_cache.items():
                if (
                    txn["date"] == stmt_date
                    and txn["amount"] == stmt_amount
                    and txn_id not in matched_txn_ids
                ):
                    matched_txn_ids.append(txn_id)
                    matched = True
                    logger.debug(f"Exact match: {txn_id}")
                    break

            # Try date variance
            if not matched:
                for txn_id, txn in self.transaction_cache.items():
                    if txn_id in matched_txn_ids:
                        continue
                    date_diff = abs((txn["date"] - stmt_date).days)
                    if (
                        date_diff <= date_variance_days
                        and txn["amount"] == stmt_amount
                    ):
                        matched_txn_ids.append(txn_id)
                        matched = True
                        logger.debug(
                            f"Date variance match: {txn_id} ({date_diff} days)"
                        )
                        break

            # Try amount variance
            if not matched:
                for txn_id, txn in self.transaction_cache.items():
                    if txn_id in matched_txn_ids:
                        continue
                    amount_diff = abs(txn["amount"] - stmt_amount)
                    if (
                        date_diff <= date_variance_days
                        and amount_diff <= amount_variance
                    ):
                        matched_txn_ids.append(txn_id)
                        matched = True
                        logger.debug(
                            f"Amount variance match: {txn_id} (${amount_diff})"
                        )
                        break

            if not matched:
                unmatched_items.append(stmt_item)
                logger.warning(f"Unmatched statement item: {stmt_amount} on {stmt_date}")

        # Calculate bank balance from statement
        bank_balance = sum(
            Decimal(str(item.get("amount", 0))) for item in bank_statement
        )

        # Perform reconciliation with matched transactions
        status = self.reconcile_account(
            account_id,
            reconciliation_date,
            bank_balance,
            cleared_transaction_ids=matched_txn_ids,
            reconciled_by="bank_reconciliation",
        )

        # Add info about unmatched items
        if unmatched_items:
            status.discrepancies.append(
                DiscrepancyItem(
                    discrepancy_type="unmatched",
                    description=f"Found {len(unmatched_items)} unmatched bank statement items",
                    items=[],
                    amount=Decimal("0.00"),
                    confidence=1.0,
                )
            )

        logger.info(
            f"Bank reconciliation complete: matched {len(matched_txn_ids)} "
            f"of {len(self.transaction_cache)} transactions, "
            f"{len(unmatched_items)} unmatched statement items"
        )

        return status

    def get_uncleared_transactions(self) -> List[Dict]:
        """
        Get list of uncleared transactions.

        Returns:
            List of uncleared transaction details
        """
        uncleared = []
        for txn_id, txn in self.transaction_cache.items():
            if not txn.get("cleared", False):
                uncleared.append({
                    "id": txn_id,
                    "amount": float(txn["amount"]),
                    "date": txn["date"].isoformat(),
                    "description": txn["description"],
                })
        return uncleared

    def get_reconciliation_report(self) -> Dict:
        """
        Get summary reconciliation report.

        Returns:
            Dictionary with reconciliation statistics
        """
        if not self.reconciliation_history:
            return {"status": "no_reconciliations", "total_reconciliations": 0}

        last_reconciliation = self.reconciliation_history[-1]

        return {
            "last_reconciliation_date": last_reconciliation.last_reconciled_at.isoformat()
            if last_reconciliation.last_reconciled_at
            else None,
            "is_reconciled": last_reconciliation.is_reconciled,
            "variance": float(last_reconciliation.variance),
            "system_balance": float(last_reconciliation.system_balance),
            "reconciled_balance": float(last_reconciliation.reconciled_balance),
            "total_reconciliations": len(self.reconciliation_history),
            "uncleared_count": (
                last_reconciliation.total_transaction_count
                - last_reconciliation.cleared_transaction_count
            ),
            "discrepancy_count": len(last_reconciliation.discrepancies),
        }
