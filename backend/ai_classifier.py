"""
AI-powered transaction classification using Google Gemini.
Separate module to keep AI logic isolated from rule-based classifier.
"""

import os
from typing import Optional

try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed. AI classification disabled.")


# Valid transaction categories
VALID_CATEGORIES = [
    "Groceries",
    "Dining Out",
    "Transport",
    "Entertainment",
    "Bills & Utilities",
    "Income",
    "Shopping",
    "Health",
    "Education",
    "Credit Card Payments",
    "Transfers",
    "Other",
]


class GeminiClassifier:
    """Google Gemini AI transaction classifier"""

    def __init__(self):
        self.enabled = False
        self.model = None

        # Try to initialize Gemini
        api_key = os.getenv("GEMINI_API_KEY")

        if not GEMINI_AVAILABLE:
            print("❌ Gemini AI: Library not installed")
            return

        if not api_key:
            print("⚠️ Gemini AI: No API key found (GEMINI_API_KEY)")
            return

        try:
            genai.configure(api_key=api_key)
            # Use gemini-2.0-flash-exp (latest free model)
            self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
            self.enabled = True
            print("✅ Gemini AI: Initialized successfully")
        except Exception as e:
            print(f"❌ Gemini AI: Initialization failed - {e}")

    def is_enabled(self) -> bool:
        """Check if AI classification is available"""
        return self.enabled and self.model is not None

    def classify(self, description: str, amount: float) -> Optional[str]:
        """
        Classify a transaction using Gemini AI.

        Args:
            description: Transaction description
            amount: Transaction amount (negative for expenses, positive for income)

        Returns:
            Category name or None if classification fails
        """
        if not self.is_enabled():
            return None

        prompt = self._build_prompt(description, amount)

        try:
            response = self.model.generate_content(prompt)
            category = response.text.strip()

            # Validate and return
            return self._validate_category(category)

        except Exception as e:
            print(f"⚠️ Gemini AI classification error: {e}")
            return None

    def _build_prompt(self, description: str, amount: float) -> str:
        """Build the prompt for Gemini"""
        return f"""You are a financial transaction classifier for a New Zealand user.

Transaction Details:
- Description: {description}
- Amount: ${amount:.2f}

Categorize this transaction into ONE of these categories:
{', '.join(VALID_CATEGORIES)}

Classification Rules:
1. If it's a transfer between accounts (e.g., "payment received"), return "Transfers"
2. If amount is positive and looks like salary/wages/income, return "Income"
3. Grocery stores (Countdown, Woolworths, Pak'n Save, New World) → "Groceries"
4. Restaurants/cafes/takeaways → "Dining Out"
5. Uber, parking, petrol, public transport → "Transport"
6. Power, internet, phone, insurance → "Bills & Utilities"
7. Credit card payments → "Credit Card Payments"
8. Be specific - choose the most accurate category

Respond with ONLY the category name from the list above. No explanation, no punctuation, just the category name."""

    def _validate_category(self, category: str) -> Optional[str]:
        """Validate AI response matches our categories"""
        # Exact match
        if category in VALID_CATEGORIES:
            return category

        # Fuzzy match (case-insensitive, partial)
        category_lower = category.lower()
        for valid_cat in VALID_CATEGORIES:
            if (
                valid_cat.lower() in category_lower
                or category_lower in valid_cat.lower()
            ):
                return valid_cat

        # No match found
        print(f"⚠️ AI returned invalid category: '{category}'")
        return None

    def get_status(self) -> dict:
        """Get AI classifier status"""
        return {
            "enabled": self.enabled,
            "provider": "Google Gemini" if self.enabled else None,
            "model": "gemini-pro" if self.enabled else None,
            "library_available": GEMINI_AVAILABLE,
            "api_key_configured": bool(os.getenv("GEMINI_API_KEY")),
        }


# Global instance (singleton pattern)
_gemini_classifier = None


def get_ai_classifier() -> GeminiClassifier:
    """Get or create the global AI classifier instance"""
    global _gemini_classifier
    if _gemini_classifier is None:
        _gemini_classifier = GeminiClassifier()
    return _gemini_classifier


def classify_with_ai(description: str, amount: float) -> Optional[str]:
    """
    Convenience function for AI classification.
    Returns None if AI is unavailable or fails.
    """
    classifier = get_ai_classifier()
    return classifier.classify(description, amount)


def is_ai_enabled() -> bool:
    """Check if AI classification is available"""
    classifier = get_ai_classifier()
    return classifier.is_enabled()
