import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from database import DatabaseManager
from api_client import APIClient


class FinanceTrackerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Finance Tracker 2.0")
        self.root.geometry("1000x700")

        # Initialize modules
        self.db = DatabaseManager(
            "https://35kdl5sqm4.execute-api.ap-southeast-2.amazonaws.com/Prod"
        )
        self.api = APIClient(
            "https://35kdl5sqm4.execute-api.ap-southeast-2.amazonaws.com/Prod"
        )

        self.create_widgets()
        self.setup_database()

    def create_widgets(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Dashboard tab
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.setup_dashboard()

        # Transactions tab
        self.transactions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.transactions_frame, text="Transactions")
        self.setup_transactions()

        # CSV Import tab
        self.csv_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.csv_frame, text="CSV Import")
        self.setup_csv_import()

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
        ttk.Label(
            self.transactions_frame,
            text="Recent Transactions",
            font=("Arial", 14, "bold"),
        ).pack(pady=10)

        columns = ("Date", "Description", "Amount", "Category", "Type")
        self.transactions_tree = ttk.Treeview(
            self.transactions_frame, columns=columns, show="headings"
        )

        for col in columns:
            self.transactions_tree.heading(col, text=col)
            self.transactions_tree.column(col, width=120)

        self.transactions_tree.pack(fill="both", expand=True, padx=10, pady=5)

        ttk.Button(
            self.transactions_frame,
            text="Load Transactions",
            command=self.load_transactions,
        ).pack(pady=10)

        self.sync_status_label = ttk.Label(
            self.transactions_frame, text="Ready", foreground="green"
        )
        self.sync_status_label.pack(pady=5)

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

        self.import_button = ttk.Button(
            self.csv_frame,
            text="Import with Smart Classification",
            command=self.import_csv,
        )
        self.import_button.pack(pady=20)

        self.results_text = tk.Text(self.csv_frame, height=15, width=80)
        self.results_text.pack(fill="both", expand=True, padx=10, pady=5)

    def setup_database(self):
        if self.db.setup_database():
            self.sync_status_label.config(text="Database Ready", foreground="green")
        else:
            self.sync_status_label.config(text="Database Error", foreground="red")

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if filename:
            self.file_path_var.set(filename)
            self.sync_status_label.config(text="File selected", foreground="green")

    def import_csv(self):
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showerror("Error", "Please select a file")
            return

        self.import_button.config(state="disabled")
        self.sync_status_label.config(text="Uploading...", foreground="blue")

        self.api.import_csv(file_path, self.on_import_complete)

    def on_import_complete(self, success, result):
        if success:
            self.show_import_results(result)
        else:
            messagebox.showerror("Error", result)

        self.import_button.config(state="normal")
        self.sync_status_label.config(text="Ready", foreground="green")

    def show_import_results(self, result):
        self.results_text.delete(1.0, tk.END)

        summary = result["summary"]
        self.results_text.insert(tk.END, f"Import Results:\n")
        self.results_text.insert(tk.END, f"Total: {summary['total']}\n")
        self.results_text.insert(
            tk.END, f"Auto-classified: {summary['auto-classified']}\n"
        )
        self.results_text.insert(tk.END, f"Needs Review: {summary['needs_review']}\n\n")

        self.results_text.insert(tk.END, "Transactions:\n")
        for tx in result["transactions"]:
            self.results_text.insert(
                tk.END, f"{tx['description']} → {tx['category']} (${tx['amount']})\n"
            )

        self.pending_transactions = result["transactions"]

        if not hasattr(self, "commit_button"):
            self.commit_button = ttk.Button(
                self.csv_frame,
                text="Commit Transactions",
                command=self.commit_transactions,
            )
            self.commit_button.pack(pady=10)

    def commit_transactions(self):
        if hasattr(self, "pending_transactions"):
            self.api.commit_transactions(
                self.pending_transactions, self.on_commit_complete
            )

    def on_commit_complete(self, success, result):
        if success:
            messagebox.showinfo("Success", f"Committed {result['saved']} transactions!")
            self.db.save_transactions(self.pending_transactions)
            if hasattr(self, "commit_button"):
                self.commit_button.pack_forget()
        else:
            messagebox.showerror("Error", result)

    def load_transactions(self):
        transactions = self.db.get_local_transactions()
        self.display_transactions(transactions)

    def display_transactions(self, transactions):
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
        self.root.mainloop()


if __name__ == "__main__":
    app = FinanceTrackerGUI()
    app.run()
