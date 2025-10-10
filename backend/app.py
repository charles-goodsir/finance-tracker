import os
import json
import csv
import io
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic import Field
from typing import List
from dotenv import load_dotenv

try:
    from backend.classifier import classify
except ImportError:
    from classifier import classify

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


class GoalIn(BaseModel):
    user_id: str = "user1"
    goal_type: str  # "savings", "debt", "investment"
    name: str
    target_amount: float
    current_amount: float = 0.0


class GoalUpdateIn(BaseModel):
    current_amount: float


class TransactionIn(BaseModel):
    user_id: str = "user1"
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
    user_id: str = "user1"
    amount: float
    category: str = "uncategorized"
    description: str = ""
    frequency: str
    type: str = "expense"
    tags: str = ""
    start_date: str
    end_date: str | None = None


class ClassifiedTx(BaseModel):
    user_id: str = "user1"
    date: str
    amount: float
    category: str
    description: str = ""
    type: str = Field(default="expense")  # "income" | "expense"
    tags: str = ""
    frequency: str = "One-Off"
    account: str = "main"


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

    # Only serve frontend if it exists (for local development)
    if os.path.exists("frontend/index.html"):
        return FileResponse("frontend/index.html")
    else:
        # Return API info for AWS deployment
        return {
            "message": "Finance Tracker 2.0 API",
            "version": "2.0.0",
            "endpoints": {
                "transactions": "/transactions",
                "categories": "/categories",
                "report": "/report",
                "csv_import": "/import-csv-smart",
            },
        }


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
            desc = (
                row.get("Other Party")
                or row.get("description")
                or row.get("Description")
                or ""
            )
            amt = float(row.get("Amount") or row.get("amount") or 0)
            date = (
                row.get("Transaction Date")
                or row.get("date")
                or row.get("Date")
                or datetime.utcnow().isoformat()
            )

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


