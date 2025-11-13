#!/usr/bin/env python3
"""
Script to update existing transactions in AWS to "Credit Card Payments" category.

This script will:
1. Fetch all transactions from AWS
2. Find transactions that look like credit card payments
3. Update them to "Credit Card Payments" category

Usage:
    python update_credit_card_payments.py
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AWS_API_URL = os.getenv("AWS_API_URL")
USER_ID = "user1"

# Keywords that indicate credit card payments
CREDIT_CARD_PAYMENT_KEYWORDS = [
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
]


def get_all_transactions():
    """Fetch all transactions from AWS"""
    print(f"📥 Fetching transactions from {AWS_API_URL}...")
    
    all_transactions = []
    limit = 500
    offset = 0
    
    while True:
        try:
            response = requests.get(
                f"{AWS_API_URL}/transactions",
                params={"user_id": USER_ID, "limit": limit},
                timeout=30,
            )
            
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code} - {response.text}")
                break
            
            data = response.json()
            transactions = data.get("items", [])
            
            if not transactions:
                break
            
            all_transactions.extend(transactions)
            print(f"   Loaded {len(all_transactions)} transactions so far...")
            
            if len(transactions) < limit:
                break
            
            offset += limit
            
        except Exception as e:
            print(f"❌ Error fetching transactions: {e}")
            break
    
    print(f"✅ Loaded {len(all_transactions)} total transactions\n")
    return all_transactions


def is_credit_card_payment(transaction):
    """Check if a transaction looks like a credit card payment"""
    description = transaction.get("description", "").lower()
    category = transaction.get("category", "").lower()
    
    # Already categorized correctly
    if category == "credit card payments":
        return False
    
    # Check if description matches credit card payment patterns
    for keyword in CREDIT_CARD_PAYMENT_KEYWORDS:
        if keyword in description:
            return True
    
    return False


def update_transaction_category(transaction_id, new_category):
    """Update a transaction's category"""
    try:
        # URL encode the transaction_id in case it has special characters
        import urllib.parse
        encoded_id = urllib.parse.quote(transaction_id, safe='')
        
        response = requests.put(
            f"{AWS_API_URL}/transactions/{encoded_id}/category",
            params={"category": new_category, "user_id": USER_ID},
            timeout=10,
        )
        
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            print(f"   ⚠️  Transaction {transaction_id[:8]}... not found (may have been deleted or doesn't exist)")
            return False
        else:
            print(f"   ⚠️  Failed to update {transaction_id[:8]}...: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error updating {transaction_id[:8]}...: {e}")
        return False


def check_endpoint_available():
    """Check if the update endpoint is available"""
    try:
        # Try a test request to see if endpoint exists
        # Use a dummy transaction ID to check if endpoint responds
        test_response = requests.put(
            f"{AWS_API_URL}/transactions/test-id-12345/category",
            params={"category": "Test", "user_id": USER_ID},
            timeout=5,
        )
        # If we get 404 with "not found" detail, endpoint exists but transaction doesn't
        # If we get 404 without detail or connection error, endpoint might not exist
        if test_response.status_code == 404:
            error_detail = test_response.json().get("detail", "")
            if "not found" in error_detail.lower():
                return True  # Endpoint exists, just transaction doesn't
        return test_response.status_code in [200, 404]  # Endpoint exists
    except requests.exceptions.RequestException:
        return False


def main():
    if not AWS_API_URL:
        print("❌ Error: AWS_API_URL not set in .env file")
        print("   Please set AWS_API_URL in your .env file")
        return
    
    # Check if endpoint is available
    print("🔍 Checking if update endpoint is available...")
    if not check_endpoint_available():
        print("⚠️  Warning: Update endpoint may not be deployed yet!")
        print("   You may need to deploy your backend first:")
        print("   cd sam-backend && sam build && sam deploy")
        print("\n   Continue anyway? (yes/no): ", end="")
        continue_anyway = input().strip().lower()
        if continue_anyway not in ["yes", "y"]:
            print("❌ Cancelled")
            return
        print()
    
    print("🔍 Finding credit card payment transactions to update...\n")
    
    # Get all transactions
    transactions = get_all_transactions()
    
    if not transactions:
        print("❌ No transactions found")
        return
    
    # Find transactions that need updating
    to_update = []
    for tx in transactions:
        if is_credit_card_payment(tx):
            to_update.append(tx)
    
    if not to_update:
        print("✅ No transactions need updating - all credit card payments are already categorized correctly!")
        return
    
    print(f"📋 Found {len(to_update)} transactions that look like credit card payments:\n")
    
    # Show what will be updated (all of them, or first 20 if too many)
    show_count = min(len(to_update), 20)
    for i, tx in enumerate(to_update[:show_count]):
        print(f"   {i+1}. {tx.get('date', '')[:10]} | ${tx.get('amount', 0):.2f} | {tx.get('description', '')[:50]}")
        print(f"      Current: {tx.get('category', 'Uncategorized')} → Credit Card Payments")
        print(f"      ID: {tx.get('transaction_id', 'N/A')[:8]}...")
    
    if len(to_update) > show_count:
        print(f"\n   ... and {len(to_update) - show_count} more transactions")
    
    # Option to save full list to file
    print(f"\n💾 Would you like to save the full list to a file for review? (yes/no)")
    save_choice = input("   Save to file? (yes/no): ").strip().lower()
    
    if save_choice in ["yes", "y"]:
        filename = "credit_card_payments_to_update.txt"
        with open(filename, "w") as f:
            f.write(f"Transactions to update to 'Credit Card Payments' category\n")
            f.write(f"Total: {len(to_update)}\n")
            f.write("=" * 80 + "\n\n")
            for i, tx in enumerate(to_update, 1):
                f.write(f"{i}. Date: {tx.get('date', '')[:10]}\n")
                f.write(f"   Amount: ${tx.get('amount', 0):.2f}\n")
                f.write(f"   Description: {tx.get('description', '')}\n")
                f.write(f"   Current Category: {tx.get('category', 'Uncategorized')}\n")
                f.write(f"   Transaction ID: {tx.get('transaction_id', 'N/A')}\n")
                f.write(f"   Account: {tx.get('account', 'main')}\n")
                f.write("-" * 80 + "\n")
        print(f"   ✅ Saved to {filename}\n")
    
    # Ask for confirmation
    print(f"\n⚠️  This will update {len(to_update)} transactions to 'Credit Card Payments' category")
    confirm = input("Proceed with update? (yes/no): ").strip().lower()
    
    if confirm not in ["yes", "y"]:
        print("❌ Cancelled")
        return
    
    # Update transactions
    print(f"\n🔄 Updating transactions...\n")
    updated = 0
    failed = 0
    
    for tx in to_update:
        transaction_id = tx.get("transaction_id")
        description = tx.get("description", "")
        
        if update_transaction_category(transaction_id, "Credit Card Payments"):
            updated += 1
            if updated % 10 == 0:
                print(f"   ✅ Updated {updated}/{len(to_update)}...")
        else:
            failed += 1
    
    print(f"\n✅ Done!")
    print(f"   Updated: {updated}")
    print(f"   Failed: {failed}")
    print(f"\n💡 Tip: Recalculate your period summary to see the updated discrepancy!")


if __name__ == "__main__":
    main()

