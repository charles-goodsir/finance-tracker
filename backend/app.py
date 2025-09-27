import os
import json
import csv
import io
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
import requests

from backend.db import init_db, get_conn

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = FastAPI(title="Personal Finance Tracker (local)")


class TransactionIn(BaseModel):
    user_id: str = "default"
    date: str | None = None
    amount: float
    category: str = "uncategorized"
    description: str = ""
    type: str = "expense" 
    tags: str = ""
    frequency: str = "One-Off"
    start_date: str | None = None
    end_date: str | None = None


class RecurringTransactionsIn(BaseModel):
    user_id: str = "default"
    amount: float
    category: str = "uncategorized"
    description: str = ""
    frequency: str
    type: str = "expense"
    tags: str = ""
    start_date: str
    end_date: str | None = None


def send_telegram(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})


@app.on_event("startup")
def startup():
    init_db()


@app.post("/transactions")
def add_transaction(tx: TransactionIn):
    date = tx.date or datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions (user_id, date, amount, category, description) VALUES (?, ?, ?, ?, ?)",
        (tx.user_id, date, tx.amount, tx.category, tx.description),
    )
    conn.commit()
    conn.close()

    text = f"Added transaction: {tx.user_id} {tx.amount} {tx.category} {tx.description}"
    send_telegram(text)
    return {"status": "ok", "message": text}


@app.get("/transactions")
def list_transactions(user_id: str = "default", limit: int = 100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT ?",
        (user_id, limit),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"items": rows}


@app.get("/report")
def report(user_id: str = "default", days: int = 7):
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM transactions WHERE user_id = ? AND date >= ?", (user_id, cutoff)
    )
    rows = [dict(r) for r in cur.fetchall()]
    total_income = sum(r["amount"] for r in rows if r["amount"] > 0)
    total_expense = sum(r["amount"] for r in rows if r["amount"] < 0)
    return {
        "user_id": user_id,
        "days": days,
        "income": total_income,
        "expense": total_expense,
        "items": rows,
    }


@app.get("/categories")
def get_categories():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories ORDER BY type, name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"categories": rows}


@app.post("/recurring-transactions")
def add_recurring_transaction(rt: RecurringTransactionsIn):
    from datetime import datetime, timedelta

    start_date = datetime.fromisoformat(rt.start_date)

    if rt.frequency == "daily":
        next_due = start_date + timedelta(days=1)
    elif rt.frequency == "weekly":
        next_due = start_date + timedelta(weeks=1)
    elif rt.frequency == "monthly":
        next_due = start_date + timedelta(days=30)
    elif rt.frequency == "yearly":
        next_due = start_date + timedelta(days=365)
    else:
        next_due = start_date

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO recurring_transactions
        (user_id, amount, category, description, frequency, type, tags, start_date, end_date, next_due_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            rt.user_id,
            rt.amount,
            rt.category,
            rt.description,
            rt.frequency,
            rt.type,
            rt.tags,
            rt.start_date,
            rt.end_date,
            next_due.isoformat(),
        ),
    )
    conn.commit()
    conn.close()

    return {"status": "ok", "message": f"Added recurring {rt.frequency} transaction"}


@app.get("/recurring-transactions")
def list_recurring_transactions(user_id: str = "default"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM recurring_transactions WHERE user_id = ? and is_active = 1",
        (user_id,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"recurring_transactions": rows}

@app.post("/import/csv")
async def import_csv_transactions(
    file: UploadFile = File(...),
    user_id: str = "default",
    date_format: str = "%Y-%m-%d"
):
    """
    Import transactions from CSV file.
    Expected CSV format: date,amount,description,category,tags
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))

        imported_count = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):
            try:

                date_str = row.get('date', '').strip()
                amount = float(row.get('amount', 0))
                description = row.get('description', '').strip()
                category = row.get('category', 'uncategorized').strip()
                tags = row.get('tags', '').strip()


                try:
                    parsed_date = datetime.strptime(date_str, date_format)
                except ValueError:

                    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        raise ValueError(f"Unable to parse date: {date_str}")
                tx_type = "income" if amount > 0 else "expense"

                conn = get_conn()
                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO transactions
                        (user_id, date, amount, category, description, type, tags, frequency)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, parsed_date.isoformat(), amount, category, description, tx_type, tags, "One-Off")
                )
                conn.commit()
                conn.close()

                imported_count += 1
            
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        return {
            "status": "ok",
            "imported_count": imported_count,
            "errors": errors,
            "message": f"Succefully imported {imported_count} transactions"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
    
@app.get("/import/template")
def get_csv_template():
    """Get a CSV template for importing transactions"""
    template = "date,amount,description,category,tags\n"
    template += "2024-01-15,-25.50,Coffe shop,Food & Dining,coffee work\n"
    template += "2024-01-16,1200.00,Salary,Salary,Income\n"
    template += "2024-01-17,-89.99,Groceries,Food & Dining,groceries\n"

    return {
        "template": template,
        "format": {
            "date": "YYYY-MM-DD format",
            "amount": "Positive for income, negative for expenses",
            "description": "Transaction description",
            "category": "Category name (will be created if doesn't exist)",
            "tags": "Comma-seperated tags (optional)"

        }
    }
