from typing import Optional, Tuple

# Import AI classifier (optional dependency)
try:
    from ai_classifier import classify_with_ai, is_ai_enabled
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    def classify_with_ai(description: str, amount: float) -> Optional[str]:
        return None
    def is_ai_enabled() -> bool:
        return False


classification_rules = {
    "Credit Card Payments": [
        "payment received",
        "credit card payment",
        "credit card bill",
        "card payment",
        "payment to card",
    ],
    "Groceries": [
        "woolworths",
        "pak n save",
        "new world",
        "countdown",
        "four square",
        "supermarket",
        "groceries",
        "foodstuffs",
    ],
    "Transportation": [
        "uber",
        "taxi",
        "bus",
        "train",
        "parking",
        "wilson parking",
        "fuel",
        "gas station",
        "z energy",
        "bp",
        "mobil",
    ],
    "Dining Out": [
        "coffee",
        "cafe",
        "restaurant",
        "mcdonalds",
        "kfc",
        "subway",
        "krispy kreme",
        "bakery",
        "korean night market",
        "3 tigers",
    ],
    "Income": [
        "salary",
        "wage",
        "income",
        "deposit",
        "refund",
        "interest",
        "datacom systems",
        # REMOVED "payment received" - this is credit card payment, not income
    ],
    "Bills & Utilities": [
        "apple.com",
        "netflix",
        "spotify",
        "amazon",
        "cursor",
        "ableton",
        "flat account"
    ],
    "Shopping": [
        "the warehouse",
        "kmart",
        "bunnings",
        "mitre 10",
        "pb tech",
        "temu",
        "etsy",
        "lego",
    ],
    "Entertainment": ["hoyts", "movie", "cinema", "f1.com", "sports", "gym"],
    "Healthcare": ["pharmacy", "chemist", "doctor", "dentist", "medical", "vape"],
    "Insurance": ["state insurance", "insurance", "cover"],
    "Travel": ["air new zealand", "air new z", "flight", "travel"],
}


def classify(description, amount, use_ai: bool = True):
    """
    Classify a transaction using hybrid approach:
    1. Try rule-based classification first (fast & free)
    2. If uncertain, use AI as fallback (if enabled)
    
    Args:
        description: Transaction description
        amount: Transaction amount
        use_ai: Enable AI fallback for uncertain cases
    
    Returns: (category, confidence, reason)
    """
    description_lower = description.lower().strip()

    # Special case for credit card payments - check this FIRST
    if "payment received" in description_lower:
        return "Credit Card Payments", 0.9, "Credit card payment detected"

    # Check each category for matches
    for category, keywords in classification_rules.items():
        for keyword in keywords:
            if keyword.lower() in description_lower:
                # Calculate confidence based on keyword match
                confidence = 0.8 if keyword.lower() in description_lower else 0.6
                reason = f"Matched keyword: {keyword}"
                return category, confidence, reason

    # Rule-based failed, try AI if enabled
    if use_ai and is_ai_enabled():
        print(f"🤖 Using AI for: {description}")
        ai_category = classify_with_ai(description, amount)
        if ai_category:
            return ai_category, 0.75, "AI classification"

    # Default classification (both rule-based and AI failed)
    if amount > 0:
        return "Income", 0.3, "Positive amount, no specific match"
    else:
        return "Uncategorized", 0.1, "No matching keywords found"
