import sqlite3
import requests
from datetime import datetime


class DatabaseManager:
    def __init__(self, aws_api_url):
        self.aws_api_url = aws_api_url
        self.local_conn = None

    def setup_database(self):
        """Setup local SQLite database"""
        try:
            self.local_conn = sqlite3.connect(
                "finance_cache.db", check_same_thread=False, timeout=30.0
            )
            self.local_conn.execute("PRAGMA journal_mode=WAL")
            self.local_conn.execute("PRAGMA synchronous=NORMAL")

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
                    synced INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            self.local_conn.commit()
            return True
        except Exception as e:
            print(f"Database setup error: {e}")
            return False

    def get_local_transactions(self):
        """Get transactions from local database"""
        if not self.local_conn:
            return []

        try:
            cursor = self.local_conn.cursor()
            cursor.execute(
                """
                SELECT date, description, amount, category, type 
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
                    }
                )
            return transactions
        except Exception as e:
            print(f"Database error: {e}")
            return []

    def save_transactions(self, transactions):
        """Save transactions to local database"""
        if not self.local_conn:
            return False

        try:
            cursor = self.local_conn.cursor()
            for tx in transactions:
                cursor.execute(
                    """
                    INSERT INTO transactions (date, amount, description, category, type, synced)
                    VALUES (?, ?, ?, ?, ?, 0)
                """,
                    (
                        tx["date"],
                        tx["amount"],
                        tx["description"],
                        tx["category"],
                        tx["type"],
                    ),
                )
            self.local_conn.commit()
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False
