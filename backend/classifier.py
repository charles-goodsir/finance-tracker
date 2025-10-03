classification_rules = {
    "Groceries": [
        "pak n save",
        "pak'nsave",
        "new world",
        "countdown",
        "woolworths",
        "four square",
        "iga",
        "supervalue",
        "supermarket",
        "groceries",
    ],
    "Transportation": [
        "uber",
        "taxi",
        "bp",
        "shell",
        "caltex",
        "fuel",
        "petrol",
        "wilson parking",
        "parking",
    ],
    "Food Delivery": [
        "uber* eats",
        "uber eats",
        "menulog",
        "delivereasy",
        "doordash",
    ],
    "Dining Out": [
        "restaurant",
        "cafe",
        "bakery",
        "korean night market",
        "coffee",
        "pizza",
        "burger",
        "kfc",
        "mcdonalds",
        "subway",
        "krispy kreme",
        "o'dowd",
        "hoppers",
        "3 tigers",
    ],
    "Bills & Utilities": [
        "electricity",
        "gas",
        "water",
        "internet",
        "telstra",
        "optus",
        "vodafone",
    ],
    "Insurance": [
        "insurance",
        "state insurance",
    ],
    "Travel": [
        "air new z",
        "air nz",
        "flight",
        "hotel",
        "accommodation",
        "audiologytouring",
    ],
    "Entertainment": [
        "netflix",
        "spotify",
        "disney",
        "hoyts",
        "cinema",
        "f1",
        "www.f1.com",
        "event tickets",
        "concert",
    ],
    "Subscriptions": [
        "apple.com/bill",
        "apple com bill",
        "cursor",
        "ableton",
        "adobe",
        "subscription",
    ],
    "Shopping": [
        "amazon",
        "ebay",
        "etsy",
        "temu",
        "lego",
        "the warehouse",
        "store",
        "retail",
    ],
    "Personal Care": [
        "vape",
        "pharmacy",
        "chemist",
    ],
    "Health & Medical": [
        "medical",
        "doctor",
        "hospital",
    ],
    "Income": [
        "salary",
        "wage",
        "pay",
        "deposit",
        "refund",
        "payment received",
        "thank you",
    ],
    "Transfers": [
        "transfer",
        "atm",
        "withdrawal",
    ],
}


def classify(description: str, amount: float):
    """
    Classify a transaction based on its description and amount.
    Returns: (Category, confidence, reason)
    """

    desc = (description or "").lower()

    for cat, kws in classification_rules.items():
        for kw in kws:
            if kw in desc:
                return (cat, 0.9, f"Matched: {kw}")
    if amount > 0:
        return ("Incom", 0.7, "Positive amount")
    return ("Uncategorized", 0.0, "No match")
