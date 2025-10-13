import boto3
import json
import uuid
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

dynamodb = boto3.resource("dynamodb")

# Get table names from environment variables
TRANSACTIONS_TABLE = os.environ.get("TRANSACTIONS_TABLE", "FinanceTracker-Transactions")
CATEGORIES_TABLE = os.environ.get("CATEGORIES_TABLE", "FinanceTracker-Categories")
RECURRING_TABLE = os.environ.get("RECURRING_TABLE", "FinanceTracker-Recurring")
GOALS_TABLE = os.environ.get("GOALS_TABLE", "FinanceTracker-Goals")
INSIGHTS_TABLE = os.environ.get("INSIGHTS_TABLE", "FinanceTracker-Insights")
ACCOUNT_BALANCES_TABLE = os.environ.get(
    "ACCOUNT_BALANCES_TABLE", "FinanceTracker-AccountBalances"
)
BALANCE_SNAPSHOTS_TABLE = os.environ.get(
    "BALANCE_SNAPSHOTS_TABLE", "FinanceTracker-BalanceSnapshots"
)
LEARNING_DATA_TABLE = os.environ.get(
    "LEARNING_DATA_TABLE", "FinanceTracker-LearningData"
)


transactions_table = dynamodb.Table(TRANSACTIONS_TABLE)
categories_table = dynamodb.Table(CATEGORIES_TABLE)
recurring_table = dynamodb.Table(RECURRING_TABLE)
goals_table = dynamodb.Table(GOALS_TABLE)
insights_table = dynamodb.Table(INSIGHTS_TABLE)
account_balances_table = dynamodb.Table(ACCOUNT_BALANCES_TABLE)
balance_snapshots_table = dynamodb.Table(BALANCE_SNAPSHOTS_TABLE)
learning_data_table = dynamodb.Table(LEARNING_DATA_TABLE)


def init_db():
    """Initialize default categories in DynamoDB"""
    default_categories = [
        {
            "category_id": "food-dining",
            "name": "Food & Dining",
            "type": "expense",
            "color": "#EF4444",
            "icon": "🍽️",
        },
        {
            "category_id": "transportation",
            "name": "Transportation",
            "type": "expense",
            "color": "#F59E0B",
            "icon": "🚗",
        },
        {
            "category_id": "salary",
            "name": "Salary",
            "type": "income",
            "color": "#22C55E",
            "icon": "🧳",
        },
    ]

    for category in default_categories:
        try:
            categories_table.put_item(
                Item=category, ConditionExpression="attribute_not_exists(category_id)"
            )
        except:
            pass  # Category already exists


def add_transaction(
    user_id,
    amount,
    category,
    description,
    tx_type,
    tags,
    frequency,
    account="main",
    date=None,
):
    """Add transaction to DynamoDB with account field and optional date"""
    import uuid
    from datetime import datetime
    from decimal import Decimal

    transaction_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    # Use provided date or default to current timestamp
    transaction_date = date if date else timestamp

    transactions_table.put_item(
        Item={
            "user_id": user_id,
            "transaction_id": transaction_id,
            "date": transaction_date,  # Use actual transaction date
            "amount": Decimal(str(amount)),
            "category": category,
            "description": description,
            "type": tx_type,
            "tags": tags,
            "frequency": frequency,
            "account": account,
            "created_at": timestamp,  # Keep track of when it was added to DB
        }
    )
    return transaction_id


def get_transactions(user_id: str, limit: int = 100) -> List[Dict]:
    """Get transactions for a user"""
    response = transactions_table.query(
        KeyConditionExpression="user_id = :user_id",
        ScanIndexForward=False,  # Sort by date descending
        Limit=limit,
        ExpressionAttributeValues={":user_id": user_id},
    )

    # Convert Decimal types back to float for JSON serialization
    items = response.get("Items", [])
    for item in items:
        if "amount" in item:
            item["amount"] = float(item["amount"])

    return items


def get_categories() -> List[Dict]:
    """Get all categories"""
    response = categories_table.scan()
    return response.get("Items", [])


