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


def classify(description, amount):
    """
    Classify a transaction based on description and amount.
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

    # Default classification
    if amount > 0:
        return "Income", 0.3, "Positive amount, no specific match"
    else:
        return "Uncategorized", 0.1, "No matching keywords found"
