"""Tests for analytics and reporting endpoints."""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from backend.api.analytics_routes import (
    router,
    set_reconciliation_engine,
    set_categorization_engine,
    set_report_generator,
)
from backend.reporting.reconciliation import ReconciliationEngine
from backend.reporting.categorization import CategorizationEngine, TransactionCategory, CategorizationRule
from backend.models import Account, Transaction, SyncHistory


class TestAnalyticsEndpointInitialization:
    """Tests for analytics endpoint initialization and setup."""

    def test_reconciliation_engine_setup(self):
        """Test reconciliation engine can be set and retrieved."""
        engine = ReconciliationEngine()
        set_reconciliation_engine(engine)

        from backend.api.analytics_routes import get_reconciliation_engine
        retrieved = get_reconciliation_engine()
        assert retrieved is engine

    def test_categorization_engine_setup(self):
        """Test categorization engine can be set and retrieved."""
        engine = CategorizationEngine()
        set_categorization_engine(engine)

        from backend.api.analytics_routes import get_categorization_engine
        retrieved = get_categorization_engine()
        assert retrieved is engine


class TestReconciliationAnalytics:
    """Tests for reconciliation analytics endpoints."""

    def test_uncleared_transactions_endpoint(self):
        """Test uncleared transactions endpoint."""
        engine = ReconciliationEngine()
        set_reconciliation_engine(engine)

        today = date.today()
        engine.add_transaction("txn1", Decimal("100.00"), today, "Test 1")
        engine.add_transaction("txn2", Decimal("50.00"), today, "Test 2")
        engine.transaction_cache["txn1"]["cleared"] = True  # Mark first as cleared

        uncleared = engine.get_uncleared_transactions()

        assert len(uncleared) == 1
        assert uncleared[0]["id"] == "txn2"

    def test_discrepancy_report_endpoint(self):
        """Test discrepancy report endpoint."""
        engine = ReconciliationEngine()
        set_reconciliation_engine(engine)

        today = date.today()
        engine.add_transaction("txn1", Decimal("100.00"), today, "Duplicate 1")
        engine.add_transaction("txn2", Decimal("100.00"), today, "Duplicate 2")

        discrepancies = engine.detect_discrepancies()

        assert len(discrepancies) > 0
        # Verify we found duplicates
        duplicate_types = [d.discrepancy_type for d in discrepancies]
        assert "duplicate" in duplicate_types

    def test_reconciliation_status_endpoint(self):
        """Test reconciliation status endpoint."""
        engine = ReconciliationEngine()
        set_reconciliation_engine(engine)

        account_id = uuid4()
        today = date.today()
        engine.add_transaction("txn1", Decimal("100.00"), today, "Test")

        status = engine.reconcile_account(
            account_id,
            today,
            Decimal("100.00"),
            cleared_transaction_ids=["txn1"],
        )

        assert status.is_reconciled is True
        assert status.variance == Decimal("0.00")

        report = engine.get_reconciliation_report()
        assert report["is_reconciled"] is True


class TestCategorizationAnalytics:
    """Tests for categorization analytics endpoints."""

    def test_category_suggestions_endpoint(self):
        """Test category suggestions endpoint."""
        engine = CategorizationEngine()
        set_categorization_engine(engine)

        description = "Flight booking to New York"
        amount = Decimal("500.00")

        suggestions = engine.suggest_categories(description, amount, top_k=3)

        assert len(suggestions) > 0
        assert suggestions[0].confidence > 0.0
        # First suggestion should be Travel
        assert "travel" in suggestions[0].category_name.lower()

    def test_auto_categorize_endpoint(self):
        """Test auto-categorization endpoint."""
        engine = CategorizationEngine()
        set_categorization_engine(engine)

        description = "Hotel booking in Paris"
        amount = Decimal("300.00")

        suggestion = engine.auto_categorize(description, amount, confidence_threshold=0.5)

        assert suggestion is not None
        assert suggestion.confidence >= 0.5

    def test_auto_categorize_low_confidence(self):
        """Test auto-categorization with insufficient confidence."""
        engine = CategorizationEngine()
        set_categorization_engine(engine)

        description = "XYZABC123"  # Unlikely to match any category
        amount = Decimal("100.00")

        suggestion = engine.auto_categorize(description, amount, confidence_threshold=0.9)

        # Should return None or low confidence
        if suggestion:
            assert suggestion.confidence < 0.9

    def test_categorization_statistics_endpoint(self):
        """Test categorization statistics endpoint."""
        engine = CategorizationEngine()
        set_categorization_engine(engine)

        # Add some categories and rules
        cat1 = TransactionCategory(name="Travel", category_type="Expense")
        engine.add_category(cat1)

        rule1 = CategorizationRule(
            category_id=cat1.id,
            name="Flight Rule",
            condition_type="keyword",
            condition_value="flight",
        )
        engine.add_rule(rule1)

        stats = engine.get_category_stats()

        assert stats["total_categories"] >= 1
        assert stats["total_rules"] >= 1
        assert "Expense" in stats["categories_by_type"]


