#!/usr/bin/env python3
"""
Learning Scanner - Learn from existing transactions

This script scans your existing transactions to create learning patterns
for better future classification.

Usage:
    python learn_from_existing.py

Requirements:
    - AWS API deployed and accessible
    - Transactions already in the database
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
API_URL = os.getenv("AWS_API_URL")
USER_ID = os.getenv("USER_ID")


def scan_existing_transactions():
    """Scan existing transactions to learn patterns"""
    print("🔍 Scanning existing transactions for learning patterns...")

    try:
        # Call the learning scan endpoint
        response = requests.post(
            f"{API_URL}/learning/scan",
            params={"user_id": USER_ID, "limit": 1000},
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()

            print(f"✅ Scan completed successfully!")
            print(f"📊 Transactions analyzed: {result.get('transactions_analyzed', 0)}")
            print(f"🏪 Merchant patterns found: {result.get('merchant_patterns', 0)}")
            print(f"🔑 Keyword patterns found: {result.get('keyword_patterns', 0)}")
            print(f"🧠 Learning patterns created: {result.get('patterns_created', 0)}")

            # Show top merchants
            top_merchants = result.get("top_merchants", [])
            if top_merchants:
                print(f"\n🏆 Top merchants learned:")
                for merchant, count in top_merchants[:5]:
                    print(f"  • {merchant}: {count} transactions")

            # Show top keywords
            top_keywords = result.get("top_keywords", [])
            if top_keywords:
                print(f"\n🔑 Top keywords learned:")
                for keyword, count in top_keywords[:5]:
                    print(f"  • {keyword}: {count} occurrences")

            return result
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error scanning transactions: {e}")
        return None


def get_learning_stats():
    """Get current learning statistics"""
    print("\n📈 Getting learning statistics...")

    try:
        response = requests.get(
            f"{API_URL}/learning/scan-stats", params={"user_id": USER_ID}, timeout=10
        )

        if response.status_code == 200:
            stats = response.json()

            print(f"📊 Learning Statistics:")
            print(f"  • Total patterns: {stats.get('total_patterns', 0)}")
            print(f"  • Historical patterns: {stats.get('historical_patterns', 0)}")
            print(f"  • Keyword patterns: {stats.get('keyword_patterns', 0)}")
            print(f"  • User corrections: {stats.get('user_corrections', 0)}")

            return stats
        else:
            print(f"❌ Error getting stats: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return None


def test_learning():
    """Test the learning system with a sample transaction"""
    print("\n🧪 Testing learning system...")

    # Test with a common merchant
    test_description = "COUNTDOWN"
    test_amount = -45.50

    try:
        response = requests.get(
            f"{API_URL}/learning/apply",
            params={
                "description": test_description,
                "amount": test_amount,
                "user_id": USER_ID,
            },
            timeout=10,
        )

        if response.status_code == 200:
            result = response.json()

            if result.get("has_learning"):
                print(f"✅ Learning test successful!")
                print(f"  • Description: {result['description']}")
                print(f"  • Learned category: {result['learned_category']}")
            else:
                print(f"ℹ️  No learning pattern found for: {test_description}")
                print(f"  • This is normal for new/unique merchants")

            return result
        else:
            print(f"❌ Error testing learning: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Error testing learning: {e}")
        return None


def main():
    """Main function"""
    print("🧠 Finance Tracker - Learning Scanner")
    print("=" * 50)

    # Check if API URL is configured
    if "your-api-url" in API_URL:
        print("❌ Please update API_URL in this script with your actual AWS API URL")
        print("   You can find it in your AWS API Gateway console")
        return

    # Step 1: Scan existing transactions
    scan_result = scan_existing_transactions()

    if scan_result and scan_result.get("patterns_created", 0) > 0:
        print(
            f"\n🎉 Learning scan completed! Created {scan_result['patterns_created']} patterns."
        )

        # Step 2: Get learning statistics
        get_learning_stats()

        # Step 3: Test learning
        test_learning()

        print(f"\n✨ Your finance tracker is now smarter!")
        print(f"   Future CSV imports will use these learned patterns.")
        print(f"   You should see fewer 'Needs Review' items!")

    else:
        print(f"\n⚠️  No learning patterns created.")
        print(f"   This could mean:")
        print(f"   • No transactions found in database")
        print(f"   • All transactions are 'Uncategorized' or 'Transfers'")
        print(f"   • Need more transaction history to find patterns")


if __name__ == "__main__":
    main()
