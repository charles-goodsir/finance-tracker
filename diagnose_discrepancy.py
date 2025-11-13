#!/usr/bin/env python3
"""
Diagnostic script to identify the source of discrepancy in period summary.

This script will:
1. Fetch transactions for the period
2. Show balance snapshots
3. Calculate both methods manually
4. Identify what's causing the discrepancy
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

AWS_API_URL = os.getenv("AWS_API_URL")
USER_ID = "user1"

# Excluded categories (same as backend)
EXCLUDED_CATEGORIES = [
    "Transfers",
    "Payment",
    "Cash Withdrawal",
    "Credit Card Payments",
]


def get_period_summary(start_date, end_date):
    """Get period summary from API"""
    try:
        response = requests.get(
            f"{AWS_API_URL}/summary/period",
            params={
                "user_id": USER_ID,
                "start_date": start_date,
                "end_date": end_date,
            },
            timeout=30,
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def get_transactions(start_date, end_date):
    """Get all transactions for the period"""
    print(f"📥 Fetching transactions from {start_date} to {end_date}...")
    
    all_transactions = []
    limit = 500
    
    try:
        response = requests.get(
            f"{AWS_API_URL}/transactions",
            params={"user_id": USER_ID, "limit": limit},
            timeout=30,
        )
        
        if response.status_code == 200:
            data = response.json()
            transactions = data.get("items", [])
            
            # Filter by date
            for tx in transactions:
                tx_date = tx.get("date", "")[:10]  # Get YYYY-MM-DD part
                if start_date <= tx_date <= end_date:
                    all_transactions.append(tx)
            
            print(f"✅ Found {len(all_transactions)} transactions in period\n")
            return all_transactions
        else:
            print(f"❌ Error: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def analyze_transactions(transactions, start_date, end_date):
    """Analyze transactions to find discrepancy sources"""
    
    print("=" * 80)
    print("TRANSACTION ANALYSIS")
    print("=" * 80)
    
    # Separate by category
    by_category = {}
    excluded_txs = []
    credit_card_txs = []
    included_txs = []
    
    for tx in transactions:
        category = tx.get("category", "Uncategorized")
        amount = float(tx.get("amount", 0))
        account = tx.get("account", "main")
        
        if category in EXCLUDED_CATEGORIES:
            excluded_txs.append(tx)
        elif account == "credit":
            credit_card_txs.append(tx)
        else:
            included_txs.append(tx)
        
        if category not in by_category:
            by_category[category] = {"count": 0, "total": 0, "transactions": []}
        by_category[category]["count"] += 1
        by_category[category]["total"] += amount
        by_category[category]["transactions"].append(tx)
    
    # Calculate transaction-based savings
    # IMPORTANT: Credit card spending is real spending and should be included
    # But we need to match the API calculation exactly
    total_income = sum(float(t["amount"]) for t in included_txs if float(t["amount"]) > 0)
    total_spending = sum(float(t["amount"]) for t in included_txs if float(t["amount"]) < 0)
    
    # Also include credit card spending (charges) as they're real expenses
    credit_card_spending = sum(float(t["amount"]) for t in credit_card_txs if float(t["amount"]) < 0)
    total_spending += credit_card_spending
    
    transaction_savings = total_income + total_spending  # spending is negative
    
    print(f"\n📊 Transaction-Based Calculation:")
    print(f"   Income: ${total_income:,.2f}")
    print(f"   Spending: ${abs(total_spending):,.2f}")
    print(f"   Net Savings: ${transaction_savings:,.2f}")
    print(f"   Transactions included: {len(included_txs)}")
    
    print(f"\n🚫 Excluded Transactions: {len(excluded_txs)}")
    excluded_total = sum(float(t["amount"]) for t in excluded_txs)
    print(f"   Total excluded amount: ${excluded_total:,.2f}")
    
    print(f"\n💳 Credit Card Transactions: {len(credit_card_txs)}")
    if credit_card_txs:
        credit_charges = sum(abs(float(t["amount"])) for t in credit_card_txs if float(t["amount"]) < 0)
        credit_payments = sum(float(t["amount"]) for t in credit_card_txs if float(t["amount"]) > 0)
        print(f"   Credit Card Charges: ${credit_charges:,.2f}")
        print(f"   Credit Card Payments: ${credit_payments:,.2f}")
        print(f"   Net Credit Card Activity: ${credit_charges - credit_payments:,.2f}")
    
    print(f"\n📋 Transactions by Category:")
    for category, data in sorted(by_category.items(), key=lambda x: abs(x[1]["total"]), reverse=True):
        print(f"   {category}: {data['count']} transactions, ${data['total']:,.2f}")
    
    # Show credit card payments specifically
    if "Credit Card Payments" in by_category:
        print(f"\n💳 Credit Card Payment Transactions:")
        for tx in by_category["Credit Card Payments"]["transactions"]:
            print(f"   • {tx.get('date', '')[:10]} | ${tx.get('amount', 0):.2f} | {tx.get('description', '')[:50]}")
            print(f"     Account: {tx.get('account', 'main')}")
    
    return {
        "transaction_savings": transaction_savings,
        "total_income": total_income,
        "total_spending": total_spending,
        "excluded_count": len(excluded_txs),
        "credit_card_count": len(credit_card_txs),
    }


def analyze_balance_snapshots(start_date, end_date):
    """Analyze balance snapshots"""
    print("\n" + "=" * 80)
    print("BALANCE SNAPSHOT ANALYSIS")
    print("=" * 80)
    
    try:
        # Get start snapshot
        start_response = requests.get(
            f"{AWS_API_URL}/snapshots/balance/{start_date}",
            params={"user_id": USER_ID},
            timeout=10,
        )
        
        # Get end snapshot
        end_response = requests.get(
            f"{AWS_API_URL}/snapshots/balance/{end_date}",
            params={"user_id": USER_ID},
            timeout=10,
        )
        
        if start_response.status_code == 200 and end_response.status_code == 200:
            start_snapshot = start_response.json()
            end_snapshot = end_response.json()
            
            start_assets = start_snapshot.get("total_assets", 0)
            end_assets = end_snapshot.get("total_assets", 0)
            balance_savings = end_assets - start_assets
            
            print(f"\n💰 Balance-Based Calculation:")
            print(f"   Start Date: {start_date}")
            print(f"   Starting Balance: ${start_assets:,.2f}")
            print(f"     Savings: ${start_snapshot.get('savings', 0):,.2f}")
            print(f"     Bills: ${start_snapshot.get('bills', 0):,.2f}")
            print(f"     Main: ${start_snapshot.get('main', 0):,.2f}")
            print(f"     Credit: ${start_snapshot.get('credit', 0):,.2f}")
            
            print(f"\n   End Date: {end_date}")
            print(f"   Ending Balance: ${end_assets:,.2f}")
            print(f"     Savings: ${end_snapshot.get('savings', 0):,.2f}")
            print(f"     Bills: ${end_snapshot.get('bills', 0):,.2f}")
            print(f"     Main: ${end_snapshot.get('main', 0):,.2f}")
            print(f"     Credit: ${end_snapshot.get('credit', 0):,.2f}")
            
            print(f"\n   Balance-Based Savings: ${balance_savings:,.2f}")
            
            # Calculate credit card debt change
            start_credit = start_snapshot.get("credit", 0)
            end_credit = end_snapshot.get("credit", 0)
            credit_change = end_credit - start_credit
            
            print(f"\n   Credit Card Debt Change: ${credit_change:,.2f}")
            if credit_change > 0:
                print(f"     ⚠️  Credit card debt INCREASED by ${credit_change:,.2f}")
            elif credit_change < 0:
                print(f"     ✅ Credit card debt DECREASED by ${abs(credit_change):,.2f}")
            
            return {
                "balance_savings": balance_savings,
                "start_assets": start_assets,
                "end_assets": end_assets,
                "credit_change": credit_change,
            }
        else:
            print(f"❌ Could not fetch snapshots")
            if start_response.status_code != 200:
                print(f"   Start snapshot: {start_response.status_code}")
            if end_response.status_code != 200:
                print(f"   End snapshot: {end_response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    if not AWS_API_URL:
        print("❌ Error: AWS_API_URL not set in .env file")
        return
    
    # Get date range from user
    print("🔍 Discrepancy Diagnostic Tool\n")
    print("Enter the date range for analysis:")
    start_date = input("Start date (YYYY-MM-DD): ").strip()
    end_date = input("End date (YYYY-MM-DD): ").strip()
    
    if not start_date or not end_date:
        print("❌ Invalid dates")
        return
    
    print("\n" + "=" * 80)
    print("FETCHING DATA")
    print("=" * 80)
    
    # Get period summary from API
    summary = get_period_summary(start_date, end_date)
    
    if summary:
        print("\n" + "=" * 80)
        print("API PERIOD SUMMARY")
        print("=" * 80)
        print(f"\nBalance-Based Savings: ${summary.get('balance_based', {}).get('savings', 0):,.2f}")
        print(f"Transaction-Based Savings: ${summary.get('transaction_based', {}).get('net_savings', 0):,.2f}")
        discrepancy = summary.get('verification', {}).get('discrepancy', 0)
        print(f"Discrepancy: ${abs(discrepancy):,.2f}")
    
    # Get transactions
    transactions = get_transactions(start_date, end_date)
    
    # Analyze transactions
    tx_analysis = analyze_transactions(transactions, start_date, end_date)
    
    # Analyze balance snapshots
    balance_analysis = analyze_balance_snapshots(start_date, end_date)
    
    # Final analysis
    print("\n" + "=" * 80)
    print("DISCREPANCY ANALYSIS")
    print("=" * 80)
    
    if balance_analysis and tx_analysis:
        discrepancy = balance_analysis["balance_savings"] - tx_analysis["transaction_savings"]
        
        print(f"\n📊 Summary:")
        print(f"   Balance-Based: ${balance_analysis['balance_savings']:,.2f}")
        print(f"   Transaction-Based: ${tx_analysis['transaction_savings']:,.2f}")
        print(f"   Discrepancy: ${abs(discrepancy):,.2f}")
        
        if abs(discrepancy) > 100:
            print(f"\n🔍 Possible Causes:")
            
            # Check credit card debt change
            credit_change = balance_analysis.get("credit_change", 0)
            if abs(credit_change) > 500:
                print(f"   ⚠️  Large credit card debt change: ${credit_change:,.2f}")
                print(f"      This affects balance-based but not transaction-based calculation")
                print(f"      Credit card spending is counted in transactions, but debt change")
                print(f"      is only reflected in balance snapshots")
            
            # Check for missing transactions
            if tx_analysis["excluded_count"] > 0:
                print(f"   ⚠️  {tx_analysis['excluded_count']} excluded transactions")
                print(f"      These are transfers/payments that don't affect savings")
            
            # Check credit card transactions
            if tx_analysis["credit_card_count"] > 0:
                print(f"   ⚠️  {tx_analysis['credit_card_count']} credit card transactions")
                print(f"      Credit card spending is counted, but payment timing matters")
            
            print(f"\n💡 Suggestions:")
            print(f"   1. Verify credit card balance changes match credit card transactions")
            print(f"   2. Check if all transactions in the period are imported")
            print(f"   3. Verify balance snapshots are accurate for start and end dates")
            print(f"   4. Check for cash transactions not recorded")


if __name__ == "__main__":
    main()

