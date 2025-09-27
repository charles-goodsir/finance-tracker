import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "finance.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT,
            description TEXT,
            frequency TEXT DEFAULT 'One-Off',
            type TEXT CHECK(type IN ('income', 'expense')),
            tags TEXT,
            start_date TEXT,
            end_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT CHECK(type IN ('income', 'expense', 'both')),
            color TEXT DEFAULT '#3B82F6',
            icon TEXT DEFAULT '💰'
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS recurring_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT,
            description TEXT,
            frequency TEXT NOT NULL CHECK(frequency IN ('daily', 'weekly', 'monthly', 'yearly')),
            type TEXT CHECK(type IN ('income', 'expense')),
            tags TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT,
            next_due_date TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    default_categories = [
        ("Food & Dining", "expense", "#EF4444", "🍽️"),
        ("Transportation", "expense", "#F59E0B", "🚗"),
        ("Shopping", "expense", "#8B5CF6", "🛍️"),
        ("Entertainment", "expense", "#EC4899", "🎬"),
        ("Bills & Utilities", "expense", "#10B981", "💡"),
        ("Healthcare", "expense", "#F97316", "🏥"),
        ("Travel", "expense", "#06B6D4", "✈️"),
        ("Salary", "income", "#22C55E", "💼"),
        ("Freelance", "income", "#84CC16", "💻"),
        ("Investment", "income", "#6366F1", "📈"),
    ]

    cur.executemany(
        "INSERT OR IGNORE INTO categories (name, type, color, icon) VALUES (?, ?, ?, ?)",
        default_categories,
    )

    conn.commit()
    conn.close()


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
