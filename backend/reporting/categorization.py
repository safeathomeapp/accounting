"""Transaction categorization engine with rule-based and ML-ready suggestions."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


@dataclass
class TransactionCategory:
    """Transaction categorization record."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    category_type: str = "Expense"  # Expense, Revenue, Other
    color: str = "#000000"  # Hex color
    parent_category_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "name": self.name,
            "description": self.description,
            "category_type": self.category_type,
            "color": self.color,
            "parent_category_id": str(self.parent_category_id) if self.parent_category_id else None,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class CategorizationRule:
    """Rule for automatic transaction categorization."""

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    category_id: UUID = field(default_factory=uuid4)
    name: str = ""
    condition_type: str = ""  # keyword, amount_range, vendor, regex
    condition_value: str = ""  # The actual condition
    enabled: bool = True
    priority: int = 100  # Higher = checked first
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "category_id": str(self.category_id),
            "name": self.name,
            "condition_type": self.condition_type,
            "condition_value": self.condition_value,
            "enabled": self.enabled,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class CategorySuggestion:
    """Suggestion for categorizing a transaction."""

    category_id: UUID
    category_name: str
    confidence: float  # 0.0-1.0
    reason: str  # Why this suggestion was made
    rule_id: Optional[UUID] = None  # If matched by a rule

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "category_id": str(self.category_id),
            "category_name": self.category_name,
            "confidence": round(self.confidence, 3),
            "reason": self.reason,
            "rule_id": str(self.rule_id) if self.rule_id else None,
        }


