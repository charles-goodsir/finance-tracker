import boto3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

dynamodb = boto3.resource('dynamodb')
transactions_table = dynamodb.Table('FinanceTracker-Transactions')
categories_table = dynamodb.Table('FinanceTracker-Categories')
recurring_table = dynamodb.Table('FinanceTracker-Recurring')



def init_db():
    """Initialize default categories in DynamoDB"""
    default_categories = [
        {
            'category_id': 'food-dining',
            'name': 'Food & Dining',
            'type': 'expense',
            'color': '#EF4444',
            'icon': '🍽️'
        },
        {
            'category_id': 'transportation',
            'name': 'Transportation',
            'type': 'expense',
            'color': '#F59E0B',
            'icon': '🚗'
        },
        {
            'category_id': 'salary',
            'name': 'Salary',
            'type': 'income',
            'color': '#22C55E',
            'icon': '🧳'
        }
    ]

    for category in default_categories:
        try:
            categories_table.put_item(
                Item=category,
                ConditionExpression='attribute_not_exists(category_id)'

            )
        except:
            pass
def add_transaction(user_id: str, amount: float, category: str, description:  str, tx_type: str = "expense", tags: str = "", frequency: str = "One-Off"):
    """Add a transaction to DynamoDB"""
    transaction_id = str(uuid.uuid4())
    item = {
        'user_id': user_id,
        'transaction_id': transaction_id,
        'date': datetime.utcnow().isoformat(),
        'amount': amount,
        'category': category,
        'description': description,
        'type': tx_type,
        'tags': tags,
        'frequency': frequency,
        'created_at': datetime.utcnow().isoformat()
    }
    
    transactions_table.put_item(Item=item)
    return transaction_id

def get_transactions(user_id: str, limit: int = 100) -> List[Dict]:
    """Get transactions for user"""
    response = transactions_table.query(
        KeyConditionExpression='user_id = :user_id',
        ScanIndexForward=False,
        Limit=limit,
        ExpressionAttributeValues={':user_id': user_id}
    )
    return response.get('Items', [])

def get_categories() -> List[Dict]:
    """Get all categories"""
    response = categories_table.scan()
    return response.get('Items', [])