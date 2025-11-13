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
        "cc payment",
        "credit payment",
        "card bill payment",
        "visa payment",
        "mastercard payment",
        "amex payment",
        "credit card transfer",
        "card transfer",
        "pay credit card",
        "credit card repayment",
        "card repayment",
        "payment - credit card",
        "automatic payment - card",
    ],
    "Payment": [
        "errington",
        "the misso",
        "goodsir",
        "partner payment",
        "personal payment",
        "sam",
    ],
    "Cash Withdrawal": [
        "atm",
        "atm transaction",
        "cash withdrawal",
        "wbc atm",
        "bnz atm",
        "anz atm",
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
        # REMOVED "payment received" - this is credit card payment, not income
    ],
    "Bills & Utilities": [
        "apple.com",
        "netflix",
        "spotify",
        "amazon",
        "cursor",
        "ableton",
        "flat account",
        "2degrees",
        "vodafone",
        "spark",
        "debitsuccess",
        "direct debit",
        "bill payment",
        "automatic payment",
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
    "Insurance": ["state insurance", "insurance", "cover", "southern cross"],
    "Travel": ["air new zealand", "air new z", "flight", "travel"],
}


def classify(description, amount, use_ai: bool = True, user_id: str = "user1"):
    """
    Classify a transaction using hybrid approach:
    1. Try learning patterns first (user corrections)
    2. Try rule-based classification (fast & free)
    3. If uncertain, use AI as fallback (if enabled)

    Args:
        description: Transaction description
        amount: Transaction amount
        use_ai: Enable AI fallback for uncertain cases
        user_id: User ID for learning patterns

    Returns: (category, confidence, reason)
    """
    description_lower = description.lower().strip()

    # Step 1: Try learning patterns first (user corrections)
    try:
        from aws_db import apply_learning_to_classification

        learned_category = apply_learning_to_classification(
            user_id, description, amount
        )
        if learned_category:
            return learned_category, 0.85, "Learned from user corrections"
    except Exception as e:
        print(f"Learning system error: {e}")

    # Step 2: Special case for credit card payments - check this FIRST
    # Common patterns: "payment received", "credit card", "card payment", etc.
    credit_card_keywords = [
        "payment received",
        "credit card payment",
        "credit card bill",
        "card payment",
        "payment to card",
        "cc payment",
        "pay credit card",
        "credit card transfer",
    ]
    if any(keyword in description_lower for keyword in credit_card_keywords):
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