@app.post("/import-bank-csv")
def import_bank_csv(
    file: UploadFile = File(...),
    user_id: str = Form("user1"),
    account: str = Form("main"),
):
    """
    Import transactions from bank CSV format.
    Supports both:
    - Credit Card: Process Date,Amount,Other Party,Credit Plan Name,Transaction Date,Foreign Details,City,Country Code
    - Bank Account: Date,Amount,Other Party,Description,Reference,Particulars,Analysis Code
    """
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
            # Auto-detect format based on column names
            if "Transaction Date" in row:
                # Credit card format
                other_party = row.get("Other Party", "").strip()
                amount_str = row.get("Amount", "0").strip()
                transaction_date = row.get("Transaction Date", "").strip()
                description = other_party
            elif "Date" in row:
                # Bank account format
                other_party = row.get("Other Party", "").strip()
                amount_str = row.get("Amount", "0").strip()
                transaction_date = row.get("Date", "").strip()
                description = row.get("Description", other_party).strip()
            else:
                continue

            try:
                amount = float(amount_str)
            except ValueError:
                continue

            try:
                parsed_date = datetime.strptime(transaction_date, "%d/%m/%Y")
                date_iso = parsed_date.isoformat()
            except ValueError:

                for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"]:
                    try:
                        parsed_date = datetime.strptime(transaction_date, fmt)
                        date_iso = parsed_date.isoformat()
                        break
                    except ValueError:
                        continue
                else:
                    date_iso = datetime.utcnow().isoformat()
            
            # Use description for classification (more detailed than other_party)
            classify_text = description if description else other_party
            
            # ✅ CHECK FOR TRANSFERS FIRST (before classification)
            # Detects transfers between accounts (masked account numbers)
            is_transfer = (
                "payment received" in classify_text.lower() or
                "to ****" in other_party.lower() or
                "from ****" in other_party.lower() or
                "frm " in other_party.lower() and len(other_party) > 10 or  # "FRM" followed by account number
                ("online banking" in description.lower() and ("to " in other_party.lower() or "from " in other_party.lower())) or
                ("direct credit" in description.lower() and any(char.isdigit() for char in other_party))  # Direct credit with numbers
            )
            
            if is_transfer:
                # This is a transfer - don't classify, mark as transfer
                cat = "Transfers"
                conf = 0.95
                reason = "Transfer between accounts detected"
                tx_type = "transfer"
            else:
                # Not a transfer - classify normally
                cat, conf, reason = classify(classify_text, amount, use_ai=True)
                
                # Determine transaction type
                if amount > 0:
                    tx_type = "income"
                else:
                    tx_type = "expense"

            tx = {
                "user_id": user_id,
                "date": date_iso,
                "amount": amount,
                "description": f"{other_party} - {description}" if description and description != other_party else other_party,
                "category": cat,
                "type": tx_type,
                "frequency": "One-Off",
                "account": account,
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
        raise HTTPException(
            status_code=500, detail=f"Error processing bank CSV: {str(e)}"
        )


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
                        tx.account,  # ADD THIS LINE
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
                        "INSERT INTO transactions (user_id, date, amount, category, description, type, tags, frequency, account) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            tx.user_id,
                            date,
                            tx.amount,
                            tx.category,
                            tx.description,
                            tx.type,
                            tx.tags,
                            tx.frequency,
                            tx.account,
                        ),
                    )
                    saved += 1
                except Exception as e:
                    failed.append({"tx": tx.model_dump(), "error": str(e)})
            conn.commit()
            conn.close()

        if saved > 0:
            send_telegram(f"💰 Bulk commit: {saved} transactions saved successfully!")

        return {
            "status": "ok",
            "saved": saved,
            "failed": failed,
            "total": len(body.transactions),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk commit failed: {str(e)}")


# Only mount static files if frontend directory exists (for local development)
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

# ===== GOALS ENDPOINTS =====


@app.post("/goals")
def add_goal_endpoint(goal: GoalIn):
    """Add a new financial goal"""
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        from aws_db import add_goal

        goal_id = add_goal(
            goal.user_id,
            goal.goal_type,
            goal.name,
            goal.target_amount,
            goal.current_amount,
        )
        send_telegram(f"🎯 New goal created: {goal.name} - ${goal.target_amount}")
        return {"status": "ok", "goal_id": goal_id}
    else:
        raise HTTPException(status_code=501, detail="Goals only supported on AWS")


@app.get("/goals")
def list_goals(user_id: str = "user1"):
    """Get all goals for a user"""
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        from aws_db import get_goals

        goals = get_goals(user_id)
        return {"goals": goals}
    else:
        raise HTTPException(status_code=501, detail="Goals only supported on AWS")


@app.put("/goals/{goal_id}")
def update_goal(goal_id: str, update: GoalUpdateIn, user_id: str = "user1"):
    """Update goal progress"""
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        from aws_db import update_goal_progress

        success = update_goal_progress(user_id, goal_id, update.current_amount)
        if success:
            return {"status": "ok", "message": "Goal updated"}
        else:
            raise HTTPException(status_code=404, detail="Goal not found")
    else:
        raise HTTPException(status_code=501, detail="Goals only supported on AWS")


# ===== INSIGHTS ENDPOINTS =====


@app.get("/insights")
def get_insights_endpoint(user_id: str = "user1"):
    """Generate and return financial insights"""
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        from aws_db import generate_insights, save_insight

        # Generate fresh insights
        insights = generate_insights(user_id)

        # Save to database for history
        save_insight(user_id, insights)

        return insights
    else:
        raise HTTPException(status_code=501, detail="Insights only supported on AWS")


# ===== ACCOUNT BALANCE ENDPOINTS =====

class AccountBalanceIn(BaseModel):
    user_id: str = "user1"
    account: str  # "savings", "bills", "main", "credit"
    balance: float


@app.post("/accounts/balance")
def set_balance_endpoint(data: AccountBalanceIn):
    """Set account balance"""
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        from aws_db import set_account_balance
        
        success = set_account_balance(data.user_id, data.account, data.balance)
        if success:
            send_telegram(f"💰 Account balance updated: {data.account} = ${data.balance:.2f}")
            return {"status": "ok", "message": f"Balance set for {data.account}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to set balance")
    else:
        raise HTTPException(status_code=501, detail="Account balances only supported on AWS")


@app.get("/accounts/balances")
def get_balances_endpoint(user_id: str = "user1"):
    """Get all account balances"""
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        from aws_db import get_account_balances
        
        balances = get_account_balances(user_id)
        return {"balances": balances}
    else:
        raise HTTPException(status_code=501, detail="Account balances only supported on AWS")


@app.get("/accounts/networth")
def get_networth_endpoint(user_id: str = "user1"):
    """Calculate net worth"""
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        from aws_db import calculate_net_worth
        
        networth_data = calculate_net_worth(user_id)
        return networth_data
    else:
        raise HTTPException(status_code=501, detail="Net worth only supported on AWS")


# ===== AI CLASSIFICATION ENDPOINTS =====

@app.get("/ai/status")
def ai_status_endpoint():
    """Get AI classification status and availability"""
    try:
        from ai_classifier import get_ai_classifier
        classifier = get_ai_classifier()
        return classifier.get_status()
    except ImportError:
        return {
            "enabled": False,
            "provider": None,
            "model": None,
            "library_available": False,
            "api_key_configured": False,
            "error": "ai_classifier module not available"
        }


@app.post("/ai/classify")
def ai_classify_endpoint(description: str, amount: float):
    """Manually classify a transaction using AI (for testing)"""
    try:
        from ai_classifier import classify_with_ai
        
        category = classify_with_ai(description, amount)
        
        if category:
            return {
                "description": description,
                "amount": amount,
                "category": category,
                "method": "ai"
            }
        else:
            return {
                "description": description,
                "amount": amount,
                "category": "Other",
                "method": "fallback",
                "error": "AI classification failed"
            }
    except ImportError:
        raise HTTPException(status_code=501, detail="AI classifier not available")


# ===== BALANCE SNAPSHOT ENDPOINTS =====

class BalanceSnapshotIn(BaseModel):
    user_id: str = "user1"
    snapshot_date: str  # Format: YYYY-MM-DD
    savings: float = 0
    bills: float = 0
    main: float = 0
    credit: float = 0


@app.post("/snapshots/balance")
def save_snapshot_endpoint(data: BalanceSnapshotIn):
    """Save balance snapshot for a specific date"""
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        from aws_db import save_balance_snapshot
        
        balances = {
            'savings': data.savings,
            'bills': data.bills,
            'main': data.main,
            'credit': data.credit
        }
        
        success = save_balance_snapshot(data.user_id, data.snapshot_date, balances)
        
        if success:
            total_assets = data.savings + data.bills + data.main
            send_telegram(f"📸 Balance snapshot saved for {data.snapshot_date}\n💰 Total Assets: ${total_assets:.2f}")
            return {
                "status": "success",
                "message": f"Snapshot saved for {data.snapshot_date}",
                "total_assets": total_assets
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save snapshot")
    else:
        raise HTTPException(status_code=501, detail="Snapshots only supported on AWS")


@app.get("/snapshots/balance/{snapshot_date}")
def get_snapshot_endpoint(snapshot_date: str, user_id: str = "user1"):
    """Get balance snapshot for a specific date"""
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        from aws_db import get_balance_snapshot
        
        snapshot = get_balance_snapshot(user_id, snapshot_date)
        
        if snapshot:
            return snapshot
        else:
            raise HTTPException(status_code=404, detail=f"No snapshot found for {snapshot_date}")
    else:
        raise HTTPException(status_code=501, detail="Snapshots only supported on AWS")


@app.get("/snapshots/list")
def list_snapshots_endpoint(user_id: str = "user1", limit: int = 12):
    """Get recent balance snapshots"""
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        from aws_db import get_balance_snapshots
        
        snapshots = get_balance_snapshots(user_id, limit)
        return {"snapshots": snapshots, "count": len(snapshots)}
    else:
        raise HTTPException(status_code=501, detail="Snapshots only supported on AWS")


@app.get("/summary/period")
def period_summary_endpoint(
    user_id: str = "user1",
    start_date: str = None,
    end_date: str = None
):
    """
    Get comprehensive period summary with both balance-based and transaction-based calculations.
    Example: /summary/period?start_date=2024-09-01&end_date=2024-09-30
    """
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        from aws_db import calculate_period_summary
        
        if not start_date or not end_date:
            raise HTTPException(
                status_code=400,
                detail="Both start_date and end_date required (format: YYYY-MM-DD)"
            )
        
        summary = calculate_period_summary(user_id, start_date, end_date)
        return summary
    else:
        raise HTTPException(status_code=501, detail="Period summary only supported on AWS")
