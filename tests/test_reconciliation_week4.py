"""Tests for account reconciliation system."""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from backend.reporting.reconciliation import (
    DiscrepancyItem,
    ReconciliationStatus,
    ReconciliationEngine,
)


class TestDiscrepancyItem:
    """Tests for DiscrepancyItem model."""

    def test_discrepancy_initialization(self):
        """Test discrepancy initialization."""
        txn_ids = ["txn1", "txn2"]
        disc = DiscrepancyItem(
            discrepancy_type="duplicate",
            description="Found duplicate transactions",
            items=txn_ids,
            amount=Decimal("100.00"),
            confidence=0.85,
        )

        assert disc.discrepancy_type == "duplicate"
        assert disc.items == txn_ids
        assert disc.amount == Decimal("100.00")
        assert disc.confidence == 0.85

    def test_discrepancy_to_dict(self):
        """Test discrepancy serialization."""
        disc = DiscrepancyItem(
            discrepancy_type="duplicate",
            description="Test discrepancy",
            items=["txn1"],
            amount=Decimal("50.00"),
            confidence=0.7654321,
        )

        data = disc.to_dict()

        assert data["type"] == "duplicate"
        assert data["confidence"] == 0.765
        assert "created_at" not in data  # Not serialized


class TestReconciliationStatus:
    """Tests for ReconciliationStatus model."""

    def test_status_initialization(self):
        """Test reconciliation status initialization."""
        account_id = uuid4()
        recon_date = date(2025, 12, 31)

        status = ReconciliationStatus(
            account_id=account_id,
            reconciliation_date=recon_date,
            system_balance=Decimal("10000.00"),
            reconciled_balance=Decimal("10000.00"),
            variance=Decimal("0.00"),
            is_reconciled=True,
            cleared_transaction_count=15,
            total_transaction_count=20,
        )

        assert status.account_id == account_id
        assert status.is_reconciled is True
        assert status.variance == Decimal("0.00")

    def test_status_with_variance(self):
        """Test reconciliation status with variance."""
        status = ReconciliationStatus(
            account_id=uuid4(),
            reconciliation_date=date(2025, 12, 31),
            system_balance=Decimal("10000.00"),
            reconciled_balance=Decimal("9950.00"),
            variance=Decimal("50.00"),
            is_reconciled=False,
        )

        assert status.variance == Decimal("50.00")
        assert status.is_reconciled is False

    def test_status_to_dict(self):
        """Test status serialization."""
        account_id = uuid4()
        status = ReconciliationStatus(
            account_id=account_id,
            reconciliation_date=date(2025, 12, 31),
            system_balance=Decimal("10000.00"),
            variance=Decimal("100.00"),
            is_reconciled=False,
        )

        data = status.to_dict()

        assert data["account_id"] == str(account_id)
        assert data["variance"] == 100.0
        assert data["is_reconciled"] is False
        assert "discrepancy_count" in data