class CategorizationEngine:
    """Engine for categorizing transactions with rules and suggestions."""

    # Predefined category keywords for suggestions
    KEYWORD_CATEGORIES = {
        "Travel": {
            "keywords": ["flight", "hotel", "uber", "taxi", "airbnb", "parking", "gas", "fuel"],
            "type": "Expense",
        },
        "Office Supplies": {
            "keywords": ["staples", "office depot", "ink", "paper", "pens", "notebook"],
            "type": "Expense",
        },
        "Software & Subscriptions": {
            "keywords": ["subscription", "saas", "software", "app", "cloud", "aws", "azure"],
            "type": "Expense",
        },
        "Meals & Entertainment": {
            "keywords": ["restaurant", "cafe", "lunch", "dinner", "food", "coffee"],
            "type": "Expense",
        },
        "Professional Services": {
            "keywords": ["accounting", "legal", "consulting", "contractor", "freelance"],
            "type": "Expense",
        },
        "Utilities": {
            "keywords": ["electric", "water", "gas", "internet", "phone", "utility"],
            "type": "Expense",
        },
        "Insurance": {
            "keywords": ["insurance", "premium", "coverage", "policy"],
            "type": "Expense",
        },
    }

    def __init__(self):
        """Initialize categorization engine."""
        self.rules: List[CategorizationRule] = []
        self.categories: Dict[UUID, TransactionCategory] = {}

    def add_rule(self, rule: CategorizationRule) -> None:
        """
        Add a categorization rule.

        Args:
            rule: CategorizationRule to add
        """
        if rule.enabled:
            self.rules.append(rule)
            # Sort by priority (higher first)
            self.rules.sort(key=lambda r: r.priority, reverse=True)
            logger.info(f"Added categorization rule: {rule.name}")

    def add_category(self, category: TransactionCategory) -> None:
        """
        Add a category.

        Args:
            category: TransactionCategory to add
        """
        self.categories[category.id] = category
        logger.info(f"Added category: {category.name}")

    def suggest_categories(
        self,
        description: str,
        amount: Decimal,
        top_k: int = 3,
    ) -> List[CategorySuggestion]:
        """
        Suggest categories for a transaction.

        Uses keyword matching and amount range heuristics.

        Args:
            description: Transaction description
            amount: Transaction amount
            top_k: Number of suggestions to return

        Returns:
            List of CategorySuggestion sorted by confidence (descending)
        """
        suggestions: List[CategorySuggestion] = []

        # Check keyword-based suggestions
        desc_lower = description.lower()

        for category_name, category_info in self.KEYWORD_CATEGORIES.items():
            keywords = category_info["keywords"]
            matches = sum(1 for kw in keywords if kw in desc_lower)

            if matches > 0:
                # Confidence: 0.5 base + 0.5 for each match (max 1.0)
                confidence = min(0.5 + (matches * 0.25), 1.0)
                suggestions.append(
                    CategorySuggestion(
                        category_id=uuid4(),
                        category_name=category_name,
                        confidence=confidence,
                        reason=f"Matched {matches} keyword(s): {', '.join(kw for kw in keywords if kw in desc_lower)}",
                    )
                )

        # Sort by confidence (descending) and return top-k
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        return suggestions[:top_k]

    def auto_categorize(
        self,
        description: str,
        amount: Decimal,
        confidence_threshold: float = 0.7,
    ) -> Optional[CategorySuggestion]:
        """
        Auto-categorize transaction if confidence exceeds threshold.

        Args:
            description: Transaction description
            amount: Transaction amount
            confidence_threshold: Minimum confidence to auto-categorize (default 0.7)

        Returns:
            CategorySuggestion if confident, None otherwise
        """
        suggestions = self.suggest_categories(description, amount, top_k=1)

        if suggestions and suggestions[0].confidence >= confidence_threshold:
            logger.info(
                f"Auto-categorized: {description[:50]} -> {suggestions[0].category_name} "
                f"(confidence: {suggestions[0].confidence:.1%})"
            )
            return suggestions[0]

        max_confidence = f"{suggestions[0].confidence:.1%}" if suggestions else "N/A"
        logger.debug(
            f"Low confidence for: {description[:50]} "
            f"(max: {max_confidence})"
        )
        return None

    def apply_rules(
        self,
        description: str,
        amount: Decimal,
    ) -> Optional[CategorySuggestion]:
        """
        Apply user-defined rules to categorize transaction.

        Rules are checked in priority order (highest first).

        Args:
            description: Transaction description
            amount: Transaction amount

        Returns:
            CategorySuggestion if rule matched, None otherwise
        """
        for rule in self.rules:
            if not rule.enabled:
                continue

            matched = False

            if rule.condition_type == "keyword":
                matched = rule.condition_value.lower() in description.lower()

            elif rule.condition_type == "vendor":
                matched = rule.condition_value.lower() in description.lower()

            elif rule.condition_type == "amount_range":
                # Parse range like "100-500" or ">100" or "<500"
                try:
                    if "-" in rule.condition_value and ".." not in rule.condition_value:
                        min_amt, max_amt = rule.condition_value.split("-")
                        min_amt = Decimal(min_amt.strip())
                        max_amt = Decimal(max_amt.strip())
                        matched = min_amt <= amount <= max_amt
                    elif rule.condition_value.startswith(">"):
                        threshold = Decimal(rule.condition_value[1:].strip())
                        matched = amount > threshold
                    elif rule.condition_value.startswith("<"):
                        threshold = Decimal(rule.condition_value[1:].strip())
                        matched = amount < threshold
                except (ValueError, TypeError):
                    logger.warning(f"Invalid amount range: {rule.condition_value}")
                    continue

            if matched:
                logger.info(
                    f"Rule matched: {rule.name} -> Category {rule.category_id}"
                )
                return CategorySuggestion(
                    category_id=rule.category_id,
                    category_name="",  # Would be looked up from database
                    confidence=1.0,
                    reason=f"Matched rule: {rule.name}",
                    rule_id=rule.id,
                )

        return None

    def categorize(
        self,
        description: str,
        amount: Decimal,
        use_rules: bool = True,
        use_suggestions: bool = True,
        confidence_threshold: float = 0.7,
    ) -> Optional[CategorySuggestion]:
        """
        Categorize a transaction using rules and/or suggestions.

        Priority:
        1. User-defined rules (if enabled)
        2. Auto-categorization if confidence high enough
        3. Return None if no confident match

        Args:
            description: Transaction description
            amount: Transaction amount
            use_rules: Check rules first (default True)
            use_suggestions: Fall back to suggestions (default True)
            confidence_threshold: Minimum confidence (default 0.7)

        Returns:
            CategorySuggestion or None
        """
        # Try rules first
        if use_rules:
            rule_match = self.apply_rules(description, amount)
            if rule_match:
                return rule_match

        # Fall back to auto-categorization
        if use_suggestions:
            return self.auto_categorize(description, amount, confidence_threshold)

        return None

    def get_category_stats(self) -> Dict:
        """
        Get statistics about available categories.

        Returns:
            Dict with category statistics
        """
        categories_by_type = {}
        for category in self.categories.values():
            cat_type = category.category_type
            if cat_type not in categories_by_type:
                categories_by_type[cat_type] = 0
            categories_by_type[cat_type] += 1

        return {
            "total_categories": len(self.categories),
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules if r.enabled),
            "categories_by_type": categories_by_type,
        }
