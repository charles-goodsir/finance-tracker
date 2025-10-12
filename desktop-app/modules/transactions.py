from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .widgets import StyledTableWidget


class TransactionsModule:
    def __init__(self, parent_widget, db_manager, api_client=None):
        self.parent = parent_widget
        self.db = db_manager
        self.api = api_client
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.parent.setLayout(layout)

        # Title
        title = QLabel("💳 All Transactions")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; padding: 10px;")
        layout.addWidget(title)

        # Search and filter bar
        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            """
            QFrame {
                background-color: #2d3748;
                border: 2px solid #4a5568;
                border-radius: 8px;
                padding: 10px;
            }
        """
        )
        filter_layout = QHBoxLayout()
        filter_frame.setLayout(filter_layout)

        # Search box
        filter_layout.addWidget(QLabel("🔍 Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search transactions...")
        self.search_box.setStyleSheet(
            """
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """
        )
        self.search_box.textChanged.connect(self.filter_transactions)
        filter_layout.addWidget(self.search_box)

        # Category filter
        filter_layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItems(
            [
                "All Categories",
                "Groceries",
                "Dining Out",
                "Transportation",
                "Shopping",
                "Bills & Utilities",
            ]
        )
        self.category_filter.currentTextChanged.connect(self.filter_transactions)
        filter_layout.addWidget(self.category_filter)

        layout.addWidget(filter_frame)

        # Transactions table
        self.transactions_table = StyledTableWidget(
            ["Date", "Description", "Amount", "Category", "Account", "Type"]
        )
        layout.addWidget(self.transactions_table)

        # Buttons
        button_layout = QHBoxLayout()

        load_btn = QPushButton("📥 Load Transactions")
        load_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """
        )
        load_btn.clicked.connect(self.load_transactions)
        button_layout.addWidget(load_btn)

        self.sync_status_label = QLabel("✅ Ready")
        self.sync_status_label.setStyleSheet(
            "color: green; font-weight: bold; padding: 10px;"
        )
        button_layout.addWidget(self.sync_status_label)

        layout.addLayout(button_layout)

    def load_transactions(self):
        """Load transactions from AWS"""
        import requests
        
        try:
            # Load from AWS API instead of local DB
            if hasattr(self, 'api') and self.api:
                response = requests.get(
                    f"{self.api.aws_api_url}/transactions?user_id=user1&limit=500",
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    transactions = data.get('items', [])
                    self.display_transactions(transactions)
                    self.sync_status_label.setText(f"✅ Loaded {len(transactions)} transactions from AWS")
                else:
                    self.sync_status_label.setText(f"❌ Error loading from AWS")
            else:
                # Fallback to local DB if no API client
                transactions = self.db.get_local_transactions()
                self.display_transactions(transactions)
                self.sync_status_label.setText(f"✅ Loaded {len(transactions)} local transactions")
        except Exception as e:
            self.sync_status_label.setText(f"❌ Error: {str(e)}")
            print(f"Error loading transactions: {e}")

    def display_transactions(self, transactions):
        """Display transactions in the table"""
        self.transactions_table.setRowCount(len(transactions))

        for row, tx in enumerate(transactions):
            self.transactions_table.setItem(row, 0, QTableWidgetItem(tx["date"]))
            self.transactions_table.setItem(row, 1, QTableWidgetItem(tx["description"]))
            self.transactions_table.setItem(
                row, 2, QTableWidgetItem(f"${tx['amount']:.2f}")
            )
            self.transactions_table.setItem(row, 3, QTableWidgetItem(tx["category"]))
            self.transactions_table.setItem(
                row, 4, QTableWidgetItem(tx.get("account", "main"))
            )  # ADD THIS
            self.transactions_table.setItem(row, 5, QTableWidgetItem(tx["type"]))

    def filter_transactions(self):
        """Filter transactions based on search and category"""
        # This would implement filtering logic
        # For now, just reload all transactions
        self.load_transactions()
