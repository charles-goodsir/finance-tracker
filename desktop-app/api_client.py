import requests
import threading


class APIClient:
    def __init__(self, aws_api_url):
        self.aws_api_url = aws_api_url

    def import_csv(self, file_path, callback):
        """Import CSV file in background thread"""

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
                        callback(True, result)
                    else:
                        callback(False, f"Import failed: {response.text}")

            except Exception as e:
                callback(False, f"Import error: {str(e)}")

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def commit_transactions(self, transactions, callback):
        """Commit transactions to AWS"""

        def worker():
            try:
                response = requests.post(
                    f"{self.aws_api_url}/transactions/commit-bulk",
                    json={"transactions": transactions},
                )

                if response.status_code == 200:
                    result = response.json()
                    callback(True, result)
                else:
                    callback(False, f"Commit failed: {response.text}")

            except Exception as e:
                callback(False, f"Commit error: {str(e)}")

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
