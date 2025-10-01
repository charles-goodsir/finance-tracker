import os
import json
import csv
import io
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic import Field
from typing import List
from dotenv import load_dotenv
from backend.classifier import classify
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import requests

try:
    from backend.classifier import classify
except ImportError:
    from classifier import classify

if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    try:
        from backend.aws_db import (
            init_db,
            add_transaction,
            get_transactions,
            get_categories,
        )
    except ImportError:
        from aws_db import init_db, add_transaction, get_transactions, get_categories

    def get_conn():
        return None

else:
    try:
        from backend.db import init_db, get_conn
    except ImportError:
        from db import init_db, get_conn

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = FastAPI(title="Personal Finance Tracker (local)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class ClassifiedTx(BaseModel):
    user_id: str = "default"
    date: str
    amount: float
    category: str
    description: str = ""
    type: str = Field(default="expense")  # "income" | "expense"
    tags: str = ""
    frequency: str = "One-Off"


class BulkCommitIn(BaseModel):
    transactions: List[ClassifiedTx]


def send_telegram(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def serve_frontend():
    from fastapi.responses import FileResponse

    return FileResponse("frontend/index.html")


@app.post("/transactions")
def add_transaction_endpoint(tx: TransactionIn):
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        # Running on AWS - use DynamoDB
        transaction_id = add_transaction(
            tx.user_id,
            tx.amount,
            tx.category,
            tx.description,
            tx.type,
            tx.tags,
            tx.frequency,
        )
        text = f"Added transaction: {tx.user_id} {tx.amount} {tx.category} {tx.description}"
    else:
        # Running locally - use SQLite
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
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        # Running on AWS - use DynamoDB
        rows = get_transactions(user_id, limit)
    else:
        # Running locally - use SQLite
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
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        # Running on AWS - use DynamoDB
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        rows = get_transactions(user_id, limit=1000)  # Get more transactions for report

        # Filter by date
        filtered_rows = [r for r in rows if r.get("date", "") >= cutoff]

        total_income = sum(r["amount"] for r in filtered_rows if r["amount"] > 0)
        total_expense = sum(r["amount"] for r in filtered_rows if r["amount"] < 0)
    else:
        # Running locally - use SQLite
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM transactions WHERE user_id = ? AND date >= ?",
            (user_id, cutoff),
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        total_income = sum(r["amount"] for r in rows if r["amount"] > 0)
        total_expense = sum(r["amount"] for r in rows if r["amount"] < 0)

    return {
        "user_id": user_id,
        "days": days,
        "income": total_income,
        "expense": total_expense,
        "items": filtered_rows if os.getenv("AWS_LAMBDA_FUNCTION_NAME") else rows,
    }


@app.get("/categories")
def get_categories_endpoint():
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        # Running on AWS - use DynamoDB
        rows = get_categories()
    else:
        # Running locally - use SQLite
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
    date_format: str = "%Y-%m-%d",
):
    """
    Import transactions from CSV file.
    Expected CSV format: date,amount,description,category,tags
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    try:
        content = await file.read()
        csv_content = content.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(csv_content))

        imported_count = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):
            try:

                date_str = row.get("date", "").strip()
                amount = float(row.get("amount", 0))
                description = row.get("description", "").strip()
                category = row.get("category", "uncategorized").strip()
                tags = row.get("tags", "").strip()

                try:
                    parsed_date = datetime.strptime(date_str, date_format)
                except ValueError:

                    for fmt in [
                        "%Y-%m-%d",
                        "%m/%d/%Y",
                        "%d/%m/%Y",
                        "%Y-%m-%d %H:%M:%S",
                    ]:
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
                    (
                        user_id,
                        parsed_date.isoformat(),
                        amount,
                        category,
                        description,
                        tx_type,
                        tags,
                        "One-Off",
                    ),
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
            "message": f"Succefully imported {imported_count} transactions",
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
            "tags": "Comma-seperated tags (optional)",
        },
    }


@app.post("/import-csv-smart")
def import_csv_smart(file: UploadFile = File(...), user_id: str = "default"):
    try:
        content = file.file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))

        results = []
        summary = {
            "total": 0,
            "auto-classified": 0,
            "needs_review": 0,
            "categories": {},
        }

        for row in reader:
            desc = row.get("description") or row.get("Description") or ""
            amt = float(row.get("amount") or row.get("Amount") or 0)
            date = row.get("date") or row.get("Date") or datetime.utcnow().isoformat()

            cat, conf, reason = classify(desc, amt)
            tx = {
                "user_id": user_id,
                "date": date,
                "amount": amt,
                "description": desc,
                "category": cat,
                "type": "income" if amt > 0 else "expense",
                "frequency": "One-Off",
                "classification": {
                    "category": cat,
                    "confidence": conf,
                    "reason": reason,
                    "needs_review": conf < 0.7,
                },
            }
            results.append(tx)
            summary["total"] += 1
            summary["categories"][cat] = summary["categories"].get(cat, 0) + 1
            if conf < 0.7:
                summary["needs_review"] += 1
            else:
                summary["auto-classified"] += 1
        return {"status": "success", "summary": summary, "transactions": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")


@app.post("/transaction/commit-bulk")
def commit_bulk(body: BulkCommitIn):
    saved, failed = 0, []
    try:
        if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            from aws_db import add_transaction as aws_add

            for tx in body.transactions:
                try:
                    aws_add(
                        tx.user_id,
                        tx.amount,
                        tx.category,
                        tx.description,
                        tx.type,
                        tx.tags,
                        tx.frequency,
                    )
                    saved += 1
                except Exception as e:
                    failed.append({"tx": tx.model_dump(), "error": str(e)})
        else:
            conn = get_conn()
            cur = conn.cursor()
            for tx in body.transactions:
                try:
                    date = tx.date or datetime.utcnow().isoformat()
                    cur.execute(
                        "INSERT INTO transactions (user_id, date, amount, category, description, type, tags, frequency) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            tx.user_id,
                            date,
                            tx.amount,
                            tx.category,
                            tx.description,
                            tx.type,
                            tx.tags,
                            tx.frequency,
                        ),
                    )
                    saved += 1
                except Exception as e:
                    failed.append({"tx": tx.model_dump(), "error": str(e)})
            conn.commit()
            conn.close()
        return {
            "status": "ok",
            "saved": saved,
            "failed": failed,
            "total": len(body.transactions),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk commit failed: {str(e)}")


app.mount("/static", StaticFiles(directory="frontend"), name="static")
