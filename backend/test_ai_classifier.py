#!/usr/bin/env python3
"""
Test script for AI classification.
Make sure to set GEMINI_API_KEY environment variable before running.
"""

import os
from classifier import classify
from dotenv import load_dotenv

load_dotenv()

# Test transactions
test_transactions = [
    ("WOOLWORTHS AUCKLAND", -45.67),
    ("UBER TRIP TO AIRPORT", -32.50),
    ("MYSTERY CAFE PONSONBY", -18.90),
    ("ATM WITHDRAWAL", -100.00),
    ("GOOGLE SYSTEMS SALARY", 5000.00),
    ("NETFLIX SUBSCRIPTION", -19.99),
    ("PAYMENT RECEIVED", 150.00),
    ("BP PETROL STATION", -75.50),
    ("SPARK NZ MOBILE", -89.00),
    ("DOMINOS PIZZA", -24.50),
]

def main():
    print("=" * 70)
    print("🤖 AI CLASSIFICATION TEST")
    print("=" * 70)
    
    # Check if AI is enabled
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        print(f"✅ GEMINI_API_KEY found (starts with: {gemini_key[:10]}...)")
    else:
        print("⚠️  GEMINI_API_KEY not set - AI will not be used")
        print("   Get your free key at: https://makersuite.google.com/app/apikey")
        print("   Then run: export GEMINI_API_KEY='your_key_here'")
    
    print()
    print("Testing transactions:")
    print("-" * 70)
    
    for description, amount in test_transactions:
        category, confidence, reason = classify(description, amount, use_ai=True)
        
        # Format output
        method_icon = "🤖" if "AI" in reason else "📋"
        print(f"{method_icon} {description:35} ${amount:8.2f}")
        print(f"   → Category: {category:20} Confidence: {confidence:.2f}")
        print(f"   → Method: {reason}")
        print()
    
    print("=" * 70)
    print("Test complete!")

if __name__ == "__main__":
    main()

