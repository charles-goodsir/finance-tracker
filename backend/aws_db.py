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
ACCOUNT_BALANCES_TABLE = os.environ.get("ACCOUNT_BALANCES_TABLE", "FinanceTracker-AccountBalances")


transactions_table = dynamodb.Table(TRANSACTIONS_TABLE)
categories_table = dynamodb.Table(CATEGORIES_TABLE)
recurring_table = dynamodb.Table(RECURRING_TABLE)
goals_table = dynamodb.Table(GOALS_TABLE)
insights_table = dynamodb.Table(INSIGHTS_TABLE)
account_balances_table = dynamodb.Table(ACCOUNT_BALANCES_TABLE)


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
    user_id, amount, category, description, tx_type, tags, frequency, account="main"
):
    """Add transaction to DynamoDB with account field"""
    import uuid
    from datetime import datetime
    from decimal import Decimal

    transaction_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    transactions_table.put_item(
        Item={
            "user_id": user_id,
            "transaction_id": transaction_id,
            "date": timestamp,
            "amount": Decimal(str(amount)),
            "category": category,
            "description": description,
            "type": tx_type,
            "tags": tags,
            "frequency": frequency,
            "account": account,  # ADD THIS LINE
            "created_at": timestamp,
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
    """Generate financial insights from transaction data"""
    from datetime import datetime, timedelta

    # Get transactions from last 30 days
    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
    transactions = get_transactions(user_id, limit=1000)
    recent_transactions = [
        t for t in transactions if t.get("date", "") >= thirty_days_ago
    ]

    # ✅ EXCLUDE TRANSFERS - only count actual spending/income
    actual_transactions = [t for t in recent_transactions if t.get('type') != 'transfer']

    # Calculate insights (on actual transactions only)
    total_spending = sum(
        float(t["amount"]) for t in actual_transactions if float(t["amount"]) < 0
    )
    total_income = sum(
        float(t["amount"]) for t in actual_transactions if float(t["amount"]) > 0
    )

    # Category breakdown (exclude transfers)
    category_spending = {}
    for t in actual_transactions:
        if float(t["amount"]) < 0:
            cat = t.get("category", "Uncategorized")
            category_spending[cat] = category_spending.get(cat, 0) + abs(
                float(t["amount"])
            )

    # Find top spending category
    top_category = (
        max(category_spending.items(), key=lambda x: x[1])
        if category_spending
        else ("None", 0)
    )

    # Generate alerts
    alerts = []
    if abs(total_spending) > total_income * 0.8:
        alerts.append(
            {
                "type": "warning",
                "message": f"⚠️ You spent ${abs(total_spending):.2f}, which is {(abs(total_spending)/total_income*100):.0f}% of your income",
            }
        )

    if top_category[1] > abs(total_spending) * 0.3:
        alerts.append(
            {
                "type": "info",
                "message": f"🍽️ {top_category[0]} is your largest expense at ${top_category[1]:.2f}",
            }
        )

    # Savings rate
    savings_rate = (
        ((total_income + total_spending) / total_income * 100)
        if total_income > 0
        else 0
    )

    if savings_rate > 20:
        alerts.append(
            {
                "type": "success",
                "message": f"🎯 Great job! Your savings rate is {savings_rate:.0f}%",
            }
        )
    elif savings_rate < 10:
        alerts.append(
            {
                "type": "warning",
                "message": f"💰 Try to save more! Current savings rate: {savings_rate:.0f}%",
            }
        )

    # Financial health score (0-100)
    health_score = min(
        100,
        max(
            0,
            (
                (savings_rate * 2)  # Savings rate worth 40%
                + (
                    30 if total_income > abs(total_spending) else 0
                )  # Income > expenses worth 30%
                + (
                    30 if len(actual_transactions) > 5 else len(actual_transactions) * 6
                )  # Transaction tracking worth 30%
            ),
        ),
    )

    return {
        "user_id": user_id,
        "total_income": float(total_income),
        "total_spending": float(abs(total_spending)),
        "savings_rate": float(savings_rate),
        "health_score": int(health_score),
        "alerts": alerts,
        "top_category": {"name": top_category[0], "amount": float(top_category[1])},
        "category_breakdown": {k: float(v) for k, v in category_spending.items()},
        "generated_at": datetime.utcnow().isoformat(),
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
                'user_id': user_id,
                'account_name': account,
                'current_balance': Decimal(str(balance)),
                'updated_at': datetime.utcnow().isoformat()
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
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        
        balances = {}
        for item in response.get('Items', []):
            balances[item['account_name']] = float(item['current_balance'])
        
        return balances
    except Exception as e:
        print(f"Error getting account balances: {e}")
        return {}


def calculate_net_worth(user_id: str) -> Dict:
    """Calculate net worth (assets - liabilities)"""
    balances = get_account_balances(user_id)
    
    # Assets (bank accounts)
    assets = (
        balances.get('savings', 0) +
        balances.get('bills', 0) +
        balances.get('main', 0)
    )
    
    # Liabilities (credit card debt - shown as positive)
    liabilities = balances.get('credit', 0)
    
    # Net worth = Assets - Liabilities
    net_worth = assets - liabilities
    
    return {
        'net_worth': net_worth,
        'total_assets': assets,
        'total_liabilities': liabilities,
        'accounts': {
            'savings': balances.get('savings', 0),
            'bills': balances.get('bills', 0),
            'main': balances.get('main', 0),
            'credit': balances.get('credit', 0)
        }
    }
