from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .widgets import StatCard, StyledTableWidget


class DashboardModule:
    def __init__(self, parent_widget, db_manager, api_client=None):
        self.parent = parent_widget
        self.db = db_manager
        self.api = api_client
        self.setup_ui()
        if self.api:
            self.load_net_worth()

    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        self.parent.setLayout(main_layout)

        # Header section
        header_frame = QFrame()
        header_frame.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5568, stop:1 #5a67d8);
                border-radius: 10px;
                margin: 5px;
            }
        """
        )
        header_layout = QVBoxLayout()
        header_frame.setLayout(header_layout)

        # Main title
        title = QLabel("💰 Finance Dashboard")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; padding: 20px;")
        header_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Track your financial health")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255,255,255,0.8); padding-bottom: 10px;")
        header_layout.addWidget(subtitle)

        main_layout.addWidget(header_frame)

        # Stats cards layout
        stats_layout = QHBoxLayout()

        # Income card
        self.income_card = StatCard("Income", "$0.00", "#4CAF50", "💰")
        stats_layout.addWidget(self.income_card)

        # Expenses card
        self.expense_card = StatCard("Expenses", "$0.00", "#F44336", "💸")
        stats_layout.addWidget(self.expense_card)

        # Net card
        self.net_card = StatCard("Net", "$0.00", "#2196F3", "📈")
        stats_layout.addWidget(self.net_card)

        main_layout.addLayout(stats_layout)

        # Recent transactions preview
        recent_frame = QGroupBox("📋 Recent Transactions")
        recent_frame.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 25px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 5px 5px 5px 5px;
            }
        """
        )
        recent_layout = QVBoxLayout()
        recent_frame.setLayout(recent_layout)

        # Recent transactions table
        self.recent_table = StyledTableWidget(
            ["Date", "Description", "Amount", "Category"]
        )
        self.recent_table.setMaximumHeight(200)
        recent_layout.addWidget(self.recent_table)

        main_layout.addWidget(recent_frame)

        # Action buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 Refresh Dashboard")
        refresh_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """
        )
        refresh_btn.clicked.connect(self.refresh_dashboard)
        button_layout.addWidget(refresh_btn)

        # Add spacer to push button to center
        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        # Add some spacing
        main_layout.addStretch()

    def refresh_dashboard(self):
        """Refresh dashboard data"""
        # Load transactions and update stats
        transactions = self.db.get_local_transactions()
        self.update_stats(transactions)
        self.update_recent_transactions(transactions)

    def update_stats(self, transactions):
        """Update the stat cards with transaction data"""
        income = sum(tx["amount"] for tx in transactions if tx["amount"] > 0)
        expenses = abs(sum(tx["amount"] for tx in transactions if tx["amount"] < 0))
        net = income - expenses

        self.income_card.update_value(f"${income:.2f}")
        self.expense_card.update_value(f"${expenses:.2f}")
        self.net_card.update_value(f"${net:.2f}")

        self.update_account_balances(transactions)

    def update_account_balances(self, transactions):
        """Calculate balances for each account"""
        from modules.accounts import ACCOUNT_TYPES

        balances = {account_id: 0 for account_id in ACCOUNT_TYPES.keys()}

        for tx in transactions:
            account = tx.get("account", "main")
            if account in balances:
                balances[account] += tx["amount"]

        # You can display these balances in the accounts module
        print(f"Account Balances: {balances}")

    def update_recent_transactions(self, transactions):
        """Update the recent transactions table"""
        # Show only last 5 transactions
        recent_transactions = transactions[:5]
        self.recent_table.setRowCount(len(recent_transactions))

        for row, tx in enumerate(recent_transactions):
            self.recent_table.setItem(row, 0, QTableWidgetItem(tx["date"]))
            self.recent_table.setItem(row, 1, QTableWidgetItem(tx["description"]))
            self.recent_table.setItem(row, 2, QTableWidgetItem(f"${tx['amount']:.2f}"))

    def load_net_worth(self):
        """Load and display net worth from AWS"""
        import requests

        if not self.api:
            return

        try:
            response = requests.get(
                f"{self.api.aws_api_url}/accounts/networth?user_id=user1", timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                print(f"💰 Net Worth: ${data['net_worth']:.2f}")
                print(f"📈 Assets: ${data['total_assets']:.2f}")
                print(f"📉 Liabilities: ${data['total_liabilities']:.2f}")
                print("Account Balances:")
                for account, balance in data["accounts"].items():
                    print(f"  {account}: ${balance:.2f}")

        except Exception as e:
            print(f"Error loading net worth: {e}")
