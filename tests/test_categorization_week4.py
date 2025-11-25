"""Tests for transaction categorization system."""

import pytest
from decimal import Decimal
from uuid import uuid4

from backend.reporting.categorization import (
    TransactionCategory,
    CategorizationRule,
    CategorySuggestion,
    CategorizationEngine,
)


class TestTransactionCategory:
    """Tests for TransactionCategory model."""

    def test_category_initialization(self):
        """Test category initialization."""
        org_id = uuid4()
        category = TransactionCategory(
            organization_id=org_id,
            name="Travel",
            description="Travel and transportation expenses",
            category_type="Expense",
            color="#FF5733",
        )

        assert category.organization_id == org_id
        assert category.name == "Travel"
        assert category.category_type == "Expense"
        assert category.color == "#FF5733"

    def test_category_to_dict(self):
        """Test category serialization."""
        org_id = uuid4()
        category = TransactionCategory(
            organization_id=org_id,
            name="Travel",
            category_type="Expense",
        )

        data = category.to_dict()

        assert data["name"] == "Travel"
        assert data["category_type"] == "Expense"
        assert "created_at" in data


class TestCategorizationRule:
    """Tests for CategorizationRule model."""

    def test_rule_initialization(self):
        """Test rule initialization."""
        org_id = uuid4()
        cat_id = uuid4()

        rule = CategorizationRule(
            organization_id=org_id,
            category_id=cat_id,
            name="Travel Expenses",
            condition_type="keyword",
            condition_value="flight",
            enabled=True,
            priority=100,
        )

        assert rule.organization_id == org_id
        assert rule.category_id == cat_id
        assert rule.name == "Travel Expenses"
        assert rule.condition_type == "keyword"
        assert rule.enabled is True

    def test_rule_to_dict(self):
        """Test rule serialization."""
        rule = CategorizationRule(
            name="Travel Expenses",
            condition_type="keyword",
            condition_value="flight",
        )

        data = rule.to_dict()

        assert data["name"] == "Travel Expenses"
        assert data["condition_type"] == "keyword"
        assert data["condition_value"] == "flight"


class TestCategorySuggestion:
    """Tests for CategorySuggestion model."""

    def test_suggestion_initialization(self):
        """Test suggestion initialization."""
        cat_id = uuid4()
        suggestion = CategorySuggestion(
            category_id=cat_id,
            category_name="Travel",
            confidence=0.85,
            reason="Matched keyword: flight",
        )

        assert suggestion.category_id == cat_id
        assert suggestion.category_name == "Travel"
        assert suggestion.confidence == 0.85

    def test_suggestion_to_dict(self):
        """Test suggestion serialization."""
        suggestion = CategorySuggestion(
            category_id=uuid4(),
            category_name="Travel",
            confidence=0.8456789,
            reason="Matched keywords",
        )

        data = suggestion.to_dict()

        assert data["category_name"] == "Travel"
        assert data["confidence"] == 0.846  # Rounded to 3 decimals


