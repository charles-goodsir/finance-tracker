import requests
import threading
from telegram_notifier import TelegramNotifier


class APIClient:
    def __init__(self, aws_api_url):
        self.aws_api_url = aws_api_url
        self.telegram = TelegramNotifier()

    def import_csv(self, file_path, callback):
        """Import CSV file in background thread - non-blocking"""

        def worker():
            try:
                with open(file_path, "rb") as f:
                    files = {"file": f}
                    data = {"user_id": "default"}

                    response = requests.post(
                        f"{self.aws_api_url}/import-bank-csv",
                        files=files,
                        data=data,
                        timeout=30,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        # Send Telegram notification for CSV import
                        summary = result.get("summary", {})
                        self.telegram.notify_csv_import(
                            summary.get("total", 0), summary.get("auto-classified", 0)
                        )
                        callback(True, result)
                    else:
                        callback(False, f"Import failed: {response.text}")

            except Exception as e:
                callback(False, f"Import error: {str(e)}")

        # Run in background thread
        threading.Thread(target=worker, daemon=True).start()

    def commit_transactions(self, transactions, callback):
        """Commit transactions in background thread - non-blocking"""

        def worker():
            try:
                response = requests.post(
                    f"{self.aws_api_url}/transaction/commit-bulk",
                    json={"transactions": transactions},
                    timeout=30,
                )

                if response.status_code == 200:
                    result = response.json()
                    # Send Telegram notification for bulk commit
                    saved_count = result.get("saved", 0)
                    self.telegram.notify_bulk_commit(saved_count)
                    callback(True, result)
                else:
                    callback(False, f"Commit failed: {response.text}")

            except Exception as e:
                callback(False, f"Commit error: {str(e)}")

        # Run in background thread
        threading.Thread(target=worker, daemon=True).start()
