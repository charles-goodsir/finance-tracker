import os
import requests
from datetime import datetime


def lambda_handler(event, context):
    """
    Sends a monthly reminder on the 10th to track finances.
    Triggered by EventBridge schedule.
    """

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("Telegram credentials not configured")
        return {"statusCode": 200, "body": "No Telegram configred"}

    current_month = datetime.now().strftime("%B %Y")
    day = datetime.now().day

    message = f"""
🔔 *Monthly Finance Tracking Reminder*

📅 Today is the {day}th - Time to update your finances!

*Your Checklist:*
1. ✅ Check all bank account balances
2. 💾 Save balance snapshot in the app
3. 📥 Download last month's CSV statements
4. 📤 Import & commit transactions
5. 📊 Calculate last month's savings

*Period:* Previous month to today
*Next reminder:* Next month on the 10th

💡 Taking 10 minutes now will give you complete financial clarity!

Open your Finance Tracker app to get started 🚀
    """

    url = "https://api.telegram.org/bot{bot_token}/sendMessage"

    try:
        response = requests.post(
            url,
            data={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10,
        )

        if response.status_code == 200:
            print("✅ Sent monthly reminder for {current_month}")
            return {"status_Code": 200, "body": f"Reminder sent for {current_month}"}
        else:
            print(f"❌ Failed to send: {response.text}")
            return {"status_Code": 500, "body": f"Failed: {response.text}"}
    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500, "body": str(e)}
