import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import requests
import json
import threading
from datetime import datetime


class FinanceTrackerGUI:
    def __init__(self):
        print("Step 1: Creating root window...")
        self.root = tk.Tk()
        self.root.title("Finance Tracker 2.0 - Desktop")
        self.root.geometry("1000x700")

        print("Step 2: Setting variables...")
        self.aws_api_url = (
            "https://35kdl5sqm4.execute-api.ap-southeast-2.amazonaws.com/Prod"
        )
        self.sync_thread = None

        print("Step 3: Creating widgets...")
        self.create_widgets()
        print("Step 4: Widgets created, forcing UI update...")
        self.root.update()

        print("Step 5: Setting up database...")
        self.setup_database_pool()
        print("Step 6: Database setup complete")

        print("Step 7: App ready!")

        # Add this to ensure the UI is fully responsive
        self.root.after(100, self.test_ui_responsiveness)

    def test_ui_responsiveness(self):
        print("UI should be responsive now - can you click buttons?")

    def setup_database_pool(self):
        """Setup database connection with better performance"""
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
                synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            self.local_conn.commit()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Database setup error: {e}")

            self.local_conn = sqlite3.connect("finance_cache.db")

    def load_transactions(self):
        """Load from local cache first, then sync with AWS"""
        
        try:

            local_transactions = self.get_local_transactions()
            self.display_transactions(local_transactions)

            if hasattr(self, "sync_status_label") and self.sync_status_label:
                self.sync_status_label.config(text="Loading...", foreground="blue")

            if self.sync_thread is None or not self.sync_thread.is_alive():
                self.sync_thread = threading.Thread(
                    target=self.sync_with_aws, daemon=True
                )
                self.sync_thread.start()
        except Exception as e:
            print(f"Error loading transactions: {e}")
            if hasattr(self, "sync_status_label") and self.sync_status_label:
                self.sync_status_label.config(text=f"Error: {e}", foreground="red")

    def get_local_transactions(self):
        """Get transactions from local SQLite"""
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
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        except Exception as e:
            print(f"Unexcepted error: {e}")
            return []

    def sync_with_aws(self):
        """Background worker for AWS Sync"""
        try:
            self.root.after(0, lambda: self.update_sync_status("Syncing...."))

            response = requests.get(f"{self.aws_api_url}/transactions", timeout=10)
            if response.status_code == 200:
                aws_transactions = response.json()
                self._merge_transactions(aws_transactions)
                self._upload_local_changes()
                self.root.after(0, self.refresh_after_sync)
            else:
                self.root.after(
                    0,
                    lambda: self.update_sync_status(
                        f"Sync failed: {response.status_code}"
                    ),
                )
        except requests.exceptions.Timeout:
            self.root.after(
                0, lambda: self.update_sync_status(f"Sync timeout - check connection")
            )
        except Exception as e:
            self.root.after(0, lambda: self.update_sync_status(f"Sync Error: {e}"))

    def update_sync_status(self, message):
        if hasattr(self, "sync_status_label"):
            self.sync_status_label.config(text=message)

    def refresh_after_sync(self):
        """Refresh transactions after successful sync"""
        local_transactions = self.get_local_transactions()
        self.display_transactions(local_transactions)
        self.update_sync_status("Sync Complete")

    def _merge_transactions(self, aws_transactions):
        """Merge AWS transactions with local ones"""
        cursor = self.local_conn.cursor()

        cursor.execute("SELECT date, amount, description FROM transactions")

        existing = set()
        for row in cursor.fetchall():
            existing.add((row[0], row[1], row[2]))

        new_transactions = []
        for tx in aws_transactions:
            key = (tx["date"], tx["amount"], tx["description"])
            if key not in existing:
                new_transactions.append(
                    (
                        tx["date"],
                        tx["amount"],
                        tx["description"],
                        tx["category"],
                        tx["type"],
                        1,
                    )
                )
        if new_transactions:
            cursor.executemany(
                "INSERT INTO transactions (date, amount, description, category, type, synced) VALUES (?, ?, ?, ?, ?, ?)",
                new_transactions,
            )
            self.local_conn.commit()

    def _upload_local_changes(self):
        """Upload unsynced local transactions to AWS"""
        cursor = self.local_conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE synced = 0")

        unsynced = cursor.fetchall()
        if unsynced:
            transactions = []
            for row in unsynced:
                transactions.append(
                    {
                        "date": row[1],
                        "amount": row[2],
                        "description": row[3],
                        "category": row[4],
                        "type": row[5],
                    }
                )
            response = requests.post(
                f"{self.aws_api_url}/transactions/commit-bulk",
                json={"transactions": transactions},
            )

            if response.status_code == 200:
                cursor.execute("UPDATE transactions SET synced = 1")
                self.local_conn.commit()

    def create_widgets(self):
        print("Creating notebook...")
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        print("Notebook created")

        print("Creating dashboard frame...")
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        print("Dashboard frame created")

        print("Creating transactions frame...")
        self.transactions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.transactions_frame, text="Transactions")
        print("Transactions frame created")

        print("Creating CSV frame...")
        self.csv_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.csv_frame, text="CSV Import")
        print("CSV frame created")

        print("Setting up dashboard...")
        self.setup_dashboard()
        print("Dashboard setup complete")

        print("Setting up transactions...")
        self.setup_transactions()
        print("Transactions setup complete")

        print("Setting up CSV import...")
        self.setup_csv_import()
        print("CSV import setup complete")

    def setup_dashboard(self):
        ttk.Label(
            self.dashboard_frame, text="Finance Dashboard", font=("Arial", 16, "bold")
        ).pack(pady=10)

        summary_frame = ttk.LabelFrame(self.dashboard_frame, text="This Week")
        summary_frame.pack(fill="x", padx=10, pady=5)

        self.income_label = ttk.Label(summary_frame, text="Income: $0.00")
        self.income_label.pack(pady=5)

        self.expense_label = ttk.Label(summary_frame, text="Expenses: $0.00")
        self.expense_label.pack(pady=5)

        self.net_label = ttk.Label(summary_frame, text="Net: $0.00")
        self.net_label.pack(pady=5)

        ttk.Button(
            summary_frame, text="Refresh Dashboard", command=self.refresh_dashboard
        ).pack(pady=10)

    def setup_transactions(self):
        print("Creating transactions label...")
        ttk.Label(
            self.transactions_frame,
            text="Recent Transactions",
            font=("Arial", 14, "bold"),
        ).pack(pady=10)

        # Add the treeview back
        print("Creating treeview...")
        columns = ("Date", "Description", "Amount", "Category", "Type")
        self.transactions_tree = ttk.Treeview(
            self.transactions_frame, columns=columns, show="headings"
        )

        for col in columns:
            self.transactions_tree.heading(col, text=col)
            self.transactions_tree.column(col, width=120)

        self.transactions_tree.pack(fill="both", expand=True, padx=10, pady=5)
        print("Treeview created")

        print("Creating load button...")
        ttk.Button(
            self.transactions_frame,
            text="Load Transactions",
            command=lambda: self.load_transactions(),  # Keep the lambda fix
        ).pack(pady=10)

        print("Creating status label...")
        self.sync_status_label = ttk.Label(
            self.transactions_frame, text="Ready", foreground="green"
        )
        self.sync_status_label.pack(pady=5)
        print("Status label created")

    def setup_csv_import(self):
        ttk.Label(
            self.csv_frame, text="Smart CSV Import", font=("Arial", 14, "bold")
        ).pack(pady=10)

        file_frame = ttk.Frame(self.csv_frame)
        file_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(file_frame, text="CSV File").pack(side="left")
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=50).pack(
            side="left", padx=5
        )
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(
            side="left"
        )

        ttk.Button(
            self.csv_frame,
            text="Import with Smart Classification",
            command=self.import_csv_smart,
        ).pack(pady=20)

        self.results_text = tk.Text(self.csv_frame, height=15, width=80)
        self.results_text.pack(fill="both", expand=True, padx=10, pady=5)

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        self.file_path_var.set(filename)

    def import_csv_smart(self):
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showerror("Error", "Please select a file")
            return
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                data = {"user_id": "default"}

                response = requests.post(
                    f"{self.aws_api_url}/import-bank-csv", files=files, data=data
                )
                if response.status_code != 200:

                    f.seek(0)
                    response = requests.post(
                        f"{self.aws_api_url}/import-csv-smart", files=files, data=data
                    )

                if response.status_code == 200:
                    result = response.json()
                    self.display_import_results(result)
                else:
                    messagebox.showerror("Error", f"Import failed: {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Import error: {str(e)}")

    def display_import_results(self, result):
        self.results_text.delete(1.0, tk.END)

        summary = result["summary"]
        self.results_text.insert(tk.END, f"Import Results:\n")
        self.results_text.insert(tk.END, f"Total: {summary['total']}\n")
        self.results_text.insert(
            tk.END, f"Auto-classified: {summary['auto_classified']}\n"
        )
        self.results_text.insert(tk.END, f"Needs Review: {summary['needs_review']}\n\n")

        self.results_text.insert(tk.END, "Transactions:\n")
        for tx in result["transactions"]:
            self.results_text.insert(
                tk.END, f"{tx['description']} → {tx['category']} (${tx['amount']})\n"
            )

            if messagebox.askyesno(
                "Commit", "Do you want to commit these transactions?"
            ):
                self.commit_transactions(result["transactions"])

    def commit_transactions(self, transactions):
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

            response = requests.post(
                f"{self.aws_api_url}/transactions/commit-bulk",
                json={"transactions": transactions},
            )

            if response.status_code == 200:
                result = response.json()
                cursor.execute("UPDATE transactions SET synced = 1 WHERE synced = 0")
                self.local_conn.commit()
                messagebox.showinfo(
                    "Success", f"Committed {result['saved']} transactions!"
                )
                self.refresh_dashboard()
            else:
                messagebox.showerror("Error", f"Commit Failed: {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Commit error: {str(e)}")

    def display_transactions(self, transactions):
        """Display transactions in the treeview widget"""

        for item in self.transactions_tree.get_children():
            self.transactions_tree.delete(item)

        for tx in transactions:
            self.transactions_tree.insert(
                "",
                "end",
                values=(
                    tx["date"],
                    tx["description"],
                    f"${tx['amount']:.2f}",
                    tx["category"],
                    tx["type"],
                ),
            )

    def refresh_dashboard(self):
        self.load_transactions()

    def run(self):
        try:
            self.root.mainloop()
        finally:
            if hasattr(self, "local_conn"):
                self.local_conn.close()


if __name__ == "__main__":
    app = FinanceTrackerGUI()
    app.run()