class TestReconciliationEngine:
    """Tests for reconciliation engine."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = ReconciliationEngine()

        assert len(engine.transaction_cache) == 0
        assert len(engine.reconciliation_history) == 0

    def test_add_transaction(self):
        """Test adding a transaction."""
        engine = ReconciliationEngine()

        engine.add_transaction(
            "txn1",
            Decimal("100.00"),
            date(2025, 12, 15),
            "Test transaction",
        )

        assert len(engine.transaction_cache) == 1
        assert "txn1" in engine.transaction_cache

    def test_calculate_system_balance_empty(self):
        """Test balance calculation with no transactions."""
        engine = ReconciliationEngine()

        balance = engine.calculate_system_balance()

        assert balance == Decimal("0.00")

    def test_calculate_system_balance_with_transactions(self):
        """Test balance calculation with transactions."""
        engine = ReconciliationEngine()

        engine.add_transaction("txn1", Decimal("100.00"), date(2025, 12, 15), "")
        engine.add_transaction("txn2", Decimal("-50.00"), date(2025, 12, 16), "")
        engine.add_transaction("txn3", Decimal("75.00"), date(2025, 12, 17), "")

        balance = engine.calculate_system_balance()

        assert balance == Decimal("125.00")

    def test_calculate_system_balance_with_starting_balance(self):
        """Test balance calculation with starting balance."""
        engine = ReconciliationEngine()

        engine.add_transaction("txn1", Decimal("100.00"), date(2025, 12, 15), "")

        balance = engine.calculate_system_balance(Decimal("1000.00"))

        assert balance == Decimal("1100.00")

    def test_reconcile_account_perfect_match(self):
        """Test reconciliation with perfect match."""
        engine = ReconciliationEngine()
        account_id = uuid4()

        engine.add_transaction("txn1", Decimal("100.00"), date(2025, 12, 15), "")
        engine.add_transaction("txn2", Decimal("50.00"), date(2025, 12, 16), "")

        status = engine.reconcile_account(
            account_id,
            date(2025, 12, 31),
            Decimal("150.00"),
            cleared_transaction_ids=["txn1", "txn2"],
        )

        assert status.is_reconciled is True
        assert status.variance == Decimal("0.00")
        assert status.system_balance == Decimal("150.00")

    def test_reconcile_account_with_variance(self):
        """Test reconciliation with variance."""
        engine = ReconciliationEngine()
        account_id = uuid4()

        engine.add_transaction("txn1", Decimal("100.00"), date(2025, 12, 15), "")
        engine.add_transaction("txn2", Decimal("75.00"), date(2025, 12, 16), "")

        status = engine.reconcile_account(
            account_id,
            date(2025, 12, 31),
            Decimal("150.00"),  # Bank says 150, but cleared is 100+75=175
            cleared_transaction_ids=["txn1", "txn2"],
        )

        assert status.is_reconciled is False
        assert status.variance == Decimal("-25.00")

    def test_reconcile_account_partial_cleared(self):
        """Test reconciliation with only some transactions cleared."""
        engine = ReconciliationEngine()
        account_id = uuid4()

        engine.add_transaction("txn1", Decimal("100.00"), date(2025, 12, 15), "")
        engine.add_transaction("txn2", Decimal("50.00"), date(2025, 12, 16), "")
        engine.add_transaction("txn3", Decimal("30.00"), date(2025, 12, 17), "")

        status = engine.reconcile_account(
            account_id,
            date(2025, 12, 31),
            Decimal("100.00"),  # Only first transaction cleared
            cleared_transaction_ids=["txn1"],
        )

        assert status.cleared_transaction_count == 1
        assert status.total_transaction_count == 3
        assert status.reconciled_balance == Decimal("100.00")

    def test_detect_duplicates(self):
        """Test duplicate transaction detection."""
        engine = ReconciliationEngine()

        today = date.today()
        engine.add_transaction("txn1", Decimal("100.00"), today, "Flight booking")
        engine.add_transaction("txn2", Decimal("100.00"), today, "Flight booking")

        discrepancies = engine.detect_discrepancies()

        duplicates = [d for d in discrepancies if d.discrepancy_type == "duplicate"]
        assert len(duplicates) > 0

    def test_detect_round_trip(self):
        """Test round-trip transaction detection."""
        engine = ReconciliationEngine()

        today = date.today()
        engine.add_transaction("txn1", Decimal("100.00"), today, "Debit")
        engine.add_transaction("txn2", Decimal("-100.00"), today + timedelta(days=1), "Credit")

        discrepancies = engine.detect_discrepancies()

        round_trips = [d for d in discrepancies if d.discrepancy_type == "round_trip"]
        assert len(round_trips) > 0

    def test_detect_unusual_amounts(self):
        """Test unusual amount detection."""
        engine = ReconciliationEngine()

        today = date.today()
        engine.add_transaction("txn1", Decimal("1.00"), today, "Normal")
        engine.add_transaction("txn2", Decimal("2.00"), today, "Normal")
        engine.add_transaction("txn3", Decimal("500.00"), today, "Unusual")

        discrepancies = engine.detect_discrepancies()

        unusual = [d for d in discrepancies if d.discrepancy_type == "unusual_amount"]
        assert len(unusual) > 0

    def test_detect_future_dated(self):
        """Test future-dated transaction detection."""
        engine = ReconciliationEngine()

        future_date = date.today() + timedelta(days=10)
        engine.add_transaction("txn1", Decimal("100.00"), future_date, "Future")

        discrepancies = engine.detect_discrepancies()

        future_dated = [d for d in discrepancies if d.discrepancy_type == "timing"]
        assert len(future_dated) > 0

    def test_bank_reconciliation_exact_match(self):
        """Test bank reconciliation with exact matches."""
        engine = ReconciliationEngine()
        account_id = uuid4()

        today = date.today()
        engine.add_transaction("txn1", Decimal("100.00"), today, "Deposit")
        engine.add_transaction("txn2", Decimal("-25.00"), today, "Check")

        bank_statement = [
            {"date": today, "amount": 100.00, "description": "Deposit"},
            {"date": today, "amount": -25.00, "description": "Check"},
        ]

        status = engine.bank_reconciliation(
            account_id,
            bank_statement,
            date.today(),
        )

        assert status.is_reconciled is True
        assert len(status.discrepancies) == 0

    def test_bank_reconciliation_with_date_variance(self):
        """Test bank reconciliation with date variance."""
        engine = ReconciliationEngine()
        account_id = uuid4()

        today = date.today()
        engine.add_transaction("txn1", Decimal("100.00"), today, "Deposit")

        bank_statement = [
            {"date": today + timedelta(days=2), "amount": 100.00, "description": "Deposit"},
        ]

        status = engine.bank_reconciliation(
            account_id,
            bank_statement,
            date.today(),
            date_variance_days=3,
        )

        assert len(status.discrepancies) == 0 or status.is_reconciled

    def test_bank_reconciliation_unmatched_items(self):
        """Test bank reconciliation with unmatched items."""
        engine = ReconciliationEngine()
        account_id = uuid4()

        today = date.today()
        engine.add_transaction("txn1", Decimal("100.00"), today, "Deposit")

        bank_statement = [
            {"date": today, "amount": 100.00, "description": "Deposit"},
            {"date": today, "amount": 50.00, "description": "Interest"},  # Won't match
        ]

        status = engine.bank_reconciliation(
            account_id,
            bank_statement,
            date.today(),
        )

        unmatched = [d for d in status.discrepancies if d.discrepancy_type == "unmatched"]
        assert len(unmatched) > 0

    def test_get_uncleared_transactions(self):
        """Test getting uncleared transactions."""
        engine = ReconciliationEngine()

        today = date.today()
        engine.add_transaction("txn1", Decimal("100.00"), today, "Cleared")
        engine.add_transaction("txn2", Decimal("50.00"), today, "Uncleared")

        # Mark first as cleared
        engine.transaction_cache["txn1"]["cleared"] = True

        uncleared = engine.get_uncleared_transactions()

        assert len(uncleared) == 1
        assert uncleared[0]["id"] == "txn2"

    def test_get_reconciliation_report_empty(self):
        """Test report with no reconciliations."""
        engine = ReconciliationEngine()

        report = engine.get_reconciliation_report()

        assert report["status"] == "no_reconciliations"
        assert report["total_reconciliations"] == 0

    def test_get_reconciliation_report_after_reconciliation(self):
        """Test report after reconciliation."""
        engine = ReconciliationEngine()
        account_id = uuid4()

        today = date.today()
        engine.add_transaction("txn1", Decimal("100.00"), today, "")
        engine.add_transaction("txn2", Decimal("50.00"), today, "")

        engine.reconcile_account(
            account_id,
            date.today(),
            Decimal("150.00"),
            cleared_transaction_ids=["txn1", "txn2"],
        )

        report = engine.get_reconciliation_report()

        assert report["is_reconciled"] is True
        assert report["total_reconciliations"] == 1
        assert report["variance"] == 0.0

    def test_reconciliation_clears_transactions(self):
        """Test that reconciliation marks transactions as cleared."""
        engine = ReconciliationEngine()
        account_id = uuid4()

        today = date.today()
        engine.add_transaction("txn1", Decimal("100.00"), today, "")

        assert engine.transaction_cache["txn1"]["cleared"] is False

        engine.reconcile_account(
            account_id,
            date.today(),
            Decimal("100.00"),
            cleared_transaction_ids=["txn1"],
        )

        assert engine.transaction_cache["txn1"]["cleared"] is True

    def test_multiple_reconciliations(self):
        """Test multiple reconciliation attempts."""
        engine = ReconciliationEngine()
        account_id = uuid4()

        today = date.today()
        engine.add_transaction("txn1", Decimal("100.00"), today, "")

        # First reconciliation
        status1 = engine.reconcile_account(
            account_id,
            date.today(),
            Decimal("100.00"),
            cleared_transaction_ids=["txn1"],
        )

        # Add another transaction
        engine.add_transaction("txn2", Decimal("50.00"), today + timedelta(days=1), "")

        # Second reconciliation
        status2 = engine.reconcile_account(
            account_id,
            date.today() + timedelta(days=1),
            Decimal("150.00"),
            cleared_transaction_ids=["txn1", "txn2"],
        )

        assert len(engine.reconciliation_history) == 2
        assert status1.is_reconciled is True
        assert status2.is_reconciled is True

    def test_discrepancy_confidence_scores(self):
        """Test that discrepancies have appropriate confidence scores."""
        engine = ReconciliationEngine()

        future_date = date.today() + timedelta(days=10)
        engine.add_transaction("txn1", Decimal("100.00"), future_date, "Future")

        discrepancies = engine.detect_discrepancies()
        timing_disc = [d for d in discrepancies if d.discrepancy_type == "timing"]

        assert len(timing_disc) > 0
        # Timing issues should have high confidence
        assert timing_disc[0].confidence >= 0.8
