import sqlite3
import requests
import threading
from datetime import datetime
from telegram_notifier import TelegramNotifier


class DatabaseManager:
    def __init__(self, aws_api_url):
        self.aws_api_url = aws_api_url
        self.local_conn = None
        self.ready = False
        self.telegram = TelegramNotifier()

    def setup_database(self):
        """Setup database in background thread - non-blocking"""

        def worker():
            try:
                self.local_conn = sqlite3.connect(
                    "finance_cache.db", check_same_thread=False, timeout=30.0
                )
                self.local_conn.execute("PRAGMA journal_mode=WAL")
                self.local_conn.execute("PRAGMA synchronous=NORMAL")
                self.local_conn.execute("PRAGMA cache_size=10000")

                cursor = self.local_conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        amount REAL,
                        description TEXT,
                        category TEXT,
                        type TEXT,
                        account TEXT,
                        synced INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Migration: Add account column if it doesn't exist
                try:
                    cursor.execute("SELECT account FROM transactions LIMIT 1")
                except sqlite3.OperationalError:
                    # Column doesn't exist, add it
                    print("Migrating database: adding account column...")
                    cursor.execute(
                        "ALTER TABLE transactions ADD COLUMN account TEXT DEFAULT 'main'"
                    )

                self.local_conn.commit()
                self.ready = True
                print("Database initialized successfully")
            except Exception as e:
                print(f"Database setup error: {e}")
                self.ready = False

        # Run in background thread
        threading.Thread(target=worker, daemon=True).start()
        return True  # Return immediately, don't wait

    def get_local_transactions(self):
        """Get transactions from local database"""
        if not self.ready or not self.local_conn:
            return []

        try:
            cursor = self.local_conn.cursor()
            cursor.execute(
                """
                SELECT date, description, amount, category, type, account 
                FROM transactions 
                ORDER BY date DESC
            """
            )

            transactions = []
            for row in cursor.fetchall():
                transactions.append(
                    {
                        "date": row[0],
                        "description": row[1],
                        "amount": row[2],
                        "category": row[3],
                        "type": row[4],
                        "account": row[5] if len(row) > 5 else "main",
                    }
                )
            return transactions
        except Exception as e:
            print(f"Database error: {e}")
            return []

    def save_transactions(self, transactions):
        """Save transactions to local database"""
        if not self.ready or not self.local_conn:
            return False

        try:
            cursor = self.local_conn.cursor()
            for tx in transactions:
                cursor.execute(
                    """
                    INSERT INTO transactions (date, amount, description, category, type, account, synced)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """,
                    (
                        tx["date"],
                        tx["amount"],
                        tx["description"],
                        tx["category"],
                        tx["type"],
                        tx.get("account", "main"),
                    ),
                )
            self.local_conn.commit()

            # Send Telegram notification for local save
            if transactions:
                self.telegram.notify_bulk_commit(len(transactions))

            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False