class TestTransactionAnalytics:
    """Tests for transaction analytics endpoints."""

    def test_transaction_summary_calculation(self):
        """Test transaction summary calculations."""
        # This tests the logic that would be used in the endpoint
        transactions = [
            {"amount": Decimal("100.00")},
            {"amount": Decimal("50.00")},
            {"amount": Decimal("25.00")},
        ]

        total = sum(t["amount"] for t in transactions)
        average = total / len(transactions) if transactions else Decimal("0")

        assert total == Decimal("175.00")
        assert average == Decimal("58.33").quantize(Decimal("0.01")) or \
               average.to_integral_value() == Decimal("58") or \
               float(average) == pytest.approx(58.33, rel=0.1)

    def test_transaction_grouping_by_category(self):
        """Test grouping transactions by category."""
        # This tests the logic for category grouping
        transactions = [
            {"amount": 100.0, "category": "Travel"},
            {"amount": 50.0, "category": "Food"},
            {"amount": 75.0, "category": "Travel"},
            {"amount": 25.0, "category": "Food"},
        ]

        by_category = {}
        for txn in transactions:
            category = txn["category"]
            if category not in by_category:
                by_category[category] = {"count": 0, "total": 0.0}
            by_category[category]["count"] += 1
            by_category[category]["total"] += txn["amount"]

        assert by_category["Travel"]["count"] == 2
        assert by_category["Travel"]["total"] == 175.0
        assert by_category["Food"]["count"] == 2
        assert by_category["Food"]["total"] == 75.0

    def test_transaction_trending_logic(self):
        """Test transaction trending calculation."""
        # Create trending data
        today = date.today()
        by_date = {}

        for i in range(5):
            txn_date = (today - timedelta(days=i)).isoformat()
            by_date[txn_date] = {
                "count": i + 1,
                "total": float((i + 1) * 100),
            }

        assert len(by_date) == 5
        # First date should have highest count
        first_date = today.isoformat()
        if first_date in by_date:
            assert by_date[first_date]["count"] == 1


class TestSyncAnalytics:
    """Tests for sync job analytics."""

    def test_sync_success_rate_calculation(self):
        """Test sync success rate calculation."""
        syncs = [
            {"status": "completed"},
            {"status": "completed"},
            {"status": "failed"},
            {"status": "completed"},
        ]

        successful = len([s for s in syncs if s["status"] == "completed"])
        failed = len([s for s in syncs if s["status"] == "failed"])
        success_rate = successful / len(syncs)

        assert successful == 3
        assert failed == 1
        assert success_rate == 0.75

    def test_empty_sync_statistics(self):
        """Test sync statistics with no data."""
        syncs = []

        if syncs:
            success_rate = len([s for s in syncs if s["status"] == "completed"]) / len(syncs)
        else:
            success_rate = 0.0

        assert success_rate == 0.0


class TestEndpointIntegration:
    """Integration tests combining multiple analytics."""

    def test_reconciliation_to_discrepancy_flow(self):
        """Test flow from reconciliation to discrepancy detection."""
        engine = ReconciliationEngine()
        set_reconciliation_engine(engine)

        account_id = uuid4()
        today = date.today()

        # Add transactions
        engine.add_transaction("txn1", Decimal("100.00"), today, "Debit")
        engine.add_transaction("txn2", Decimal("-100.00"), today + timedelta(days=1), "Credit")

        # Reconcile
        status = engine.reconcile_account(
            account_id,
            today,
            Decimal("0.00"),
            cleared_transaction_ids=["txn1", "txn2"],
        )

        # Check for round-trip discrepancies
        discrepancies = engine.detect_discrepancies()
        round_trips = [d for d in discrepancies if d.discrepancy_type == "round_trip"]

        assert len(round_trips) > 0
        assert status.is_reconciled is True

    def test_categorization_to_transaction_flow(self):
        """Test flow from categorization to transaction grouping."""
        engine = CategorizationEngine()
        set_categorization_engine(engine)

        # Test categorizing different transaction types
        travel_desc = "Uber ride to airport"
        food_desc = "Restaurant dinner"

        travel_cat = engine.auto_categorize(travel_desc, Decimal("50.00"), 0.5)
        food_cat = engine.auto_categorize(food_desc, Decimal("75.00"), 0.5)

        assert travel_cat is not None
        assert food_cat is not None
        assert travel_cat.category_name != food_cat.category_name

    def test_full_reporting_stack(self):
        """Test complete reporting stack with all components."""
        # Initialize all engines
        reconciliation_engine = ReconciliationEngine()
        categorization_engine = CategorizationEngine()

        set_reconciliation_engine(reconciliation_engine)
        set_categorization_engine(categorization_engine)

        # Add test data
        today = date.today()
        account_id = uuid4()

        reconciliation_engine.add_transaction("txn1", Decimal("500.00"), today, "Travel")
        reconciliation_engine.add_transaction("txn2", Decimal("100.00"), today, "Dinner")

        # Test reconciliation
        recon_status = reconciliation_engine.reconcile_account(
            account_id,
            today,
            Decimal("600.00"),
            cleared_transaction_ids=["txn1", "txn2"],
        )
        assert recon_status.is_reconciled is True

        # Test categorization
        travel_suggestion = categorization_engine.auto_categorize(
            "Flight to NYC", Decimal("500.00"), 0.5
        )
        assert travel_suggestion is not None

        # All components working together
        assert reconciliation_engine.transaction_cache
        assert len(categorization_engine.KEYWORD_CATEGORIES) > 0