def add_goal(
    user_id: str,
    goal_type: str,
    name: str,
    target_amount: float,
    current_amount: float = 0.0,
) -> str:
    """Add a financial goal"""
    goal_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    progress = (current_amount / target_amount * 100) if target_amount > 0 else 0

    goals_table.put_item(
        Item={
            "user_id": user_id,
            "goal_id": goal_id,
            "goal_type": goal_type,  # 'savings', 'debt', 'investment'
            "name": name,
            "target_amount": Decimal(str(target_amount)),
            "current_amount": Decimal(str(current_amount)),
            "progress": Decimal(str(progress)),
            "status": "active",
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    )
    return goal_id


def get_goals(user_id: str) -> List[Dict]:
    """Get all goals for a user"""
    response = goals_table.query(
        KeyConditionExpression="user_id = :user_id",
        ExpressionAttributeValues={":user_id": user_id},
    )

    items = response.get("Items", [])
    # Convert Decimal to float
    for item in items:
        if "target_amount" in item:
            item["target_amount"] = float(item["target_amount"])
        if "current_amount" in item:
            item["current_amount"] = float(item["current_amount"])

    return items


def update_goal_progress(user_id: str, goal_id: str, current_amount: float) -> bool:
    """Update goal progress"""
    try:
        # Get the goal first to calculate progress
        response = goals_table.get_item(Key={"user_id": user_id, "goal_id": goal_id})

        if "Item" not in response:
            return False

        goal = response["Item"]
        target = float(goal["target_amount"])
        progress = (current_amount / target * 100) if target > 0 else 0

        goals_table.update_item(
            Key={"user_id": user_id, "goal_id": goal_id},
            UpdateExpression="SET current_amount = :amount, progress = :progress, updated_at = :timestamp",
            ExpressionAttributeValues={
                ":amount": Decimal(str(current_amount)),
                ":progress": Decimal(str(progress)),
                ":timestamp": datetime.utcnow().isoformat(),
            },
        )
        return True
    except Exception as e:
        print(f"Error updating goal: {e}")
        return False


# ===== INSIGHTS FUNCTIONS =====


def generate_insights(user_id: str) -> Dict:
    """Generate enhanced financial insights with trends, forecasts, and actionable recommendations"""
    from datetime import datetime, timedelta

    now = datetime.utcnow()

    # Define periods
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)
    month_start = now.replace(day=1, hour=0, minute=0, second=0)
    days_in_month = 30
    days_elapsed = (now - month_start).days + 1

    # Get all transactions
    transactions = get_transactions(user_id, limit=1000)

    # Exclude transfers, payments, cash withdrawals, credit card payments
    excluded_categories = [
        "Transfers",
        "Payment",
        "Cash Withdrawal",
        "Credit Card Payments",
    ]

    def filter_transactions(txs, start, end):
        """Filter transactions by date and exclude certain categories"""
        return [
            t
            for t in txs
            if start.isoformat() <= t.get("date", "")[:19] <= end.isoformat()
            and t.get("category") not in excluded_categories
        ]

    # Get current and previous period transactions
    current_period = filter_transactions(transactions, thirty_days_ago, now)
    previous_period = filter_transactions(transactions, sixty_days_ago, thirty_days_ago)
    current_month = filter_transactions(transactions, month_start, now)

    # Calculate metrics for current period
    current_spending = abs(
        sum(float(t["amount"]) for t in current_period if float(t["amount"]) < 0)
    )
    current_income = sum(
        float(t["amount"]) for t in current_period if float(t["amount"]) > 0
    )
    current_savings = current_income - current_spending
    current_savings_rate = (
        (current_savings / current_income * 100) if current_income > 0 else 0
    )

    # Calculate metrics for previous period
    previous_spending = abs(
        sum(float(t["amount"]) for t in previous_period if float(t["amount"]) < 0)
    )
    previous_income = sum(
        float(t["amount"]) for t in previous_period if float(t["amount"]) > 0
    )

    # Calculate trends
    spending_change = (
        ((current_spending - previous_spending) / previous_spending * 100)
        if previous_spending > 0
        else 0
    )
    income_change = (
        ((current_income - previous_income) / previous_income * 100)
        if previous_income > 0
        else 0
    )

    # Category breakdown for current period
    category_spending = {}
    for t in current_period:
        if float(t["amount"]) < 0:
            cat = t.get("category", "Uncategorized")
            category_spending[cat] = category_spending.get(cat, 0) + abs(
                float(t["amount"])
            )

    # Previous period category breakdown for comparison
    prev_category_spending = {}
    for t in previous_period:
        if float(t["amount"]) < 0:
            cat = t.get("category", "Uncategorized")
            prev_category_spending[cat] = prev_category_spending.get(cat, 0) + abs(
                float(t["amount"])
            )

    # Find top spending categories
    top_categories = sorted(
        category_spending.items(), key=lambda x: x[1], reverse=True
    )[:3]

    # Spending forecast for current month
    month_spending = abs(
        sum(float(t["amount"]) for t in current_month if float(t["amount"]) < 0)
    )
    projected_monthly_spending = (
        (month_spending / days_elapsed) * days_in_month if days_elapsed > 0 else 0
    )

    # Generate alerts with trends
    alerts = []
    suggestions = []

    # 1. Trend Analysis Alert
    if abs(spending_change) > 10:
        direction = "increased" if spending_change > 0 else "decreased"
        emoji = "📈" if spending_change > 0 else "📉"
        alert_type = "warning" if spending_change > 0 else "success"
        alerts.append(
            {
                "type": alert_type,
                "message": f"{emoji} Spending {direction} by {abs(spending_change):.0f}% vs last month (${abs(current_spending - previous_spending):.0f})",
            }
        )

    # 2. Spending Forecast
    if projected_monthly_spending > current_spending * 1.1:
        alerts.append(
            {
                "type": "info",
                "message": f"📊 On track to spend ${projected_monthly_spending:.0f} this month ({days_in_month - days_elapsed} days left)",
            }
        )

    # 3. Spending vs Income
    if current_spending > current_income * 0.8:
        alerts.append(
            {
                "type": "warning",
                "message": f"⚠️ You spent ${current_spending:.0f}, which is {(current_spending/current_income*100):.0f}% of your income",
            }
        )

    # 4. Savings Rate
    if current_savings_rate > 20:
        alerts.append(
            {
                "type": "success",
                "message": f"🎯 Great savings rate of {current_savings_rate:.0f}%!",
            }
        )
    elif current_savings_rate < 10:
        target_savings = current_income * 0.15  # 15% target
        need_to_save = target_savings - current_savings
        alerts.append(
            {
                "type": "warning",
                "message": f"💰 Save ${need_to_save:.0f} more to reach 15% savings rate (currently {current_savings_rate:.0f}%)",
            }
        )

    # 5. Actionable Recommendations (Top 3 categories)
    for i, (category, amount) in enumerate(top_categories):
        if amount > current_income * 0.15:  # If > 15% of income
            # Check trend
            prev_amount = prev_category_spending.get(category, 0)
            cat_change = (
                ((amount - prev_amount) / prev_amount * 100) if prev_amount > 0 else 0
            )

            # Calculate potential savings
            reduction_pct = 0.20  # 20% reduction
            potential_monthly = amount * reduction_pct
            potential_yearly = potential_monthly * 12

            priority = "high" if amount > current_income * 0.25 else "medium"

            # Include trend in suggestion
            trend_text = ""
            if abs(cat_change) > 10:
                trend_emoji = "📈" if cat_change > 0 else "📉"
                trend_text = f" ({trend_emoji} {abs(cat_change):.0f}% vs last month)"

            suggestions.append(
                {
                    "category": category,
                    "current_spending": float(amount),
                    "previous_spending": float(prev_amount),
                    "change_percent": float(cat_change),
                    "priority": priority,
                    "potential_monthly_savings": float(potential_monthly),
                    "potential_yearly_savings": float(potential_yearly),
                    "message": f"💡 Cut {category} by 20% to save ${potential_monthly:.0f}/month (${potential_yearly:.0f}/year){trend_text}",
                }
            )

    # 6. Category-specific insights
    for category, amount in top_categories[:1]:  # Top category only
        if amount > current_spending * 0.3:
            alerts.append(
                {
                    "type": "info",
                    "message": f"🔍 {category} is your largest expense at ${amount:.0f}",
                }
            )

    # Generate natural language summary
    if current_savings_rate > 20:
        tone = "You're doing great!"
    elif current_savings_rate > 10:
        tone = "You're on the right track."
    elif current_savings_rate > 0:
        tone = "There's room for improvement."
    else:
        tone = "You're spending more than you earn."

    top_cat_name = top_categories[0][0] if top_categories else "None"

    summary = f"{tone} Over the last 30 days, you earned ${current_income:.0f} and spent ${current_spending:.0f}, "
    summary += f"saving {current_savings_rate:.0f}% of your income. "

    if spending_change != 0:
        direction = "up" if spending_change > 0 else "down"
        summary += (
            f"Spending is {direction} {abs(spending_change):.0f}% from last month. "
        )

    summary += f"Your biggest expense was {top_cat_name}."

    # Financial health score (enhanced)
    health_score = min(
        100,
        max(
            0,
            int(
                (current_savings_rate * 2)  # Savings rate worth 40 points
                + (
                    30 if current_income > current_spending else 10
                )  # Income > expenses worth 30 points
                + (
                    20 if len(current_period) > 10 else len(current_period) * 2
                )  # Transaction tracking worth 20 points
                + (10 if spending_change < 0 else 0)  # Bonus for reducing spending
            ),
        ),
    )

    return {
        "user_id": user_id,
        "total_income": float(current_income),
        "total_spending": float(current_spending),
        "savings_rate": float(current_savings_rate),
        "health_score": int(health_score),
        "alerts": alerts,
        "suggestions": suggestions,
        "summary": summary,
        "top_category": {
            "name": top_cat_name,
            "amount": float(top_categories[0][1]) if top_categories else 0,
        },
        "category_breakdown": {k: float(v) for k, v in category_spending.items()},
        "trends": {
            "spending_change_percent": float(spending_change),
            "income_change_percent": float(income_change),
            "previous_spending": float(previous_spending),
            "previous_income": float(previous_income),
        },
        "forecast": {
            "projected_monthly_spending": float(projected_monthly_spending),
            "current_month_spending": float(month_spending),
            "days_elapsed": days_elapsed,
            "days_remaining": days_in_month - days_elapsed,
        },
        "generated_at": now.isoformat(),
    }


