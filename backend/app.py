import os
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import requests

from .db import init_db, get_conn

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = FastAPI(title="Personal Finance Tracker (local)")


class TransactionIn(BaseModel):
    user_id: str = "defauly"
    date: str = None
    amount: float
    category: str = "uncategorized"
    description: str = ""


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
