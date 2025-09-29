import json
import boto3
import os
import uuid
import requests
from datetime import datetime, timedelta
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource("dynamodb")
recurring_table = dynamodb.Table(os.environ["RECURRING_TABLE"])
transactions_table = dynamodb.Table(os.environ["TRANSACTIONS_TABLE"])


def lambda_handler(event, context):
    """
    Process recurring transactions and create new transactions
    """
    try:
        # Get all active recurring transactions
        response = recurring_table.scan(
            FilterExpression="is_active = :active",
            ExpressionAttributeValues={":active": True},
        )

        recurring_transactions = response.get("Items", [])
        processed_count = 0

        for recurring in recurring_transactions:
            if should_process_recurring(recurring):
                # Create new transaction
                create_transaction_from_recurring(recurring)

                # Update next due date
                update_next_due_date(recurring)

                processed_count += 1

        # Send summary notification
        if processed_count > 0:
            send_telegram_notification(
                f"🤖 *Recurring Transactions Processed*\n\nProcessed {processed_count} recurring transactions today!"
            )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Processed {processed_count} recurring transactions",
                    "processed_count": processed_count,
                }
            ),
        }

    except Exception as e:
        print(f"Error processing recurring transactions: {str(e)}")
        send_telegram_notification(
            f"❌ *Error Processing Recurring Transactions*\n\n{str(e)}"
        )
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def should_process_recurring(recurring):
    """Check if a recurring transaction should be processed today"""
    next_due_date = datetime.fromisoformat(recurring["next_due_date"])
    today = datetime.utcnow().date()

    # Check if it's due today or overdue
    return next_due_date.date() <= today


def create_transaction_from_recurring(recurring):
    """Create a new transaction from a recurring transaction"""
    transaction_id = str(uuid.uuid4())

    transaction = {
        "user_id": recurring["user_id"],
        "transaction_id": transaction_id,
        "date": datetime.utcnow().isoformat(),
        "amount": recurring["amount"],
        "category": recurring["category"],
        "description": recurring["description"],
        "type": recurring["type"],
        "tags": recurring.get("tags", ""),
        "frequency": "One-Off",  # Mark as one-off since it's now a real transaction
        "created_at": datetime.utcnow().isoformat(),
        "source": "recurring",  # Track that this came from recurring
        "recurring_id": recurring["recurring_id"],
    }

    transactions_table.put_item(Item=transaction)

    # Send Telegram notification
    emoji = "💰" if recurring["type"] == "income" else "💸"
    message = f"{emoji} *Recurring Transaction Processed*\n\n"
    message += f"*{recurring['description']}*\n"
    message += f"Amount: ${abs(recurring['amount']):.2f}\n"
    message += f"Category: {recurring['category']}\n"
    message += f"Frequency: {recurring['frequency']}"

    send_telegram_notification(message)
    print(f"Created transaction for recurring: {recurring['description']}")


def update_next_due_date(recurring):
    """Update the next due date based on frequency"""
    current_due = datetime.fromisoformat(recurring["next_due_date"])
    frequency = recurring["frequency"]

    if frequency == "daily":
        next_due = current_due + timedelta(days=1)
    elif frequency == "weekly":
        next_due = current_due + timedelta(weeks=1)
    elif frequency == "monthly":
        # Add one month (approximate)
        next_due = current_due + timedelta(days=30)
    elif frequency == "yearly":
        next_due = current_due + timedelta(days=365)
    else:
        next_due = current_due + timedelta(days=30)  # Default to monthly

    # Check if we've passed the end date
    if recurring.get("end_date"):
        end_date = datetime.fromisoformat(recurring["end_date"])
        if next_due > end_date:
            # Deactivate this recurring transaction
            recurring_table.update_item(
                Key={
                    "user_id": recurring["user_id"],
                    "recurring_id": recurring["recurring_id"],
                },
                UpdateExpression="SET is_active = :inactive",
                ExpressionAttributeValues={":inactive": False},
            )
            send_telegram_notification(
                f"⏹️ *Recurring Transaction Ended*\n\n{recurring['description']} has reached its end date and has been deactivated."
            )
            print(f"Deactivated recurring transaction: {recurring['description']}")
            return

    # Update next due date
    recurring_table.update_item(
        Key={
            "user_id": recurring["user_id"],
            "recurring_id": recurring["recurring_id"],
        },
        UpdateExpression="SET next_due_date = :next_due",
        ExpressionAttributeValues={":next_due": next_due.isoformat()},
    )
    print(f"Updated next due date for: {recurring['description']}")


def send_telegram_notification(message: str):
    """Send notification to Telegram"""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("Telegram credentials not configured")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        requests.post(
            url, data={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        )
    except Exception as e:
        print(f"Failed to send Telegram notification: {e}")