def save_insight(user_id: str, insight_data: Dict) -> str:
    """Save generated insight to DynamoDB"""
    insight_id = str(uuid.uuid4())

    # Convert floats to Decimals for DynamoDB recursively
    def convert_floats(obj):
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: convert_floats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_floats(item) for item in obj]
        else:
            return obj

    processed_data = convert_floats(insight_data)

    insights_table.put_item(
        Item={"user_id": user_id, "insight_id": insight_id, **processed_data}
    )
    return insight_id


# ===== ACCOUNT BALANCE FUNCTIONS =====


def set_account_balance(user_id: str, account: str, balance: float) -> bool:
    """Set the current balance for an account"""
    try:
        account_balances_table.put_item(
            Item={
                "user_id": user_id,
                "account_name": account,
                "current_balance": Decimal(str(balance)),
                "updated_at": datetime.utcnow().isoformat(),
            }
        )
        return True
    except Exception as e:
        print(f"Error setting account balance: {e}")
        return False


def get_account_balances(user_id: str) -> Dict[str, float]:
    """Get all account balances"""
    try:
        response = account_balances_table.query(
            KeyConditionExpression="user_id = :user_id",
            ExpressionAttributeValues={":user_id": user_id},
        )

        balances = {}
        for item in response.get("Items", []):
            balances[item["account_name"]] = float(item["current_balance"])

        return balances
    except Exception as e:
        print(f"Error getting account balances: {e}")
        return {}


