classification_rules = {
    "Groceries": [
        "pak n save",
        "pak'nsave",
        "new world",
        "countdown",
        "iga",
        "supervalue",
        "supermarket",
        "groceries",
    ],
    "Transportation": ["uber", "taxi", "bp", "shell", "caltex", "fuel", "petrol"],
    "Bills & Utilities": [
        "electricity",
        "gas",
        "water",
        "internet",
        "telstra",
        "optus",
        "vodafone",
    ],
    "Entertainment": ["netflix", "spotify", "disney", "cinema", "f1"],
    "Dining Out": [
        "restaurant",
        "cafe",
        "coffee",
        "pizza",
        "burger",
        "kfc",
        "mcdonalds",
        "subway",
    ],
    "Shopping": ["amazon", "ebay", "store", "retail"],
    "Health & Medical": ["pharmacy", "chemist", "medical", "doctor", "hospital"],
    "Income": ["salary", "wage", "pay", "deposit", "refund"],
    "Transfers": ["transfer", "atm", "withdrawal"],
}


def classify(description: str, amount: float):
    desc = (description or "").lower()
    for cat, kws in classification_rules.items():
        for kw in kws:
            if kw in desc:
                return (cat, 0.9, f"Matched: {kw}")
    if amount > 0:
        return ("Incom", 0.7, "Positive amount")
    return ("Uncategorized", 0.0, "No match")