class TestCategorizationEngine:
    """Tests for categorization engine."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = CategorizationEngine()

        assert len(engine.rules) == 0
        assert len(engine.categories) == 0

    def test_add_category(self):
        """Test adding a category."""
        engine = CategorizationEngine()
        category = TransactionCategory(
            name="Travel",
            category_type="Expense",
        )

        engine.add_category(category)

        assert len(engine.categories) == 1
        assert category.id in engine.categories

    def test_add_rule(self):
        """Test adding a rule."""
        engine = CategorizationEngine()
        rule = CategorizationRule(
            name="Flight Expenses",
            condition_type="keyword",
            condition_value="flight",
            enabled=True,
        )

        engine.add_rule(rule)

        assert len(engine.rules) == 1
        assert engine.rules[0].name == "Flight Expenses"

    def test_add_disabled_rule(self):
        """Test that disabled rules are not added."""
        engine = CategorizationEngine()
        rule = CategorizationRule(
            name="Disabled Rule",
            condition_type="keyword",
            condition_value="test",
            enabled=False,
        )

        engine.add_rule(rule)

        assert len(engine.rules) == 0

    def test_suggest_categories_travel(self):
        """Test suggesting travel category."""
        engine = CategorizationEngine()

        suggestions = engine.suggest_categories(
            "Flight to New York on Delta",
            Decimal("500.00"),
            top_k=3,
        )

        assert len(suggestions) > 0
        assert suggestions[0].category_name == "Travel"
        assert suggestions[0].confidence > 0.5

    def test_suggest_categories_office_supplies(self):
        """Test suggesting office supplies category."""
        engine = CategorizationEngine()

        suggestions = engine.suggest_categories(
            "Office Depot - printer paper and ink",
            Decimal("100.00"),
            top_k=3,
        )

        assert len(suggestions) > 0
        assert any(s.category_name == "Office Supplies" for s in suggestions)

    def test_suggest_categories_software(self):
        """Test suggesting software category."""
        engine = CategorizationEngine()

        suggestions = engine.suggest_categories(
            "AWS cloud subscription",
            Decimal("200.00"),
            top_k=3,
        )

        assert len(suggestions) > 0
        assert any(s.category_name == "Software & Subscriptions" for s in suggestions)

    def test_suggest_categories_no_match(self):
        """Test suggestions with no obvious match."""
        engine = CategorizationEngine()

        suggestions = engine.suggest_categories(
            "Random transaction",
            Decimal("50.00"),
            top_k=3,
        )

        assert len(suggestions) == 0

    def test_auto_categorize_confident(self):
        """Test auto-categorization with high confidence."""
        engine = CategorizationEngine()

        result = engine.auto_categorize(
            "Flight booking confirmation",
            Decimal("600.00"),
            confidence_threshold=0.5,
        )

        assert result is not None
        assert result.category_name == "Travel"
        assert result.confidence > 0.5

    def test_auto_categorize_low_confidence(self):
        """Test auto-categorization below threshold."""
        engine = CategorizationEngine()

        result = engine.auto_categorize(
            "Random text",
            Decimal("100.00"),
            confidence_threshold=0.9,
        )

        assert result is None

    def test_apply_keyword_rule(self):
        """Test applying keyword-based rule."""
        engine = CategorizationEngine()
        rule = CategorizationRule(
            category_id=uuid4(),
            name="All flights are travel",
            condition_type="keyword",
            condition_value="flight",
            enabled=True,
            priority=100,
        )
        engine.add_rule(rule)

        result = engine.apply_rules("Flight booking", Decimal("500.00"))

        assert result is not None
        assert result.confidence == 1.0
        assert result.rule_id == rule.id

    def test_apply_vendor_rule(self):
        """Test applying vendor-based rule."""
        engine = CategorizationEngine()
        rule = CategorizationRule(
            category_id=uuid4(),
            name="Starbucks is meals",
            condition_type="vendor",
            condition_value="starbucks",
            enabled=True,
            priority=100,
        )
        engine.add_rule(rule)

        result = engine.apply_rules("Starbucks Coffee", Decimal("8.50"))

        assert result is not None
        assert result.rule_id == rule.id

    def test_apply_amount_range_rule(self):
        """Test applying amount range rule."""
        engine = CategorizationEngine()
        rule = CategorizationRule(
            category_id=uuid4(),
            name="Small expenses",
            condition_type="amount_range",
            condition_value="0-100",
            enabled=True,
            priority=100,
        )
        engine.add_rule(rule)

        result = engine.apply_rules("Random expense", Decimal("50.00"))

        assert result is not None

    def test_apply_amount_greater_than_rule(self):
        """Test applying greater than amount rule."""
        engine = CategorizationEngine()
        rule = CategorizationRule(
            category_id=uuid4(),
            name="Large expenses",
            condition_type="amount_range",
            condition_value=">500",
            enabled=True,
            priority=100,
        )
        engine.add_rule(rule)

        result_match = engine.apply_rules("Large expense", Decimal("600.00"))
        result_no_match = engine.apply_rules("Small expense", Decimal("400.00"))

        assert result_match is not None
        assert result_no_match is None

    def test_apply_amount_less_than_rule(self):
        """Test applying less than amount rule."""
        engine = CategorizationEngine()
        rule = CategorizationRule(
            category_id=uuid4(),
            name="Micro expenses",
            condition_type="amount_range",
            condition_value="<25",
            enabled=True,
            priority=100,
        )
        engine.add_rule(rule)

        result_match = engine.apply_rules("Small expense", Decimal("10.00"))
        result_no_match = engine.apply_rules("Large expense", Decimal("50.00"))

        assert result_match is not None
        assert result_no_match is None

    def test_rule_priority(self):
        """Test that rules are checked in priority order."""
        engine = CategorizationEngine()

        rule_high = CategorizationRule(
            category_id=uuid4(),
            name="High priority",
            condition_type="keyword",
            condition_value="test",
            enabled=True,
            priority=200,
        )

        rule_low = CategorizationRule(
            category_id=uuid4(),
            name="Low priority",
            condition_type="keyword",
            condition_value="test",
            enabled=True,
            priority=50,
        )

        engine.add_rule(rule_low)
        engine.add_rule(rule_high)

        # High priority should be first
        assert engine.rules[0].priority == 200

    def test_categorize_with_rules_only(self):
        """Test categorize with rules enabled, suggestions disabled."""
        engine = CategorizationEngine()
        rule = CategorizationRule(
            category_id=uuid4(),
            name="Flight rule",
            condition_type="keyword",
            condition_value="flight",
            enabled=True,
        )
        engine.add_rule(rule)

        # With matching rule
        result = engine.categorize(
            "Flight booking",
            Decimal("500.00"),
            use_rules=True,
            use_suggestions=False,
        )
        assert result is not None

        # Without matching rule
        result = engine.categorize(
            "Random transaction",
            Decimal("100.00"),
            use_rules=True,
            use_suggestions=False,
        )
        assert result is None

    def test_categorize_with_suggestions_only(self):
        """Test categorize with suggestions enabled, rules disabled."""
        engine = CategorizationEngine()

        result = engine.categorize(
            "Flight booking",
            Decimal("500.00"),
            use_rules=False,
            use_suggestions=True,
            confidence_threshold=0.5,
        )

        assert result is not None
        assert result.category_name == "Travel"

    def test_categorize_rules_priority_over_suggestions(self):
        """Test that rules take priority over suggestions."""
        engine = CategorizationEngine()

        rule = CategorizationRule(
            category_id=uuid4(),
            name="Flight rule",
            condition_type="keyword",
            condition_value="flight",
            enabled=True,
            priority=100,
        )
        engine.add_rule(rule)

        result = engine.categorize(
            "Flight booking",
            Decimal("500.00"),
            use_rules=True,
            use_suggestions=True,
        )

        assert result is not None
        assert result.rule_id == rule.id

    def test_get_category_stats(self):
        """Test getting category statistics."""
        engine = CategorizationEngine()

        # Add categories
        engine.add_category(
            TransactionCategory(name="Travel", category_type="Expense")
        )
        engine.add_category(
            TransactionCategory(name="Revenue", category_type="Revenue")
        )

        # Add rules
        engine.add_rule(
            CategorizationRule(
                name="Rule 1",
                condition_type="keyword",
                condition_value="test",
                enabled=True,
            )
        )
        engine.add_rule(
            CategorizationRule(
                name="Rule 2",
                condition_type="keyword",
                condition_value="test",
                enabled=False,
            )
        )

        stats = engine.get_category_stats()

        assert stats["total_categories"] == 2
        assert stats["total_rules"] == 1  # Only enabled rules counted in add_rule
        assert stats["enabled_rules"] == 1
        assert stats["categories_by_type"]["Expense"] == 1
        assert stats["categories_by_type"]["Revenue"] == 1

    def test_multiple_keyword_matches(self):
        """Test suggestion confidence with multiple keyword matches."""
        engine = CategorizationEngine()

        suggestions = engine.suggest_categories(
            "Delta flight and hotel booking in New York",
            Decimal("1000.00"),
            top_k=3,
        )

        # Should have high confidence due to multiple matching keywords
        travel_suggestions = [s for s in suggestions if s.category_name == "Travel"]
        assert len(travel_suggestions) > 0
        assert travel_suggestions[0].confidence > 0.5

    def test_case_insensitive_matching(self):
        """Test that keyword matching is case-insensitive."""
        engine = CategorizationEngine()

        suggestions_lower = engine.suggest_categories(
            "flight booking",
            Decimal("500.00"),
            top_k=1,
        )

        suggestions_upper = engine.suggest_categories(
            "FLIGHT BOOKING",
            Decimal("500.00"),
            top_k=1,
        )

        assert len(suggestions_lower) > 0
        assert len(suggestions_upper) > 0
        assert suggestions_lower[0].category_name == suggestions_upper[0].category_name