def calculate_net_worth(user_id: str) -> Dict:
    """Calculate net worth (assets - liabilities)"""
    balances = get_account_balances(user_id)

    # Assets (bank accounts)
    assets = (
        balances.get("savings", 0) + balances.get("bills", 0) + balances.get("main", 0)
    )

    # Liabilities (credit card debt - shown as positive)
    liabilities = balances.get("credit", 0)

    # Net worth = Assets - Liabilities
    net_worth = assets - liabilities

    return {
        "net_worth": net_worth,
        "total_assets": assets,
        "total_liabilities": liabilities,
        "accounts": {
            "savings": balances.get("savings", 0),
            "bills": balances.get("bills", 0),
            "main": balances.get("main", 0),
            "credit": balances.get("credit", 0),
        },
    }


# ===== BALANCE SNAPSHOT FUNCTIONS =====


def save_balance_snapshot(
    user_id: str, snapshot_date: str, balances: Dict[str, float]
) -> bool:
    """
    Save a balance snapshot for a specific date.
    Used for month-end balance tracking.
    """
    try:
        total_assets = (
            balances.get("savings", 0)
            + balances.get("bills", 0)
            + balances.get("main", 0)
        )

        balance_snapshots_table.put_item(
            Item={
                "user_id": user_id,
                "snapshot_date": snapshot_date,
                "savings": Decimal(str(balances.get("savings", 0))),
                "bills": Decimal(str(balances.get("bills", 0))),
                "main": Decimal(str(balances.get("main", 0))),
                "credit": Decimal(str(balances.get("credit", 0))),
                "total_assets": Decimal(str(total_assets)),
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        return True
    except Exception as e:
        print(f"Error saving balance snapshot: {e}")
        return False


def get_balance_snapshot(user_id: str, snapshot_date: str) -> Dict:
    """Get balance snapshot for a specific date"""
    try:
        response = balance_snapshots_table.get_item(
            Key={"user_id": user_id, "snapshot_date": snapshot_date}
        )

        if "Item" in response:
            item = response["Item"]
            return {
                "snapshot_date": item["snapshot_date"],
                "savings": float(item["savings"]),
                "bills": float(item["bills"]),
                "main": float(item["main"]),
                "credit": float(item["credit"]),
                "total_assets": float(item["total_assets"]),
            }
        return None
    except Exception as e:
        print(f"Error getting balance snapshot: {e}")
        return None


def get_balance_snapshots(user_id: str, limit: int = 12) -> List[Dict]:
    """Get recent balance snapshots (last N months)"""
    try:
        response = balance_snapshots_table.query(
            KeyConditionExpression="user_id = :user_id",
            ExpressionAttributeValues={":user_id": user_id},
            ScanIndexForward=False,  # Sort descending (newest first)
            Limit=limit,
        )

        snapshots = []
        for item in response.get("Items", []):
            snapshots.append(
                {
                    "snapshot_date": item["snapshot_date"],
                    "savings": float(item["savings"]),
                    "bills": float(item["bills"]),
                    "main": float(item["main"]),
                    "credit": float(item["credit"]),
                    "total_assets": float(item["total_assets"]),
                }
            )

        return snapshots
    except Exception as e:
        print(f"Error getting balance snapshots: {e}")
        return []


def calculate_period_summary(user_id: str, start_date: str, end_date: str) -> Dict:
    """
    Calculate financial summary for a period using BOTH methods:
    1. Balance-based (from snapshots)
    2. Transaction-based (from transactions)
    """
    from datetime import datetime

    # Get balance snapshots
    start_snapshot = get_balance_snapshot(user_id, start_date)
    end_snapshot = get_balance_snapshot(user_id, end_date)

    # Get transactions in period
    # Include ALL accounts (savings, bills, main, credit) for transaction-based calculation
    transactions = get_transactions(user_id, limit=10000)

    # Categories to exclude from spending/income calculations
    excluded_categories = [
        "Transfers",
        "Payment",
        "Cash Withdrawal",
        "Credit Card Payments",
    ]

    period_transactions = [
        t
        for t in transactions
        if start_date
        <= t.get("date", "")[:10]
        <= end_date  # Extract date part only (YYYY-MM-DD)
        and t.get("category") not in excluded_categories
    ]

    # Calculate transaction-based (including credit card transactions)
    total_income = sum(
        float(t["amount"]) for t in period_transactions if float(t["amount"]) > 0
    )
    total_spending = sum(
        float(t["amount"]) for t in period_transactions if float(t["amount"]) < 0
    )
    transaction_savings = total_income + total_spending  # spending is negative

    # Calculate balance-based (if snapshots exist)
    balance_savings = None
    discrepancy = None
    if start_snapshot and end_snapshot:
        balance_savings = end_snapshot["total_assets"] - start_snapshot["total_assets"]
        discrepancy = balance_savings - transaction_savings

    # Calculate savings rate
    savings_rate = (transaction_savings / total_income * 100) if total_income > 0 else 0

    # Generate verification status
    if discrepancy is not None:
        if abs(discrepancy) < 10:
            status = "verified"
            status_message = "✅ Accounts balance perfectly!"
        elif abs(discrepancy) < 100:
            status = "minor_difference"
            status_message = f"⚠️ Small ${abs(discrepancy):.2f} difference - check for cash transactions"
        else:
            status = "needs_review"
            status_message = (
                f"⚠️ ${abs(discrepancy):.2f} unaccounted for - review transactions"
            )
    else:
        status = "no_snapshots"
        status_message = (
            "⚠️ No balance snapshots - enter start/end balances for verification"
        )

    return {
        "user_id": user_id,
        "period": {"start_date": start_date, "end_date": end_date},
        "balance_based": (
            {
                "starting_balance": (
                    start_snapshot["total_assets"] if start_snapshot else None
                ),
                "ending_balance": (
                    end_snapshot["total_assets"] if end_snapshot else None
                ),
                "savings": balance_savings,
            }
            if start_snapshot and end_snapshot
            else None
        ),
        "transaction_based": {
            "income": total_income,
            "spending": abs(total_spending),
            "net_savings": transaction_savings,
            "savings_rate": round(savings_rate, 1),
        },
        "verification": {
            "status": status,
            "message": status_message,
            "discrepancy": discrepancy,
        },
        "transaction_count": len(period_transactions),
    }


# ===== LEARNING SYSTEM FUNCTIONS =====


def save_learning_correction(
    user_id: str,
    description: str,
    original_category: str,
    corrected_category: str,
    amount: float,
    confidence: float,
) -> str:
    """
    Save a user correction to the learning database.

    Args:
        user_id: User ID
        description: Transaction description
        original_category: What the system classified it as
        corrected_category: What the user changed it to
        amount: Transaction amount
        confidence: Original confidence score

    Returns:
        learning_id: Unique ID for this learning entry
    """
    learning_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    # Extract keywords from description for pattern matching
    keywords = extract_keywords(description)

    learning_data_table.put_item(
        Item={
            "user_id": user_id,
            "learning_id": learning_id,
            "type": "correction",
            "description": description,
            "keywords": keywords,
            "original_category": original_category,
            "corrected_category": corrected_category,
            "amount": Decimal(str(amount)),
            "original_confidence": Decimal(str(confidence)),
            "timestamp": timestamp,
            "learned_at": timestamp,
        }
    )

    return learning_id


def get_learning_patterns(user_id: str, limit: int = 100) -> List[Dict]:
    """
    Get learning patterns for a user to improve classification.

    Args:
        user_id: User ID
        limit: Maximum number of patterns to return

    Returns:
        List of learning patterns
    """
    try:
        response = learning_data_table.query(
            KeyConditionExpression="user_id = :user_id",
            ExpressionAttributeValues={":user_id": user_id},
            ScanIndexForward=False,  # Most recent first
            Limit=limit,
        )

        return response.get("Items", [])
    except Exception as e:
        print(f"Error getting learning patterns: {e}")
        return []


def extract_keywords(description: str) -> List[str]:
    """
    Extract meaningful keywords from transaction description.

    Args:
        description: Transaction description

    Returns:
        List of keywords for pattern matching
    """
    import re

    # Clean and normalize
    text = description.lower().strip()

    # Remove common words that don't help classification
    stop_words = {
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "up",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "among",
        "under",
        "over",
        "around",
    }

    # Extract words (alphanumeric + some special chars)
    words = re.findall(r"\b[a-z0-9]+\b", text)

    # Filter out stop words and short words
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]

    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for word in keywords:
        if word not in seen:
            seen.add(word)
            unique_keywords.append(word)

    return unique_keywords[:10]  # Limit to 10 most relevant keywords


def apply_learning_to_classification(
    user_id: str, description: str, amount: float
) -> Optional[str]:
    """
    Apply learned patterns to improve classification.

    Args:
        user_id: User ID
        description: Transaction description
        amount: Transaction amount

    Returns:
        Learned category if pattern matches, None otherwise
    """
    try:
        # Get recent learning patterns
        patterns = get_learning_patterns(user_id, limit=50)

        if not patterns:
            return None

        # Extract keywords from current description
        current_keywords = extract_keywords(description)

        # Find matching patterns
        for pattern in patterns:
            if pattern.get("type") != "correction":
                continue

            pattern_keywords = pattern.get("keywords", [])
            corrected_category = pattern.get("corrected_category")

            # Check for keyword overlap
            overlap = set(current_keywords) & set(pattern_keywords)
            overlap_ratio = len(overlap) / max(len(current_keywords), 1)

            # If significant overlap, use the learned category
            if overlap_ratio >= 0.3:  # 30% keyword overlap
                print(
                    f"🧠 Learning applied: '{description}' → '{corrected_category}' (overlap: {overlap_ratio:.1%})"
                )
                return corrected_category

        return None

    except Exception as e:
        print(f"Error applying learning: {e}")
        return None


def get_learning_stats(user_id: str) -> Dict:
    """
    Get learning statistics for a user.

    Args:
        user_id: User ID

    Returns:
        Dictionary with learning statistics
    """
    try:
        patterns = get_learning_patterns(user_id, limit=1000)

        if not patterns:
            return {
                "total_corrections": 0,
                "categories_learned": {},
                "accuracy_improvement": 0,
                "recent_activity": [],
            }

        # Count corrections by category
        category_counts = {}
        recent_corrections = []

        for pattern in patterns:
            if pattern.get("type") == "correction":
                corrected_cat = pattern.get("corrected_category", "Unknown")
                category_counts[corrected_cat] = (
                    category_counts.get(corrected_cat, 0) + 1
                )

                # Recent activity (last 10)
                if len(recent_corrections) < 10:
                    recent_corrections.append(
                        {
                            "description": pattern.get("description", "")[:50],
                            "from": pattern.get("original_category", ""),
                            "to": corrected_cat,
                            "timestamp": pattern.get("timestamp", ""),
                        }
                    )

        return {
            "total_corrections": len(patterns),
            "categories_learned": category_counts,
            "accuracy_improvement": min(len(patterns) * 2, 50),  # Estimate improvement
            "recent_activity": recent_corrections,
        }

    except Exception as e:
        print(f"Error getting learning stats: {e}")
        return {"error": str(e)}


def scan_existing_transactions_for_learning(user_id: str, limit: int = 1000) -> Dict:
    """
    Scan existing transactions to learn patterns and create learning data.

    This analyzes your historical transactions to:
    1. Find common merchant patterns
    2. Extract category-to-description mappings
    3. Create learning entries for future classification

    Args:
        user_id: User ID
        limit: Maximum transactions to analyze

    Returns:
        Dictionary with scan results and learning statistics
    """
    try:
        # Get all transactions
        transactions = get_transactions(user_id, limit=limit)

        if not transactions:
            return {
                "status": "no_data",
                "message": "No transactions found to learn from",
                "patterns_created": 0,
            }

        # Analyze patterns
        patterns_created = 0
        merchant_patterns = {}
        category_patterns = {}

        for tx in transactions:
            description = tx.get("description", "").strip()
            category = tx.get("category", "").strip()
            amount = float(tx.get("amount", 0))

            if (
                not description
                or not category
                or category in ["Uncategorized", "Transfers"]
            ):
                continue

            # Extract keywords from description
            keywords = extract_keywords(description)
            if not keywords:
                continue

            # Build merchant patterns (same merchant → same category)
            merchant_key = description.lower().strip()
            if merchant_key not in merchant_patterns:
                merchant_patterns[merchant_key] = {
                    "category": category,
                    "count": 0,
                    "keywords": keywords,
                    "amounts": [],
                }

            merchant_patterns[merchant_key]["count"] += 1
            merchant_patterns[merchant_key]["amounts"].append(amount)

            # Build category patterns (keywords → category)
            for keyword in keywords:
                if keyword not in category_patterns:
                    category_patterns[keyword] = {}
                if category not in category_patterns[keyword]:
                    category_patterns[keyword][category] = 0
                category_patterns[keyword][category] += 1

        # Create learning entries for strong patterns
        for merchant, pattern in merchant_patterns.items():
            if pattern["count"] >= 2:  # At least 2 transactions with same merchant
                # Create a learning entry
                learning_id = str(uuid.uuid4())
                timestamp = datetime.utcnow().isoformat()

                # Calculate confidence based on consistency
                confidence = min(0.8, 0.5 + (pattern["count"] * 0.1))

                learning_data_table.put_item(
                    Item={
                        "user_id": user_id,
                        "learning_id": learning_id,
                        "type": "historical_pattern",
                        "description": merchant,
                        "keywords": pattern["keywords"],
                        "original_category": "Uncategorized",  # Assume it was unclassified
                        "corrected_category": pattern["category"],
                        "amount": Decimal(
                            str(sum(pattern["amounts"]) / len(pattern["amounts"]))
                        ),  # Average amount
                        "original_confidence": Decimal(str(confidence)),
                        "timestamp": timestamp,
                        "learned_at": timestamp,
                        "pattern_strength": pattern["count"],
                        "source": "historical_scan",
                    }
                )
                patterns_created += 1

        # Create category keyword patterns
        for keyword, categories in category_patterns.items():
            if len(categories) == 1:  # Keyword only maps to one category
                category = list(categories.keys())[0]
                count = list(categories.values())[0]

                if count >= 3:  # Strong keyword pattern
                    learning_id = str(uuid.uuid4())
                    timestamp = datetime.utcnow().isoformat()

                    learning_data_table.put_item(
                        Item={
                            "user_id": user_id,
                            "learning_id": learning_id,
                            "type": "keyword_pattern",
                            "description": f"Keyword: {keyword}",
                            "keywords": [keyword],
                            "original_category": "Uncategorized",
                            "corrected_category": category,
                            "amount": Decimal("0"),  # No specific amount
                            "original_confidence": Decimal("0.7"),
                            "timestamp": timestamp,
                            "learned_at": timestamp,
                            "pattern_strength": count,
                            "source": "keyword_scan",
                        }
                    )
                    patterns_created += 1

        return {
            "status": "success",
            "transactions_analyzed": len(transactions),
            "merchant_patterns": len(merchant_patterns),
            "keyword_patterns": len(category_patterns),
            "patterns_created": patterns_created,
            "top_merchants": sorted(
                [(k, v["count"]) for k, v in merchant_patterns.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:10],
            "top_keywords": sorted(
                [(k, sum(v.values())) for k, v in category_patterns.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:10],
        }

    except Exception as e:
        print(f"Error scanning transactions for learning: {e}")
        return {"error": str(e)}


def get_learning_scan_stats(user_id: str) -> Dict:
    """
    Get statistics about learning scan results.

    Args:
        user_id: User ID

    Returns:
        Dictionary with scan statistics
    """
    try:
        # Get all learning patterns
        patterns = get_learning_patterns(user_id, limit=1000)

        # Separate by source
        historical_patterns = [
            p for p in patterns if p.get("source") == "historical_scan"
        ]
        keyword_patterns = [p for p in patterns if p.get("source") == "keyword_scan"]
        user_corrections = [p for p in patterns if p.get("type") == "correction"]

        return {
            "total_patterns": len(patterns),
            "historical_patterns": len(historical_patterns),
            "keyword_patterns": len(keyword_patterns),
            "user_corrections": len(user_corrections),
            "learning_sources": {
                "historical_scan": len(historical_patterns),
                "keyword_scan": len(keyword_patterns),
                "user_corrections": len(user_corrections),
            },
        }

    except Exception as e:
        print(f"Error getting learning scan stats: {e}")
        return {"error": str(e)}
