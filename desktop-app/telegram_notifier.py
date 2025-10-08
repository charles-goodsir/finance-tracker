import requests
import os
from dotenv import load_dotenv


class TelegramNotifier:
    def __init__(self):
        load_dotenv()
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)

        if not self.enabled:
            print(
                "⚠️  Telegram notifications disabled - missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"
            )

    def send_message(self, text: str):
        """Send message to Telegram"""
        if not self.enabled:
            print(f"📱 Telegram (disabled): {text}")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            response = requests.post(
                url, data={"chat_id": self.chat_id, "text": text}, timeout=10
            )

            if response.status_code == 200:
                print(f"📱 Telegram sent: {text}")
                return True
            else:
                print(f"❌ Telegram failed: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False

    def notify_transaction_added(self, amount, category, description):
        """Notify when a transaction is added"""
        emoji = "💰" if amount > 0 else "💸"
        message = (
            f"{emoji} Transaction Added: ${amount:.2f} - {category} - {description}"
        )
        self.send_message(message)

    def notify_bulk_commit(self, saved_count):
        """Notify when transactions are committed in bulk"""
        message = f"💰 Bulk commit: {saved_count} transactions saved successfully!"
        self.send_message(message)

    def notify_csv_import(self, total, auto_classified):
        """Notify when CSV is imported"""
        message = (
            f"📊 CSV Import: {total} transactions, {auto_classified} auto-classified"
        )
        self.send_message(message)
