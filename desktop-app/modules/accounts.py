from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from .widgets import AccountCard
from .credit_card import CreditCardWidget
import requests
from datetime import datetime

ACCOUNT_TYPES = {
    "savings": {"name": "Savings Account", "color": "#4CAF50", "icon": "💰"},
    "bills": {"name": "Bills Account", "color": "#FF9800", "icon": "💳"},
    "main": {"name": "Main Account", "color": "#2196F3", "icon": "🏦"},
    "credit": {"name": "Credit Card", "color": "#F44336", "icon": "💳"},
}


class AccountsModule:
    def __init__(self, parent_widget, api_client=None):
        self.parent = parent_widget
        self.api = api_client
        self.balance_inputs = {}
        self.setup_ui()

    def setup_ui(self):
        # Wrap entire page in a scroll area to avoid squishing
        main_layout = QVBoxLayout()
        self.parent.setLayout(main_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content_widget = QWidget()
        layout = QVBoxLayout()
        content_widget.setLayout(layout)

        # Title
        title = QLabel("🏦 Account Management")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; padding: 10px;")
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "Set your current account balances to track net worth accurately"
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #a0aec0; padding: 5px; font-size: 13px;")
        layout.addWidget(instructions)

        # Account balance inputs
        for account_key, account_info in ACCOUNT_TYPES.items():
            card_frame = QFrame()
            card_frame.setStyleSheet(
                """
                QFrame {
                    background-color: #2d3748;
                    border: 2px solid #4a5568;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 5px;
                }
            """
            )

            card_layout = QHBoxLayout()
            card_frame.setLayout(card_layout)

            # Account icon and name
            account_label = QLabel(f"{account_info['icon']} {account_info['name']}")
            account_label.setStyleSheet(
                f"color: white; font-weight: bold; font-size: 14px;"
            )
            account_label.setMinimumWidth(150)  # Ensure minimum space for text
            card_layout.addWidget(account_label)

            card_layout.addStretch()

            # Balance input
            balance_input = QLineEdit()
            balance_input.setPlaceholderText("$0.00")
            balance_input.setFixedWidth(200)  # Fixed width so it doesn't shrink
            balance_input.setSizePolicy(
                QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
            )
            balance_input.setStyleSheet(
                """
                QLineEdit {
                    background-color: #4a5568;
                    color: white;
                    padding: 8px;
                    border: 1px solid #718096;
                    border-radius: 4px;
                    font-size: 13px;
                }
            """
            )
            card_layout.addWidget(balance_input)
            self.balance_inputs[account_key] = balance_input

            # Save button
            save_btn = QPushButton("Save")
            save_btn.setFixedWidth(100)
            save_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            save_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """
            )
            save_btn.clicked.connect(
                lambda checked, acc=account_key: self.save_balance(acc)
            )
            card_layout.addWidget(save_btn)

            layout.addWidget(card_frame)

        # ===== Credit Card Management Section =====
        layout.addSpacing(20)

        # Create credit card widget
        self.credit_card_widget = CreditCardWidget(self.api)
        layout.addWidget(self.credit_card_widget)

        # Connect button actions
        self.credit_card_widget.view_transactions_btn.clicked.connect(
            self.view_credit_transactions
        )
        self.credit_card_widget.payment_history_btn.clicked.connect(
            self.show_payment_history
        )

        # ===== NEW: Monthly Snapshot Section =====
        layout.addSpacing(20)

        snapshot_title = QLabel("📸 Monthly Balance Snapshots")
        snapshot_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        snapshot_title.setStyleSheet("color: white; padding: 10px;")
        layout.addWidget(snapshot_title)

        snapshot_instructions = QLabel(
            "Save snapshots at month-end to enable accurate savings tracking"
        )
        snapshot_instructions.setStyleSheet(
            "color: #a0aec0; padding: 5px; font-size: 13px;"
        )
        snapshot_instructions.setWordWrap(True)
        layout.addWidget(snapshot_instructions)

        # Snapshot control panel
        snapshot_panel = QFrame()
        snapshot_panel.setStyleSheet(
            """
            QFrame {
                background-color: #2d3748;
                border: 2px solid #4a5568;
                border-radius: 8px;
                padding: 15px;
            }
        """
        )
        snapshot_layout = QHBoxLayout()
        snapshot_panel.setLayout(snapshot_layout)

        # Date picker
        date_label = QLabel("📅 Snapshot Date:")
        date_label.setStyleSheet("color: white; font-weight: bold;")
        snapshot_layout.addWidget(date_label)

        self.snapshot_date = QDateEdit()
        self.snapshot_date.setCalendarPopup(True)
        self.snapshot_date.setDate(datetime.now().date())
        self.snapshot_date.setDisplayFormat("yyyy-MM-dd")
        self.snapshot_date.setStyleSheet(
            """
            QDateEdit {
                background-color: #4a5568;
                color: white;
                padding: 8px;
                border: 1px solid #718096;
                border-radius: 4px;
                font-size: 13px;
                min-width: 150px;
            }
        """
        )
        snapshot_layout.addWidget(self.snapshot_date)

        snapshot_layout.addStretch()

        # Save snapshot button
        save_snapshot_btn = QPushButton("💾 Save Monthly Snapshot")
        save_snapshot_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3b82f6;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """
        )
        save_snapshot_btn.clicked.connect(self.save_snapshot)
        snapshot_layout.addWidget(save_snapshot_btn)

        # Load snapshots button
        load_snapshots_btn = QPushButton("🔄 Load Snapshots")
        load_snapshots_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """
        )
        load_snapshots_btn.clicked.connect(self.load_snapshots)
        snapshot_layout.addWidget(load_snapshots_btn)

        layout.addWidget(snapshot_panel)

        # Snapshots table
        self.snapshots_table = QTableWidget()
        self.snapshots_table.setColumnCount(6)
        self.snapshots_table.setHorizontalHeaderLabels(
            ["Date", "Savings", "Bills", "Main", "Credit", "Total Assets"]
        )
        self.snapshots_table.setStyleSheet(
            """
            QTableWidget {
                background-color: #2d3748;
                color: white;
                border: 2px solid #4a5568;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #1a202c;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """
        )
        self.snapshots_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.snapshots_table)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            "color: #4CAF50; font-weight: bold; padding: 10px;"
        )
        layout.addWidget(self.status_label)

        # Finish scroll setup
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def save_balance(self, account):
        """Save individual account balance"""
        if not self.api:
            self.show_status("⚠️ API client not configured", "orange")
            return

        balance_input = self.balance_inputs[account]
        balance_text = balance_input.text().replace("$", "").replace(",", "").strip()

        if not balance_text:
            self.show_status("⚠️ Please enter a balance", "orange")
            return

        try:
            balance = float(balance_text)

            # Save to AWS
            response = requests.post(
                f"{self.api.aws_api_url}/accounts/balance",
                json={"user_id": "user1", "account": account, "balance": balance},
                timeout=10,
            )

            if response.status_code == 200:
                self.show_status(
                    f"✅ {ACCOUNT_TYPES[account]['name']} balance saved!", "#4CAF50"
                )
            else:
                self.show_status(f"❌ Failed to save: {response.text}", "#F44336")

        except ValueError:
            self.show_status("⚠️ Invalid balance amount", "orange")
        except Exception as e:
            self.show_status(f"❌ Error: {str(e)}", "#F44336")

    def save_snapshot(self):
        """Save monthly snapshot of all balances"""
        if not self.api:
            self.show_status("⚠️ API client not configured", "orange")
            return

        # Collect all balances
        balances = {}
        missing = []

        for account_key in ACCOUNT_TYPES.keys():
            balance_text = (
                self.balance_inputs[account_key]
                .text()
                .replace("$", "")
                .replace(",", "")
                .strip()
            )
            if balance_text:
                try:
                    balances[account_key] = float(balance_text)
                except ValueError:
                    missing.append(ACCOUNT_TYPES[account_key]["name"])
            else:
                missing.append(ACCOUNT_TYPES[account_key]["name"])

        if missing:
            self.show_status(f"⚠️ Missing balances: {', '.join(missing)}", "orange")
            return

        # Get selected date
        snapshot_date = self.snapshot_date.date().toString("yyyy-MM-dd")

        try:
            response = requests.post(
                f"{self.api.aws_api_url}/snapshots/balance",
                json={"user_id": "user1", "snapshot_date": snapshot_date, **balances},
                timeout=10,
            )

            if response.status_code == 200:
                self.show_status(f"✅ Snapshot saved for {snapshot_date}!", "#4CAF50")
                # Reload snapshots table
                QTimer.singleShot(500, self.load_snapshots)
            else:
                self.show_status(f"❌ Failed: {response.text}", "#F44336")

        except Exception as e:
            self.show_status(f"❌ Error: {str(e)}", "#F44336")

    def load_snapshots(self):
        """Load recent snapshots from AWS and update credit card widget"""
        if not self.api:
            return

        try:
            response = requests.get(
                f"{self.api.aws_api_url}/snapshots/list?user_id=user1&limit=12",
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                snapshots = data.get("snapshots", [])
                self.display_snapshots(snapshots)
                self.show_status(f"✅ Loaded {len(snapshots)} snapshots", "#4CAF50")

                # Also load credit card data
                if hasattr(self, "credit_card_widget"):
                    self.credit_card_widget.load_from_aws()
            else:
                self.show_status("⚠️ No snapshots found", "orange")

        except Exception as e:
            self.show_status(f"❌ Error loading: {str(e)}", "#F44336")

    def display_snapshots(self, snapshots):
        """Display snapshots in table"""
        self.snapshots_table.setRowCount(len(snapshots))

        for row, snapshot in enumerate(snapshots):
            self.snapshots_table.setItem(
                row, 0, QTableWidgetItem(snapshot["snapshot_date"])
            )
            self.snapshots_table.setItem(
                row, 1, QTableWidgetItem(f"${snapshot['savings']:.2f}")
            )
            self.snapshots_table.setItem(
                row, 2, QTableWidgetItem(f"${snapshot['bills']:.2f}")
            )
            self.snapshots_table.setItem(
                row, 3, QTableWidgetItem(f"${snapshot['main']:.2f}")
            )
            self.snapshots_table.setItem(
                row, 4, QTableWidgetItem(f"${snapshot['credit']:.2f}")
            )
            self.snapshots_table.setItem(
                row, 5, QTableWidgetItem(f"${snapshot['total_assets']:.2f}")
            )

    def show_status(self, message, color):
        """Show status message"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(
            f"color: {color}; font-weight: bold; padding: 10px;"
        )

    def view_credit_transactions(self):
        """Open Transactions tab filtered to credit card"""
        # This will be connected to switch to Transactions tab with credit filter
        self.credit_card_widget.show_status(
            "💳 Opening credit card transactions...", "#3b82f6"
        )
        # In a full implementation, this would emit a signal or call parent to switch tabs
        # For now, show a helpful message
        QTimer.singleShot(
            1500, lambda: self.credit_card_widget.show_status("", "white")
        )

    def show_payment_history(self):
        """Show credit card payment history"""
        if not self.api:
            self.credit_card_widget.show_status("⚠️ API not configured", "#f59e0b")
            return

        try:
            # Get transactions with "Credit Card Payments" category
            response = requests.get(
                f"{self.api.aws_api_url}/transactions?user_id=user1&limit=200",
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                transactions = data.get("items", [])

                # Filter for credit card payments
                payments = [
                    t
                    for t in transactions
                    if t.get("category") == "Credit Card Payments"
                ]

                # Sort by date descending
                payments.sort(key=lambda x: x.get("date", ""), reverse=True)

                # Show in a dialog
                self.display_payment_history_dialog(payments[:10])  # Last 10 payments
            else:
                self.credit_card_widget.show_status(
                    f"❌ Error: {response.status_code}", "#ef4444"
                )

        except Exception as e:
            self.credit_card_widget.show_status(f"❌ Error: {str(e)}", "#ef4444")
            print(f"Error loading payment history: {e}")

    def display_payment_history_dialog(self, payments):
        """Display payment history in a dialog"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("💰 Credit Card Payment History")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Title
        title = QLabel("Recent Credit Card Payments")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("padding: 10px;")
        layout.addWidget(title)

        # Table
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Date", "Amount", "Description"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setRowCount(len(payments))

        for row, payment in enumerate(payments):
            table.setItem(row, 0, QTableWidgetItem(payment.get("date", "")[:10]))
            table.setItem(row, 1, QTableWidgetItem(f"${payment.get('amount', 0):.2f}"))
            table.setItem(row, 2, QTableWidgetItem(payment.get("description", "")))

        layout.addWidget(table)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3b82f6;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """
        )
        layout.addWidget(close_btn)

        dialog.exec()
