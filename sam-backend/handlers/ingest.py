import os, json, time, uuid
import boto3
from decimal import Decimal
from datetime import datetime

dynamodb = boto3
TABLE_NAME = os.environ.get("TRANSACTIONS_TABLE", "Transactions")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")
    user_id = body.get("user_id", "default")
    amount = float(body.get("amount", 0.0))
    category = body.get("category", "Uncategorized")
    description = body.get("description", "")
    date_iso = body.get("date") or datetime.utcnow().isoformat()

    item = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "date": date_iso,
        "date_ts": int(time.time()),
        "amount": Decimal(str(amount)),
        "category": category,
        "description": description,
    }

    table.put_item(Item=item)
    return {
        "status_code": 200,
        "body": json.dumps({"message": "saved", "item": item}, default=str),
    }
