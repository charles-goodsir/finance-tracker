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

transactions_table = dynamodb.Table(TRANSACTIONS_TABLE)
categories_table = dynamodb.Table(CATEGORIES_TABLE)
recurring_table = dynamodb.Table(RECURRING_TABLE)


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
